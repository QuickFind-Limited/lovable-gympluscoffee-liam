#!/usr/bin/env node

/**
 * Command Line Interface for Odoo Ingestion Validation
 * Provides easy access to all validation tools and utilities
 */

import { Command } from 'commander';
const program = new Command();
import { validateProductFile } from './validators/product-validator.js';
import { validateCustomerFile } from './validators/customer-validator.js'; 
import { validateOrderFile } from './validators/order-validator.js';
import { validateInventoryFile } from './validators/inventory-validator.js';
import { runIntegrationTest } from './integration/test-validation-pipeline.js';
import { TestDataGenerator } from './fixtures/generate-test-data.js';
import chalk from 'chalk';
import { existsSync } from 'fs';
import { readFileSync } from 'fs';

// Version from package.json
const packagePath = new URL('./package.json', import.meta.url);
const packageInfo = JSON.parse(readFileSync(packagePath, 'utf8'));

program
  .name('odoo-validation')
  .description('Comprehensive validation tools for Odoo data ingestion')
  .version(packageInfo.version);

// Product validation command
program
  .command('validate-products')
  .description('Validate product data for Odoo ingestion')
  .argument('<file>', 'JSON file containing product data')
  .option('-o, --output <file>', 'Output report file (JSON format)')
  .option('-s, --strict', 'Enable strict validation mode', false)
  .option('--allow-missing', 'Allow missing optional fields', false)
  .option('--custom-rules <file>', 'JSON file with custom validation rules')
  .action(async (file, options) => {
    try {
      console.log(chalk.blue(`🏷️ Validating products from: ${file}\n`));
      
      if (!existsSync(file)) {
        throw new Error(`File not found: ${file}`);
      }

      const validationOptions = {
        strictMode: options.strict,
        allowMissingFields: options.allowMissing,
        outputFile: options.output
      };

      // Load custom rules if provided
      if (options.customRules) {
        if (!existsSync(options.customRules)) {
          throw new Error(`Custom rules file not found: ${options.customRules}`);
        }
        const customRules = JSON.parse(readFileSync(options.customRules, 'utf8'));
        validationOptions.customRules = customRules;
      }

      const report = await validateProductFile(file, validationOptions);
      
      const stats = report.getStats();
      console.log(chalk.blue(`\n📊 Validation Summary:`));
      console.log(`✅ Success Rate: ${stats.successRate.toFixed(1)}%`);
      console.log(`❌ Errors: ${stats.errorCount}`);
      console.log(`⚠️ Warnings: ${stats.warningCount}`);
      
      if (report.hasErrors()) {
        process.exit(1);
      }
    } catch (error) {
      console.error(chalk.red(`❌ Error: ${error.message}`));
      process.exit(1);
    }
  });

// Customer validation command
program
  .command('validate-customers')
  .description('Validate customer/partner data for Odoo ingestion')
  .argument('<file>', 'JSON file containing customer data')
  .option('-o, --output <file>', 'Output report file (JSON format)')
  .option('-s, --strict', 'Enable strict validation mode', false)
  .option('--allow-missing', 'Allow missing optional fields', false)
  .option('--custom-rules <file>', 'JSON file with custom validation rules')
  .action(async (file, options) => {
    try {
      console.log(chalk.blue(`👥 Validating customers from: ${file}\n`));
      
      if (!existsSync(file)) {
        throw new Error(`File not found: ${file}`);
      }

      const validationOptions = {
        strictMode: options.strict,
        allowMissingFields: options.allowMissing,
        outputFile: options.output
      };

      if (options.customRules) {
        if (!existsSync(options.customRules)) {
          throw new Error(`Custom rules file not found: ${options.customRules}`);
        }
        const customRules = JSON.parse(readFileSync(options.customRules, 'utf8'));
        validationOptions.customRules = customRules;
      }

      const report = await validateCustomerFile(file, validationOptions);
      
      const stats = report.getStats();
      console.log(chalk.blue(`\n📊 Validation Summary:`));
      console.log(`✅ Success Rate: ${stats.successRate.toFixed(1)}%`);
      console.log(`❌ Errors: ${stats.errorCount}`);
      console.log(`⚠️ Warnings: ${stats.warningCount}`);
      
      if (report.hasErrors()) {
        process.exit(1);
      }
    } catch (error) {
      console.error(chalk.red(`❌ Error: ${error.message}`));
      process.exit(1);
    }
  });

