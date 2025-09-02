/**
 * Order Consistency Validation for Odoo Ingestion
 * Validates purchase order data integrity and business logic
 */

import { BaseValidator } from '../utils/base-validator.js';
import { SchemaValidator } from '../utils/schema-validator.js';
import chalk from 'chalk';

export class OrderValidator extends BaseValidator {
  constructor(options = {}) {
    super({
      strictMode: true,
      allowMissingFields: false,
      ...options
    });
    
    this.schemaValidator = new SchemaValidator();
    this.requiredFields = ['partner_id', 'date_order', 'order_line'];
    this.businessRules = this.initializeBusinessRules();
  }

  initializeBusinessRules() {
    return [
      {
        name: 'order_total_validation',
        description: 'Order total should match sum of line items',
        validate: (order) => {
          if (order.order_line && order.order_line.length > 0) {
            const calculatedTotal = order.order_line.reduce((sum, line) => {
              const lineTotal = (line.product_qty || 0) * (line.price_unit || 0);
              return sum + lineTotal;
            }, 0);
            
            const declaredTotal = order.amount_untaxed || order.amount_total;
            
            if (declaredTotal && Math.abs(calculatedTotal - declaredTotal) > 0.01) {
              return {
                valid: false,
                message: `Order total mismatch. Calculated: ${calculatedTotal.toFixed(2)}, Declared: ${declaredTotal.toFixed(2)}`,
                field: 'amount_total'
              };
            }
          }
          return { valid: true };
        },
        severity: 'error'
      },
      {
        name: 'date_consistency',
        description: 'Order dates should be logical',
        validate: (order) => {
          const orderDate = new Date(order.date_order);
          const plannedDate = order.date_planned ? new Date(order.date_planned) : null;
          
          if (plannedDate && plannedDate < orderDate) {
            return {
              valid: false,
              message: 'Planned date cannot be before order date',
              field: 'date_planned'
            };
          }
          
          // Check if order date is not too far in the future
          const maxFutureDate = new Date();
          maxFutureDate.setMonth(maxFutureDate.getMonth() + 6);
          
          if (orderDate > maxFutureDate) {
            return {
              valid: false,
              message: 'Order date is suspiciously far in the future',
              field: 'date_order'
            };
          }
          
          return { valid: true };
        },
        severity: 'warning'
      },
      {
        name: 'order_line_validation',
        description: 'Order lines should have valid products and quantities',
        validate: (order) => {
          if (!order.order_line || order.order_line.length === 0) {
            return {
              valid: false,
              message: 'Order must have at least one order line',
              field: 'order_line'
            };
          }
          
          // Check each order line
          for (let i = 0; i < order.order_line.length; i++) {
            const line = order.order_line[i];
            
            if (!line.product_id) {
              return {
                valid: false,
                message: `Order line ${i + 1} missing product_id`,
                field: `order_line[${i}].product_id`
              };
            }
            
            if (!line.product_qty || line.product_qty <= 0) {
              return {
                valid: false,
                message: `Order line ${i + 1} has invalid quantity`,
                field: `order_line[${i}].product_qty`
              };
            }
            
            if (!line.price_unit || line.price_unit < 0) {
              return {
                valid: false,
                message: `Order line ${i + 1} has invalid price`,
                field: `order_line[${i}].price_unit`
              };
            }
          }
          
          return { valid: true };
        },
        severity: 'error'
      },
      {
        name: 'state_validation',
        description: 'Order state should be valid',
        validate: (order) => {
          const validStates = ['draft', 'sent', 'to approve', 'purchase', 'done', 'cancel'];
          
          if (order.state && !validStates.includes(order.state)) {
            return {
              valid: false,
              message: `Invalid order state. Must be one of: ${validStates.join(', ')}`,
              field: 'state'
            };
          }
          
          return { valid: true };
        },
        severity: 'error'
      },
      {
        name: 'currency_consistency',
        description: 'Currency should be consistent throughout order',
        validate: (order) => {
          // This is a placeholder - in real implementation, you'd validate against
          // actual currency data and ensure all amounts are in the same currency
          if (order.currency_id && !Array.isArray(order.currency_id)) {
            return {
              valid: false,
              message: 'Currency ID should be in [id, name] format',
              field: 'currency_id'
            };
          }
          
          return { valid: true };
        },
        severity: 'warning'
      },
      {
        name: 'quantity_reasonableness',
        description: 'Quantities should be reasonable',
        validate: (order) => {
          if (order.order_line) {
            for (let i = 0; i < order.order_line.length; i++) {
              const line = order.order_line[i];
              
              if (line.product_qty > 10000) {
                return {
                  valid: false,
                  message: `Order line ${i + 1} has unusually high quantity: ${line.product_qty}`,
                  field: `order_line[${i}].product_qty`
                };
              }
              
              // Check for fractional quantities where they might not make sense
              if (line.product_qty % 1 !== 0 && line.product_qty < 1) {
                return {
                  valid: false,
                  message: `Order line ${i + 1} has suspicious fractional quantity: ${line.product_qty}`,
                  field: `order_line[${i}].product_qty`
                };
              }
            }
          }
          
          return { valid: true };
        },
        severity: 'warning'
      }
    ];
  }

