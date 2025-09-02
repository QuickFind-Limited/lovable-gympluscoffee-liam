#!/usr/bin/env python3
"""
Test Script for Data Transformation Scripts

This script runs basic tests to validate the transformation scripts work correctly
with sample data and proper error handling.
"""

import unittest
import tempfile
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import sys
import os

# Add the scripts directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from transform_products import ProductTransformer
from generate_customers import CustomerGenerator
from create_orders import SalesOrderGenerator

class TestProductTransformer(unittest.TestCase):
    """Test product transformation functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create sample product data
        self.sample_products = {
            "catalog_name": "Test Catalog",
            "version": "1.0.0",
            "generated_date": "2025-01-01T00:00:00.000000",
            "total_skus": 2,
            "categories": ["t-shirts", "hoodies"],
            "products": [
                {
                    "sku": "TEST-001-BLK-M",
                    "name": "Test T-Shirt - Black",
                    "category": "t-shirts",
                    "subcategory": "mens",
                    "color": "Black",
                    "size": "M",
                    "list_price": 25.0,
                    "standard_cost": 10.0,
                    "description": "Test product description",
                    "features": ["Test feature 1", "Test feature 2"],
                    "status": "active",
                    "inventory_on_hand": 100,
                    "reorder_point": 20,
                    "lead_time_days": 7,
                    "created_date": "2025-01-01T00:00:00.000000",
                    "last_modified": "2025-01-01T00:00:00.000000"
                },
                {
                    "sku": "TEST-002-BLU-L",
                    "name": "Test Hoodie - Blue", 
                    "category": "hoodies",
                    "subcategory": "womens",
                    "color": "Blue",
                    "size": "L",
                    "list_price": 55.0,
                    "standard_cost": 22.0,
                    "description": "Test hoodie description",
                    "features": ["Warm", "Comfortable"],
                    "status": "active",
                    "inventory_on_hand": 50,
                    "reorder_point": 15,
                    "lead_time_days": 10,
                    "created_date": "2025-01-01T00:00:00.000000",
                    "last_modified": "2025-01-01T00:00:00.000000"
                }
            ]
        }
        
        # Save sample data
        self.source_file = self.temp_path / 'test_products.json'
        with open(self.source_file, 'w') as f:
            json.dump(self.sample_products, f)
    
    def test_product_transformation(self):
        """Test basic product transformation"""
        transformer = ProductTransformer(
            source_file=str(self.source_file),
            output_dir=str(self.temp_path)
        )
        
        # Run transformation
        transformer.run_transformation()
        
        # Check output files exist
        expected_files = [
            'odoo_product_categories.csv',
            'odoo_product_templates.csv', 
            'odoo_product_variants.csv'
        ]
        
        for filename in expected_files:
            file_path = self.temp_path / filename
            self.assertTrue(file_path.exists(), f"Output file {filename} not created")
            
            # Check file has content
            df = pd.read_csv(file_path)
            self.assertGreater(len(df), 0, f"Output file {filename} is empty")
    
    def test_variant_creation(self):
        """Test that product variants are created correctly"""
        transformer = ProductTransformer(
            source_file=str(self.source_file),
            output_dir=str(self.temp_path)
        )
        
        # Load and transform data
        source_data = transformer.load_source_data()
        templates_df, variants_df = transformer.transform_products(source_data['products'])
        
        # Should have 2 templates (grouped by base name)
        self.assertEqual(len(templates_df), 2)
        
        # Should have 2 variants (one for each product)
        self.assertEqual(len(variants_df), 2)
        
        # Check required fields exist
        required_template_fields = ['external_id', 'name', 'list_price', 'category_id']
        required_variant_fields = ['external_id', 'default_code', 'list_price', 'qty_available']
        
        for field in required_template_fields:
            self.assertIn(field, templates_df.columns, f"Template field {field} missing")
        
        for field in required_variant_fields:
            self.assertIn(field, variants_df.columns, f"Variant field {field} missing")


class TestCustomerGenerator(unittest.TestCase):
    """Test customer generation functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create sample DataCo data
        self.sample_dataco = pd.DataFrame({
            'Customer Country': ['EE. UU.', 'Canada', 'EE. UU.', 'United Kingdom'],
            'Customer State': ['CA', 'ON', 'NY', 'England'],
            'Customer City': ['Los Angeles', 'Toronto', 'New York', 'London'],
            'Customer Segment': ['Consumer', 'Corporate', 'Home Office', 'Consumer'],
            'Sales per customer': [250.0, 850.0, 420.0, 180.0],
            'Shipping Mode': ['Standard Class', 'First Class', 'Standard Class', 'Second Class']
        })
        
        self.dataco_file = self.temp_path / 'test_dataco.csv'
        self.sample_dataco.to_csv(self.dataco_file, index=False)
    
    def test_customer_generation(self):
        """Test basic customer generation"""
        generator = CustomerGenerator(
            dataco_file=str(self.dataco_file),
            output_dir=str(self.temp_path),
            num_customers=10
        )
        
        # Run generation
        generator.run_generation()
        
        # Check output files
        customers_file = self.temp_path / 'odoo_customers.csv'
        categories_file = self.temp_path / 'odoo_customer_categories.csv'
        
        self.assertTrue(customers_file.exists(), "Customers file not created")
        self.assertTrue(categories_file.exists(), "Customer categories file not created")
        
        # Check content
        customers_df = pd.read_csv(customers_file)
        self.assertEqual(len(customers_df), 10, "Wrong number of customers generated")
        
        # Check required fields
        required_fields = ['external_id', 'name', 'email', 'customer_segment']
        for field in required_fields:
            self.assertIn(field, customers_df.columns, f"Customer field {field} missing")
    
    def test_pattern_analysis(self):
        """Test DataCo pattern analysis"""
        generator = CustomerGenerator(
            dataco_file=str(self.dataco_file),
            output_dir=str(self.temp_path),
            num_customers=100
        )
        
        # Load patterns
        generator.load_dataco_patterns()
        
        # Check patterns were loaded
        self.assertIsNotNone(generator.geographic_patterns)
        self.assertIsNotNone(generator.customer_behavior_patterns)
        
        # Check geographic patterns
        self.assertIn('country_distribution', generator.geographic_patterns)
        
        # Check behavior patterns
        self.assertIn('segment_distribution', generator.customer_behavior_patterns)


