# Odoo Ingestion Validation Framework

A comprehensive validation and testing framework designed to ensure data quality and integrity before importing data into Odoo. This framework provides robust validation for products, customers, orders, and inventory data with detailed error reporting and correction suggestions.

## 🚀 Features

### Core Validation Capabilities
- **Product Data Validation**: SKU formats, pricing logic, category validation, inventory consistency
- **Customer Data Validation**: Email formats, address completeness, VAT numbers, contact information
- **Order Data Validation**: Order total calculations, date consistency, line item validation, state transitions  
- **Inventory Data Validation**: Quantity consistency, stock aging analysis, location validation, lot tracking

### Advanced Features
- **Odoo Schema Compliance**: Validates against actual Odoo model schemas (product.template, res.partner, etc.)
- **Business Rule Engine**: Configurable business rules with custom validation logic
- **Data Quality Analysis**: Completeness scoring, duplicate detection, suspicious value identification
- **Correction Suggestions**: Automated suggestions for common data issues
- **Integration Testing**: Comprehensive pipeline testing with synthetic datasets
- **Performance Monitoring**: Validation speed and memory usage tracking

## 📁 Project Structure

```
odoo-ingestion/tests/
├── package.json              # Dependencies and scripts
├── cli.js                    # Command-line interface
├── README.md                 # This documentation
├── utils/
│   ├── base-validator.js     # Core validation framework
│   └── schema-validator.js   # Odoo schema validation
├── validators/
│   ├── product-validator.js  # Product-specific validation
│   ├── customer-validator.js # Customer/partner validation  
│   ├── order-validator.js    # Purchase order validation
│   └── inventory-validator.js# Stock/inventory validation
├── fixtures/
│   ├── generate-test-data.js # Test data generator
│   └── generated/            # Generated test datasets
├── integration/
│   └── test-validation-pipeline.js # End-to-end testing
└── reports/                  # Validation reports output
```

## 🛠️ Installation

1. Navigate to the tests directory:
```bash
cd odoo-ingestion/tests
```

2. Install dependencies:
```bash
npm install
```

3. Make CLI executable (optional):
```bash
chmod +x cli.js
```

## 🚀 Quick Start

### Generate Test Data
```bash
# Generate comprehensive test datasets
npm run generate:fixtures

# Or use CLI
node cli.js generate-test-data
```

### Validate Data Files

#### Products
```bash
# Basic validation
node cli.js validate-products data/products.json

# Strict mode with output report
node cli.js validate-products data/products.json --strict -o products-report.json
```

#### Customers
```bash
# Validate customer data
node cli.js validate-customers data/customers.json

# With custom validation rules
node cli.js validate-customers data/customers.json --custom-rules custom-rules.json
```

#### Orders
```bash
# Validate purchase orders
node cli.js validate-orders data/orders.json --strict
```

#### Inventory
```bash
# Validate stock/inventory data
node cli.js validate-inventory data/inventory.json
```

### Validate All Data Types
```bash
# Validate all data types from individual files
node cli.js validate-all -p products.json -c customers.json -o orders.json -i inventory.json

# Validate with output directory for reports
node cli.js validate-all -p products.json -c customers.json --output-dir ./reports
```

### Schema Validation
```bash
# Validate against specific Odoo models
node cli.js check-schemas products.json -m product.template
node cli.js check-schemas customers.json -m res.partner -o schema-report.json
```

### Integration Testing
```bash
# Run full validation pipeline test
npm run integration:test

# Or use CLI
node cli.js integration-test --output ./test-reports
```

## 📋 Validation Rules

### Product Validation Rules

#### Required Fields
- `name` - Product name (2-100 characters)
- `sku` - Stock keeping unit (format: PREFIX-IDENTIFIER)
- `category` - Product category from approved list
- `list_price` - Retail price (positive number)
- `standard_cost` - Cost price (positive number)