  async validateRecord(order, recordId) {
    // Basic field validation
    await this.validateBasicFields(order, recordId);
    
    // Schema validation against Odoo purchase.order model
    await this.validateAgainstOdooSchema(order, recordId);
    
    // Business rule validation
    await this.validateBusinessRules(order, recordId);
    
    // Order-specific validations
    await this.validateOrderSpecific(order, recordId);
    
    // Custom validation rules
    this.applyCustomRules(order, recordId);
  }

  async validateBasicFields(order, recordId) {
    // Required fields
    this.validateRequired(order.partner_id, 'partner_id', recordId);
    this.validateRequired(order.date_order, 'date_order', recordId);
    this.validateRequired(order.order_line, 'order_line', recordId);
    
    // Partner ID validation (should be [id, name] format)
    if (order.partner_id) {
      if (!Array.isArray(order.partner_id) || order.partner_id.length !== 2) {
        this.report.addError('partner_id', 'Partner ID must be in [id, name] format', 
          order.partner_id, recordId);
      } else {
        const [id, name] = order.partner_id;
        if (typeof id !== 'number' || typeof name !== 'string') {
          this.report.addError('partner_id', 'Partner ID format should be [number, string]', 
            order.partner_id, recordId);
        }
      }
    }
    
    // Date validation
    this.validateDate(order.date_order, 'date_order', recordId, false);
    this.validateDate(order.date_planned, 'date_planned', recordId, true);
    
    // String fields
    this.validateString(order.name, 'name', recordId, { optional: true, maxLength: 100 });
    this.validateString(order.notes, 'notes', recordId, { optional: true, maxLength: 2000 });
    
    // State validation
    this.validateEnum(order.state, 'state', recordId, 
      ['draft', 'sent', 'to approve', 'purchase', 'done', 'cancel'], true);
    
    // Numeric fields
    this.validateNumber(order.amount_total, 'amount_total', recordId, { 
      min: 0, 
      optional: true 
    });
    
    this.validateNumber(order.amount_untaxed, 'amount_untaxed', recordId, { 
      min: 0, 
      optional: true 
    });
    
    this.validateNumber(order.amount_tax, 'amount_tax', recordId, { 
      min: 0, 
      optional: true 
    });
    
    // Order lines validation
    this.validateArray(order.order_line, 'order_line', recordId, { 
      minItems: 1,
      maxItems: 100 
    });
    
    // Currency ID validation
    if (order.currency_id) {
      if (!Array.isArray(order.currency_id) || order.currency_id.length !== 2) {
        this.report.addError('currency_id', 'Currency ID must be in [id, name] format', 
          order.currency_id, recordId);
      }
    }
    
    // Company ID validation
    if (order.company_id) {
      if (!Array.isArray(order.company_id) || order.company_id.length !== 2) {
        this.report.addError('company_id', 'Company ID must be in [id, name] format', 
          order.company_id, recordId);
      }
    }
  }