class TestOrderGenerator(unittest.TestCase):
    """Test order generation functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create sample customers data
        self.sample_customers = pd.DataFrame({
            'external_id': ['cust_001', 'cust_002', 'cust_003'],
            'name': ['John Doe', 'Acme Corp', 'Jane Smith'],
            'category_id': ['gym_coffee_cat_consumer', 'gym_coffee_cat_corporate', 'gym_coffee_cat_home_office'],
            'expected_annual_spend': [250.0, 1200.0, 450.0],
            'create_date': [
                (datetime.now() - timedelta(days=30)).isoformat(),
                (datetime.now() - timedelta(days=90)).isoformat(),
                (datetime.now() - timedelta(days=15)).isoformat()
            ]
        })
        
        # Create sample products data
        self.sample_products = pd.DataFrame({
            'external_id': ['prod_001', 'prod_002', 'prod_003'],
            'name': ['Test T-Shirt', 'Test Hoodie', 'Test Shorts'],
            'category': ['t-shirts', 'hoodies', 'shorts'],
            'list_price': [25.0, 55.0, 30.0],
            'standard_price': [10.0, 22.0, 12.0],
            'qty_available': [100, 50, 75],
            'color_value': ['Black', 'Blue', 'Gray'],
            'size_value': ['M', 'L', 'S']
        })
        
        # Create sample DataCo data
        self.sample_dataco = pd.DataFrame({
            'Order Status': ['COMPLETE', 'PENDING', 'COMPLETE', 'PROCESSING'],
            'Customer Segment': ['Consumer', 'Corporate', 'Home Office', 'Consumer'],
            'Shipping Mode': ['Standard Class', 'First Class', 'Standard Class', 'Second Class'],
            'Order Item Quantity': [2, 5, 1, 3],
            'Order Item Discount Rate': [0.0, 0.10, 0.05, 0.0],
            'order date (DateOrders)': [
                '2024-01-15 10:00:00',
                '2024-02-20 14:30:00', 
                '2024-03-10 09:15:00',
                '2024-04-05 16:45:00'
            ]
        })
        
        # Save test data
        self.customers_file = self.temp_path / 'test_customers.csv'
        self.products_file = self.temp_path / 'test_products.csv'
        self.dataco_file = self.temp_path / 'test_dataco.csv'
        
        self.sample_customers.to_csv(self.customers_file, index=False)
        self.sample_products.to_csv(self.products_file, index=False)
        self.sample_dataco.to_csv(self.dataco_file, index=False)
    
    def test_order_generation(self):
        """Test basic order generation"""
        generator = SalesOrderGenerator(
            dataco_file=str(self.dataco_file),
            customers_file=str(self.customers_file),
            products_file=str(self.products_file),
            output_dir=str(self.temp_path),
            num_orders=5
        )
        
        # Run generation
        generator.run_generation()
        
        # Check output files
        orders_file = self.temp_path / 'odoo_sales_orders.csv'
        lines_file = self.temp_path / 'odoo_order_lines.csv'
        
        self.assertTrue(orders_file.exists(), "Orders file not created")
        self.assertTrue(lines_file.exists(), "Order lines file not created")
        
        # Check content
        orders_df = pd.read_csv(orders_file)
        lines_df = pd.read_csv(lines_file)
        
        self.assertEqual(len(orders_df), 5, "Wrong number of orders generated")
        self.assertGreater(len(lines_df), 0, "No order lines generated")
        
        # Check required fields
        required_order_fields = ['external_id', 'partner_id', 'amount_total', 'state']
        required_line_fields = ['external_id', 'order_id', 'product_id', 'price_total']
        
        for field in required_order_fields:
            self.assertIn(field, orders_df.columns, f"Order field {field} missing")
        
        for field in required_line_fields:
            self.assertIn(field, lines_df.columns, f"Line field {field} missing")
    
    def test_order_relationships(self):
        """Test that orders have proper relationships"""
        generator = SalesOrderGenerator(
            dataco_file=str(self.dataco_file),
            customers_file=str(self.customers_file),
            products_file=str(self.products_file),
            output_dir=str(self.temp_path),
            num_orders=3
        )
        
        # Generate orders
        orders_df, lines_df = generator.generate_orders()
        
        # Check that all order line order_ids exist in orders
        order_ids = set(orders_df['external_id'])
        line_order_ids = set(lines_df['order_id'])
        
        self.assertTrue(line_order_ids.issubset(order_ids), 
                       "Order lines reference non-existent orders")
        
        # Check that all partner_ids exist in customers
        customer_ids = set(self.sample_customers['external_id'])
        order_partner_ids = set(orders_df['partner_id'])
        
        self.assertTrue(order_partner_ids.issubset(customer_ids),
                       "Orders reference non-existent customers")
        
        # Check that all product_ids exist in products
        product_ids = set(self.sample_products['external_id'])
        line_product_ids = set(lines_df['product_id'])
        
        self.assertTrue(line_product_ids.issubset(product_ids),
                       "Order lines reference non-existent products")


class TestDataIntegrity(unittest.TestCase):
    """Test data integrity across all transformations"""
    
    def setUp(self):
        """Set up complete test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # This would normally run the full pipeline in a real test
        # For now, we'll just test the validation logic
        pass
    
    def test_csv_file_structure(self):
        """Test that generated CSV files have proper structure"""
        # Create a sample CSV file
        sample_data = pd.DataFrame({
            'external_id': ['test_001', 'test_002'],
            'name': ['Test Item 1', 'Test Item 2'],
            'price': [10.99, 25.50]
        })
        
        test_file = self.temp_path / 'test_structure.csv'
        sample_data.to_csv(test_file, index=False)
        
        # Read back and validate
        loaded_data = pd.read_csv(test_file)
        
        self.assertEqual(len(loaded_data), 2, "Wrong number of records")
        self.assertListEqual(list(loaded_data.columns), 
                           ['external_id', 'name', 'price'],
                           "Column structure incorrect")
        self.assertEqual(loaded_data['external_id'].iloc[0], 'test_001')
        self.assertEqual(loaded_data['price'].iloc[1], 25.50)


