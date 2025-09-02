#!/usr/bin/env python3
"""
Direct test of Odoo API to debug product access issue
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

def test_odoo_connection():
    try:
        # Connect to common endpoint
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', context=context)
        version = common.version()
        print(f"Odoo version: {version}")
        
        # Authenticate
        uid = common.authenticate(db, username, password, {})
        print(f"Authentication successful. UID: {uid}")
        
        # Connect to object endpoint
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', context=context)
        
        # Test 1: Count products
        product_count = models.execute_kw(db, uid, password,
            'product.product', 'search_count',
            [[]])
        print(f"\nTotal products count: {product_count}")
        
        # Test 2: Search for product IDs
        product_ids = models.execute_kw(db, uid, password,
            'product.product', 'search',
            [[]], {'limit': 10})
        print(f"Product IDs found: {product_ids}")
        
        # Test 3: Try different domain filters
        print("\nTrying different filters:")
        
        # Active products
        active_count = models.execute_kw(db, uid, password,
            'product.product', 'search_count',
            [[['active', '=', True]]])
        print(f"Active products: {active_count}")
        
        # Products that can be sold
        sale_ok_count = models.execute_kw(db, uid, password,
            'product.product', 'search_count',
            [[['sale_ok', '=', True]]])
        print(f"Products marked for sale: {sale_ok_count}")
        
        # Products that can be purchased
        purchase_ok_count = models.execute_kw(db, uid, password,
            'product.product', 'search_count',
            [[['purchase_ok', '=', True]]])
        print(f"Products marked for purchase: {purchase_ok_count}")
        
        # Test 4: Try product.template
        template_count = models.execute_kw(db, uid, password,
            'product.template', 'search_count',
            [[]])
        print(f"\nProduct templates count: {template_count}")
        
        template_ids = models.execute_kw(db, uid, password,
            'product.template', 'search',
            [[]], {'limit': 10})
        print(f"Template IDs found: {template_ids}")
        
        # Test 5: If we have template IDs, read them
        if template_ids:
            templates = models.execute_kw(db, uid, password,
                'product.template', 'read',
                [template_ids[:5]], {'fields': ['id', 'name', 'default_code', 'type']})
            print(f"\nFirst 5 templates:")
            for t in templates:
                print(f"  - {t['name']} (ID: {t['id']}, Code: {t.get('default_code', 'N/A')})")
        
        # Test 6: Check user permissions
        print("\nChecking user permissions:")
        has_access = models.execute_kw(db, uid, password,
            'ir.model.access', 'check',
            ['product.product', 'read'])
        print(f"Has read access to product.product: {has_access}")
        
        # Test 7: Get products via search_read on templates
        print("\nTrying to get product variants from templates:")
        if template_ids:
            # Get the first template
            template_id = template_ids[0]
            
            # Try to get product variants for this template
            variants = models.execute_kw(db, uid, password,
                'product.product', 'search_read',
                [[['product_tmpl_id', '=', template_id]]],
                {'fields': ['id', 'name', 'default_code']})
            print(f"Variants for template {template_id}: {variants}")
        
        # Test 8: Check if products are archived
        print("\nChecking for archived products:")
        archived_count = models.execute_kw(db, uid, password,
            'product.product', 'search_count',
            [[['active', '=', False]]])
        print(f"Archived products: {archived_count}")
        
        # Test 9: Try with no domain at all in search_read
        print("\nTrying search_read with no restrictions:")
        products = models.execute_kw(db, uid, password,
            'product.product', 'search_read',
            [[]],
            {'fields': ['id', 'name'], 'limit': 5})
        print(f"Products via search_read: {products}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_odoo_connection()