  async validateAgainstOdooSchema(order, recordId) {
    // Convert to Odoo format if needed
    const odooOrder = this.convertToOdooFormat(order);
    
    // Validate against Odoo schema
    const schemaResult = this.schemaValidator.validateAgainstSchema(odooOrder, 'purchase.order');
    
    if (!schemaResult.valid) {
      schemaResult.errors.forEach(error => {
        this.report.addError(error.field, error.message, error.value, recordId);
      });
    }
    
    schemaResult.warnings.forEach(warning => {
      this.report.addWarning(warning.field, warning.message, warning.value, recordId);
    });
  }

  async validateBusinessRules(order, recordId) {
    this.businessRules.forEach(rule => {
      try {
        const result = rule.validate(order);
        if (!result.valid) {
          if (rule.severity === 'error') {
            this.report.addError(result.field, result.message, order[result.field], recordId);
          } else {
            this.report.addWarning(result.field, result.message, order[result.field], recordId);
          }
        }
      } catch (error) {
        this.report.addError('business_rule', `Rule '${rule.name}' failed: ${error.message}`, null, recordId);
      }
    });
  }

  async validateOrderSpecific(order, recordId) {
    // Validate order lines in detail
    if (order.order_line && Array.isArray(order.order_line)) {
      order.order_line.forEach((line, lineIndex) => {
        this.validateOrderLine(line, lineIndex, recordId);
      });
    }
    
    // Check for suspicious patterns
    this.checkSuspiciousPatterns(order, recordId);
    
    // Validate order consistency
    this.validateOrderConsistency(order, recordId);
  }

  validateOrderLine(line, lineIndex, recordId) {
    const lineId = `${recordId}_line_${lineIndex}`;
    
    // Product ID validation
    if (line.product_id) {
      if (!Array.isArray(line.product_id) || line.product_id.length !== 2) {
        this.report.addError(`order_line[${lineIndex}].product_id`, 
          'Product ID must be in [id, name] format', 
          line.product_id, recordId);
      } else {
        const [id, name] = line.product_id;
        if (typeof id !== 'number' || typeof name !== 'string') {
          this.report.addError(`order_line[${lineIndex}].product_id`, 
            'Product ID format should be [number, string]', 
            line.product_id, recordId);
        }
      }
    }
    
    // Required line fields
    this.validateRequired(line.name, `order_line[${lineIndex}].name`, recordId);
    this.validateRequired(line.product_qty, `order_line[${lineIndex}].product_qty`, recordId);
    this.validateRequired(line.price_unit, `order_line[${lineIndex}].price_unit`, recordId);
    
    // Numeric validations
    this.validateNumber(line.product_qty, `order_line[${lineIndex}].product_qty`, recordId, {
      positive: true,
      max: 100000
    });
    
    this.validateNumber(line.price_unit, `order_line[${lineIndex}].price_unit`, recordId, {
      min: 0,
      max: 1000000
    });
    
    // String validations
    this.validateString(line.name, `order_line[${lineIndex}].name`, recordId, {
      minLength: 1,
      maxLength: 200
    });
    
    // UOM validation
    if (line.product_uom) {
      if (!Array.isArray(line.product_uom) || line.product_uom.length !== 2) {
        this.report.addError(`order_line[${lineIndex}].product_uom`, 
          'Product UOM must be in [id, name] format', 
          line.product_uom, recordId);
      }
    }
    
    // Date planned validation
    this.validateDate(line.date_planned, `order_line[${lineIndex}].date_planned`, recordId, true);
    
    // Line total validation
    if (line.product_qty && line.price_unit) {
      const expectedTotal = line.product_qty * line.price_unit;
      
      if (line.price_subtotal && Math.abs(line.price_subtotal - expectedTotal) > 0.01) {
        this.report.addWarning(`order_line[${lineIndex}].price_subtotal`, 
          `Line subtotal mismatch. Expected: ${expectedTotal.toFixed(2)}, Got: ${line.price_subtotal}`,
          line.price_subtotal, recordId);
      }
    }
  }

