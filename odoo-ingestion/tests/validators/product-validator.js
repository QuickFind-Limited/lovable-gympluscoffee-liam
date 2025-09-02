/**
 * Product Data Validation for Odoo Ingestion
 * Validates product data completeness, integrity, and business rules
 */

import { BaseValidator } from '../utils/base-validator.js';
import { SchemaValidator } from '../utils/schema-validator.js';
import chalk from 'chalk';

export class ProductValidator extends BaseValidator {
  constructor(options = {}) {
    super({
      strictMode: true,
      allowMissingFields: false,
      ...options
    });
    
    this.schemaValidator = new SchemaValidator();
    this.requiredFields = [
      'name', 'sku', 'category', 'list_price', 'standard_cost'
    ];
    this.businessRules = this.initializeBusinessRules();
  }

  initializeBusinessRules() {
    return [
      {
        name: 'price_validation',
        description: 'List price should be greater than standard cost',
        validate: (product) => {
          if (product.list_price && product.standard_cost) {
            return {
              valid: product.list_price >= product.standard_cost,
              message: 'List price should be greater than or equal to standard cost',
              field: 'list_price'
            };
          }
          return { valid: true };
        },
        severity: 'warning'
      },
      {
        name: 'sku_format',
        description: 'SKU should follow standard format',
        validate: (product) => {
          if (product.sku) {
            const skuPattern = /^[A-Z0-9]{2,}-[A-Z0-9-]+$/;
            return {
              valid: skuPattern.test(product.sku),
              message: 'SKU should follow format: PREFIX-IDENTIFIER (e.g., GC10000-BLA-XS)',
              field: 'sku'
            };
          }
          return { valid: true };
        },
        severity: 'error'
      },
      {
        name: 'inventory_consistency',
        description: 'Inventory levels should be consistent',
        validate: (product) => {
          if (product.inventory_on_hand && product.reorder_point) {
            const valid = product.inventory_on_hand >= 0 && product.reorder_point >= 0;
            return {
              valid,
              message: 'Inventory levels must be non-negative',
              field: 'inventory_on_hand'
            };
          }
          return { valid: true };
        },
        severity: 'error'
      },
      {
        name: 'category_validation',
        description: 'Product category should be from approved list',
        validate: (product) => {
          const validCategories = [
            'sports-bras', 'joggers', 't-shirts', 'accessories', 'shorts',
            'hoodies', 'jackets', 'tops', 'beanies', 'leggings'
          ];
          
          if (product.category) {
            return {
              valid: validCategories.includes(product.category),
              message: `Category must be one of: ${validCategories.join(', ')}`,
              field: 'category'
            };
          }
          return { valid: true };
        },
        severity: 'error'
      },
      {
        name: 'description_length',
        description: 'Product description should be meaningful',
        validate: (product) => {
          if (product.description) {
            const minLength = 10;
            const maxLength = 1000;
            const length = product.description.length;
            
            if (length < minLength) {
              return {
                valid: false,
                message: `Description too short (${length} chars). Minimum: ${minLength} chars`,
                field: 'description'
              };
            }
            
            if (length > maxLength) {
              return {
                valid: false,
                message: `Description too long (${length} chars). Maximum: ${maxLength} chars`,
                field: 'description'
              };
            }
          }
          return { valid: true };
        },
        severity: 'warning'
      }
    ];
  }

  async validateRecord(product, recordId) {
    // Basic field validation
    await this.validateBasicFields(product, recordId);
    
    // Schema validation against Odoo product.template model
    await this.validateAgainstOdooSchema(product, recordId);
    
    // Business rule validation
    await this.validateBusinessRules(product, recordId);
    
    // Data quality checks
    await this.validateDataQuality(product, recordId);
    
    // Custom validation rules
    this.applyCustomRules(product, recordId);
  }

