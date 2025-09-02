#!/usr/bin/env python3
"""
Update Odoo products with stock data and custom fields
Sets realistic values for qty_available, virtual_available, and custom fields
"""

import xmlrpc.client
import random
from datetime import datetime

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

def update_product_stock(uid, models):
    """Update product stock quantities and add custom fields"""
    print("=== Updating Product Stock Data ===\n")
    
    # First, get all products that have supplier info
    supplier_products = models.execute_kw(
        db, uid, password,
        'product.supplierinfo', 'search_read',
        [[]],
        {
            'fields': ['id', 'product_id', 'product_name', 'min_qty'],
            'limit': 100  # Update first 100 products
        }
    )
    
    print(f"Found {len(supplier_products)} supplier products to update\n")
    
    # Track unique product IDs to avoid duplicates
    updated_products = set()
    
    for sp in supplier_products:
        if not sp['product_id']:
            continue
            
        product_id = sp['product_id'][0] if isinstance(sp['product_id'], list) else sp['product_id']
        
        # Skip if already updated
        if product_id in updated_products:
            continue
            
        updated_products.add(product_id)
        
        # Get product details
        try:
            product = models.execute_kw(
                db, uid, password,
                'product.product', 'read',
                [[product_id]],
                {'fields': ['name', 'default_code', 'type']}
            )[0]
            
            # Only update products that can have stock (not services)
            if product.get('type') == 'service':
                print(f"Skipping service product: {product['name']}")
                continue
            
            # Generate realistic stock data
            min_qty = float(sp['min_qty'] or 1)
            
            # Generate pack size based on MOQ
            if min_qty >= 50:
                pack_size = random.choice([10, 12, 20, 24])
            elif min_qty >= 20:
                pack_size = random.choice([6, 8, 10, 12])
            elif min_qty >= 10:
                pack_size = random.choice([4, 5, 6])
            else:
                pack_size = random.choice([1, 2, 3])
            
            # Generate minimum level (reorder point)
            # Usually 2-4x the MOQ
            minimum_level = int(min_qty * random.uniform(2, 4))
            
            # Generate current stock
            # Some products are out of stock, some low, some well-stocked
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
            
            # Update product with stock quantities
            print(f"Updating {product['name']} ({product.get('default_code', 'N/A')})")
            print(f"  - Available: {qty_available}, Virtual: {virtual_available}")
            print(f"  - Min Level: {minimum_level}, Pack Size: {pack_size}")
            
            # Update qty_available and virtual_available
            # Note: In a real Odoo instance, these are computed fields
            # We're simulating by creating stock quants
            
            # First check if we can access stock.quant
            try:
                # Try to create a stock quant (inventory adjustment)
                location_id = 1  # Usually the main stock location
                
                # Check existing quants
                existing_quants = models.execute_kw(
                    db, uid, password,
                    'stock.quant', 'search_read',
                    [[['product_id', '=', product_id]]],
                    {'fields': ['id', 'quantity', 'location_id'], 'limit': 1}
                )
                
                if existing_quants:
                    # Update existing quant
                    quant_id = existing_quants[0]['id']
                    models.execute_kw(
                        db, uid, password,
                        'stock.quant', 'write',
                        [[quant_id], {'quantity': qty_available}]
                    )
                    print(f"  ✓ Updated stock quant")
                else:
                    # Try to find the stock location
                    locations = models.execute_kw(
                        db, uid, password,
                        'stock.location', 'search_read',
                        [[['usage', '=', 'internal']]],
                        {'fields': ['id', 'name'], 'limit': 1}
                    )
                    
                    if locations:
                        location_id = locations[0]['id']
                        # Create new quant
                        quant_id = models.execute_kw(
                            db, uid, password,
                            'stock.quant', 'create',
                            [{
                                'product_id': product_id,
                                'location_id': location_id,
                                'quantity': qty_available
                            }]
                        )
                        print(f"  ✓ Created stock quant")
                
            except Exception as e:
                print(f"  ⚠ Could not update stock quant: {e}")
            
            # Try to add custom fields to product.supplierinfo
            # These would need to be created in Odoo first
            try:
                # Update supplier info with pack_size and minimum_level
                # Note: These fields need to exist in Odoo
                models.execute_kw(
                    db, uid, password,
                    'product.supplierinfo', 'write',
                    [[sp['id']], {
                        'x_pack_size': pack_size,
                        'x_minimum_level': minimum_level
                    }]
                )
                print(f"  ✓ Updated custom fields")
            except Exception as e:
                print(f"  ⚠ Could not update custom fields (may need to be created in Odoo): {e}")
                
                # Try alternative approach - store in description/notes
                try:
                    current_desc = sp.get('product_name', '')
                    if not current_desc or current_desc == 'False':
                        current_desc = ''
                    
                    # Add info to product name/description
                    updated_desc = f"{current_desc} | Pack: {pack_size} | Min Level: {minimum_level}"
                    
                    models.execute_kw(
                        db, uid, password,
                        'product.supplierinfo', 'write',
                        [[sp['id']], {'product_name': updated_desc}]
                    )
                    print(f"  ✓ Added info to product description")
                except Exception as e2:
                    print(f"  ⚠ Could not update description: {e2}")
            
            print()
            
        except Exception as e:
            print(f"Error updating product {product_id}: {e}\n")
            continue
    
    print(f"\nUpdated {len(updated_products)} unique products")