  checkSuspiciousPatterns(order, recordId) {
    // Check for suspiciously round numbers
    if (order.amount_total) {
      const total = order.amount_total;
      if (total > 100 && total % 100 === 0) {
        this.report.addWarning('amount_total', 
          'Suspiciously round total amount', 
          total, recordId);
      }
    }
    
    // Check for orders with single very expensive item
    if (order.order_line && order.order_line.length === 1) {
      const line = order.order_line[0];
      if (line.price_unit > 50000) {
        this.report.addWarning('order_line[0].price_unit', 
          'Single very expensive item - please verify',
          line.price_unit, recordId);
      }
    }
    
    // Check for duplicate products in order lines
    if (order.order_line && order.order_line.length > 1) {
      const productIds = new Map();
      
      order.order_line.forEach((line, index) => {
        if (line.product_id && Array.isArray(line.product_id)) {
          const productId = line.product_id[0];
          if (productIds.has(productId)) {
            this.report.addWarning(`order_line[${index}].product_id`, 
              'Duplicate product in order lines',
              line.product_id, recordId);
          } else {
            productIds.set(productId, index);
          }
        }
      });
    }
  }

  validateOrderConsistency(order, recordId) {
    // Check amount consistency
    if (order.amount_total && order.amount_untaxed && order.amount_tax) {
      const calculatedTotal = order.amount_untaxed + order.amount_tax;
      
      if (Math.abs(calculatedTotal - order.amount_total) > 0.01) {
        this.report.addError('amount_total', 
          `Amount total inconsistency. Untaxed: ${order.amount_untaxed}, Tax: ${order.amount_tax}, Total: ${order.amount_total}`,
          order.amount_total, recordId);
      }
    }
    
    // Check state consistency with dates
    if (order.state === 'done' && order.date_planned) {
      const plannedDate = new Date(order.date_planned);
      const now = new Date();
      
      if (plannedDate > now) {
        this.report.addWarning('state', 
          'Order marked as done but planned date is in the future',
          order.state, recordId);
      }
    }
    
    // Check for minimum order requirements
    if (order.order_line && order.amount_total) {
      if (order.amount_total < 1.0) {
        this.report.addWarning('amount_total', 
          'Order total is very low - may not meet minimum requirements',
          order.amount_total, recordId);
      }
    }
  }

  convertToOdooFormat(order) {
    return {
      name: order.name || order.order_number,
      partner_id: order.partner_id,
      date_order: order.date_order,
      date_planned: order.date_planned,
      state: order.state || 'draft',
      currency_id: order.currency_id,
      company_id: order.company_id,
      order_line: order.order_line || [],
      notes: order.notes,
      amount_total: order.amount_total,
      amount_untaxed: order.amount_untaxed,
      amount_tax: order.amount_tax
    };
  }

  // Utility methods for order-specific analysis
  analyzeOrderPatterns(orders) {
    const patterns = {
      averageOrderValue: 0,
      averageLineItems: 0,
      commonStates: new Map(),
      suspiciousOrders: [],
      topSuppliers: new Map()
    };
    
    if (!Array.isArray(orders) || orders.length === 0) {
      return patterns;
    }
    
    let totalValue = 0;
    let totalLineItems = 0;
    let validOrderCount = 0;
    
    orders.forEach((order, index) => {
      const recordId = this.getRecordId(order, index);
      
      // Calculate averages
      if (order.amount_total && order.amount_total > 0) {
        totalValue += order.amount_total;
        validOrderCount++;
      }
      
      if (order.order_line && Array.isArray(order.order_line)) {
        totalLineItems += order.order_line.length;
      }
      
      // Count states
      if (order.state) {
        const count = patterns.commonStates.get(order.state) || 0;
        patterns.commonStates.set(order.state, count + 1);
      }
      
      // Track suppliers
      if (order.partner_id && Array.isArray(order.partner_id)) {
        const supplierName = order.partner_id[1];
        const count = patterns.topSuppliers.get(supplierName) || 0;
        patterns.topSuppliers.set(supplierName, count + 1);
      }
      
      // Identify suspicious orders
      if (this.isSuspiciousOrder(order)) {
        patterns.suspiciousOrders.push(recordId);
      }
    });
    
    patterns.averageOrderValue = validOrderCount > 0 ? totalValue / validOrderCount : 0;
    patterns.averageLineItems = orders.length > 0 ? totalLineItems / orders.length : 0;
    
    return patterns;
  }

