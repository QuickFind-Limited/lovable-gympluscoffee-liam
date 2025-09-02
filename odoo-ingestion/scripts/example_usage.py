#!/usr/bin/env python3
"""
Example Usage of Odoo Import System
==================================

Demonstrates how to use the Odoo import system with real-world examples.

Agent: Documentation Specialist
"""

import os
import json
from pathlib import Path
from datetime import datetime

# Import the main components
from odoo_import import OdooImporter, ImportConfig, load_config_from_env
from data_models import ProductTemplate, Partner, SaleOrder


def example_basic_product_import():
    """
    Example 1: Basic Product Import
    ==============================
    
    Import products from the gym+coffee JSON data
    """
    print("🚀 Example 1: Basic Product Import")
    print("=" * 50)
    
    # Load configuration
    config = load_config_from_env()
    
    # Initialize importer
    importer = OdooImporter(config)
    
    # Set up data file path
    data_file = Path("../data/gym_plus_coffee_products.json")
    
    if not data_file.exists():
        print(f"❌ Data file not found: {data_file}")
        return
    
    try:
        # Import products
        results = importer.import_product_data(str(data_file))
        
        print("✅ Import completed successfully!")
        print(f"📊 Categories imported: {results['categories']['imported']}")
        print(f"📦 Products imported: {results['products']['imported']}")
        print(f"📈 Inventory updated: {results['inventory']['updated']}")
        
    except Exception as e:
        print(f"❌ Import failed: {e}")


def example_custom_data_import():
    """
    Example 2: Custom Data Import
    ============================
    
    Create and import custom product data
    """
    print("\n🚀 Example 2: Custom Data Import")
    print("=" * 50)
    
    # Create custom product data
    custom_data = {
        "catalog_name": "Custom Products",
        "version": "1.0.0", 
        "generated_date": datetime.now().isoformat(),
        "total_skus": 3,
        "categories": ["electronics", "accessories"],
        "products": [
            {
                "sku": "CUSTOM001",
                "name": "Custom Product 1",
                "category": "electronics",
                "subcategory": "gadgets",
                "color": "Black",
                "size": "Medium",
                "list_price": 199.99,
                "standard_cost": 89.99,
                "description": "High-quality electronic gadget",
                "status": "active",
                "inventory_on_hand": 25,
                "reorder_point": 10,
                "lead_time_days": 7
            },
            {
                "sku": "CUSTOM002", 
                "name": "Custom Product 2",
                "category": "accessories",
                "subcategory": "lifestyle",
                "color": "Blue",
                "size": "Large",
                "list_price": 49.99,
                "standard_cost": 19.99,
                "description": "Stylish lifestyle accessory",
                "status": "active", 
                "inventory_on_hand": 50,
                "reorder_point": 20,
                "lead_time_days": 5
            },
            {
                "sku": "CUSTOM003",
                "name": "Custom Product 3", 
                "category": "electronics",
                "subcategory": "components",
                "color": "Silver",
                "size": "Small",
                "list_price": 299.99,
                "standard_cost": 149.99,
                "description": "Professional electronic component",
                "status": "active",
                "inventory_on_hand": 15,
                "reorder_point": 5,
                "lead_time_days": 14
            }
        ]
    }
    
    # Save to temporary file
    temp_file = Path("temp_custom_products.json")
    with open(temp_file, 'w') as f:
        json.dump(custom_data, f, indent=2)
    
    try:
        # Load configuration and import
        config = load_config_from_env()
        importer = OdooImporter(config)
        
        results = importer.import_product_data(str(temp_file))
        
        print("✅ Custom import completed!")
        print(f"📊 Results: {results}")
        
    except Exception as e:
        print(f"❌ Custom import failed: {e}")
    finally:
        # Clean up temp file
        if temp_file.exists():
            temp_file.unlink()