  async validateBasicFields(product, recordId) {
    // Required fields
    this.validateRequired(product.name, 'name', recordId);
    this.validateRequired(product.sku, 'sku', recordId);
    
    // String fields with constraints
    this.validateString(product.name, 'name', recordId, {
      minLength: 2,
      maxLength: 100
    });
    
    this.validateString(product.sku, 'sku', recordId, {
      minLength: 3,
      maxLength: 50,
      pattern: /^[A-Z0-9-]+$/
    });
    
    this.validateString(product.category, 'category', recordId, {
      optional: false,
      minLength: 2
    });
    
    this.validateString(product.subcategory, 'subcategory', recordId, {
      optional: true
    });
    
    this.validateString(product.color, 'color', recordId, {
      optional: true,
      minLength: 2,
      maxLength: 30
    });
    
    this.validateString(product.size, 'size', recordId, {
      optional: true,
      maxLength: 10
    });
    
    this.validateString(product.description, 'description', recordId, {
      optional: true,
      minLength: 10,
      maxLength: 2000
    });
    
    // Numeric fields
    this.validateNumber(product.list_price, 'list_price', recordId, {
      min: 0,
      positive: true
    });
    
    this.validateNumber(product.standard_cost, 'standard_cost', recordId, {
      min: 0,
      positive: true
    });
    
    this.validateNumber(product.inventory_on_hand, 'inventory_on_hand', recordId, {
      min: 0,
      optional: true
    });
    
    this.validateNumber(product.reorder_point, 'reorder_point', recordId, {
      min: 0,
      optional: true
    });
    
    this.validateNumber(product.lead_time_days, 'lead_time_days', recordId, {
      min: 0,
      max: 365,
      optional: true
    });
    
    // Enum validations
    this.validateEnum(product.status, 'status', recordId, 
      ['active', 'inactive', 'discontinued'], true);
    
    // Array fields
    this.validateArray(product.features, 'features', recordId, {
      optional: true,
      minItems: 0,
      maxItems: 20
    });
    
    // Date fields
    this.validateDate(product.created_date, 'created_date', recordId, true);
    this.validateDate(product.last_modified, 'last_modified', recordId, true);
  }

  async validateAgainstOdooSchema(product, recordId) {
    // Convert to Odoo format
    const odooProduct = this.convertToOdooFormat(product);
    
    // Validate against Odoo schema
    const schemaResult = this.schemaValidator.validateAgainstSchema(odooProduct, 'product.template');
    
    if (!schemaResult.valid) {
      schemaResult.errors.forEach(error => {
        this.report.addError(error.field, error.message, error.value, recordId);
      });
    }
    
    schemaResult.warnings.forEach(warning => {
      this.report.addWarning(warning.field, warning.message, warning.value, recordId);
    });
  }

  async validateBusinessRules(product, recordId) {
    this.businessRules.forEach(rule => {
      try {
        const result = rule.validate(product);
        if (!result.valid) {
          if (rule.severity === 'error') {
            this.report.addError(result.field, result.message, product[result.field], recordId);
          } else {
            this.report.addWarning(result.field, result.message, product[result.field], recordId);
          }
        }
      } catch (error) {
        this.report.addError('business_rule', `Rule '${rule.name}' failed: ${error.message}`, null, recordId);
      }
    });
  }

  async validateDataQuality(product, recordId) {
    // Check for suspicious values
    this.checkSuspiciousValues(product, recordId);
    
    // Validate price reasonableness
    this.validatePriceReasonableness(product, recordId);
    
    // Check for data consistency
    this.checkDataConsistency(product, recordId);
  }

  checkSuspiciousValues(product, recordId) {
    // Check for placeholder text
    const placeholderPatterns = [
      /^(test|sample|placeholder|dummy|temp)/i,
      /^(lorem|ipsum)/i,
      /^(product|item)\s*\d*$/i
    ];
    
    ['name', 'description'].forEach(field => {
      if (product[field]) {
        const isSuspicious = placeholderPatterns.some(pattern => 
          pattern.test(product[field].trim())
        );
        
        if (isSuspicious) {
          this.report.addWarning(field, 'Suspicious placeholder-like value detected', 
            product[field], recordId);
        }
      }
    });
    
    // Check for unusual price values
    if (product.list_price === 0) {
      this.report.addWarning('list_price', 'Zero price may indicate missing data', 
        product.list_price, recordId);
    }
    
    if (product.list_price && product.list_price > 10000) {
      this.report.addWarning('list_price', 'Unusually high price detected', 
        product.list_price, recordId);
    }
  }

  validatePriceReasonableness(product, recordId) {
    if (product.list_price && product.standard_cost) {
      const margin = ((product.list_price - product.standard_cost) / product.list_price) * 100;
      
      if (margin < 10) {
        this.report.addWarning('list_price', 
          `Low margin detected: ${margin.toFixed(1)}%`, 
          margin, recordId);
      }
      
      if (margin > 300) {
        this.report.addWarning('list_price', 
          `Unusually high margin: ${margin.toFixed(1)}%`, 
          margin, recordId);
      }
    }
  }

