#!/usr/bin/env python3
"""
Update ALL vendors' product info with metadata (available, minimum level, pack size, MOQ)
This script ensures all suppliers have the new fields populated with realistic data
"""

import xmlrpc.client
import random
import json

# Odoo connection details
odoo_url = 'https://source-animalfarmacy.odoo.com'
db = 'source-animalfarmacy'
username = 'admin@quickfindai.com'
password = 'BJ62wX2J4yzjS$i'

def connect():
    """Connect to Odoo and authenticate"""
    common = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})
    
    if not uid:
        raise Exception("Failed to authenticate with Odoo")
    
    models = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/object')
    
    return uid, models

def get_all_suppliers(uid, models):
    """Get all suppliers from Odoo"""
    print("=== Fetching All Suppliers ===\n")
    
    # Get all partners who are suppliers
    suppliers = models.execute_kw(
        db, uid, password,
        'res.partner', 'search_read',
        [[['supplier_rank', '>', 0]]],
        {
            'fields': ['id', 'name', 'supplier_rank'],
            'limit': 100  # Get up to 100 suppliers
        }
    )
    
    print(f"Found {len(suppliers)} suppliers\n")
    return suppliers

def update_vendor_products(uid, models, vendor_id, vendor_name):
    """Update all products for a specific vendor with metadata"""
    print(f"\n=== Updating products for {vendor_name} (ID: {vendor_id}) ===")
    
    # Get all supplier products for this vendor
    supplier_products = models.execute_kw(
        db, uid, password,
        'product.supplierinfo', 'search_read',
        [[['partner_id', '=', vendor_id]]],
        {
            'fields': ['id', 'product_id', 'product_name', 'product_code', 'min_qty', 'partner_id'],
            'limit': 200  # Update up to 200 products per vendor
        }
    )
    
    print(f"Found {len(supplier_products)} products for {vendor_name}")
    
    updated_count = 0
    skipped_count = 0
    
    for sp in supplier_products:
        if not sp['product_id']:
            continue
            
        try:
            # Get current product name
            current_name = sp.get('product_name', '')
            if current_name == 'False' or not current_name:
                # Use product_id name if available
                if isinstance(sp['product_id'], list) and len(sp['product_id']) > 1:
                    current_name = sp['product_id'][1]
                else:
                    current_name = f"Product {sp['id']}"
            
            # Skip if already has metadata
            if '|META|' in current_name:
                skipped_count += 1
                continue
            
            # Generate pack size and minimum level based on vendor type and MOQ
            min_qty = float(sp['min_qty'] or 1)
            
            # Vary pack sizes by vendor to make it realistic
            vendor_factor = (vendor_id % 5) + 1  # Creates variety between vendors
            
            # Pack size based on MOQ and vendor factor
            if min_qty >= 50:
                pack_size = random.choice([10, 12, 20, 24, 30]) + vendor_factor
            elif min_qty >= 20:
                pack_size = random.choice([6, 8, 10, 12]) + (vendor_factor // 2)
            elif min_qty >= 10:
                pack_size = random.choice([4, 5, 6, 8])
            else:
                pack_size = random.choice([1, 2, 3, 4])
            
            # Minimum level (reorder point) - varies by vendor
            min_level_factor = 2 + (vendor_factor * 0.3)  # 2.3 to 3.8
            minimum_level = int(min_qty * random.uniform(min_level_factor, min_level_factor + 1.5))
            
            # Generate stock levels with vendor-specific patterns
            stock_patterns = ['out', 'low', 'normal', 'high']
            # Some vendors have better stock management
            if vendor_id % 3 == 0:  # Every third vendor has better stock
                stock_weights = [5, 15, 50, 30]  # More likely to be normal/high
            else:
                stock_weights = [10, 25, 45, 20]  # More balanced distribution
            
            stock_scenario = random.choices(stock_patterns, weights=stock_weights, k=1)[0]
            
            if stock_scenario == 'out':
                qty_available = 0
                virtual_available = random.randint(0, int(min_qty * 2))
            elif stock_scenario == 'low':
                qty_available = random.randint(1, max(1, minimum_level - 1))
                virtual_available = qty_available + random.randint(0, int(min_qty))
            elif stock_scenario == 'normal':
                qty_available = random.randint(minimum_level, minimum_level * 2)
                virtual_available = qty_available + random.randint(0, int(min_qty * 2))
            else:  # high
                qty_available = random.randint(minimum_level * 2, minimum_level * 4)
                virtual_available = qty_available + random.randint(-int(min_qty), int(min_qty))
            
            # Create metadata
            metadata = {
                'pack_size': pack_size,
                'minimum_level': minimum_level,
                'qty_available': qty_available,
                'virtual_available': virtual_available
            }
            
            # Encode metadata as JSON string
            meta_str = json.dumps(metadata, separators=(',', ':'))
            
            # Update product name with metadata appended
            updated_name = f"{current_name} |META|{meta_str}"
            
            # Update the product_name field
            models.execute_kw(
                db, uid, password,
                'product.supplierinfo', 'write',
                [[sp['id']], {'product_name': updated_name}]
            )
            
            updated_count += 1
            
        except Exception as e:
            print(f"  Error updating product {sp['id']}: {e}")
            continue
    
    print(f"  ✓ Updated {updated_count} products, skipped {skipped_count} (already had metadata)")
    return updated_count, skipped_count

def main():
    try:
        uid, models = connect()
        print(f"Successfully connected to Odoo (UID: {uid})\n")
        
        # Get all suppliers
        suppliers = get_all_suppliers(uid, models)
        
        total_updated = 0
        total_skipped = 0
        vendors_processed = 0
        
        # Process each supplier
        for supplier in suppliers:
            vendor_id = supplier['id']
            vendor_name = supplier['name']
            
            # Update products for this vendor
            updated, skipped = update_vendor_products(uid, models, vendor_id, vendor_name)
            
            total_updated += updated
            total_skipped += skipped
            vendors_processed += 1
            
            # Add a small delay to avoid overwhelming the API
            import time
            time.sleep(0.5)
        
        print("\n" + "="*60)
        print("=== SUMMARY ===")
        print(f"✓ Processed {vendors_processed} vendors")
        print(f"✓ Updated {total_updated} products with metadata")
        print(f"✓ Skipped {total_skipped} products (already had metadata)")
        print("\nMetadata includes:")
        print("  - pack_size: Units per package")
        print("  - minimum_level: Reorder point")
        print("  - qty_available: Current stock")
        print("  - virtual_available: Forecasted availability")
        print("\nThe edge function will parse this metadata to display in the UI")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()