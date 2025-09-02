/**
 * Test Data Generator for Validation Testing
 * Creates comprehensive test datasets with known issues for validation testing
 */

import { writeFileSync, mkdirSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

class TestDataGenerator {
  constructor() {
    this.outputDir = join(__dirname, 'generated');
    this.ensureOutputDir();
  }

  ensureOutputDir() {
    if (!existsSync(this.outputDir)) {
      mkdirSync(this.outputDir, { recursive: true });
    }
  }

  generateProductTestData() {
    const products = {
      catalog_name: "Test Product Dataset",
      version: "1.0.0-test",
      generated_date: new Date().toISOString(),
      total_skus: 15,
      categories: ["hoodies", "t-shirts", "accessories", "invalid-category"],
      products: [
        // Valid products
        {
          sku: "GC10001-BLA-M",
          name: "Test Essential Hoodie - Black",
          category: "hoodies",
          subcategory: "unisex",
          color: "Black",
          size: "M",
          list_price: 75.00,
          standard_cost: 25.00,
          description: "A comfortable hoodie perfect for testing validation rules",
          features: ["Cotton blend", "Kangaroo pocket"],
          status: "active",
          inventory_on_hand: 100,
          reorder_point: 20,
          lead_time_days: 10,
          created_date: "2024-01-01T10:00:00Z",
          last_modified: "2024-01-02T10:00:00Z"
        },
        {
          sku: "GC10002-RED-L",
          name: "Test Basic Tee - Red",
          category: "t-shirts", 
          subcategory: "womens",
          color: "Red",
          size: "L",
          list_price: 35.00,
          standard_cost: 12.00,
          description: "Basic t-shirt for everyday wear and testing purposes",
          features: ["100% Cotton", "Comfortable fit"],
          status: "active",
          inventory_on_hand: 150,
          reorder_point: 30,
          lead_time_days: 7
        },
        // Products with validation issues
        {
          sku: "invalid-sku-format", // Invalid SKU format
          name: "Test Product With Issues",
          category: "t-shirts",
          list_price: 10.00,
          standard_cost: 15.00, // Cost higher than price (should warn)
          description: "Short", // Too short description
          status: "active",
          inventory_on_hand: -5, // Negative inventory
          reorder_point: 10
        },
        {
          sku: "GC10004-BLU-XS",
          name: "", // Missing name (required field)
          category: "invalid-category", // Invalid category
          list_price: 0, // Zero price (suspicious)
          standard_cost: 0,
          description: "Test product with missing required fields",
          status: "active"
        },
        {
          sku: "GC10005-GRN-S",
          name: "Test Product Placeholder", // Placeholder name
          category: "hoodies",
          list_price: "not-a-number", // Invalid price type
          standard_cost: 20.00,
          description: "Lorem ipsum dolor sit amet", // Placeholder description
          status: "inactive",
          inventory_on_hand: "fifty", // Invalid inventory type
          reorder_point: 25
        },
        {
          sku: "GC10006-WHT-M",
          name: "Test Expensive Item",
          category: "accessories",
          list_price: 15000.00, // Suspiciously high price
          standard_cost: 100.00,
          description: "Very expensive test accessory for validation testing purposes",
          status: "active",
          inventory_on_hand: 1,
          reorder_point: 1
        },
        // Duplicate SKU
        {
          sku: "GC10001-BLA-M", // Duplicate of first product
          name: "Duplicate SKU Test Product",
          category: "hoodies",
          list_price: 80.00,
          standard_cost: 30.00,
          description: "This product has a duplicate SKU which should be flagged",
          status: "active"
        },
        // Product variation inconsistencies
        {
          sku: "GC10007-BLA-XS",
          name: "Different Base Name - Black", // Inconsistent with variation pattern
          category: "t-shirts",
          list_price: 30.00,
          standard_cost: 10.00,
          description: "Product with inconsistent variation naming",
          status: "active"
        },
        {
          sku: "GC10007-RED-S",
          name: "Test Variation Tee - Red", // Different base name
          category: "t-shirts",
          list_price: 30.00,
          standard_cost: 10.00,
          description: "Another variation with different base name",
          status: "active"
        },
        // Edge cases
        {
          sku: "GC10008-BLA-XXXL",
          name: "Test Oversized Item",
          category: "hoodies",
          list_price: 45.00,
          standard_cost: 15.00,
          description: "Item with unusual size that should still be valid for validation testing",
          status: "active",
          inventory_on_hand: 5,
          reorder_point: 2
        },
        {
          sku: "GC10009-PNK-ONE",
          name: "Test Accessory Item",
          category: "accessories",
          size: "One Size", // Size for accessories (should warn in some categories)
          list_price: 25.00,
          standard_cost: 8.00,
          description: "Test accessory with size specification",
          status: "active"
        },
        // Product with future dates (suspicious)
        {
          sku: "GC10010-BLU-M",
          name: "Future Date Product",
          category: "hoodies",
          list_price: 50.00,
          standard_cost: 20.00,
          description: "Product with suspicious future creation date for testing",
          status: "active",
          created_date: "2025-12-31T10:00:00Z", // Future date
          last_modified: "2025-12-31T12:00:00Z"
        },
        // Product with extremely long description
        {
          sku: "GC10011-YEL-L",
          name: "Long Description Test Product",
          category: "t-shirts",
          list_price: 40.00,
          standard_cost: 15.00,
          description: "This is an extremely long product description that exceeds reasonable limits and should trigger validation warnings about content length. ".repeat(20), // Very long description
          status: "active"
        },
        // Product missing standard cost
        {
          sku: "GC10012-BLK-S",
          name: "Missing Cost Product",
          category: "t-shirts",
          list_price: 30.00,
          // standard_cost missing (required field)
          description: "Product missing standard cost for testing validation",
          status: "active",
          inventory_on_hand: 50
        },
        // Product with special characters in name
        {
          sku: "GC10013-PUR-M",
          name: "Test Product with Special Chars! @#$%",
          category: "hoodies",
          list_price: 60.00,
          standard_cost: 22.00,
          description: "Product name contains special characters that may cause issues",
          status: "active"
        }
      ]
    };

    const filePath = join(this.outputDir, 'test-products.json');
    writeFileSync(filePath, JSON.stringify(products, null, 2));
    console.log(`Generated product test data: ${filePath}`);
    return products;
  }

  generateCustomerTestData() {
    const customers = {
      dataset_name: "Test Customer Dataset",
      version: "1.0.0-test", 
      generated_date: new Date().toISOString(),
      total_customers: 12,
      customers: [
        // Valid customers
        {
          id: 1,
          name: "Test Company Ltd.",
          email: "contact@testcompany.com",
          is_company: true,
          phone: "+1-555-123-4567",
          street: "123 Business Avenue",
          city: "New York",
          zip: "10001",
          country_id: [233, "United States"],
          vat: "US123456789",
          customer_rank: 1,
          supplier_rank: 0,
          active: true
        },
        {
          id: 2,
          name: "John Smith",
          email: "john.smith@email.com",
          is_company: false,
          phone: "555-987-6543",
          mobile: "555-123-9876",
          street: "456 Residential Street",
          city: "Los Angeles", 
          zip: "90210",
          country_id: [233, "United States"],
          customer_rank: 1,
          supplier_rank: 0,
          active: true
        },
        // Customers with validation issues
        {
          id: 3,
          name: "Test Customer", // Placeholder-like name
          email: "invalid-email-format", // Invalid email
          is_company: false,
          phone: "123", // Invalid phone format
          street: "",
          city: "",
          customer_rank: 0,
          supplier_rank: 0, // Both ranks zero (should error)
          active: true
        },
        {
          id: 4,
          name: "", // Missing name (required)
          email: "test@example.com", // Suspicious email domain
          is_company: true,
          vat: "INVALID", // Invalid VAT format
          customer_rank: 1,
          supplier_rank: 0,
          active: true
        },
        {
          id: 5,
          name: "Duplicate Email Customer",
          email: "john.smith@email.com", // Duplicate email
          is_company: false,
          phone: "+1-555-123-4567", // Duplicate phone
          customer_rank: 1,
          supplier_rank: 0,
          active: true
        },
        {
          id: 6,
          name: "Future VAT Company",
          email: "info@futurecompany.com",
          is_company: true,
          street: "789 Corporate Blvd",
          city: "Chicago",
          zip: "INVALID", // Invalid ZIP for US
          country_id: [233, "United States"],
          vat: "US987654321",
          customer_rank: 1,
          supplier_rank: 1, // Both customer and supplier
          active: true
        },
        {
          id: 7,
          name: "No Contact Info Customer",
          email: "", // No email
          phone: "", // No phone
          street: "", // No address
          customer_rank: 1,
          supplier_rank: 0,
          active: true
        },
        {
          id: 8,
          name: "Long Name That Exceeds Reasonable Limits For Customer Names And Should Trigger Validation Warnings",
          email: "longname@domain.com",
          is_company: false,
          customer_rank: 1,
          supplier_rank: 0,
          active: true
        },
        {
          id: 9,
          name: "Negative Rank Customer",
          email: "negative@test.com",
          is_company: false,
          customer_rank: -1, // Invalid negative rank
          supplier_rank: 0,
          active: true
        },
        {
          id: 10,
          name: "Website Test Company",
          email: "contact@websitetest.com",
          is_company: true,
          website: "not-a-valid-url", // Invalid URL
          customer_rank: 1,
          supplier_rank: 1,
          active: true
        },
        {
          id: 11,
          name: "Same Phone Mobile Customer", 
          email: "samephone@test.com",
          phone: "555-999-8888",
          mobile: "555-999-8888", // Same as phone (should warn)
          customer_rank: 1,
          supplier_rank: 0,
          active: true
        },
        {
          id: 12,
          name: "Incomplete Company",
          email: "incomplete@company.com",
          is_company: true,
          street: "100 Incomplete Street", // Has address but missing other fields
          customer_rank: 1,
          supplier_rank: 1,
          // Missing VAT for company customer
          active: true
        }
      ]
    };

    const filePath = join(this.outputDir, 'test-customers.json');
    writeFileSync(filePath, JSON.stringify(customers, null, 2));
    console.log(`Generated customer test data: ${filePath}`);
    return customers;
  }

  generateOrderTestData() {
    const orders = {
      dataset_name: "Test Order Dataset",
      version: "1.0.0-test",
      generated_date: new Date().toISOString(),
      total_orders: 8,
      orders: [
        // Valid orders
        {
          id: 1,
          name: "PO00001",
          partner_id: [1, "Test Company Ltd."],
          date_order: "2024-01-15T10:00:00Z",
          date_planned: "2024-01-25T10:00:00Z", 
          state: "draft",
          currency_id: [1, "USD"],
          company_id: [1, "Test Company"],
          order_line: [
            {
              product_id: [1, "Test Product 1"],
              name: "Test Product 1 - Large",
              product_qty: 10,
              product_uom: [1, "Units"],
              price_unit: 25.00,
              date_planned: "2024-01-25T10:00:00Z"
            },
            {
              product_id: [2, "Test Product 2"],
              name: "Test Product 2 - Medium", 
              product_qty: 5,
              product_uom: [1, "Units"],
              price_unit: 50.00,
              date_planned: "2024-01-25T10:00:00Z"
            }
          ],
          amount_untaxed: 500.00,
          amount_tax: 50.00,
          amount_total: 550.00,
          notes: "Standard test order with valid data"
        },
        // Orders with validation issues
        {
          id: 2,
          name: "PO00002",
          partner_id: [2, "Test Supplier"],
          date_order: "2024-01-20T10:00:00Z",
          state: "purchase",
          order_line: [
            {
              product_id: [1, "Test Product 1"],
              name: "Test Product 1",
              product_qty: 20,
              price_unit: 30.00
            }
          ],
          amount_untaxed: 600.00,
          amount_tax: 60.00,
          amount_total: 700.00 // Total doesn't match calculation (should be 660)
        },
        {
          id: 3,
          name: "PO00003",
          partner_id: [3, "Future Supplier"],
          date_order: "2025-06-01T10:00:00Z", // Future date (suspicious)
          date_planned: "2024-01-01T10:00:00Z", // Planned before order date (error)
          state: "invalid_state", // Invalid state
          order_line: [
            {
              product_id: [1, "Test Product"],
              name: "Test Product",
              product_qty: -5, // Negative quantity (error)
              price_unit: 25.00
            }
          ],
          amount_total: -125.00
        },
        {
          id: 4,
          name: "PO00004",
          partner_id: "invalid-format", // Invalid partner_id format
          date_order: "invalid-date", // Invalid date format
          state: "draft",
          order_line: [], // Empty order lines (error)
          amount_total: 0
        },
        {
          id: 5,
          name: "PO00005",
          partner_id: [4, "High Value Supplier"],
          date_order: "2024-01-10T10:00:00Z",
          state: "purchase",
          order_line: [
            {
              product_id: [10, "Expensive Product"],
              name: "Very Expensive Product",
              product_qty: 1,
              price_unit: 75000.00 // Very high price (suspicious)
            }
          ],
          amount_total: 75000.00
        },
        {
          id: 6,
          name: "PO00006",
          partner_id: [5, "Duplicate Product Supplier"],
          date_order: "2024-01-12T10:00:00Z",
          state: "draft",
          order_line: [
            {
              product_id: [1, "Test Product"],
              name: "Test Product", 
              product_qty: 5,
              price_unit: 20.00
            },
            {
              product_id: [1, "Test Product"], // Duplicate product (warning)
              name: "Test Product - Different Description",
              product_qty: 3,
              price_unit: 25.00
            }
          ],
          amount_total: 175.00
        },
        {
          id: 7,
          name: "PO00007",
          partner_id: [6, "Quantity Issue Supplier"],
          date_order: "2024-01-14T10:00:00Z", 
          state: "done", // Marked as done
          date_planned: "2024-02-01T10:00:00Z", // But planned date is future (warning)
          order_line: [
            {
              product_id: [5, "Fractional Product"],
              name: "Product with fractional quantity",
              product_qty: 0.1, // Very small fractional quantity (suspicious)
              price_unit: 100.00
            },
            {
              product_id: [6, "High Quantity Product"],
              name: "Product with high quantity",
              product_qty: 50000, // Unusually high quantity (warning)
              price_unit: 1.00
            }
          ],
          amount_total: 50010.00
        },
        {
          id: 8,
          name: "PO00008",
          partner_id: [7, "Round Numbers Supplier"],
          date_order: "2024-01-16T10:00:00Z",
          state: "purchase",
          order_line: [
            {
              product_id: [7, "Round Number Product"],
              name: "Product with round numbers",
              product_qty: 10,
              price_unit: 100.00 // Round numbers (suspicious)
            }
          ],
          amount_untaxed: 1000.00, // All round numbers
          amount_tax: 100.00,
          amount_total: 1100.00,
          notes: "Order with suspiciously round numbers throughout"
        }
      ]
    };

    const filePath = join(this.outputDir, 'test-orders.json');
    writeFileSync(filePath, JSON.stringify(orders, null, 2));
    console.log(`Generated order test data: ${filePath}`);
    return orders;
  }

  generateInventoryTestData() {
    const inventory = {
      dataset_name: "Test Inventory Dataset",
      version: "1.0.0-test",
      generated_date: new Date().toISOString(),
      total_records: 10,
      stock_records: [
        // Valid inventory records
        {
          id: 1,
          product_id: [1, "Test Product 1"],
          location_id: [1, "Main Warehouse"],
          quantity: 100.0,
          reserved_quantity: 10.0,
          available_quantity: 90.0,
          in_date: "2024-01-01T10:00:00Z"
        },
        {
          id: 2,
          product_id: [2, "Test Product 2"],
          location_id: [2, "Secondary Warehouse"],
          lot_id: [1, "LOT001"],
          quantity: 50.0,
          reserved_quantity: 5.0,
          available_quantity: 45.0,
          in_date: "2024-01-05T10:00:00Z"
        },
        // Inventory with validation issues
        {
          id: 3,
          product_id: [3, "Negative Stock Product"],
          location_id: [1, "Main Warehouse"],
          quantity: -25.0, // Negative stock (may be valid in some cases)
          reserved_quantity: 0.0,
          available_quantity: -25.0,
          in_date: "2024-01-10T10:00:00Z"
        },
        {
          id: 4,
          product_id: [4, "Inconsistent Quantities Product"],
          location_id: [3, "Store Front"],
          quantity: 100.0,
          reserved_quantity: 20.0,
          available_quantity: 90.0, // Should be 80 (100-20)
          in_date: "2024-01-03T10:00:00Z"
        },
        {
          id: 5,
          product_id: [5, "Over-reserved Product"],
          location_id: [1, "Main Warehouse"],
          quantity: 30.0,
          reserved_quantity: 50.0, // Reserved more than available
          available_quantity: -20.0,
          in_date: "2024-01-07T10:00:00Z"
        },
        {
          id: 6,
          product_id: "invalid-format", // Invalid product_id format
          location_id: [2, "Secondary Warehouse"],
          quantity: 75.0,
          reserved_quantity: 0.0,
          available_quantity: 75.0,
          in_date: "2024-01-08T10:00:00Z"
        },
        {
          id: 7,
          product_id: [6, "Very High Stock Product"],
          location_id: [1, "Main Warehouse"],
          quantity: 999999.0, // Suspiciously high quantity
          reserved_quantity: 0.0,
          available_quantity: 999999.0,
          in_date: "2024-01-02T10:00:00Z"
        },
        {
          id: 8,
          product_id: [7, "Old Stock Product"],
          location_id: [4, "Old Warehouse"],
          quantity: 25.0,
          reserved_quantity: 0.0,
          available_quantity: 25.0,
          in_date: "2020-01-01T10:00:00Z" // Very old stock (3+ years)
        },
        {
          id: 9,
          product_id: [8, "Future Date Product"],
          location_id: [1, "Main Warehouse"],
          quantity: 40.0,
          reserved_quantity: 0.0,
          available_quantity: 40.0,
          in_date: "2025-01-01T10:00:00Z" // Future date (error)
        },
        {
          id: 10,
          product_id: [1, "Test Product 1"], // Duplicate product-location
          location_id: [1, "Main Warehouse"], // Same as record 1
          quantity: 20.0,
          reserved_quantity: 0.0,
          available_quantity: 20.0,
          in_date: "2024-01-15T10:00:00Z"
        },
        {
          id: 11,
          product_id: [9, "Fractional Quantity Product"],
          location_id: [1, "Main Warehouse"],
          quantity: 0.1, // Very small fractional quantity
          reserved_quantity: 0.05,
          available_quantity: 0.05,
          in_date: "2024-01-12T10:00:00Z"
        },
        {
          id: 12,
          product_id: [10, "Zero Stock with Lot"],
          location_id: [2, "Secondary Warehouse"],
          lot_id: [2, "LOT002"], // Has lot but zero quantity
          quantity: 0.0,
          reserved_quantity: 0.0,
          available_quantity: 0.0,
          in_date: "2024-01-20T10:00:00Z"
        }
      ]
    };

    const filePath = join(this.outputDir, 'test-inventory.json');
    writeFileSync(filePath, JSON.stringify(inventory, null, 2));
    console.log(`Generated inventory test data: ${filePath}`);
    return inventory;
  }

  generateAllTestData() {
    console.log('Generating comprehensive test datasets...\n');
    
    const datasets = {
      products: this.generateProductTestData(),
      customers: this.generateCustomerTestData(), 
      orders: this.generateOrderTestData(),
      inventory: this.generateInventoryTestData()
    };

    // Generate summary report
    const summary = {
      generated_date: new Date().toISOString(),
      datasets: {
        products: {
          total_records: datasets.products.products.length,
          expected_issues: [
            'Invalid SKU formats',
            'Missing required fields', 
            'Duplicate SKUs',
            'Price validation warnings',
            'Suspicious placeholder values',
            'Invalid categories'
          ]
        },
        customers: {
          total_records: datasets.customers.customers.length,
          expected_issues: [
            'Invalid email formats',
            'Missing required fields',
            'Duplicate contact information',
            'Invalid VAT numbers',
            'Address completeness issues',
            'Rank validation errors'
          ]
        },
        orders: {
          total_records: datasets.orders.orders.length,
          expected_issues: [
            'Order total mismatches',
            'Invalid date sequences',
            'Empty order lines',
            'Invalid state values',
            'Suspicious quantities and prices',
            'Format validation errors'
          ]
        },
        inventory: {
          total_records: datasets.inventory.stock_records.length,
          expected_issues: [
            'Quantity consistency errors',
            'Over-reserved stock',
            'Future dates',
            'Very old stock warnings',
            'Duplicate stock records',
            'Format validation errors'
          ]
        }
      }
    };

    const summaryPath = join(this.outputDir, 'test-data-summary.json');
    writeFileSync(summaryPath, JSON.stringify(summary, null, 2));
    console.log(`\nGenerated test data summary: ${summaryPath}`);
    
    console.log('\n✅ All test datasets generated successfully!');
    console.log(`Output directory: ${this.outputDir}`);
    
    return datasets;
  }
}

// CLI functionality
if (import.meta.url === `file://${process.argv[1]}`) {
  const generator = new TestDataGenerator();
  generator.generateAllTestData();
}

export { TestDataGenerator };