  checkDataConsistency(product, recordId) {
    // Check size-color combinations make sense
    if (product.category && product.size) {
      const sizelessCategories = ['accessories', 'beanies'];
      if (sizelessCategories.includes(product.category) && product.size) {
        this.report.addWarning('size', 
          `Size specified for category '${product.category}' that typically doesn't have sizes`,
          product.size, recordId);
      }
    }
    
    // Check inventory consistency
    if (product.inventory_on_hand && product.reorder_point) {
      if (product.inventory_on_hand > 0 && product.inventory_on_hand < product.reorder_point) {
        this.report.addWarning('inventory_on_hand', 
          'Inventory below reorder point', 
          product.inventory_on_hand, recordId);
      }
    }
  }

  convertToOdooFormat(product) {
    return {
      name: product.name,
      default_code: product.sku,
      type: 'product', // Assuming all are stockable products
      list_price: product.list_price || 0,
      standard_price: product.standard_cost || 0,
      description: product.description,
      active: product.status !== 'inactive',
      sale_ok: true,
      purchase_ok: true,
      tracking: 'none', // Default tracking
      // Map category to categ_id (would need lookup in real implementation)
      categ_id: [1, product.category || 'Uncategorized']
    };
  }

  // Utility methods for product-specific validations
  validateProductVariations(products) {
    const variationGroups = new Map();
    
    products.forEach((product, index) => {
      const basePattern = product.sku?.replace(/-[A-Z0-9]+$/, ''); // Remove size/color suffix
      if (!variationGroups.has(basePattern)) {
        variationGroups.set(basePattern, []);
      }
      variationGroups.get(basePattern).push({ product, index });
    });
    
    // Check for incomplete variation sets
    variationGroups.forEach((variations, basePattern) => {
      if (variations.length > 1) {
        // Check if all variations have consistent base information
        const baseName = variations[0].product.name?.replace(/ - [A-Za-z]+$/, '');
        const inconsistent = variations.filter(v => 
          !v.product.name?.startsWith(baseName)
        );
        
        if (inconsistent.length > 0) {
          inconsistent.forEach(v => {
            this.report.addWarning('name', 
              'Product variation has inconsistent naming with base product',
              v.product.name, this.getRecordId(v.product, v.index));
          });
        }
      }
    });
  }

  suggestCorrection(field, value, context = {}) {
    const suggestions = [];
    
    switch (field) {
      case 'sku':
        if (value && !value.match(/^[A-Z0-9-]+$/)) {
          suggestions.push(`Convert to uppercase: ${value.toUpperCase()}`);
          suggestions.push(`Remove special characters: ${value.replace(/[^A-Z0-9-]/g, '-')}`);
        }
        break;
        
      case 'category':
        const validCategories = [
          'sports-bras', 'joggers', 't-shirts', 'accessories', 'shorts',
          'hoodies', 'jackets', 'tops', 'beanies', 'leggings'
        ];
        
        if (value) {
          const similar = validCategories.filter(cat => 
            cat.includes(value.toLowerCase()) || 
            value.toLowerCase().includes(cat.replace('-', ''))
          );
          suggestions.push(...similar);
        }
        break;
        
      case 'list_price':
      case 'standard_cost':
        if (typeof value === 'string' && value.match(/[\d.,]+/)) {
          const numericValue = parseFloat(value.replace(/[^0-9.]/g, ''));
          if (!isNaN(numericValue)) {
            suggestions.push(`Convert to number: ${numericValue}`);
          }
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

  async generateValidationReport(products) {
    console.log(chalk.blue('\n🔍 Starting Product Validation...'));
    
    const report = await this.validate(products);
    
    // Additional batch validations
    if (Array.isArray(products)) {
      this.checkForDuplicates(products, 'sku');
      this.checkForDuplicates(products, 'name');
      this.checkFieldCompleteness(products, this.requiredFields);
      this.validateProductVariations(products);
    }
    
    console.log(chalk.green('\n✅ Product validation completed'));
    report.printSummary();
    
    return report;
  }
}

// CLI functionality
export async function validateProductFile(filePath, options = {}) {
  try {
    const fs = await import('fs');
    const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    
    const validator = new ProductValidator(options);
    let products;
    
    // Handle different JSON structures
    if (data.products) {
      products = data.products;
    } else if (Array.isArray(data)) {
      products = data;
    } else {
      products = [data];
    }
    
    const report = await validator.generateValidationReport(products);
    
    // Save report if requested
    if (options.outputFile) {
      fs.writeFileSync(options.outputFile, JSON.stringify(report.toJSON(), null, 2));
      console.log(chalk.blue(`\n📁 Report saved to: ${options.outputFile}`));
    }
    
    return report;
    
  } catch (error) {
    console.error(chalk.red(`❌ Error validating products: ${error.message}`));
    throw error;
  }
}

export default ProductValidator;