// Order validation command
program
  .command('validate-orders')
  .description('Validate purchase order data for Odoo ingestion')
  .argument('<file>', 'JSON file containing order data')
  .option('-o, --output <file>', 'Output report file (JSON format)')
  .option('-s, --strict', 'Enable strict validation mode', false)
  .option('--allow-missing', 'Allow missing optional fields', false)
  .option('--custom-rules <file>', 'JSON file with custom validation rules')
  .action(async (file, options) => {
    try {
      console.log(chalk.blue(`📋 Validating orders from: ${file}\n`));
      
      if (!existsSync(file)) {
        throw new Error(`File not found: ${file}`);
      }

      const validationOptions = {
        strictMode: options.strict,
        allowMissingFields: options.allowMissing,
        outputFile: options.output
      };

      if (options.customRules) {
        if (!existsSync(options.customRules)) {
          throw new Error(`Custom rules file not found: ${options.customRules}`);
        }
        const customRules = JSON.parse(readFileSync(options.customRules, 'utf8'));
        validationOptions.customRules = customRules;
      }

      const report = await validateOrderFile(file, validationOptions);
      
      const stats = report.getStats();
      console.log(chalk.blue(`\n📊 Validation Summary:`));
      console.log(`✅ Success Rate: ${stats.successRate.toFixed(1)}%`);
      console.log(`❌ Errors: ${stats.errorCount}`);
      console.log(`⚠️ Warnings: ${stats.warningCount}`);
      
      if (report.hasErrors()) {
        process.exit(1);
      }
    } catch (error) {
      console.error(chalk.red(`❌ Error: ${error.message}`));
      process.exit(1);
    }
  });

// Inventory validation command
program
  .command('validate-inventory')
  .description('Validate inventory/stock data for Odoo ingestion')
  .argument('<file>', 'JSON file containing inventory data')
  .option('-o, --output <file>', 'Output report file (JSON format)')
  .option('-s, --strict', 'Enable strict validation mode', false)
  .option('--allow-missing', 'Allow missing optional fields', false)
  .option('--custom-rules <file>', 'JSON file with custom validation rules')
  .action(async (file, options) => {
    try {
      console.log(chalk.blue(`📦 Validating inventory from: ${file}\n`));
      
      if (!existsSync(file)) {
        throw new Error(`File not found: ${file}`);
      }

      const validationOptions = {
        strictMode: options.strict,
        allowMissingFields: options.allowMissing,
        outputFile: options.output
      };

      if (options.customRules) {
        if (!existsSync(options.customRules)) {
          throw new Error(`Custom rules file not found: ${options.customRules}`);
        }
        const customRules = JSON.parse(readFileSync(options.customRules, 'utf8'));
        validationOptions.customRules = customRules;
      }

      const report = await validateInventoryFile(file, validationOptions);
      
      const stats = report.getStats();
      console.log(chalk.blue(`\n📊 Validation Summary:`));
      console.log(`✅ Success Rate: ${stats.successRate.toFixed(1)}%`);
      console.log(`❌ Errors: ${stats.errorCount}`);
      console.log(`⚠️ Warnings: ${stats.warningCount}`);
      
      if (report.hasErrors()) {
        process.exit(1);
      }
    } catch (error) {
      console.error(chalk.red(`❌ Error: ${error.message}`));
      process.exit(1);
    }
  });

