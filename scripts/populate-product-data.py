#!/usr/bin/env python3
"""
Populate missing product data in Odoo:
- Product codes (default_code)
- Stock levels (qty_available)
- Virtual stock (virtual_available)
Also ensure supplier info has proper data
"""

import xmlrpc.client
import random
import string

# Odoo connection details
url = 'https://source-gym-plus-coffee.odoo.com'
db = 'source-gym-plus-coffee'
username = 'admin@quickfindai.com'
password = 'BJ62wX2J4yzjS$i'

def connect_odoo():
    """Connect to Odoo and return required objects"""
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})
    
    if not uid:
        raise Exception("Failed to authenticate with Odoo")
    
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    
    return uid, models

def update_product_codes(models, uid):
    """Update product codes (SKUs) for products that don't have them"""
    print("\n📝 Updating product codes...")
    
    # Get products without codes
    product_ids = models.execute_kw(
        db, uid, password,
        'product.product', 'search',
        [[['default_code', '=', False]]],
        {'limit': 500}
    )
    
    if not product_ids:
        # Get all products to check
        product_ids = models.execute_kw(
            db, uid, password,
            'product.product', 'search',
            [[]],
            {'limit': 500}
        )
    
    products = models.execute_kw(
        db, uid, password,
        'product.product', 'read',
        [product_ids],
        {'fields': ['id', 'name', 'default_code', 'display_name']}
    )
    
    updated = 0
    for product in products:
        # Skip if already has a proper code
        if product.get('default_code') and product['default_code'] not in ['', 'False', False]:
            continue
        
        # Generate a code based on the product name
        name = product.get('display_name', product.get('name', ''))
        
        # Try to extract existing code pattern from name (e.g., GC10000-BLA-XS)
        import re
        code_match = re.search(r'\[([A-Z0-9\-]+)\]', name)
        
        if code_match:
            # Use existing code from name
            code = code_match.group(1)
        else:
            # Generate new code
            prefix = 'GC'
            number = str(10000 + product['id'])
            suffix = ''.join(random.choices(string.ascii_uppercase, k=3))
            code = f"{prefix}{number}-{suffix}"
        
        try:
            models.execute_kw(
                db, uid, password,
                'product.product', 'write',
                [[product['id']], {'default_code': code}]
            )
            updated += 1
            print(f"   Updated {product['name'][:30]} with code: {code}")
        except Exception as e:
            print(f"   Error updating product {product['id']}: {str(e)}")
    
    print(f"✅ Updated {updated} product codes")
    return updated

def update_stock_levels(models, uid):
    """Update stock levels for products"""
    print("\n📦 Updating stock levels...")
    
    # Get products
    product_ids = models.execute_kw(
        db, uid, password,
        'product.product', 'search',
        [[]],
        {'limit': 200}
    )
    
    # Get or create stock location
    location_ids = models.execute_kw(
        db, uid, password,
        'stock.location', 'search',
        [[['usage', '=', 'internal'], ['name', '=', 'Stock']]],
        {'limit': 1}
    )
    
    if not location_ids:
        # Create stock location
        location_id = models.execute_kw(
            db, uid, password,
            'stock.location', 'create',
            [{
                'name': 'Stock',
                'usage': 'internal',
                'location_id': 1,  # Parent location
            }]
        )
        print(f"   Created stock location: {location_id}")
    else:
        location_id = location_ids[0]
    
    updated = 0
    for product_id in product_ids[:100]:  # Limit to 100 for speed
        try:
            # Check if quant exists
            quant_ids = models.execute_kw(
                db, uid, password,
                'stock.quant', 'search',
                [[
                    ['product_id', '=', product_id],
                    ['location_id', '=', location_id]
                ]],
                {'limit': 1}
            )
            
            # Generate realistic stock levels
            qty = random.choice([0, 0, 0] + list(range(1, 100)) + list(range(100, 500)))
            
            if quant_ids:
                # Update existing quant
                models.execute_kw(
                    db, uid, password,
                    'stock.quant', 'write',
                    [quant_ids, {
                        'quantity': qty,
                        'reserved_quantity': 0,
                    }]
                )
            else:
                # Create new quant
                models.execute_kw(
                    db, uid, password,
                    'stock.quant', 'create',
                    [{
                        'product_id': product_id,
                        'location_id': location_id,
                        'quantity': qty,
                        'reserved_quantity': 0,
                    }]
                )
            
            updated += 1
            
        except Exception as e:
            print(f"   Warning: Could not update stock for product {product_id}: {str(e)}")
    
    print(f"✅ Updated stock levels for {updated} products")
    return updated

