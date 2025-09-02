/**
 * Odoo Schema Validation Utilities
 * Validates data against Odoo model schemas and field definitions
 */

import { z } from 'zod';
import Ajv from 'ajv';
import addFormats from 'ajv-formats';
import chalk from 'chalk';

const ajv = new Ajv({ allErrors: true });
addFormats(ajv);

// Odoo field type mappings
export const ODOO_FIELD_TYPES = {
  'char': { type: 'string' },
  'text': { type: 'string' },
  'html': { type: 'string' },
  'boolean': { type: 'boolean' },
  'integer': { type: 'integer' },
  'float': { type: 'number' },
  'monetary': { type: 'number', minimum: 0 },
  'date': { type: 'string', format: 'date' },
  'datetime': { type: 'string', format: 'date-time' },
  'selection': { type: 'string' },
  'many2one': { type: 'array', items: { type: ['integer', 'string'] } },
  'one2many': { type: 'array', items: { type: 'integer' } },
  'many2many': { type: 'array', items: { type: 'integer' } },
  'binary': { type: 'string' },
  'reference': { type: 'string' }
};

// Common Odoo model schemas
export const ODOO_SCHEMAS = {
  'product.template': {
    type: 'object',
    properties: {
      name: { type: 'string', minLength: 1 },
      default_code: { type: 'string' },
      categ_id: { type: 'array', items: { type: ['integer', 'string'] } },
      type: { 
        type: 'string',
        enum: ['product', 'consu', 'service']
      },
      list_price: { type: 'number', minimum: 0 },
      standard_price: { type: 'number', minimum: 0 },
      uom_id: { type: 'array', items: { type: ['integer', 'string'] } },
      uom_po_id: { type: 'array', items: { type: ['integer', 'string'] } },
      description: { type: 'string' },
      description_purchase: { type: 'string' },
      description_sale: { type: 'string' },
      active: { type: 'boolean' },
      sale_ok: { type: 'boolean' },
      purchase_ok: { type: 'boolean' },
      tracking: {
        type: 'string',
        enum: ['none', 'lot', 'serial']
      }
    },
    required: ['name'],
    additionalProperties: true
  },

  'res.partner': {
    type: 'object',
    properties: {
      name: { type: 'string', minLength: 1 },
      is_company: { type: 'boolean' },
      parent_id: { type: 'array', items: { type: ['integer', 'string'] } },
      street: { type: 'string' },
      street2: { type: 'string' },
      city: { type: 'string' },
      state_id: { type: 'array', items: { type: ['integer', 'string'] } },
      zip: { type: 'string' },
      country_id: { type: 'array', items: { type: ['integer', 'string'] } },
      phone: { type: 'string' },
      mobile: { type: 'string' },
      email: { type: 'string', format: 'email' },
      website: { type: 'string', format: 'uri' },
      vat: { type: 'string' },
      supplier_rank: { type: 'integer', minimum: 0 },
      customer_rank: { type: 'integer', minimum: 0 },
      category_id: { type: 'array', items: { type: 'integer' } },
      active: { type: 'boolean' }
    },
    required: ['name'],
    additionalProperties: true
  },

  'purchase.order': {
    type: 'object',
    properties: {
      name: { type: 'string' },
      partner_id: { type: 'array', items: { type: ['integer', 'string'] } },
      date_order: { type: 'string', format: 'date-time' },
      date_planned: { type: 'string', format: 'date-time' },
      state: {
        type: 'string',
        enum: ['draft', 'sent', 'to approve', 'purchase', 'done', 'cancel']
      },
      currency_id: { type: 'array', items: { type: ['integer', 'string'] } },
      company_id: { type: 'array', items: { type: ['integer', 'string'] } },
      order_line: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            product_id: { type: 'array', items: { type: ['integer', 'string'] } },
            name: { type: 'string' },
            product_qty: { type: 'number', minimum: 0 },
            product_uom: { type: 'array', items: { type: ['integer', 'string'] } },
            price_unit: { type: 'number', minimum: 0 },
            date_planned: { type: 'string', format: 'date-time' }
          },
          required: ['product_id', 'name', 'product_qty', 'price_unit']
        }
      },
      notes: { type: 'string' }
    },
    required: ['partner_id', 'date_order'],
    additionalProperties: true
  },

  'stock.quant': {
    type: 'object',
    properties: {
      product_id: { type: 'array', items: { type: ['integer', 'string'] } },
      location_id: { type: 'array', items: { type: ['integer', 'string'] } },
      lot_id: { type: 'array', items: { type: ['integer', 'string'] } },
      package_id: { type: 'array', items: { type: ['integer', 'string'] } },
      owner_id: { type: 'array', items: { type: ['integer', 'string'] } },
      quantity: { type: 'number' },
      reserved_quantity: { type: 'number', minimum: 0 },
      available_quantity: { type: 'number' },
      in_date: { type: 'string', format: 'date-time' }
    },
    required: ['product_id', 'location_id', 'quantity'],
    additionalProperties: true
  }
};