// Validate all command
program
  .command('validate-all')
  .description('Validate all data types from a directory or multiple files')
  .option('-d, --dir <directory>', 'Directory containing data files')
  .option('-p, --products <file>', 'Products JSON file')
  .option('-c, --customers <file>', 'Customers JSON file')
  .option('-o, --orders <file>', 'Orders JSON file')
  .option('-i, --inventory <file>', 'Inventory JSON file')
  .option('--output-dir <dir>', 'Output directory for reports')
  .option('-s, --strict', 'Enable strict validation mode', false)
  .option('--summary-only', 'Only show summary, not detailed reports', false)
  .action(async (options) => {
    try {
      console.log(chalk.blue('🚀 Running comprehensive validation suite...\n'));
      
      const results = {};
      let totalErrors = 0;
      let totalWarnings = 0;
      let totalRecords = 0;
      let validRecords = 0;

      const validationOptions = {
        strictMode: options.strict,
        outputFile: options.outputDir ? null : undefined // Will be set per validator
      };

      // Validate products
      if (options.products && existsSync(options.products)) {
        console.log(chalk.yellow('🏷️ Validating products...'));
        if (options.outputDir) {
          validationOptions.outputFile = `${options.outputDir}/products-report.json`;
        }
        const report = await validateProductFile(options.products, validationOptions);
        results.products = report.getStats();
        
        if (!options.summaryOnly) {
          report.printSummary();
        }
      }

      // Validate customers
      if (options.customers && existsSync(options.customers)) {
        console.log(chalk.yellow('👥 Validating customers...'));
        if (options.outputDir) {
          validationOptions.outputFile = `${options.outputDir}/customers-report.json`;
        }
        const report = await validateCustomerFile(options.customers, validationOptions);
        results.customers = report.getStats();
        
        if (!options.summaryOnly) {
          report.printSummary();
        }
      }

      // Validate orders
      if (options.orders && existsSync(options.orders)) {
        console.log(chalk.yellow('📋 Validating orders...'));
        if (options.outputDir) {
          validationOptions.outputFile = `${options.outputDir}/orders-report.json`;
        }
        const report = await validateOrderFile(options.orders, validationOptions);
        results.orders = report.getStats();
        
        if (!options.summaryOnly) {
          report.printSummary();
        }
      }

      // Validate inventory
      if (options.inventory && existsSync(options.inventory)) {
        console.log(chalk.yellow('📦 Validating inventory...'));
        if (options.outputDir) {
          validationOptions.outputFile = `${options.outputDir}/inventory-report.json`;
        }
        const report = await validateInventoryFile(options.inventory, validationOptions);
        results.inventory = report.getStats();
        
        if (!options.summaryOnly) {
          report.printSummary();
        }
      }

      // Calculate totals
      Object.values(results).forEach(stats => {
        totalErrors += stats.errorCount;
        totalWarnings += stats.warningCount;
        totalRecords += stats.totalRecords;
        validRecords += stats.validRecords;
      });

      const overallSuccessRate = totalRecords > 0 ? (validRecords / totalRecords) * 100 : 0;

      // Print overall summary
      console.log(chalk.blue('\n📊 OVERALL VALIDATION SUMMARY'));
      console.log(chalk.blue('=' .repeat(40)));
      console.log(`📈 Overall Success Rate: ${overallSuccessRate.toFixed(1)}%`);
      console.log(`📋 Total Records: ${totalRecords}`);
      console.log(`✅ Valid Records: ${validRecords}`);
      console.log(`❌ Total Errors: ${totalErrors}`);
      console.log(`⚠️ Total Warnings: ${totalWarnings}`);

      console.log(chalk.blue('\n📊 By Data Type:'));
      Object.entries(results).forEach(([type, stats]) => {
        const icon = stats.successRate >= 80 ? '✅' : stats.successRate >= 60 ? '⚠️' : '❌';
        console.log(`  ${icon} ${type}: ${stats.successRate.toFixed(1)}% (${stats.validRecords}/${stats.totalRecords})`);
      });

      if (totalErrors > 0) {
        console.log(chalk.red('\n⚠️ Validation completed with errors. Review reports before proceeding.'));
        process.exit(1);
      } else {
        console.log(chalk.green('\n✅ All validations completed successfully!'));
      }

    } catch (error) {
      console.error(chalk.red(`❌ Error: ${error.message}`));
      process.exit(1);
    }
  });

// Generate test data command
program
  .command('generate-test-data')
  .description('Generate comprehensive test datasets for validation testing')
  .option('-o, --output <directory>', 'Output directory for test data', './fixtures/generated')
  .option('--products-only', 'Generate only product test data', false)
  .option('--customers-only', 'Generate only customer test data', false)
  .option('--orders-only', 'Generate only order test data', false)
  .option('--inventory-only', 'Generate only inventory test data', false)
  .action(async (options) => {
    try {
      console.log(chalk.blue('📋 Generating test datasets...\n'));
      
      const generator = new TestDataGenerator();
      
      if (options.productsOnly) {
        generator.generateProductTestData();
      } else if (options.customersOnly) {
        generator.generateCustomerTestData();
      } else if (options.ordersOnly) {
        generator.generateOrderTestData();
      } else if (options.inventoryOnly) {
        generator.generateInventoryTestData();
      } else {
        generator.generateAllTestData();
      }
      
      console.log(chalk.green('\n✅ Test data generation completed!'));
    } catch (error) {
      console.error(chalk.red(`❌ Error: ${error.message}`));
      process.exit(1);
    }
  });