def example_partner_import():
    """
    Example 3: Partner (Customer) Import
    ===================================
    
    Import customer/partner data
    """
    print("\n🚀 Example 3: Partner Import")
    print("=" * 50)
    
    # Create partner data
    partner_data = {
        "partners": [
            {
                "name": "Acme Corporation",
                "is_company": True,
                "email": "contact@acme.com",
                "phone": "+1-555-0123",
                "street": "123 Business Ave",
                "city": "Business City",
                "zip": "12345",
                "country": "US",
                "is_customer": True,
                "is_supplier": False
            },
            {
                "name": "John Smith",
                "is_company": False,
                "email": "john.smith@email.com", 
                "phone": "+1-555-0456",
                "street": "456 Residential St",
                "city": "Home Town",
                "zip": "67890",
                "country": "US",
                "is_customer": True,
                "is_supplier": False
            }
        ]
    }
    
    # Save to temp file
    temp_file = Path("temp_partners.json")
    with open(temp_file, 'w') as f:
        json.dump(partner_data, f, indent=2)
    
    try:
        config = load_config_from_env()
        importer = OdooImporter(config)
        
        results = importer.import_partner_data(str(temp_file))
        
        print("✅ Partner import completed!")
        print(f"👥 Partners imported: {results.get('imported', 0)}")
        print(f"⏭️  Partners skipped: {results.get('skipped', 0)}")
        print(f"❌ Partners failed: {results.get('errors', 0)}")
        
    except Exception as e:
        print(f"❌ Partner import failed: {e}")
    finally:
        if temp_file.exists():
            temp_file.unlink()


def example_batch_processing():
    """
    Example 4: Large Dataset Batch Processing
    ========================================
    
    Demonstrate batch processing with progress tracking
    """
    print("\n🚀 Example 4: Batch Processing")
    print("=" * 50)
    
    # Generate large dataset
    large_dataset = {
        "catalog_name": "Large Product Catalog",
        "categories": ["category_1", "category_2", "category_3"],
        "products": []
    }
    
    # Generate 500 products for batch processing demo
    for i in range(500):
        product = {
            "sku": f"BATCH{i:04d}",
            "name": f"Batch Product {i+1}",
            "category": f"category_{(i % 3) + 1}",
            "list_price": round(20.0 + (i * 0.5), 2),
            "standard_cost": round(10.0 + (i * 0.25), 2),
            "description": f"Batch generated product number {i+1}",
            "status": "active",
            "inventory_on_hand": 10 + (i % 50)
        }
        large_dataset["products"].append(product)
    
    large_dataset["total_skus"] = len(large_dataset["products"])
    
    # Save to temp file
    temp_file = Path("temp_large_dataset.json")
    with open(temp_file, 'w') as f:
        json.dump(large_dataset, f)
    
    try:
        # Configure for batch processing
        config = load_config_from_env()
        config.batch_size = 50  # Process in smaller batches
        
        importer = OdooImporter(config)
        
        # Add progress callback
        def progress_callback(current, total):
            percentage = (current / total) * 100
            print(f"📈 Progress: {current}/{total} ({percentage:.1f}%)")
        
        importer.progress_tracker.add_progress_callback(
            lambda op: progress_callback(op.processed_records, op.total_records)
        )
        
        print(f"🔄 Starting batch import of {len(large_dataset['products'])} products...")
        results = importer.import_product_data(str(temp_file))
        
        print("✅ Batch processing completed!")
        print(f"📊 Batches processed: {importer.stats['batches_processed']}")
        print(f"⏱️  Processing time: {importer.stats.get('end_time', datetime.now()) - importer.stats.get('start_time', datetime.now())}")
        
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")
    finally:
        if temp_file.exists():
            temp_file.unlink()