def create_reorder_rules(uid, models):
    """Try to create reorder rules (stock.warehouse.orderpoint)"""
    print("\n=== Creating Reorder Rules ===\n")
    
    try:
        # Get some products with supplier info
        supplier_products = models.execute_kw(
            db, uid, password,
            'product.supplierinfo', 'search_read',
            [[]],
            {
                'fields': ['id', 'product_id', 'min_qty'],
                'limit': 10
            }
        )
        
        # Get warehouse
        warehouses = models.execute_kw(
            db, uid, password,
            'stock.warehouse', 'search_read',
            [[]],
            {'fields': ['id', 'name', 'lot_stock_id'], 'limit': 1}
        )
        
        if not warehouses:
            print("No warehouse found")
            return
            
        warehouse = warehouses[0]
        location_id = warehouse['lot_stock_id'][0] if warehouse.get('lot_stock_id') else None
        
        if not location_id:
            # Try to find stock location
            locations = models.execute_kw(
                db, uid, password,
                'stock.location', 'search_read',
                [[['usage', '=', 'internal']]],
                {'fields': ['id', 'name'], 'limit': 1}
            )
            if locations:
                location_id = locations[0]['id']
        
        created_count = 0
        for sp in supplier_products:
            if not sp['product_id']:
                continue
                
            product_id = sp['product_id'][0] if isinstance(sp['product_id'], list) else sp['product_id']
            min_qty = float(sp['min_qty'] or 1)
            
            # Check if orderpoint already exists
            existing = models.execute_kw(
                db, uid, password,
                'stock.warehouse.orderpoint', 'search_count',
                [[['product_id', '=', product_id]]]
            )
            
            if existing > 0:
                continue
            
            # Create reorder rule
            try:
                minimum_level = int(min_qty * random.uniform(2, 4))
                maximum_level = minimum_level * 2
                
                orderpoint_id = models.execute_kw(
                    db, uid, password,
                    'stock.warehouse.orderpoint', 'create',
                    [{
                        'product_id': product_id,
                        'location_id': location_id,
                        'warehouse_id': warehouse['id'],
                        'product_min_qty': minimum_level,
                        'product_max_qty': maximum_level,
                        'qty_multiple': 1,
                        'name': f"Reorder Rule - Product {product_id}"
                    }]
                )
                created_count += 1
                print(f"Created reorder rule for product {sp['product_id']}")
            except Exception as e:
                print(f"Could not create reorder rule: {e}")
                
        print(f"\nCreated {created_count} reorder rules")
        
    except Exception as e:
        print(f"Error creating reorder rules: {e}")

def main():
    try:
        uid, models = connect()
        print(f"Successfully connected to Odoo (UID: {uid})\n")
        
        # Update product stock data
        update_product_stock(uid, models)
        
        # Try to create reorder rules
        create_reorder_rules(uid, models)
        
        print("\n=== Summary ===")
        print("✓ Stock quantities updated (where possible)")
        print("✓ Pack sizes and minimum levels added to descriptions")
        print("⚠ Note: For full functionality, custom fields should be added in Odoo:")
        print("  - x_pack_size (Integer) on product.supplierinfo")
        print("  - x_minimum_level (Integer) on product.supplierinfo")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()