// Integration test command
program
  .command('integration-test')
  .description('Run comprehensive integration tests for the validation pipeline')
  .option('--no-test-data', 'Skip test data generation', false)
  .option('--no-save-reports', 'Skip saving validation reports', false)
  .option('-o, --output <directory>', 'Output directory for reports')
  .action(async (options) => {
    try {
      console.log(chalk.blue('🧪 Running integration tests...\n'));
      
      const testOptions = {
        generateTestData: !options.noTestData,
        saveReports: !options.noSaveReports
      };
      
      if (options.output) {
        testOptions.outputDir = options.output;
      }

      const results = await runIntegrationTest();
      
      if (results.success) {
        console.log(chalk.green('\n✅ Integration tests passed!'));
        process.exit(0);
      } else {
        console.log(chalk.red('\n❌ Integration tests failed!'));
        process.exit(1);
      }
    } catch (error) {
      console.error(chalk.red(`❌ Integration test error: ${error.message}`));
      process.exit(1);
    }
  });

// Schema validation command
program
  .command('check-schemas')
  .description('Validate data against Odoo model schemas')
  .argument('<file>', 'JSON file to validate')
  .requiredOption('-m, --model <model>', 'Odoo model name (e.g., product.template, res.partner)')
  .option('-o, --output <file>', 'Output validation report')
  .action(async (file, options) => {
    try {
      console.log(chalk.blue(`🔍 Validating against Odoo schema: ${options.model}\n`));
      
      if (!existsSync(file)) {
        throw new Error(`File not found: ${file}`);
      }

      const { SchemaValidator } = await import('./utils/schema-validator.js');
      const validator = new SchemaValidator();
      
      const data = JSON.parse(readFileSync(file, 'utf8'));
      const records = Array.isArray(data) ? data : [data];
      
      let totalValid = 0;
      let totalErrors = 0;
      
      records.forEach((record, index) => {
        const result = validator.validateAgainstSchema(record, options.model);
        
        if (result.valid) {
          totalValid++;
          console.log(chalk.green(`✅ Record ${index + 1}: Valid`));
        } else {
          totalErrors += result.errors.length;
          console.log(chalk.red(`❌ Record ${index + 1}: ${result.errors.length} errors`));
          result.errors.forEach(error => {
            console.log(chalk.red(`   • ${error.field}: ${error.message}`));
          });
        }
        
        if (result.warnings.length > 0) {
          result.warnings.forEach(warning => {
            console.log(chalk.yellow(`   ⚠️ ${warning.field}: ${warning.message}`));
          });
        }
      });
      
      console.log(chalk.blue(`\n📊 Schema Validation Summary:`));
      console.log(`✅ Valid Records: ${totalValid}/${records.length}`);
      console.log(`❌ Total Errors: ${totalErrors}`);
      
      if (options.output) {
        const report = {
          model: options.model,
          total_records: records.length,
          valid_records: totalValid,
          total_errors: totalErrors,
          validation_timestamp: new Date().toISOString()
        };
        
        writeFileSync(options.output, JSON.stringify(report, null, 2));
        console.log(chalk.blue(`📄 Report saved: ${options.output}`));
      }
      
      if (totalErrors > 0) {
        process.exit(1);
      }
    } catch (error) {
      console.error(chalk.red(`❌ Error: ${error.message}`));
      process.exit(1);
    }
  });

// Help command with examples
program
  .command('examples')
  .description('Show usage examples')
  .action(() => {
    console.log(chalk.blue('\n📖 USAGE EXAMPLES\n'));
    
    console.log(chalk.yellow('Validate product data:'));
    console.log('  odoo-validation validate-products data/products.json');
    console.log('  odoo-validation validate-products data/products.json --strict -o report.json\n');
    
    console.log(chalk.yellow('Validate all data types:'));
    console.log('  odoo-validation validate-all -p products.json -c customers.json -o orders.json');
    console.log('  odoo-validation validate-all --dir ./data --output-dir ./reports\n');
    
    console.log(chalk.yellow('Generate test data:'));
    console.log('  odoo-validation generate-test-data');
    console.log('  odoo-validation generate-test-data --products-only -o ./test-data\n');
    
    console.log(chalk.yellow('Run integration tests:'));
    console.log('  odoo-validation integration-test');
    console.log('  odoo-validation integration-test --output ./test-reports\n');
    
    console.log(chalk.yellow('Schema validation:'));
    console.log('  odoo-validation check-schemas data.json -m product.template');
    console.log('  odoo-validation check-schemas customers.json -m res.partner -o schema-report.json\n');
  });

// Parse command line arguments
program.parse();