#### Business Rules
- List price should be greater than or equal to standard cost
- SKU must follow format: `GC10000-BLA-XS` (prefix-color-size)
- Category must be from approved list: hoodies, t-shirts, accessories, etc.
- Description should be 10-1000 characters
- Inventory levels must be non-negative

#### Data Quality Checks
- Detects placeholder/test values
- Validates price reasonableness (margin analysis)
- Checks for duplicate SKUs
- Validates product variations consistency

### Customer Validation Rules

#### Required Fields
- `name` - Customer/company name (2-200 characters)
- `email` - Valid email address

#### Business Rules
- Email must be valid format
- Phone numbers should follow standard formats
- VAT numbers must match country patterns
- Companies should have VAT numbers for B2B customers
- At least one contact method required (email/phone/address)
- Customer rank or supplier rank must be > 0

#### Data Quality Checks
- Detects duplicate email addresses and phone numbers
- Validates address completeness
- Checks for suspicious test/placeholder data
- Validates geographical consistency (ZIP codes)

### Order Validation Rules

#### Required Fields
- `partner_id` - Supplier/partner reference ([id, name] format)
- `date_order` - Order date
- `order_line` - Array of order lines (minimum 1)

#### Business Rules  
- Order total must match sum of line items
- Planned date cannot be before order date
- Order lines must have valid products and quantities
- State must be valid Odoo purchase order state
- Quantities must be positive and reasonable

#### Data Quality Checks
- Detects suspiciously round numbers
- Validates currency consistency
- Checks for duplicate products in order lines
- Analyzes order patterns and anomalies

### Inventory Validation Rules

#### Required Fields
- `product_id` - Product reference ([id, name] format)
- `location_id` - Location reference ([id, name] format)  
- `quantity` - Stock quantity

#### Business Rules
- Available quantity = Total quantity - Reserved quantity
- Reserved quantity cannot exceed total quantity
- Negative stock only allowed when explicitly permitted
- Stock records should have reasonable in-dates

#### Data Quality Checks
- Identifies very old stock (aging analysis)
- Detects impossible quantity combinations
- Validates lot tracking consistency
- Checks for duplicate stock records

## 🔧 Configuration

### Custom Validation Rules

Create a JSON file with custom rules:

```json
{
  "customRules": [
    {
      "name": "brand_validation",
      "field": "name", 
      "validate": "function(product) { return { valid: product.name.includes('GymCoffee'), message: 'Product name must include brand' }; }",
      "severity": "warning"
    }
  ]
}
```

### Validation Options

```javascript
const options = {
  strictMode: true,           // Enforce strict validation
  allowMissingFields: false,  // Allow optional fields to be missing
  customRules: [],           // Array of custom validation rules
  outputFile: 'report.json'  // Save validation report
};
```

## 📊 Validation Reports

### Report Structure

```json
{
  "stats": {
    "totalRecords": 100,
    "validRecords": 85,
    "invalidRecords": 15,
    "errorCount": 23,
    "warningCount": 12,
    "successRate": 85.0,
    "duration": 1250
  },
  "errors": [
    {
      "type": "error",
      "field": "sku",
      "message": "Invalid SKU format",
      "value": "invalid-sku",
      "recordId": "product_001",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ],
  "warnings": [...],
  "infos": [...]
}
```

### Report Types
- **Detailed Reports**: Complete validation results with all errors and warnings
- **Summary Reports**: High-level statistics and key findings
- **Schema Reports**: Validation against Odoo model schemas
- **Integration Reports**: End-to-end pipeline testing results

## 🧪 Testing

### Unit Tests
```bash
npm test
```

### Integration Tests
```bash
npm run integration:test
```

### Watch Mode
```bash
npm run test:watch
```

### Coverage Reports
```bash
npm run test:coverage
```

## 🛠️ Development

### Adding New Validators

1. Create validator class extending `BaseValidator`:

```javascript
import { BaseValidator } from '../utils/base-validator.js';

export class MyCustomValidator extends BaseValidator {
  constructor(options = {}) {
    super(options);
    this.requiredFields = ['field1', 'field2'];
  }

  async validateRecord(record, recordId) {
    // Implement validation logic
    this.validateRequired(record.field1, 'field1', recordId);
    // Add custom business rules
  }
}
```

