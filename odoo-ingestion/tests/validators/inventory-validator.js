/**
 * Inventory Accuracy Validation for Odoo Ingestion
 * Validates inventory/stock data accuracy and consistency
 */

import { BaseValidator } from '../utils/base-validator.js';
import { SchemaValidator } from '../utils/schema-validator.js';
import chalk from 'chalk';

export class InventoryValidator extends BaseValidator {
  constructor(options = {}) {
    super({
      strictMode: true,
      allowMissingFields: false,
      ...options
    });
    
    this.schemaValidator = new SchemaValidator();
    this.requiredFields = ['product_id', 'location_id', 'quantity'];
    this.businessRules = this.initializeBusinessRules();
  }

  initializeBusinessRules() {
    return [
      {
        name: 'quantity_consistency',
        description: 'Available quantity should equal total minus reserved',
        validate: (stock) => {
          if (stock.quantity !== undefined && 
              stock.reserved_quantity !== undefined && 
              stock.available_quantity !== undefined) {
            
            const expectedAvailable = stock.quantity - stock.reserved_quantity;
            
            if (Math.abs(stock.available_quantity - expectedAvailable) > 0.001) {
              return {
                valid: false,
                message: `Quantity mismatch. Available: ${stock.available_quantity}, Expected: ${expectedAvailable}`,
                field: 'available_quantity'
              };
            }
          }
          return { valid: true };
        },
        severity: 'error'
      },
      {
        name: 'negative_stock_check',
        description: 'Quantities should not be negative unless specifically allowed',
        validate: (stock) => {
          if (stock.quantity < 0 && !stock.allow_negative) {
            return {
              valid: false,
              message: 'Negative stock quantity detected',
              field: 'quantity'
            };
          }
          
          if (stock.reserved_quantity < 0) {
            return {
              valid: false,
              message: 'Reserved quantity cannot be negative',
              field: 'reserved_quantity'
            };
          }
          
          return { valid: true };
        },
        severity: 'error'
      },
      {
        name: 'reserved_quantity_logic',
        description: 'Reserved quantity should not exceed total quantity',
        validate: (stock) => {
          if (stock.quantity !== undefined && stock.reserved_quantity !== undefined) {
            if (stock.reserved_quantity > stock.quantity) {
              return {
                valid: false,
                message: `Reserved quantity (${stock.reserved_quantity}) exceeds total quantity (${stock.quantity})`,
                field: 'reserved_quantity'
              };
            }
          }
          return { valid: true };
        },
        severity: 'error'
      },
      {
        name: 'lot_consistency',
        description: 'Lot tracking should be consistent with product settings',
        validate: (stock) => {
          // This would need product tracking info in real implementation
          if (stock.lot_id && stock.quantity === 0) {
            return {
              valid: false,
              message: 'Stock record has lot ID but zero quantity',
              field: 'lot_id'
            };
          }
          return { valid: true };
        },
        severity: 'warning'
      },
      {
        name: 'location_validation',
        description: 'Location should be valid and active',
        validate: (stock) => {
          // In real implementation, this would validate against actual locations
          if (!stock.location_id) {
            return {
              valid: false,
              message: 'Location ID is required',
              field: 'location_id'
            };
          }
          
          if (Array.isArray(stock.location_id) && stock.location_id.length === 2) {
            const [id, name] = stock.location_id;
            if (typeof id !== 'number' || typeof name !== 'string') {
              return {
                valid: false,
                message: 'Location ID format should be [number, string]',
                field: 'location_id'
              };
            }
          }
          
          return { valid: true };
        },
        severity: 'error'
      },
      {
        name: 'aging_analysis',
        description: 'Stock aging should be reasonable',
        validate: (stock) => {
          if (stock.in_date) {
            const inDate = new Date(stock.in_date);
            const now = new Date();
            const ageInDays = (now - inDate) / (1000 * 60 * 60 * 24);
            
            if (ageInDays > 365 * 3) { // 3 years
              return {
                valid: false,
                message: `Very old stock (${Math.floor(ageInDays)} days old)`,
                field: 'in_date'
              };
            }
            
            if (inDate > now) {
              return {
                valid: false,
                message: 'Stock in-date is in the future',
                field: 'in_date'
              };
            }
          }
          return { valid: true };
        },
        severity: 'warning'
      }
    ];
  }