export class SchemaValidator {
  constructor(options = {}) {
    this.options = {
      strictMode: true,
      allowAdditionalProperties: false,
      validateReferences: true,
      ...options
    };
    
    this.compiledSchemas = new Map();
    this.initializeSchemas();
  }

  initializeSchemas() {
    Object.entries(ODOO_SCHEMAS).forEach(([model, schema]) => {
      try {
        const compiled = ajv.compile(schema);
        this.compiledSchemas.set(model, compiled);
      } catch (error) {
        console.error(chalk.red(`Failed to compile schema for ${model}:`, error.message));
      }
    });
  }

  validateAgainstSchema(data, modelName) {
    const results = {
      valid: true,
      errors: [],
      warnings: [],
      model: modelName
    };

    if (!this.compiledSchemas.has(modelName)) {
      results.valid = false;
      results.errors.push({
        field: 'schema',
        message: `No schema found for model: ${modelName}`,
        value: modelName
      });
      return results;
    }

    const validate = this.compiledSchemas.get(modelName);
    const isValid = validate(data);

    if (!isValid) {
      results.valid = false;
      results.errors = validate.errors?.map(error => ({
        field: error.instancePath || error.schemaPath,
        message: error.message || 'Validation failed',
        value: error.data,
        schemaPath: error.schemaPath,
        allowedValues: error.params?.allowedValues
      })) || [];
    }

    // Additional validation for Odoo-specific patterns
    this.validateOdooSpecificPatterns(data, modelName, results);

    return results;
  }

  validateOdooSpecificPatterns(data, modelName, results) {
    // Validate many2one fields format [id, name]
    this.validateRelationshipFields(data, modelName, results);
    
    // Validate selection fields
    this.validateSelectionFields(data, modelName, results);
    
    // Validate required field combinations
    this.validateFieldCombinations(data, modelName, results);
  }

  validateRelationshipFields(data, modelName, results) {
    const schema = ODOO_SCHEMAS[modelName];
    if (!schema?.properties) return;

    Object.entries(schema.properties).forEach(([field, fieldSchema]) => {
      if (this.isRelationshipField(fieldSchema) && data[field]) {
        const value = data[field];
        
        if (Array.isArray(value)) {
          if (value.length === 2) {
            const [id, name] = value;
            if (typeof id !== 'number' || typeof name !== 'string') {
              results.errors.push({
                field,
                message: 'Many2one field must be [number, string] tuple',
                value
              });
              results.valid = false;
            }
          } else if (value.length > 0 && typeof value[0] === 'number') {
            // Many2many or one2many - array of IDs
            const invalidIds = value.filter(id => typeof id !== 'number');
            if (invalidIds.length > 0) {
              results.errors.push({
                field,
                message: 'Relationship field must contain only numeric IDs',
                value: invalidIds
              });
              results.valid = false;
            }
          }
        }
      }
    });
  }

  validateSelectionFields(data, modelName, results) {
    const selectionFields = this.getSelectionFields(modelName);
    
    selectionFields.forEach(({ field, allowedValues }) => {
      if (data[field] && !allowedValues.includes(data[field])) {
        results.errors.push({
          field,
          message: `Invalid selection value. Allowed: ${allowedValues.join(', ')}`,
          value: data[field],
          allowedValues
        });
        results.valid = false;
      }
    });
  }

