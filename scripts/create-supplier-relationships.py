#!/usr/bin/env python3
"""
Create supplier-product relationships in Odoo
"""

import xmlrpc.client
import ssl
import sys

# Odoo credentials from tools/odoo_mcp/.env
url = 'https://source-animalfarmacy.odoo.com'
db = 'source-animalfarmacy'
username = 'admin@quickfindai.com'
password = 'BJ62wX2J4yzjS$i'

# Create SSL context to handle certificates
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

def create_supplier_relationships():
    try:
        # Connect to common endpoint
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', context=context)
        
        # Authenticate
        uid = common.authenticate(db, username, password, {})
        print(f"Authentication successful. UID: {uid}")
        
        # Connect to object endpoint
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', context=context)
        
        # Get products
        products = models.execute_kw(db, uid, password,
            'product.product', 'search_read',
            [[]],
            {'fields': ['id', 'name', 'default_code', 'product_tmpl_id'], 'limit': 20})
        print(f"\nFound {len(products)} products")
        
        # Get suppliers
        suppliers = models.execute_kw(db, uid, password,
            'res.partner', 'search_read',
            [[['supplier_rank', '>', 0]]],
            {'fields': ['id', 'name'], 'limit': 10})
        print(f"Found {len(suppliers)} suppliers")
        
        # Check existing relationships
        existing = models.execute_kw(db, uid, password,
            'product.supplierinfo', 'search_read',
            [[]],
            {'fields': ['id', 'partner_id', 'product_id'], 'limit': 1000})
        print(f"Found {len(existing)} existing relationships")
        
        # Create relationships
        created = 0
        errors = 0
        
        for i, product in enumerate(products[:10]):  # First 10 products
            supplier_idx = i % len(suppliers)
            supplier = suppliers[supplier_idx]
            
            # Check if relationship already exists
            exists = any(
                rel.get('product_id') and rel['product_id'][0] == product['id'] and
                rel.get('partner_id') and rel['partner_id'][0] == supplier['id']
                for rel in existing
            )
            
            if exists:
                print(f"Relationship already exists: {product['name']} -> {supplier['name']}")
                continue
            
            try:
                # Create supplier info
                supplier_info = {
                    'partner_id': supplier['id'],
                    'product_tmpl_id': product['product_tmpl_id'][0] if product.get('product_tmpl_id') else None,
                    'product_id': product['id'],
                    'product_name': product['name'],
                    'product_code': product.get('default_code', ''),
                    'min_qty': 1.0,
                    'price': 50.0 + (i * 5),  # Variable price
                    'delay': 7,  # 7 days delivery
                }
                
                new_id = models.execute_kw(db, uid, password,
                    'product.supplierinfo', 'create',
                    [supplier_info])
                
                print(f"Created relationship: {product['name']} -> {supplier['name']} (ID: {new_id})")
                created += 1
                
            except Exception as e:
                print(f"Error creating relationship for {product['name']}: {e}")
                errors += 1
        
        print(f"\nSummary:")
        print(f"- Created {created} new relationships")
        print(f"- Errors: {errors}")
        
        # Verify by fetching relationships for first supplier
        if suppliers:
            first_supplier = suppliers[0]
            supplier_products = models.execute_kw(db, uid, password,
                'product.supplierinfo', 'search_read',
                [[['partner_id', '=', first_supplier['id']]]],
                {'fields': ['id', 'product_id', 'product_name', 'price'], 'limit': 10})
            
            print(f"\nProducts for supplier '{first_supplier['name']}':")
            for sp in supplier_products:
                print(f"  - {sp.get('product_name', 'Unknown')} (Price: ${sp.get('price', 0):.2f})")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_supplier_relationships()