  async validateRecord(stock, recordId) {
    // Basic field validation
    await this.validateBasicFields(stock, recordId);
    
    // Schema validation against Odoo stock.quant model
    await this.validateAgainstOdooSchema(stock, recordId);
    
    // Business rule validation
    await this.validateBusinessRules(stock, recordId);
    
    // Inventory-specific validations
    await this.validateInventorySpecific(stock, recordId);
    
    // Custom validation rules
    this.applyCustomRules(stock, recordId);
  }

  async validateBasicFields(stock, recordId) {
    // Required fields
    this.validateRequired(stock.product_id, 'product_id', recordId);
    this.validateRequired(stock.location_id, 'location_id', recordId);
    this.validateRequired(stock.quantity, 'quantity', recordId);
    
    // Product ID validation (should be [id, name] format)
    if (stock.product_id) {
      if (!Array.isArray(stock.product_id) || stock.product_id.length !== 2) {
        this.report.addError('product_id', 'Product ID must be in [id, name] format', 
          stock.product_id, recordId);
      } else {
        const [id, name] = stock.product_id;
        if (typeof id !== 'number' || typeof name !== 'string') {
          this.report.addError('product_id', 'Product ID format should be [number, string]', 
            stock.product_id, recordId);
        }
      }
    }
    
    // Location ID validation
    if (stock.location_id) {
      if (!Array.isArray(stock.location_id) || stock.location_id.length !== 2) {
        this.report.addError('location_id', 'Location ID must be in [id, name] format', 
          stock.location_id, recordId);
      } else {
        const [id, name] = stock.location_id;
        if (typeof id !== 'number' || typeof name !== 'string') {
          this.report.addError('location_id', 'Location ID format should be [number, string]', 
            stock.location_id, recordId);
        }
      }
    }
    
    // Numeric fields validation
    this.validateNumber(stock.quantity, 'quantity', recordId, {
      // Allow negative quantities in some cases (returns, adjustments)
      min: -999999,
      max: 999999
    });
    
    this.validateNumber(stock.reserved_quantity, 'reserved_quantity', recordId, {
      min: 0,
      max: 999999,
      optional: true
    });
    
    this.validateNumber(stock.available_quantity, 'available_quantity', recordId, {
      min: -999999,
      max: 999999,
      optional: true
    });
    
    // Date validation
    this.validateDate(stock.in_date, 'in_date', recordId, true);
    
    // Optional relationship fields
    if (stock.lot_id) {
      if (!Array.isArray(stock.lot_id) || stock.lot_id.length !== 2) {
        this.report.addError('lot_id', 'Lot ID must be in [id, name] format', 
          stock.lot_id, recordId);
      }
    }
    
    if (stock.package_id) {
      if (!Array.isArray(stock.package_id) || stock.package_id.length !== 2) {
        this.report.addError('package_id', 'Package ID must be in [id, name] format', 
          stock.package_id, recordId);
      }
    }
    
    if (stock.owner_id) {
      if (!Array.isArray(stock.owner_id) || stock.owner_id.length !== 2) {
        this.report.addError('owner_id', 'Owner ID must be in [id, name] format', 
          stock.owner_id, recordId);
      }
    }
  }

  async validateAgainstOdooSchema(stock, recordId) {
    // Convert to Odoo format
    const odooStock = this.convertToOdooFormat(stock);
    
    // Validate against Odoo schema
    const schemaResult = this.schemaValidator.validateAgainstSchema(odooStock, 'stock.quant');
    
    if (!schemaResult.valid) {
      schemaResult.errors.forEach(error => {
        this.report.addError(error.field, error.message, error.value, recordId);
      });
    }
    
    schemaResult.warnings.forEach(warning => {
      this.report.addWarning(warning.field, warning.message, warning.value, recordId);
    });
  }

  async validateBusinessRules(stock, recordId) {
    this.businessRules.forEach(rule => {
      try {
        const result = rule.validate(stock);
        if (!result.valid) {
          if (rule.severity === 'error') {
            this.report.addError(result.field, result.message, stock[result.field], recordId);
          } else {
            this.report.addWarning(result.field, result.message, stock[result.field], recordId);
          }
        }
      } catch (error) {
        this.report.addError('business_rule', `Rule '${rule.name}' failed: ${error.message}`, null, recordId);
      }
    });
  }