  validateFieldCombinations(data, modelName, results) {
    switch (modelName) {
      case 'product.template':
        // If it's a stockable product, tracking should be valid
        if (data.type === 'product' && data.tracking && !['none', 'lot', 'serial'].includes(data.tracking)) {
          results.warnings.push({
            field: 'tracking',
            message: 'Invalid tracking value for stockable product',
            value: data.tracking
          });
        }
        break;

      case 'res.partner':
        // If supplier_rank > 0, should be marked as supplier
        if (data.supplier_rank > 0 && !data.is_company) {
          results.warnings.push({
            field: 'supplier_rank',
            message: 'Supplier should typically be marked as company',
            value: data.supplier_rank
          });
        }
        break;

      case 'purchase.order':
        // Validate order lines exist
        if (!data.order_line || data.order_line.length === 0) {
          results.errors.push({
            field: 'order_line',
            message: 'Purchase order must have at least one order line',
            value: data.order_line
          });
          results.valid = false;
        }
        break;
    }
  }

  isRelationshipField(fieldSchema) {
    return fieldSchema.type === 'array' && 
           fieldSchema.items && 
           Array.isArray(fieldSchema.items.type) && 
           fieldSchema.items.type.includes('integer');
  }

  getSelectionFields(modelName) {
    const schema = ODOO_SCHEMAS[modelName];
    const selectionFields = [];

    if (schema?.properties) {
      Object.entries(schema.properties).forEach(([field, fieldSchema]) => {
        if (fieldSchema.enum) {
          selectionFields.push({
            field,
            allowedValues: fieldSchema.enum
          });
        }
      });
    }

    return selectionFields;
  }

  validateFieldTypes(data, modelName) {
    const results = {
      valid: true,
      errors: [],
      warnings: []
    };

    const schema = ODOO_SCHEMAS[modelName];
    if (!schema?.properties) {
      results.errors.push({
        field: 'schema',
        message: `Unknown model: ${modelName}`,
        value: modelName
      });
      results.valid = false;
      return results;
    }

    Object.entries(data).forEach(([field, value]) => {
      const fieldSchema = schema.properties[field];
      
      if (!fieldSchema && !schema.additionalProperties) {
        results.warnings.push({
          field,
          message: 'Field not defined in schema',
          value
        });
        return;
      }

      if (fieldSchema && value !== null && value !== undefined) {
        const typeValidation = this.validateFieldType(value, fieldSchema, field);
        if (!typeValidation.valid) {
          results.errors.push(...typeValidation.errors);
          results.valid = false;
        }
        results.warnings.push(...typeValidation.warnings);
      }
    });

    return results;
  }

  validateFieldType(value, fieldSchema, fieldName) {
    const results = {
      valid: true,
      errors: [],
      warnings: []
    };

    const expectedType = fieldSchema.type;
    const actualType = typeof value;

    // Handle array types (relationships)
    if (expectedType === 'array') {
      if (!Array.isArray(value)) {
        results.errors.push({
          field: fieldName,
          message: `Expected array, got ${actualType}`,
          value
        });
        results.valid = false;
        return results;
      }

      // Validate array items
      if (fieldSchema.items) {
        value.forEach((item, index) => {
          const itemValidation = this.validateArrayItem(item, fieldSchema.items, `${fieldName}[${index}]`);
          if (!itemValidation.valid) {
            results.errors.push(...itemValidation.errors);
            results.valid = false;
          }
        });
      }

      return results;
    }

    // Handle basic type validation
    if (expectedType === 'number' && actualType !== 'number') {
      results.errors.push({
        field: fieldName,
        message: `Expected number, got ${actualType}`,
        value
      });
      results.valid = false;
    } else if (expectedType === 'integer' && (!Number.isInteger(value) || actualType !== 'number')) {
      results.errors.push({
        field: fieldName,
        message: `Expected integer, got ${actualType}`,
        value
      });
      results.valid = false;
    } else if (expectedType === 'string' && actualType !== 'string') {
      results.errors.push({
        field: fieldName,
        message: `Expected string, got ${actualType}`,
        value
      });
      results.valid = false;
    } else if (expectedType === 'boolean' && actualType !== 'boolean') {
      results.errors.push({
        field: fieldName,
        message: `Expected boolean, got ${actualType}`,
        value
      });
      results.valid = false;
    }

    // Validate constraints
    if (fieldSchema.minimum !== undefined && value < fieldSchema.minimum) {
      results.errors.push({
        field: fieldName,
        message: `Value must be at least ${fieldSchema.minimum}`,
        value
      });
      results.valid = false;
    }

    if (fieldSchema.maximum !== undefined && value > fieldSchema.maximum) {
      results.errors.push({
        field: fieldName,
        message: `Value must be no more than ${fieldSchema.maximum}`,
        value
      });
      results.valid = false;
    }

    if (fieldSchema.minLength !== undefined && typeof value === 'string' && value.length < fieldSchema.minLength) {
      results.errors.push({
        field: fieldName,
        message: `String must be at least ${fieldSchema.minLength} characters`,
        value
      });
      results.valid = false;
    }

    return results;
  }