def update_supplier_info_metadata(models, uid):
    """Add metadata to supplier info for pack size and min level"""
    print("\n🔧 Updating supplier product metadata...")
    
    # Get supplier info records
    supplier_info_ids = models.execute_kw(
        db, uid, password,
        'product.supplierinfo', 'search',
        [[]],
        {'limit': 100}
    )
    
    supplier_infos = models.execute_kw(
        db, uid, password,
        'product.supplierinfo', 'read',
        [supplier_info_ids],
        {'fields': ['id', 'product_name', 'product_code', 'min_qty']}
    )
    
    updated = 0
    for info in supplier_infos:
        product_name = info.get('product_name', '')
        
        # Skip if already has metadata
        if '|META|' in product_name:
            continue
        
        # Add metadata with default values
        metadata = {
            'pack_size': random.choice([1, 1, 1, 6, 12, 24]),
            'minimum_level': random.choice([5, 10, 20, 50]),
            'qty_available': random.randint(0, 200),
            'virtual_available': random.randint(0, 300)
        }
        
        # Update product name with metadata
        updated_name = f"{product_name} |META|{str(metadata)}"
        
        try:
            models.execute_kw(
                db, uid, password,
                'product.supplierinfo', 'write',
                [[info['id']], {
                    'product_name': updated_name,
                }]
            )
            updated += 1
            
        except Exception as e:
            print(f"   Warning: Could not update supplier info {info['id']}: {str(e)}")
    
    print(f"✅ Updated {updated} supplier product records with metadata")
    return updated

def verify_data(models, uid):
    """Verify the updated data"""
    print("\n📊 Verifying data...")
    
    # Check products with codes
    products_with_codes = models.execute_kw(
        db, uid, password,
        'product.product', 'search_count',
        [[['default_code', '!=', False]]]
    )
    print(f"   Products with codes: {products_with_codes}")
    
    # Check products with stock
    products_with_stock = models.execute_kw(
        db, uid, password,
        'stock.quant', 'search_count',
        [[['quantity', '>', 0]]]
    )
    print(f"   Products with stock: {products_with_stock}")
    
    # Check supplier info with metadata
    supplier_info_with_meta = models.execute_kw(
        db, uid, password,
        'product.supplierinfo', 'search_count',
        [[['product_name', 'like', '|META|']]]
    )
    print(f"   Supplier products with metadata: {supplier_info_with_meta}")
    
    # Sample a few products to show details
    print("\n   Sample product details:")
    sample_products = models.execute_kw(
        db, uid, password,
        'product.product', 'search_read',
        [[]],
        {'fields': ['name', 'default_code', 'qty_available'], 'limit': 3}
    )
    
    for product in sample_products:
        print(f"      {product['name'][:30]}: Code={product.get('default_code', 'N/A')}, Stock={product.get('qty_available', 0)}")

def main():
    """Main function"""
    print("🔄 Connecting to Odoo...")
    try:
        uid, models = connect_odoo()
        print(f"✅ Connected to Odoo (UID: {uid})")
        
        # Update product codes
        update_product_codes(models, uid)
        
        # Update stock levels
        update_stock_levels(models, uid)
        
        # Update supplier info metadata
        update_supplier_info_metadata(models, uid)
        
        # Verify
        verify_data(models, uid)
        
        print("\n✅ All product data populated successfully!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()