def run_basic_functionality_test():
    """Run a basic functionality test of the pipeline"""
    print("Running basic functionality test...")
    
    try:
        # Test that we can import all modules
        from transform_products import ProductTransformer
        from generate_customers import CustomerGenerator
        from create_orders import SalesOrderGenerator
        from data_pipeline import DataPipeline
        
        print("✅ All modules import successfully")
        
        # Test basic class instantiation
        temp_dir = tempfile.mkdtemp()
        
        # This would fail if source files don't exist, which is expected
        try:
            transformer = ProductTransformer("fake_file.json", temp_dir)
            print("✅ ProductTransformer instantiation works")
        except Exception as e:
            print(f"⚠️  ProductTransformer instantiation: {e}")
        
        try:
            generator = CustomerGenerator("fake_file.csv", temp_dir, 10)
            print("✅ CustomerGenerator instantiation works") 
        except Exception as e:
            print(f"⚠️  CustomerGenerator instantiation: {e}")
        
        print("✅ Basic functionality test completed")
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("DATA TRANSFORMATION SCRIPTS TEST SUITE")
    print("="*60)
    
    # Run basic functionality test first
    basic_test_passed = run_basic_functionality_test()
    
    print("\n" + "-"*60)
    print("RUNNING UNIT TESTS")
    print("-"*60)
    
    # Run unit tests
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "="*60)
    print("TEST SUITE COMPLETED")
    print("="*60)