  validateArrayItem(item, itemSchema, fieldPath) {
    const results = {
      valid: true,
      errors: []
    };

    if (itemSchema.type) {
      if (Array.isArray(itemSchema.type)) {
        // Union type - value must match one of the types
        const validTypes = itemSchema.type.some(type => {
          if (type === 'integer') {
            return Number.isInteger(item);
          } else if (type === 'number') {
            return typeof item === 'number';
          } else {
            return typeof item === type;
          }
        });

        if (!validTypes) {
          results.errors.push({
            field: fieldPath,
            message: `Expected one of [${itemSchema.type.join(', ')}], got ${typeof item}`,
            value: item
          });
          results.valid = false;
        }
      } else {
        const expectedType = itemSchema.type;
        const actualType = typeof item;

        if (expectedType === 'integer' && !Number.isInteger(item)) {
          results.errors.push({
            field: fieldPath,
            message: `Expected integer, got ${actualType}`,
            value: item
          });
          results.valid = false;
        } else if (expectedType !== 'integer' && actualType !== expectedType) {
          results.errors.push({
            field: fieldPath,
            message: `Expected ${expectedType}, got ${actualType}`,
            value: item
          });
          results.valid = false;
        }
      }
    }

    return results;
  }

  // Utility methods
  getAvailableModels() {
    return Array.from(this.compiledSchemas.keys());
  }

  getModelSchema(modelName) {
    return ODOO_SCHEMAS[modelName];
  }

  addCustomSchema(modelName, schema) {
    try {
      const compiled = ajv.compile(schema);
      this.compiledSchemas.set(modelName, compiled);
      ODOO_SCHEMAS[modelName] = schema;
      return true;
    } catch (error) {
      console.error(chalk.red(`Failed to add custom schema for ${modelName}:`, error.message));
      return false;
    }
  }

  generateSampleData(modelName) {
    const schema = ODOO_SCHEMAS[modelName];
    if (!schema) return null;

    const sampleData = {};
    
    if (schema.properties) {
      Object.entries(schema.properties).forEach(([field, fieldSchema]) => {
        sampleData[field] = this.generateSampleValue(fieldSchema, field);
      });
    }

    return sampleData;
  }

  generateSampleValue(fieldSchema, fieldName) {
    const type = fieldSchema.type;
    
    switch (type) {
      case 'string':
        if (fieldSchema.format === 'email') return 'example@domain.com';
        if (fieldSchema.format === 'uri') return 'https://example.com';
        if (fieldSchema.format === 'date') return '2024-01-01';
        if (fieldSchema.format === 'date-time') return '2024-01-01T10:00:00Z';
        if (fieldSchema.enum) return fieldSchema.enum[0];
        return `Sample ${fieldName}`;
        
      case 'number':
      case 'integer':
        const min = fieldSchema.minimum || 0;
        const max = fieldSchema.maximum || 100;
        return type === 'integer' ? Math.floor(min + Math.random() * (max - min)) : min + Math.random() * (max - min);
        
      case 'boolean':
        return true;
        
      case 'array':
        if (fieldSchema.items?.type?.includes('integer')) {
          return [1, 'Sample Name']; // Many2one format
        }
        return [];
        
      default:
        return null;
    }
  }
}

export default SchemaValidator;