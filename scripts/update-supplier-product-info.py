#!/usr/bin/env python3
"""
Update supplier product info with pack size and minimum level in the product name
This works around the limitations of the Odoo trial instance
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

def update_supplier_products(uid, models):
    """Update supplier product info with JSON metadata in product_name"""
    print("=== Updating Supplier Product Info ===\n")
    
    # Get all supplier products
    supplier_products = models.execute_kw(
        db, uid, password,
        'product.supplierinfo', 'search_read',
        [[]],
        {
            'fields': ['id', 'product_id', 'product_name', 'product_code', 'min_qty', 'partner_id'],
            'limit': 50  # Update first 50 products
        }
    )
    
    print(f"Found {len(supplier_products)} supplier products to update\n")
    
    updated_count = 0
    
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
                print(f"Skipping {current_name} - already has metadata")
                continue
            
            # Generate pack size and minimum level
            min_qty = float(sp['min_qty'] or 1)
            
            # Pack size based on MOQ
            if min_qty >= 50:
                pack_size = random.choice([10, 12, 20, 24])
            elif min_qty >= 20:
                pack_size = random.choice([6, 8, 10, 12])
            elif min_qty >= 10:
                pack_size = random.choice([4, 5, 6])
            else:
                pack_size = random.choice([1, 2, 3])
            
            # Minimum level (reorder point) - usually 2-4x the MOQ
            minimum_level = int(min_qty * random.uniform(2, 4))
            
            # Generate stock levels
            stock_scenario = random.choice(['out', 'low', 'normal', 'high'])
            
            if stock_scenario == 'out':
                qty_available = 0
                virtual_available = random.randint(0, int(min_qty * 2))
            elif stock_scenario == 'low':
                qty_available = random.randint(1, minimum_level - 1)
                virtual_available = qty_available + random.randint(0, int(min_qty))
            elif stock_scenario == 'normal':
                qty_available = random.randint(minimum_level, minimum_level * 2)
                virtual_available = qty_available + random.randint(0, int(min_qty * 2))
            else:  # high
                qty_available = random.randint(minimum_level * 2, minimum_level * 4)
                virtual_available = qty_available
            
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
            # Format: Original Name |META|{"pack_size":6,"minimum_level":40,...}
            updated_name = f"{current_name} |META|{meta_str}"
            
            print(f"Updating {current_name}")
            print(f"  - Pack Size: {pack_size}, Min Level: {minimum_level}")
            print(f"  - Available: {qty_available}, Virtual: {virtual_available}")
            
            # Update the product_name field
            models.execute_kw(
                db, uid, password,
                'product.supplierinfo', 'write',
                [[sp['id']], {'product_name': updated_name}]
            )
            
            updated_count += 1
            print("  ✓ Updated successfully\n")
            
        except Exception as e:
            print(f"Error updating product {sp['id']}: {e}\n")
            continue
    
    print(f"\nSuccessfully updated {updated_count} products")

def main():
    try:
        uid, models = connect()
        print(f"Successfully connected to Odoo (UID: {uid})\n")
        
        # Update supplier products
        update_supplier_products(uid, models)
        
        print("\n=== Summary ===")
        print("✓ Product metadata added to product names")
        print("✓ Data includes: pack_size, minimum_level, qty_available, virtual_available")
        print("✓ Edge function will parse this metadata to display the values")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()