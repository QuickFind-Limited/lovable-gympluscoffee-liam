/**
 * Customer Data Quality Validation for Odoo Ingestion
 * Validates customer/partner data integrity and business compliance
 */

import { BaseValidator } from '../utils/base-validator.js';
import { SchemaValidator } from '../utils/schema-validator.js';
import chalk from 'chalk';

export class CustomerValidator extends BaseValidator {
  constructor(options = {}) {
    super({
      strictMode: true,
      allowMissingFields: false,
      ...options
    });
    
    this.schemaValidator = new SchemaValidator();
    this.requiredFields = ['name', 'email'];
    this.businessRules = this.initializeBusinessRules();
  }

  initializeBusinessRules() {
    return [
      {
        name: 'email_format',
        description: 'Email must be valid format',
        validate: (customer) => {
          if (customer.email) {
            const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
            return {
              valid: emailPattern.test(customer.email),
              message: 'Invalid email format',
              field: 'email'
            };
          }
          return { valid: true };
        },
        severity: 'error'
      },
      {
        name: 'phone_format',
        description: 'Phone number should be valid format',
        validate: (customer) => {
          if (customer.phone) {
            // Basic phone validation - adjust pattern based on requirements
            const phonePattern = /^[\+]?[\d\s\-\(\)]{10,15}$/;
            return {
              valid: phonePattern.test(customer.phone.replace(/\s/g, '')),
              message: 'Invalid phone number format',
              field: 'phone'
            };
          }
          return { valid: true };
        },
        severity: 'warning'
      },
      {
        name: 'vat_validation',
        description: 'VAT number should be valid if provided',
        validate: (customer) => {
          if (customer.vat) {
            // Basic VAT validation - should be expanded based on country requirements
            const vatPattern = /^[A-Z]{2}[0-9A-Z]{2,15}$/;
            return {
              valid: vatPattern.test(customer.vat.replace(/\s/g, '')),
              message: 'Invalid VAT number format (expected: country code + identifier)',
              field: 'vat'
            };
          }
          return { valid: true };
        },
        severity: 'warning'
      },
      {
        name: 'company_consistency',
        description: 'Company flag should be consistent with other fields',
        validate: (customer) => {
          if (customer.is_company === true) {
            // Companies should typically have VAT numbers
            if (!customer.vat && customer.customer_rank > 0) {
              return {
                valid: false,
                message: 'Company customers should typically have VAT numbers',
                field: 'vat'
              };
            }
          }
          return { valid: true };
        },
        severity: 'warning'
      },
      {
        name: 'address_completeness',
        description: 'Address should be reasonably complete',
        validate: (customer) => {
          if (customer.street || customer.city) {
            const hasStreet = !!customer.street;
            const hasCity = !!customer.city;
            const hasCountry = !!customer.country_id;
            
            if (hasStreet && !hasCity) {
              return {
                valid: false,
                message: 'Street provided but city is missing',
                field: 'city'
              };
            }
            
            if ((hasStreet || hasCity) && !hasCountry) {
              return {
                valid: false,
                message: 'Address provided but country is missing',
                field: 'country_id'
              };
            }
          }
          return { valid: true };
        },
        severity: 'warning'
      },
      {
        name: 'rank_validation',
        description: 'Customer/Supplier ranks should be valid',
        validate: (customer) => {
          const customerRank = customer.customer_rank || 0;
          const supplierRank = customer.supplier_rank || 0;
          
          if (customerRank < 0 || supplierRank < 0) {
            return {
              valid: false,
              message: 'Customer and supplier ranks must be non-negative',
              field: customerRank < 0 ? 'customer_rank' : 'supplier_rank'
            };
          }
          
          if (customerRank === 0 && supplierRank === 0) {
            return {
              valid: false,
              message: 'Partner must be either a customer or supplier (or both)',
              field: 'customer_rank'
            };
          }
          
          return { valid: true };
        },
        severity: 'error'
      }
    ];
  }

  async validateRecord(customer, recordId) {
    // Basic field validation
    await this.validateBasicFields(customer, recordId);
    
    // Schema validation against Odoo res.partner model
    await this.validateAgainstOdooSchema(customer, recordId);
    
    // Business rule validation
    await this.validateBusinessRules(customer, recordId);
    
    // Data quality checks
    await this.validateDataQuality(customer, recordId);
    
    // Custom validation rules
    this.applyCustomRules(customer, recordId);
  }