  isSuspiciousOrder(order) {
    // Define criteria for suspicious orders
    const suspiciousFactors = [];
    
    // Very high order value
    if (order.amount_total > 100000) {
      suspiciousFactors.push('high_value');
    }
    
    // Order in the future
    if (order.date_order) {
      const orderDate = new Date(order.date_order);
      const futureThreshold = new Date();
      futureThreshold.setDate(futureThreshold.getDate() + 30);
      
      if (orderDate > futureThreshold) {
        suspiciousFactors.push('future_date');
      }
    }
    
    // Too many line items
    if (order.order_line && order.order_line.length > 50) {
      suspiciousFactors.push('too_many_lines');
    }
    
    // Round numbers everywhere
    if (order.amount_total && 
        order.amount_total % 100 === 0 && 
        order.order_line &&
        order.order_line.every(line => line.price_unit % 10 === 0)) {
      suspiciousFactors.push('round_numbers');
    }
    
    return suspiciousFactors.length > 1;
  }

  suggestCorrection(field, value, context = {}) {
    const suggestions = [];
    
    switch (field) {
      case 'date_order':
      case 'date_planned':
        if (value && typeof value === 'string') {
          // Try to fix common date format issues
          const dateAttempts = [
            new Date(value),
            new Date(value.replace(/\//g, '-')),
            new Date(value.replace(/\./g, '-'))
          ];
          
          dateAttempts.forEach(date => {
            if (!isNaN(date.getTime())) {
              suggestions.push(date.toISOString());
            }
          });
        }
        break;
        
      case 'state':
        if (value) {
          const validStates = ['draft', 'sent', 'to approve', 'purchase', 'done', 'cancel'];
          const similar = validStates.filter(state => 
            state.includes(value.toLowerCase()) || 
            value.toLowerCase().includes(state)
          );
          suggestions.push(...similar);
        }
        break;
    }
    
    return {
      field,
      originalValue: value,
      suggestions,
      context
    };
  }

  async generateValidationReport(orders) {
    console.log(chalk.blue('\n🔍 Starting Order Validation...'));
    
    const report = await this.validate(orders);
    
    // Additional batch validations
    if (Array.isArray(orders)) {
      this.checkForDuplicates(orders, 'name');
      this.checkFieldCompleteness(orders, this.requiredFields);
      
      // Analyze patterns
      const patterns = this.analyzeOrderPatterns(orders);
      
      report.addInfo(`Average order value: $${patterns.averageOrderValue.toFixed(2)}`);
      report.addInfo(`Average line items per order: ${patterns.averageLineItems.toFixed(1)}`);
      
      if (patterns.suspiciousOrders.length > 0) {
        report.addInfo(`Suspicious orders detected: ${patterns.suspiciousOrders.length}`);
      }
    }
    
    console.log(chalk.green('\n✅ Order validation completed'));
    report.printSummary();
    
    return report;
  }
}

// CLI functionality
export async function validateOrderFile(filePath, options = {}) {
  try {
    const fs = await import('fs');
    const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    
    const validator = new OrderValidator(options);
    let orders;
    
    // Handle different JSON structures
    if (data.orders || data.purchase_orders) {
      orders = data.orders || data.purchase_orders;
    } else if (Array.isArray(data)) {
      orders = data;
    } else {
      orders = [data];
    }
    
    const report = await validator.generateValidationReport(orders);
    
    // Save report if requested
    if (options.outputFile) {
      fs.writeFileSync(options.outputFile, JSON.stringify(report.toJSON(), null, 2));
      console.log(chalk.blue(`\n📁 Report saved to: ${options.outputFile}`));
    }
    
    return report;
    
  } catch (error) {
    console.error(chalk.red(`❌ Error validating orders: ${error.message}`));
    throw error;
  }
}

export default OrderValidator;