def example_error_handling():
    """
    Example 5: Error Handling and Recovery
    ====================================
    
    Demonstrate error handling with invalid data
    """
    print("\n🚀 Example 5: Error Handling")
    print("=" * 50)
    
    # Create data with intentional errors
    error_data = {
        "categories": ["valid_category"],
        "products": [
            {
                "sku": "VALID001",
                "name": "Valid Product",
                "category": "valid_category",
                "list_price": 100.0,
                "standard_cost": 50.0,
                "status": "active"
            },
            {
                "sku": "",  # Invalid: empty SKU
                "name": "Invalid Product 1",
                "category": "nonexistent_category",  # Invalid: nonexistent category
                "list_price": "invalid_price",  # Invalid: non-numeric price
                "standard_cost": -10.0,  # Invalid: negative cost
                "status": "active"
            },
            {
                # Missing required fields
                "sku": "INVALID002",
                "category": "valid_category"
                # Missing name, prices, etc.
            }
        ]
    }
    
    # Save to temp file
    temp_file = Path("temp_error_data.json")
    with open(temp_file, 'w') as f:
        json.dump(error_data, f, indent=2)
    
    try:
        config = load_config_from_env()
        importer = OdooImporter(config)
        
        print("🔄 Processing data with intentional errors...")
        results = importer.import_product_data(str(temp_file))
        
        # Display results
        print("📊 Import Results:")
        print(f"✅ Successful: {results.get('products', {}).get('imported', 0)}")
        print(f"❌ Failed: {results.get('products', {}).get('errors', 0)}")
        print(f"⏭️  Skipped: {results.get('products', {}).get('skipped', 0)}")
        
        # Display error report
        error_report = importer.error_handler.generate_error_report()
        if error_report.get('summary'):
            print("\n🚨 Error Report:")
            print(f"Total Errors: {error_report['summary']['total_errors']}")
            print(f"Most Common Category: {error_report['summary']['most_common_category']}")
            
            if error_report.get('recent_errors'):
                print("\nRecent Errors:")
                for error in error_report['recent_errors'][:3]:  # Show first 3
                    print(f"  - {error['message']} ({error['category']})")
        
    except Exception as e:
        print(f"❌ Error handling demo failed: {e}")
    finally:
        if temp_file.exists():
            temp_file.unlink()


def example_progress_monitoring():
    """
    Example 6: Progress Monitoring
    =============================
    
    Demonstrate real-time progress monitoring
    """
    print("\n🚀 Example 6: Progress Monitoring")
    print("=" * 50)
    
    config = load_config_from_env()
    importer = OdooImporter(config)
    
    # Start a mock operation
    progress = importer.progress_tracker.start_operation(
        operation_id="demo_operation",
        operation_type="products", 
        total_records=100
    )
    
    print(f"📊 Started operation: {progress.operation_id}")
    print(f"📈 Initial progress: {progress.progress_percentage:.1f}%")
    
    # Simulate progress updates
    import time
    for i in range(0, 101, 10):
        importer.progress_tracker.update_progress(
            operation_id="demo_operation",
            processed=i,
            successful=max(0, i - 2),  # Simulate 2% error rate
            failed=min(2, i)
        )
        
        updated_progress = importer.progress_tracker.get_operation_progress("demo_operation")
        print(f"📈 Progress: {updated_progress.progress_percentage:.1f}% "
              f"(Success rate: {updated_progress.success_rate:.1f}%)")
        
        time.sleep(0.5)  # Brief pause for demo
    
    # Complete operation
    final_progress = importer.progress_tracker.complete_operation(
        operation_id="demo_operation",
        final_stats={'successful': 95, 'failed': 5, 'processed': 100}
    )
    
    print(f"✅ Operation completed!")
    print(f"📊 Final success rate: {final_progress.success_rate:.1f}%")
    print(f"⏱️  Duration: {final_progress.duration}")
    print(f"⚡ Throughput: {final_progress.throughput_per_second:.2f} records/second")
    
    # Generate summary report
    summary = importer.progress_tracker.get_summary()
    print(f"\n📋 Summary:")
    print(f"Completed Operations: {summary['completed_operations']}")
    print(f"Total Records Processed: {summary['analytics']['total_records_processed']}")


def main():
    """
    Main function to run all examples
    """
    print("🎯 Odoo Import System - Example Usage")
    print("=" * 60)
    
    # Check if environment is configured
    if not all([os.getenv('ODOO_URL'), os.getenv('ODOO_DB'), 
                os.getenv('ODOO_USERNAME'), os.getenv('ODOO_PASSWORD')]):
        print("⚠️  Environment not configured!")
        print("Please set up your .env file with:")
        print("  - ODOO_URL")
        print("  - ODOO_DB") 
        print("  - ODOO_USERNAME")
        print("  - ODOO_PASSWORD")
        print("\nUsing example data for demonstration...")
        
        # Run examples that don't require actual Odoo connection
        example_progress_monitoring()
        return
    
    # Run all examples
    try:
        example_basic_product_import()
        example_custom_data_import()
        example_partner_import()
        example_batch_processing()
        example_error_handling()
        example_progress_monitoring()
        
        print("\n🎉 All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Examples failed: {e}")
        print("Please check your Odoo connection and configuration.")


if __name__ == '__main__':
    main()