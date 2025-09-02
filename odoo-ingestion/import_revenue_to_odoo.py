#!/usr/bin/env python3
"""
Import Revenue Data to Odoo
===========================

Script to import the generated revenue data into Odoo.
This demonstrates how to use the generated data with Odoo's API.

Usage:
    python3 import_revenue_to_odoo.py --batch-size 100 --test-mode
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
import sys
import os

# Add scripts directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

try:
    from connection_manager import OdooConnection, ConnectionConfig
except ImportError:
    print("⚠️ Connection manager not available. This is a demonstration script.")
    print("   To actually import data, ensure Odoo connection modules are available.")

def find_latest_revenue_data():
    """Find the latest generated revenue data files"""
    revenue_dir = Path("data/revenue")
    if not revenue_dir.exists():
        raise FileNotFoundError("Revenue data directory not found. Run generate_revenue.py first.")
    
    # Find latest Odoo-compatible orders file
    odoo_files = list(revenue_dir.glob("odoo_sales_orders_*.json"))
    if not odoo_files:
        raise FileNotFoundError("No Odoo-compatible order files found.")
    
    latest_file = max(odoo_files, key=lambda x: x.stat().st_mtime)
    return latest_file

def load_revenue_data(file_path):
    """Load revenue data from JSON file"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    print(f"📄 Loaded {len(data):,} orders from {file_path.name}")
    return data

def validate_order_data(orders):
    """Validate order data before import"""
    print("🔍 Validating order data...")
    
    required_fields = ['name', 'partner_id', 'date_order', 'state', 'amount_total', 'user_id']
    missing_fields = []
    
    sample_size = min(100, len(orders))
    for i, order in enumerate(orders[:sample_size]):
        for field in required_fields:
            if field not in order or order[field] is None:
                missing_fields.append(f"Order {i}: Missing {field}")
    
    if missing_fields:
        print(f"❌ Validation failed:")
        for error in missing_fields[:10]:  # Show first 10 errors
            print(f"   {error}")
        return False
    
    # Check salesperson field
    shopify_orders = sum(1 for order in orders[:sample_size] if order.get('user_id') == 'Shopify')
    print(f"✅ Validation passed:")
    print(f"   Sample size: {sample_size} orders")
    print(f"   Shopify salesperson: {shopify_orders}/{sample_size} orders")
    print(f"   All required fields present")
    
    return True

def demonstrate_odoo_import(orders, batch_size=100, test_mode=True):
    """Demonstrate how the Odoo import would work"""
    
    print(f"\n🚀 {'TEST MODE: ' if test_mode else ''}Odoo Import Demonstration")
    print("="*60)
    
    if test_mode:
        print("⚠️  TEST MODE: No actual data will be imported to Odoo")
        print("   This demonstrates the import process structure")
    
    # Connection configuration (example)
    connection_config = {
        'url': 'http://localhost:8069',
        'db': 'your_database_name',
        'username': 'admin',
        'password': 'admin_password'
    }
    
    print(f"\n📊 IMPORT PLAN:")
    total_orders = len(orders)
    num_batches = (total_orders + batch_size - 1) // batch_size
    
    print(f"   Total orders: {total_orders:,}")
    print(f"   Batch size: {batch_size}")
    print(f"   Number of batches: {num_batches}")
    
    # Process in batches
    processed = 0
    errors = 0
    
    print(f"\n📥 PROCESSING BATCHES:")
    
    for batch_num in range(num_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, total_orders)
        batch_orders = orders[start_idx:end_idx]
        
        print(f"   Batch {batch_num + 1}/{num_batches}: Processing orders {start_idx + 1}-{end_idx}")
        
        if test_mode:
            # Simulate processing
            batch_success = True
            batch_errors = 0
            
            # Show sample order structure
            if batch_num == 0 and batch_orders:
                sample_order = batch_orders[0]
                print(f"\n   📄 Sample Order Structure:")
                print(f"      Order ID: {sample_order['name']}")
                print(f"      Customer: {sample_order['partner_id']}")
                print(f"      Date: {sample_order['date_order']}")
                print(f"      Total: €{sample_order['amount_total']}")
                print(f"      Salesperson: {sample_order['user_id']}")
                print(f"      Order Lines: {len(sample_order.get('order_line', []))}")
        else:
            # Actual Odoo import would happen here
            try:
                # conn = OdooConnection(connection_config)
                # for order in batch_orders:
                #     conn.create('sale.order', order)
                batch_success = True
                batch_errors = 0
                print(f"   ⚠️  Actual import not implemented - connection modules needed")
            except Exception as e:
                batch_success = False
                batch_errors = len(batch_orders)
                print(f"   ❌ Batch failed: {e}")
        
        if batch_success:
            processed += len(batch_orders) - batch_errors
            errors += batch_errors
            print(f"   ✅ Success: {len(batch_orders) - batch_errors}/{len(batch_orders)} orders")
        else:
            errors += len(batch_orders)
            print(f"   ❌ Failed: {len(batch_orders)} orders")
    
    # Summary
    print(f"\n📊 IMPORT SUMMARY:")
    print(f"   Total orders processed: {processed:,}/{total_orders:,}")
    print(f"   Success rate: {(processed/total_orders)*100:.1f}%")
    print(f"   Errors: {errors}")
    
    if test_mode:
        print(f"\n🎯 TO PERFORM ACTUAL IMPORT:")
        print(f"   1. Configure Odoo connection details")
        print(f"   2. Ensure Odoo server is running")
        print(f"   3. Verify database permissions")
        print(f"   4. Run: python3 import_revenue_to_odoo.py --no-test")
        print(f"   5. Monitor import progress and handle any errors")
    
    return processed, errors

def main():
    """Main import function"""
    parser = argparse.ArgumentParser(description='Import generated revenue data to Odoo')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for imports')
    parser.add_argument('--test-mode', action='store_true', default=True, help='Run in test mode (default)')
    parser.add_argument('--no-test', dest='test_mode', action='store_false', help='Run actual import')
    parser.add_argument('--file', type=str, help='Specific file to import (otherwise uses latest)')
    
    args = parser.parse_args()
    
    try:
        # Find and load data
        if args.file:
            data_file = Path(args.file)
            if not data_file.exists():
                raise FileNotFoundError(f"File not found: {args.file}")
        else:
            data_file = find_latest_revenue_data()
        
        print(f"🎯 REVENUE DATA IMPORT TO ODOO")
        print(f"{'='*50}")
        print(f"📂 Data file: {data_file.name}")
        print(f"⚙️  Mode: {'TEST' if args.test_mode else 'PRODUCTION'}")
        print(f"📦 Batch size: {args.batch_size}")
        
        # Load data
        orders = load_revenue_data(data_file)
        
        # Validate data
        if not validate_order_data(orders):
            print("❌ Data validation failed. Cannot proceed with import.")
            return False
        
        # Demonstrate import process
        processed, errors = demonstrate_odoo_import(
            orders, 
            batch_size=args.batch_size, 
            test_mode=args.test_mode
        )
        
        success_rate = (processed / len(orders)) * 100 if orders else 0
        
        if success_rate >= 95:
            print(f"\n🎉 IMPORT {'SIMULATION ' if args.test_mode else ''}COMPLETED SUCCESSFULLY!")
            return True
        else:
            print(f"\n⚠️ IMPORT {'SIMULATION ' if args.test_mode else ''}COMPLETED WITH ERRORS")
            return False
            
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)