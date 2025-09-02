/**
 * Base Validation Framework for Odoo Data Ingestion
 * Provides core validation utilities and patterns for all data types
 */

import { z } from 'zod';
import chalk from 'chalk';

export class ValidationError extends Error {
  constructor(message, field, value, code = 'VALIDATION_ERROR') {
    super(message);
    this.name = 'ValidationError';
    this.field = field;
    this.value = value;
    this.code = code;
  }
}

export class ValidationReport {
  constructor() {
    this.errors = [];
    this.warnings = [];
    this.infos = [];
    this.totalRecords = 0;
    this.validRecords = 0;
    this.invalidRecords = 0;
    this.startTime = Date.now();
  }

  addError(field, message, value, recordId = null) {
    this.errors.push({
      type: 'error',
      field,
      message,
      value,
      recordId,
      timestamp: new Date().toISOString()
    });
  }

  addWarning(field, message, value, recordId = null) {
    this.warnings.push({
      type: 'warning', 
      field,
      message,
      value,
      recordId,
      timestamp: new Date().toISOString()
    });
  }

  addInfo(message, context = null) {
    this.infos.push({
      type: 'info',
      message,
      context,
      timestamp: new Date().toISOString()
    });
  }

  hasErrors() {
    return this.errors.length > 0;
  }

  hasWarnings() {
    return this.warnings.length > 0;
  }

  getStats() {
    const duration = Date.now() - this.startTime;
    return {
      totalRecords: this.totalRecords,
      validRecords: this.validRecords,
      invalidRecords: this.invalidRecords,
      errorCount: this.errors.length,
      warningCount: this.warnings.length,
      successRate: this.totalRecords > 0 ? (this.validRecords / this.totalRecords) * 100 : 0,
      duration
    };
  }

  printSummary() {
    const stats = this.getStats();
    
    console.log(chalk.blue('\n=== VALIDATION SUMMARY ==='));
    console.log(chalk.gray(`Total Records: ${stats.totalRecords}`));
    console.log(chalk.green(`Valid Records: ${stats.validRecords}`));
    console.log(chalk.red(`Invalid Records: ${stats.invalidRecords}`));
    console.log(chalk.yellow(`Warnings: ${stats.warningCount}`));
    console.log(chalk.blue(`Success Rate: ${stats.successRate.toFixed(2)}%`));
    console.log(chalk.gray(`Duration: ${stats.duration}ms`));

    if (this.errors.length > 0) {
      console.log(chalk.red('\n=== ERRORS ==='));
      this.errors.forEach(error => {
        console.log(chalk.red(`❌ ${error.field}: ${error.message}`));
        if (error.recordId) {
          console.log(chalk.gray(`   Record ID: ${error.recordId}`));
        }
        if (error.value !== undefined) {
          console.log(chalk.gray(`   Value: ${JSON.stringify(error.value)}`));
        }
      });
    }

    if (this.warnings.length > 0) {
      console.log(chalk.yellow('\n=== WARNINGS ==='));
      this.warnings.forEach(warning => {
        console.log(chalk.yellow(`⚠️  ${warning.field}: ${warning.message}`));
        if (warning.recordId) {
          console.log(chalk.gray(`   Record ID: ${warning.recordId}`));
        }
      });
    }

    if (this.infos.length > 0) {
      console.log(chalk.blue('\n=== INFO ==='));
      this.infos.forEach(info => {
        console.log(chalk.blue(`ℹ️  ${info.message}`));
      });
    }
  }

  toJSON() {
    return {
      stats: this.getStats(),
      errors: this.errors,
      warnings: this.warnings,
      infos: this.infos
    };
  }
}

export class BaseValidator {
  constructor(options = {}) {
    this.options = {
      strictMode: false,
      allowMissingFields: false,
      customRules: [],
      ...options
    };
    this.report = new ValidationReport();
  }

  // Core validation methods
  async validate(data) {
    this.report = new ValidationReport();
    
    if (!data) {
      this.report.addError('data', 'Data is required', data);
      return this.report;
    }

    if (Array.isArray(data)) {
      return this.validateBatch(data);
    } else {
      return this.validateSingle(data);
    }
  }

  async validateBatch(records) {
    this.report.addInfo(`Starting batch validation of ${records.length} records`);
    this.report.totalRecords = records.length;

    for (let i = 0; i < records.length; i++) {
      try {
        const record = records[i];
        const recordId = this.getRecordId(record, i);
        
        await this.validateRecord(record, recordId);
        
        if (!this.hasRecordErrors(recordId)) {
          this.report.validRecords++;
        } else {
          this.report.invalidRecords++;
        }
      } catch (error) {
        this.report.addError('record', `Validation failed: ${error.message}`, records[i], i);
        this.report.invalidRecords++;
      }
    }

    return this.report;
  }

  async validateSingle(record) {
    this.report.totalRecords = 1;
    
    try {
      const recordId = this.getRecordId(record, 0);
      await this.validateRecord(record, recordId);
      
      if (!this.hasRecordErrors(recordId)) {
        this.report.validRecords = 1;
      } else {
        this.report.invalidRecords = 1;
      }
    } catch (error) {
      this.report.addError('record', `Validation failed: ${error.message}`, record, 0);
      this.report.invalidRecords = 1;
    }

    return this.report;
  }

  // Override in subclasses
  async validateRecord(record, recordId) {
    throw new Error('validateRecord must be implemented by subclass');
  }

  getRecordId(record, index) {
    return record.id || record.sku || record.code || record.name || `record_${index}`;
  }

  hasRecordErrors(recordId) {
    return this.report.errors.some(error => error.recordId === recordId);
  }

