#!/usr/bin/env python3
"""
Check specific product EUR-ANF-8904 that shows "Page not found" as name
"""

import xmlrpc.client
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Odoo credentials from environment
url = os.getenv('ODOO_URL', 'https://goldenpawsholistics.odoo.com')
db = os.getenv('ODOO_DB', 'goldenpawsholistics')
username = os.getenv('ODOO_USERNAME', 'thelovableai@gmail.com')
password = os.getenv('ODOO_PASSWORD')

if not password:
    print("Error: ODOO_PASSWORD not found in environment variables")
    exit(1)

# Connect to Odoo
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

if not uid:
    print("Authentication failed")
    exit(1)

models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Search for products with code EUR-ANF-8904
print("Searching for products with code EUR-ANF-8904...")

# Search in product.product
product_ids = models.execute_kw(
    db, uid, password,
    'product.product', 'search',
    [[['default_code', '=', 'EUR-ANF-8904']]]
)

if product_ids:
    print(f"\nFound {len(product_ids)} product(s) with code EUR-ANF-8904")
    
    products = models.execute_kw(
        db, uid, password,
        'product.product', 'read',
        [product_ids],
        {'fields': ['id', 'name', 'display_name', 'default_code', 'product_tmpl_id']}
    )
    
    for product in products:
        print(f"\nProduct ID: {product['id']}")
        print(f"Name: {product['name']}")
        print(f"Display Name: {product['display_name']}")
        print(f"Default Code: {product['default_code']}")
        print(f"Product Template ID: {product['product_tmpl_id']}")
else:
    print("No products found with code EUR-ANF-8904")

# Search in product.template
print("\n" + "="*50)
print("Searching in product.template...")

template_ids = models.execute_kw(
    db, uid, password,
    'product.template', 'search',
    [[['default_code', '=', 'EUR-ANF-8904']]]
)

if template_ids:
    print(f"\nFound {len(template_ids)} template(s) with code EUR-ANF-8904")
    
    templates = models.execute_kw(
        db, uid, password,
        'product.template', 'read',
        [template_ids],
        {'fields': ['id', 'name', 'display_name', 'default_code']}
    )
    
    for template in templates:
        print(f"\nTemplate ID: {template['id']}")
        print(f"Name: {template['name']}")
        print(f"Display Name: {template['display_name']}")
        print(f"Default Code: {template['default_code']}")
else:
    print("No templates found with code EUR-ANF-8904")

# Now check supplier info for this product
print("\n" + "="*50)
print("Checking supplier info for EUR-ANF-8904...")

# Search for supplier info containing this code
supplier_info_ids = models.execute_kw(
    db, uid, password,
    'product.supplierinfo', 'search',
    [[['product_code', '=', 'EUR-ANF-8904']]]
)

if supplier_info_ids:
    print(f"\nFound {len(supplier_info_ids)} supplier info record(s) with product_code EUR-ANF-8904")
    
    supplier_infos = models.execute_kw(
        db, uid, password,
        'product.supplierinfo', 'read',
        [supplier_info_ids],
        {'fields': ['id', 'partner_id', 'product_name', 'product_code', 'product_id', 'product_tmpl_id']}
    )
    
    for info in supplier_infos:
        print(f"\nSupplier Info ID: {info['id']}")
        print(f"Partner ID: {info['partner_id']}")
        print(f"Product Name: {info['product_name']} (type: {type(info['product_name'])})")
        print(f"Product Code: {info['product_code']}")
        print(f"Product ID: {info['product_id']} (type: {type(info['product_id'])})")
        print(f"Product Template ID: {info['product_tmpl_id']}")
        
        # If product_id is set, fetch the product details
        if info['product_id']:
            if isinstance(info['product_id'], list) and len(info['product_id']) > 0:
                prod_id = info['product_id'][0]
            else:
                prod_id = info['product_id']
            
            try:
                prod_details = models.execute_kw(
                    db, uid, password,
                    'product.product', 'read',
                    [[prod_id]],
                    {'fields': ['name', 'display_name', 'default_code']}
                )
                if prod_details:
                    print(f"\nLinked Product Details:")
                    print(f"  - Name: {prod_details[0]['name']}")
                    print(f"  - Display Name: {prod_details[0]['display_name']}")
                    print(f"  - Default Code: {prod_details[0]['default_code']}")
            except Exception as e:
                print(f"Error fetching product details: {e}")
else:
    print("No supplier info found with product_code EUR-ANF-8904")

# Also check if "Page not found" appears anywhere in product names
print("\n" + "="*50)
print("Checking for products with 'Page not found' in name...")

page_not_found_products = models.execute_kw(
    db, uid, password,
    'product.product', 'search_read',
    [[['name', 'ilike', 'Page not found']]],
    {'fields': ['id', 'name', 'default_code'], 'limit': 10}
)

if page_not_found_products:
    print(f"\nFound {len(page_not_found_products)} product(s) with 'Page not found' in name:")
    for prod in page_not_found_products:
        print(f"  - ID: {prod['id']}, Code: {prod['default_code']}, Name: {prod['name']}")
else:
    print("No products found with 'Page not found' in name")