  async validateInventorySpecific(stock, recordId) {
    // Check for suspicious stock levels
    this.checkSuspiciousStockLevels(stock, recordId);
    
    // Validate stock movements consistency
    this.validateStockMovementLogic(stock, recordId);
    
    // Check for data quality issues
    this.validateDataQuality(stock, recordId);
  }

  checkSuspiciousStockLevels(stock, recordId) {
    // Very high quantities that might be data entry errors
    if (stock.quantity > 100000) {
      this.report.addWarning('quantity', 
        `Very high stock quantity detected: ${stock.quantity}`, 
        stock.quantity, recordId);
    }
    
    // Unusual fractional quantities for typically whole-unit products
    if (stock.quantity % 1 !== 0 && stock.quantity < 10) {
      const productName = Array.isArray(stock.product_id) ? stock.product_id[1] : '';
      if (!this.isExpectedFractionalProduct(productName)) {
        this.report.addWarning('quantity', 
          `Fractional quantity for product that may not support it: ${stock.quantity}`,
          stock.quantity, recordId);
      }
    }
    
    // Zero quantities with reservations
    if (stock.quantity === 0 && stock.reserved_quantity > 0) {
      this.report.addWarning('reserved_quantity', 
        'Reserved quantity exists but no stock available',
        stock.reserved_quantity, recordId);
    }
    
    // Very old stock
    if (stock.in_date) {
      const inDate = new Date(stock.in_date);
      const now = new Date();
      const ageInMonths = (now - inDate) / (1000 * 60 * 60 * 24 * 30);
      
      if (ageInMonths > 24) {
        this.report.addWarning('in_date', 
          `Very old stock: ${Math.floor(ageInMonths)} months old`,
          stock.in_date, recordId);
      }
    }
  }

  isExpectedFractionalProduct(productName) {
    // Products that commonly have fractional quantities
    const fractionalPatterns = [
      /fabric/i,
      /textile/i,
      /material/i,
      /liquid/i,
      /chemical/i,
      /paint/i,
      /oil/i,
      /meter/i,
      /yard/i,
      /kg/i,
      /lb/i
    ];
    
    return fractionalPatterns.some(pattern => pattern.test(productName));
  }

  validateStockMovementLogic(stock, recordId) {
    // If we have stock but no in-date, that's suspicious
    if (stock.quantity > 0 && !stock.in_date) {
      this.report.addWarning('in_date', 
        'Stock exists but no in-date recorded',
        stock.in_date, recordId);
    }
    
    // Check for impossible stock combinations
    if (stock.quantity === 0 && stock.available_quantity > 0) {
      this.report.addError('available_quantity', 
        'Available quantity cannot be positive when total quantity is zero',
        stock.available_quantity, recordId);
    }
    
    // Package consistency
    if (stock.package_id && stock.quantity <= 0) {
      this.report.addWarning('package_id', 
        'Package assigned but no stock quantity',
        stock.package_id, recordId);
    }
  }

  validateDataQuality(stock, recordId) {
    // Check for precision issues
    if (typeof stock.quantity === 'number' && stock.quantity.toString().includes('e')) {
      this.report.addWarning('quantity', 
        'Scientific notation detected - may cause precision issues',
        stock.quantity, recordId);
    }
    
    // Location name consistency
    if (Array.isArray(stock.location_id)) {
      const locationName = stock.location_id[1];
      if (!locationName || locationName.trim() === '') {
        this.report.addWarning('location_id', 
          'Location name is empty',
          stock.location_id, recordId);
      }
    }
    
    // Product name consistency
    if (Array.isArray(stock.product_id)) {
      const productName = stock.product_id[1];
      if (!productName || productName.trim() === '') {
        this.report.addWarning('product_id', 
          'Product name is empty',
          stock.product_id, recordId);
      }
    }
  }

  convertToOdooFormat(stock) {
    return {
      product_id: stock.product_id,
      location_id: stock.location_id,
      lot_id: stock.lot_id || false,
      package_id: stock.package_id || false,
      owner_id: stock.owner_id || false,
      quantity: stock.quantity || 0,
      reserved_quantity: stock.reserved_quantity || 0,
      available_quantity: stock.available_quantity,
      in_date: stock.in_date || false
    };
  }