  // Common validation utilities
  validateRequired(value, field, recordId) {
    if (value === null || value === undefined || value === '') {
      this.report.addError(field, 'Field is required', value, recordId);
      return false;
    }
    return true;
  }

  validateString(value, field, recordId, options = {}) {
    if (!this.validateRequired(value, field, recordId) && !options.optional) {
      return false;
    }

    if (value && typeof value !== 'string') {
      this.report.addError(field, 'Field must be a string', value, recordId);
      return false;
    }

    if (options.minLength && value && value.length < options.minLength) {
      this.report.addError(field, `Field must be at least ${options.minLength} characters`, value, recordId);
      return false;
    }

    if (options.maxLength && value && value.length > options.maxLength) {
      this.report.addError(field, `Field must be no more than ${options.maxLength} characters`, value, recordId);
      return false;
    }

    if (options.pattern && value && !options.pattern.test(value)) {
      this.report.addError(field, 'Field does not match required pattern', value, recordId);
      return false;
    }

    return true;
  }

  validateNumber(value, field, recordId, options = {}) {
    if (!this.validateRequired(value, field, recordId) && !options.optional) {
      return false;
    }

    if (value !== null && value !== undefined && typeof value !== 'number') {
      this.report.addError(field, 'Field must be a number', value, recordId);
      return false;
    }

    if (options.min !== undefined && value < options.min) {
      this.report.addError(field, `Field must be at least ${options.min}`, value, recordId);
      return false;
    }

    if (options.max !== undefined && value > options.max) {
      this.report.addError(field, `Field must be no more than ${options.max}`, value, recordId);
      return false;
    }

    if (options.positive && value <= 0) {
      this.report.addError(field, 'Field must be positive', value, recordId);
      return false;
    }

    return true;
  }

  validateEmail(value, field, recordId, optional = true) {
    if (!value && optional) return true;
    
    if (!this.validateRequired(value, field, recordId) && !optional) {
      return false;
    }

    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (value && !emailPattern.test(value)) {
      this.report.addError(field, 'Invalid email format', value, recordId);
      return false;
    }

    return true;
  }

  validateEnum(value, field, recordId, allowedValues, optional = false) {
    if (!value && optional) return true;
    
    if (!this.validateRequired(value, field, recordId) && !optional) {
      return false;
    }

    if (value && !allowedValues.includes(value)) {
      this.report.addError(field, `Field must be one of: ${allowedValues.join(', ')}`, value, recordId);
      return false;
    }

    return true;
  }

  validateDate(value, field, recordId, optional = true) {
    if (!value && optional) return true;
    
    if (!this.validateRequired(value, field, recordId) && !optional) {
      return false;
    }

    if (value) {
      const date = new Date(value);
      if (isNaN(date.getTime())) {
        this.report.addError(field, 'Invalid date format', value, recordId);
        return false;
      }
    }

    return true;
  }

  validateArray(value, field, recordId, options = {}) {
    if (!value && options.optional) return true;
    
    if (!this.validateRequired(value, field, recordId) && !options.optional) {
      return false;
    }

    if (value && !Array.isArray(value)) {
      this.report.addError(field, 'Field must be an array', value, recordId);
      return false;
    }

    if (options.minItems && value && value.length < options.minItems) {
      this.report.addError(field, `Array must have at least ${options.minItems} items`, value, recordId);
      return false;
    }

    if (options.maxItems && value && value.length > options.maxItems) {
      this.report.addError(field, `Array must have no more than ${options.maxItems} items`, value, recordId);
      return false;
    }

    return true;
  }

  // Data quality checks
  checkForDuplicates(records, field) {
    const seen = new Set();
    const duplicates = [];

    records.forEach((record, index) => {
      const value = record[field];
      if (value && seen.has(value)) {
        duplicates.push({ value, record, index });
      } else if (value) {
        seen.add(value);
      }
    });

    if (duplicates.length > 0) {
      duplicates.forEach(dup => {
        this.report.addWarning(field, `Duplicate value found`, dup.value, this.getRecordId(dup.record, dup.index));
      });
    }

    return duplicates.length === 0;
  }

  checkFieldCompleteness(records, requiredFields) {
    const stats = {};
    
    requiredFields.forEach(field => {
      const complete = records.filter(record => 
        record[field] !== null && 
        record[field] !== undefined && 
        record[field] !== ''
      ).length;
      
      stats[field] = {
        complete,
        total: records.length,
        percentage: (complete / records.length) * 100
      };

      if (stats[field].percentage < 90) {
        this.report.addWarning(field, `Low completeness: ${stats[field].percentage.toFixed(1)}%`, null);
      }
    });

    return stats;
  }

  // Custom rule validation
  applyCustomRules(record, recordId) {
    this.options.customRules.forEach(rule => {
      try {
        const result = rule.validate(record);
        if (!result.valid) {
          if (rule.severity === 'error') {
            this.report.addError(rule.field || 'custom', result.message, record[rule.field], recordId);
          } else {
            this.report.addWarning(rule.field || 'custom', result.message, record[rule.field], recordId);
          }
        }
      } catch (error) {
        this.report.addError('custom_rule', `Custom rule failed: ${error.message}`, null, recordId);
      }
    });
  }

  // Utility methods
  sanitizeValue(value, field) {
    if (typeof value === 'string') {
      return value.trim();
    }
    return value;
  }

  suggestCorrection(field, value, context = {}) {
    // Override in subclasses for specific correction suggestions
    return {
      field,
      originalValue: value,
      suggestions: [],
      context
    };
  }
}

export default BaseValidator;