  async validateBasicFields(customer, recordId) {
    // Required fields
    this.validateRequired(customer.name, 'name', recordId);
    this.validateRequired(customer.email, 'email', recordId);
    
    // String fields with constraints
    this.validateString(customer.name, 'name', recordId, {
      minLength: 2,
      maxLength: 200
    });
    
    // Email validation
    this.validateEmail(customer.email, 'email', recordId, false);
    
    // Optional string fields
    this.validateString(customer.street, 'street', recordId, {
      optional: true,
      maxLength: 200
    });
    
    this.validateString(customer.street2, 'street2', recordId, {
      optional: true,
      maxLength: 200
    });
    
    this.validateString(customer.city, 'city', recordId, {
      optional: true,
      maxLength: 100
    });
    
    this.validateString(customer.zip, 'zip', recordId, {
      optional: true,
      maxLength: 20
    });
    
    this.validateString(customer.phone, 'phone', recordId, {
      optional: true,
      maxLength: 30
    });
    
    this.validateString(customer.mobile, 'mobile', recordId, {
      optional: true,
      maxLength: 30
    });
    
    this.validateString(customer.website, 'website', recordId, {
      optional: true,
      maxLength: 200
    });
    
    this.validateString(customer.vat, 'vat', recordId, {
      optional: true,
      maxLength: 20
    });
    
    // Numeric fields
    this.validateNumber(customer.customer_rank, 'customer_rank', recordId, {
      min: 0,
      optional: true
    });
    
    this.validateNumber(customer.supplier_rank, 'supplier_rank', recordId, {
      min: 0,
      optional: true
    });
    
    // Boolean fields
    if (customer.is_company !== undefined && typeof customer.is_company !== 'boolean') {
      this.report.addError('is_company', 'Field must be boolean', customer.is_company, recordId);
    }
    
    if (customer.active !== undefined && typeof customer.active !== 'boolean') {
      this.report.addError('active', 'Field must be boolean', customer.active, recordId);
    }
    
    // Array fields (for category_id)
    this.validateArray(customer.category_id, 'category_id', recordId, {
      optional: true
    });
    
    // Website URL validation
    if (customer.website) {
      try {
        new URL(customer.website);
      } catch {
        this.report.addError('website', 'Invalid URL format', customer.website, recordId);
      }
    }
  }

  async validateAgainstOdooSchema(customer, recordId) {
    // Convert to Odoo format
    const odooCustomer = this.convertToOdooFormat(customer);
    
    // Validate against Odoo schema
    const schemaResult = this.schemaValidator.validateAgainstSchema(odooCustomer, 'res.partner');
    
    if (!schemaResult.valid) {
      schemaResult.errors.forEach(error => {
        this.report.addError(error.field, error.message, error.value, recordId);
      });
    }
    
    schemaResult.warnings.forEach(warning => {
      this.report.addWarning(warning.field, warning.message, warning.value, recordId);
    });
  }

  async validateBusinessRules(customer, recordId) {
    this.businessRules.forEach(rule => {
      try {
        const result = rule.validate(customer);
        if (!result.valid) {
          if (rule.severity === 'error') {
            this.report.addError(result.field, result.message, customer[result.field], recordId);
          } else {
            this.report.addWarning(result.field, result.message, customer[result.field], recordId);
          }
        }
      } catch (error) {
        this.report.addError('business_rule', `Rule '${rule.name}' failed: ${error.message}`, null, recordId);
      }
    });
  }

  async validateDataQuality(customer, recordId) {
    // Check for suspicious values
    this.checkSuspiciousValues(customer, recordId);
    
    // Validate contact information consistency
    this.validateContactConsistency(customer, recordId);
    
    // Check for data completeness
    this.checkDataCompleteness(customer, recordId);
    
    // Validate geographical consistency
    this.validateGeographicalData(customer, recordId);
  }