  // Utility methods for inventory-specific analysis
  analyzeInventoryPatterns(stockRecords) {
    const patterns = {
      totalProducts: 0,
      totalLocations: 0,
      totalQuantity: 0,
      negativeStockCount: 0,
      zeroStockCount: 0,
      highValueStock: [],
      locationDistribution: new Map(),
      productDistribution: new Map(),
      ageAnalysis: {
        veryOld: 0,
        old: 0,
        recent: 0,
        noDate: 0
      }
    };
    
    if (!Array.isArray(stockRecords) || stockRecords.length === 0) {
      return patterns;
    }
    
    const products = new Set();
    const locations = new Set();
    
    stockRecords.forEach((stock, index) => {
      // Track unique products and locations
      if (Array.isArray(stock.product_id)) {
        products.add(stock.product_id[0]);
        
        const productName = stock.product_id[1];
        const productCount = patterns.productDistribution.get(productName) || 0;
        patterns.productDistribution.set(productName, productCount + 1);
      }
      
      if (Array.isArray(stock.location_id)) {
        locations.add(stock.location_id[0]);
        
        const locationName = stock.location_id[1];
        const locationCount = patterns.locationDistribution.get(locationName) || 0;
        patterns.locationDistribution.set(locationName, locationCount + 1);
      }
      
      // Quantity analysis
      if (typeof stock.quantity === 'number') {
        patterns.totalQuantity += stock.quantity;
        
        if (stock.quantity < 0) {
          patterns.negativeStockCount++;
        } else if (stock.quantity === 0) {
          patterns.zeroStockCount++;
        }
        
        // High value stock (assuming we have cost data)
        if (stock.quantity > 1000) {
          patterns.highValueStock.push(this.getRecordId(stock, index));
        }
      }
      
      // Age analysis
      if (stock.in_date) {
        const inDate = new Date(stock.in_date);
        const now = new Date();
        const ageInDays = (now - inDate) / (1000 * 60 * 60 * 24);
        
        if (ageInDays > 730) { // 2 years
          patterns.ageAnalysis.veryOld++;
        } else if (ageInDays > 365) { // 1 year
          patterns.ageAnalysis.old++;
        } else {
          patterns.ageAnalysis.recent++;
        }
      } else {
        patterns.ageAnalysis.noDate++;
      }
    });
    
    patterns.totalProducts = products.size;
    patterns.totalLocations = locations.size;
    
    return patterns;
  }

  validateInventoryBalance(stockRecords) {
    const balanceReport = {
      valid: true,
      errors: [],
      warnings: [],
      summary: {}
    };
    
    // Group by product
    const productTotals = new Map();
    
    stockRecords.forEach((stock, index) => {
      if (Array.isArray(stock.product_id) && typeof stock.quantity === 'number') {
        const productId = stock.product_id[0];
        const productName = stock.product_id[1];
        
        if (!productTotals.has(productId)) {
          productTotals.set(productId, {
            name: productName,
            totalQuantity: 0,
            locations: new Set(),
            records: []
          });
        }
        
        const productTotal = productTotals.get(productId);
        productTotal.totalQuantity += stock.quantity;
        productTotal.locations.add(stock.location_id[1]);
        productTotal.records.push({ stock, index });
      }
    });
    
    // Check for anomalies
    productTotals.forEach((productData, productId) => {
      // Products with negative total stock
      if (productData.totalQuantity < 0) {
        balanceReport.errors.push({
          type: 'negative_total',
          product: productData.name,
          quantity: productData.totalQuantity,
          message: 'Product has negative total stock across all locations'
        });
        balanceReport.valid = false;
      }
      
      // Products in too many locations (might indicate data issues)
      if (productData.locations.size > 10) {
        balanceReport.warnings.push({
          type: 'too_many_locations',
          product: productData.name,
          locationCount: productData.locations.size,
          message: 'Product exists in unusually many locations'
        });
      }
      
      // Products with only negative quantities
      const allNegative = productData.records.every(r => r.stock.quantity <= 0);
      if (allNegative && productData.records.length > 1) {
        balanceReport.warnings.push({
          type: 'all_negative',
          product: productData.name,
          message: 'All stock records for product are zero or negative'
        });
      }
    });
    
    balanceReport.summary = {
      totalProducts: productTotals.size,
      productsWithNegativeStock: balanceReport.errors.filter(e => e.type === 'negative_total').length,
      averageLocationsPerProduct: Array.from(productTotals.values())
        .reduce((sum, p) => sum + p.locations.size, 0) / productTotals.size
    };
    
    return balanceReport;
  }