2. Add CLI command in `cli.js`
3. Create test cases with known issues
4. Add to integration test suite

### Adding Business Rules

```javascript
const customRule = {
  name: 'my_business_rule',
  description: 'Validates my business requirement',
  validate: (record) => {
    // Return { valid: boolean, message: string, field: string }
    return {
      valid: record.someField > 0,
      message: 'Some field must be positive',
      field: 'someField'
    };
  },
  severity: 'error' // 'error' or 'warning'
};
```

### Adding Odoo Schema Support

Update `utils/schema-validator.js` to add new Odoo models:

```javascript
export const ODOO_SCHEMAS = {
  'my.custom.model': {
    type: 'object',
    properties: {
      name: { type: 'string', minLength: 1 },
      // Define field schemas
    },
    required: ['name'],
    additionalProperties: true
  }
};
```

## 📚 API Reference

### BaseValidator

Core validation framework class providing common validation methods.

#### Methods
- `validate(data)` - Main validation entry point
- `validateRequired(value, field, recordId)` - Validate required fields
- `validateString(value, field, recordId, options)` - String validation
- `validateNumber(value, field, recordId, options)` - Numeric validation
- `validateEmail(value, field, recordId, optional)` - Email validation
- `validateEnum(value, field, recordId, allowedValues)` - Enumeration validation

### SchemaValidator

Validates data against Odoo model schemas.

#### Methods
- `validateAgainstSchema(data, modelName)` - Schema validation
- `validateFieldTypes(data, modelName)` - Field type validation
- `generateSampleData(modelName)` - Generate sample data for model

### ValidationReport

Contains validation results and statistics.

#### Methods
- `hasErrors()` - Check if validation has errors
- `hasWarnings()` - Check if validation has warnings  
- `getStats()` - Get validation statistics
- `printSummary()` - Print formatted summary
- `toJSON()` - Export results as JSON

## 🐛 Troubleshooting

### Common Issues

**Issue**: "Module not found" errors
**Solution**: Ensure you're running Node.js 16+ with ES modules support

**Issue**: Schema validation fails
**Solution**: Check that your data matches Odoo field formats (e.g., many2one as [id, name])

**Issue**: High memory usage with large datasets
**Solution**: Process data in batches or increase Node.js memory limit

**Issue**: Custom rules not working
**Solution**: Ensure custom rule functions return proper validation result objects

### Debug Mode

Enable debug logging:
```bash
DEBUG=validation* node cli.js validate-products data.json
```

### Performance Tuning

For large datasets:
```bash
node --max-old-space-size=8192 cli.js validate-all --dir ./large-dataset
```

## 🔒 Security Considerations

- Validation functions should not execute untrusted code
- File paths are validated before access
- Custom rules are JSON-only (no code execution)
- Sensitive data is not logged in validation reports
- All file operations use safe path resolution

## 🤝 Contributing

1. Follow the existing code style and patterns
2. Add comprehensive tests for new validators
3. Update documentation for new features
4. Ensure all existing tests pass
5. Add example data for new validation scenarios

## 📄 License

MIT License - see LICENSE file for details.

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review existing validation rules and examples
3. Test with generated sample data first
4. Create detailed issue reports with sample data

## 🗺️ Roadmap

### Planned Features
- [ ] Real-time validation API
- [ ] Web-based validation dashboard  
- [ ] Advanced ML-based anomaly detection
- [ ] Multi-language support for error messages
- [ ] Integration with Odoo API for live validation
- [ ] Automated data correction suggestions
- [ ] Performance benchmarking suite
- [ ] Cloud deployment templates

### Version History
- **v1.0.0** - Initial release with core validation framework
- **v1.1.0** - Added schema validation and CLI improvements
- **v1.2.0** - Integration testing and performance monitoring
- **v1.3.0** - Advanced business rules and correction suggestions