  checkSuspiciousValues(customer, recordId) {
    // Check for placeholder or test values
    const placeholderPatterns = [
      /^(test|sample|placeholder|dummy|temp)/i,
      /^(lorem|ipsum)/i,
      /^(customer|partner|company)\s*\d*$/i,
      /^(john|jane)\s+(doe|smith)$/i
    ];
    
    ['name', 'street', 'city'].forEach(field => {
      if (customer[field]) {
        const isSuspicious = placeholderPatterns.some(pattern => 
          pattern.test(customer[field].trim())
        );
        
        if (isSuspicious) {
          this.report.addWarning(field, 'Suspicious placeholder-like value detected', 
            customer[field], recordId);
        }
      }
    });
    
    // Check for suspicious email patterns
    if (customer.email) {
      const suspiciousEmailPatterns = [
        /test@/i,
        /example\./i,
        /sample@/i,
        /noreply@/i,
        /@test\./i
      ];
      
      const isSuspiciousEmail = suspiciousEmailPatterns.some(pattern => 
        pattern.test(customer.email)
      );
      
      if (isSuspiciousEmail) {
        this.report.addWarning('email', 'Suspicious test-like email address', 
          customer.email, recordId);
      }
    }
  }

  validateContactConsistency(customer, recordId) {
    // Check if at least one contact method is provided
    const hasEmail = !!customer.email;
    const hasPhone = !!customer.phone;
    const hasMobile = !!customer.mobile;
    const hasAddress = !!(customer.street || customer.city);
    
    if (!hasEmail && !hasPhone && !hasMobile && !hasAddress) {
      this.report.addWarning('contact_info', 
        'No contact information provided (email, phone, or address)', 
        null, recordId);
    }
    
    // Check for duplicate contact methods
    if (customer.phone && customer.mobile && customer.phone === customer.mobile) {
      this.report.addWarning('mobile', 'Mobile number is same as phone number', 
        customer.mobile, recordId);
    }
  }

  checkDataCompleteness(customer, recordId) {
    // Check completeness score
    const fields = ['name', 'email', 'phone', 'street', 'city', 'country_id', 'vat'];
    const completed = fields.filter(field => 
      customer[field] && 
      customer[field].toString().trim() !== ''
    ).length;
    
    const completenessScore = (completed / fields.length) * 100;
    
    if (completenessScore < 50) {
      this.report.addWarning('completeness', 
        `Low data completeness: ${completenessScore.toFixed(1)}%`, 
        completenessScore, recordId);
    }
    
    // Company-specific completeness checks
    if (customer.is_company) {
      if (!customer.vat && customer.customer_rank > 0) {
        this.report.addWarning('vat', 'Company customer should have VAT number', 
          null, recordId);
      }
      
      if (!customer.website && customer.supplier_rank > 0) {
        this.report.addInfo('Website URL would be helpful for supplier companies');
      }
    }
  }

  validateGeographicalData(customer, recordId) {
    // Basic geographical consistency checks
    if (customer.zip && customer.country_id) {
      // This would be expanded with actual country-specific ZIP code validation
      const zipPatterns = {
        'US': /^\d{5}(-\d{4})?$/,
        'UK': /^[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}$/i,
        'DE': /^\d{5}$/,
        'FR': /^\d{5}$/,
        'IE': /^[A-Z]\d{2}\s?[A-Z\d]{4}$/i
      };
      
      // This is a simplified check - in practice, you'd need to resolve country_id to country code
      if (customer.country_code && zipPatterns[customer.country_code]) {
        const pattern = zipPatterns[customer.country_code];
        if (!pattern.test(customer.zip)) {
          this.report.addWarning('zip', 
            `ZIP code format may not match country: ${customer.country_code}`, 
            customer.zip, recordId);
        }
      }
    }
  }

  convertToOdooFormat(customer) {
    return {
      name: customer.name,
      is_company: customer.is_company || false,
      email: customer.email,
      phone: customer.phone,
      mobile: customer.mobile,
      street: customer.street,
      street2: customer.street2,
      city: customer.city,
      zip: customer.zip,
      state_id: customer.state_id || false,
      country_id: customer.country_id || false,
      website: customer.website,
      vat: customer.vat,
      customer_rank: customer.customer_rank || 0,
      supplier_rank: customer.supplier_rank || 0,
      category_id: customer.category_id || [],
      active: customer.active !== false
    };
  }