  suggestCorrection(field, value, context = {}) {
    const suggestions = [];
    
    switch (field) {
      case 'quantity':
        if (typeof value === 'string' && value.match(/[\d.,]+/)) {
          const numericValue = parseFloat(value.replace(/[^0-9.-]/g, ''));
          if (!isNaN(numericValue)) {
            suggestions.push(`Convert to number: ${numericValue}`);
          }
        }
        
        if (typeof value === 'number' && value < 0 && !context.allowNegative) {
          suggestions.push(`Set to zero: 0`);
          suggestions.push(`Use absolute value: ${Math.abs(value)}`);
        }
        break;
        
      case 'in_date':
        if (value && typeof value === 'string') {
          // Try to fix common date format issues
          const today = new Date().toISOString().split('T')[0];
          suggestions.push(`Use today's date: ${today}`);
          
          const dateAttempts = [
            new Date(value.replace(/\//g, '-')),
            new Date(value.replace(/\./g, '-'))
          ];
          
          dateAttempts.forEach(date => {
            if (!isNaN(date.getTime())) {
              suggestions.push(date.toISOString().split('T')[0]);
            }
          });
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

  async generateValidationReport(stockRecords) {
    console.log(chalk.blue('\n🔍 Starting Inventory Validation...'));
    
    const report = await this.validate(stockRecords);
    
    // Additional batch validations
    if (Array.isArray(stockRecords)) {
      // Check for duplicates
      this.checkForDuplicateStockRecords(stockRecords);
      this.checkFieldCompleteness(stockRecords, this.requiredFields);
      
      // Analyze patterns
      const patterns = this.analyzeInventoryPatterns(stockRecords);
      const balanceReport = this.validateInventoryBalance(stockRecords);
      
      report.addInfo(`Total unique products: ${patterns.totalProducts}`);
      report.addInfo(`Total locations: ${patterns.totalLocations}`);
      report.addInfo(`Total quantity across all products: ${patterns.totalQuantity.toFixed(2)}`);
      report.addInfo(`Records with negative stock: ${patterns.negativeStockCount}`);
      report.addInfo(`Records with zero stock: ${patterns.zeroStockCount}`);
      
      if (!balanceReport.valid) {
        report.addError('inventory_balance', 
          `Inventory balance issues: ${balanceReport.errors.length} errors`,
          balanceReport.errors.length);
      }
    }
    
    console.log(chalk.green('\n✅ Inventory validation completed'));
    report.printSummary();
    
    return report;
  }

  checkForDuplicateStockRecords(stockRecords) {
    const seen = new Set();
    
    stockRecords.forEach((stock, index) => {
      if (Array.isArray(stock.product_id) && Array.isArray(stock.location_id)) {
        const key = `${stock.product_id[0]}-${stock.location_id[0]}-${stock.lot_id ? stock.lot_id[0] : 'no-lot'}`;
        
        if (seen.has(key)) {
          this.report.addWarning('duplicate', 
            'Duplicate stock record (same product, location, and lot)',
            key, this.getRecordId(stock, index));
        } else {
          seen.add(key);
        }
      }
    });
  }
}

// CLI functionality
export async function validateInventoryFile(filePath, options = {}) {
  try {
    const fs = await import('fs');
    const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    
    const validator = new InventoryValidator(options);
    let inventory;
    
    // Handle different JSON structures
    if (data.inventory || data.stock || data.quants) {
      inventory = data.inventory || data.stock || data.quants;
    } else if (Array.isArray(data)) {
      inventory = data;
    } else {
      inventory = [data];
    }
    
    const report = await validator.generateValidationReport(inventory);
    
    // Save report if requested
    if (options.outputFile) {
      fs.writeFileSync(options.outputFile, JSON.stringify(report.toJSON(), null, 2));
      console.log(chalk.blue(`\n📁 Report saved to: ${options.outputFile}`));
    }
    
    return report;
    
  } catch (error) {
    console.error(chalk.red(`❌ Error validating inventory: ${error.message}`));
    throw error;
  }
}

export default InventoryValidator;