  // Utility methods for customer-specific validations
  validateCustomerRelationships(customers) {
    // Check for parent-child relationships consistency
    customers.forEach((customer, index) => {
      if (customer.parent_id) {
        const parentExists = customers.some(c => 
          c.id === customer.parent_id || 
          c.name === customer.parent_id
        );
        
        if (!parentExists) {
          this.report.addWarning('parent_id', 
            'Parent customer not found in dataset',
            customer.parent_id, 
            this.getRecordId(customer, index));
        }
      }
    });
  }

  checkForDuplicateContacts(customers) {
    const emailMap = new Map();
    const phoneMap = new Map();
    const vatMap = new Map();
    
    customers.forEach((customer, index) => {
      const recordId = this.getRecordId(customer, index);
      
      // Check email duplicates
      if (customer.email) {
        const email = customer.email.toLowerCase().trim();
        if (emailMap.has(email)) {
          this.report.addWarning('email', 'Duplicate email address found',
            customer.email, recordId);
        } else {
          emailMap.set(email, recordId);
        }
      }
      
      // Check phone duplicates
      if (customer.phone) {
        const phone = customer.phone.replace(/\D/g, ''); // Remove non-digits
        if (phone.length >= 10) {
          if (phoneMap.has(phone)) {
            this.report.addWarning('phone', 'Duplicate phone number found',
              customer.phone, recordId);
          } else {
            phoneMap.set(phone, recordId);
          }
        }
      }
      
      // Check VAT duplicates
      if (customer.vat) {
        const vat = customer.vat.replace(/\s/g, '').toUpperCase();
        if (vatMap.has(vat)) {
          this.report.addWarning('vat', 'Duplicate VAT number found',
            customer.vat, recordId);
        } else {
          vatMap.set(vat, recordId);
        }
      }
    });
  }

  suggestCorrection(field, value, context = {}) {
    const suggestions = [];
    
    switch (field) {
      case 'email':
        if (value && typeof value === 'string') {
          // Common email typos
          const commonDomains = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com'];
          const corrected = value.toLowerCase().trim();
          
          if (corrected.includes('@') && !corrected.match(/\.[a-z]{2,}$/)) {
            suggestions.push(...commonDomains.map(domain => 
              corrected.split('@')[0] + '@' + domain
            ));
          }
        }
        break;
        
      case 'phone':
        if (value && typeof value === 'string') {
          const digits = value.replace(/\D/g, '');
          if (digits.length === 10) {
            suggestions.push(`+1${digits}`, `(${digits.slice(0,3)}) ${digits.slice(3,6)}-${digits.slice(6)}`);
          }
        }
        break;
        
      case 'zip':
        if (value && context.country_code === 'US') {
          const digits = value.replace(/\D/g, '');
          if (digits.length === 5) {
            suggestions.push(digits);
          } else if (digits.length === 9) {
            suggestions.push(`${digits.slice(0,5)}-${digits.slice(5)}`);
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

  async generateValidationReport(customers) {
    console.log(chalk.blue('\n🔍 Starting Customer Validation...'));
    
    const report = await this.validate(customers);
    
    // Additional batch validations
    if (Array.isArray(customers)) {
      this.checkForDuplicateContacts(customers);
      this.validateCustomerRelationships(customers);
      this.checkFieldCompleteness(customers, this.requiredFields);
    }
    
    console.log(chalk.green('\n✅ Customer validation completed'));
    report.printSummary();
    
    return report;
  }
}

// CLI functionality
export async function validateCustomerFile(filePath, options = {}) {
  try {
    const fs = await import('fs');
    const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    
    const validator = new CustomerValidator(options);
    let customers;
    
    // Handle different JSON structures
    if (data.customers || data.partners) {
      customers = data.customers || data.partners;
    } else if (Array.isArray(data)) {
      customers = data;
    } else {
      customers = [data];
    }
    
    const report = await validator.generateValidationReport(customers);
    
    // Save report if requested
    if (options.outputFile) {
      fs.writeFileSync(options.outputFile, JSON.stringify(report.toJSON(), null, 2));
      console.log(chalk.blue(`\n📁 Report saved to: ${options.outputFile}`));
    }
    
    return report;
    
  } catch (error) {
    console.error(chalk.red(`❌ Error validating customers: ${error.message}`));
    throw error;
  }
}

export default CustomerValidator;