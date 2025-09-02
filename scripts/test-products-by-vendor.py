#!/usr/bin/env python3
import xmlrpc.client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('../tools/odoo_mcp/.env')

# Odoo connection details
url = os.getenv('ODOO_URL', 'https://source-animalfarmacy.odoo.com')
db = os.getenv('ODOO_DB', 'source-animalfarmacy')
username = os.getenv('ODOO_USERNAME', 'admin@quickfindai.com')
password = os.getenv('ODOO_PASSWORD', 'BJ62wX2J4yzjS$i')

# Connect to Odoo
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
print(f"Authenticated with UID: {uid}")

models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Test vendor ID 23 (European Pet Distributors)
vendor_id = 23
print(f"\n=== Testing products for vendor ID {vendor_id} ===")

# Method 1: Search product.product where seller_ids.name = vendor_id
print("\nMethod 1: Using product.product with seller_ids.name filter")
try:
    products = models.execute_kw(db, uid, password,
        'product.product', 'search_read',
        [[['seller_ids.name', '=', vendor_id]]],
        {
            'fields': ['id', 'name', 'default_code', 'list_price', 'qty_available'],
            'limit': 5
        })
    
    print(f"Found {len(products)} products")
    for product in products:
        print(f"- {product['name']} (ID: {product['id']})")
        print(f"  Code: {product.get('default_code', 'N/A')}")
        print(f"  Price: ${product.get('list_price', 0):.2f}")
except Exception as e:
    print(f"Error: {e}")

# Method 2: Use product.supplierinfo to get products
print("\n\nMethod 2: Using product.supplierinfo")
try:
    supplier_infos = models.execute_kw(db, uid, password,
        'product.supplierinfo', 'search_read',
        [[['partner_id', '=', vendor_id]]],
        {
            'fields': ['id', 'product_id', 'product_tmpl_id', 'product_name', 'product_code', 'price', 'min_qty'],
            'limit': 5
        })
    
    print(f"Found {len(supplier_infos)} supplier info records")
    for info in supplier_infos:
        print(f"- {info.get('product_name', 'Unknown')}")
        print(f"  Product ID: {info.get('product_id', 'N/A')}")
        print(f"  Template ID: {info.get('product_tmpl_id', 'N/A')}")
        print(f"  Code: {info.get('product_code', 'N/A')}")
        print(f"  Price: ${info.get('price', 0):.2f}")
        print(f"  Min Qty: {info.get('min_qty', 0)}")
        
        # Get the actual product details if product_id exists
        if info.get('product_id'):
            product_id = info['product_id'][0] if isinstance(info['product_id'], list) else info['product_id']
            try:
                product = models.execute_kw(db, uid, password,
                    'product.product', 'read',
                    [[product_id]],
                    {'fields': ['name', 'default_code', 'list_price']})
                if product:
                    print(f"  Product Details: {product[0]['name']}")
            except:
                pass
except Exception as e:
    print(f"Error: {e}")

# Method 3: Check if we need to use product.template instead
print("\n\nMethod 3: Checking product.template")
try:
    # First get a product template ID from supplier info
    supplier_info = models.execute_kw(db, uid, password,
        'product.supplierinfo', 'search_read',
        [[['partner_id', '=', vendor_id]]],
        {
            'fields': ['product_tmpl_id'],
            'limit': 1
        })
    
    if supplier_info and supplier_info[0].get('product_tmpl_id'):
        tmpl_id = supplier_info[0]['product_tmpl_id'][0] if isinstance(supplier_info[0]['product_tmpl_id'], list) else supplier_info[0]['product_tmpl_id']
        
        # Get product variants for this template
        products = models.execute_kw(db, uid, password,
            'product.product', 'search_read',
            [[['product_tmpl_id', '=', tmpl_id]]],
            {
                'fields': ['id', 'name', 'default_code', 'list_price'],
                'limit': 5
            })
        
        print(f"Found {len(products)} product variants for template {tmpl_id}")
        for product in products:
            print(f"- {product['name']} (ID: {product['id']})")
except Exception as e:
    print(f"Error: {e}")

# Method 4: Direct search on product.template with seller_ids
print("\n\nMethod 4: Using product.template with seller_ids filter")
try:
    templates = models.execute_kw(db, uid, password,
        'product.template', 'search_read',
        [[['seller_ids.name', '=', vendor_id]]],
        {
            'fields': ['id', 'name', 'default_code', 'list_price'],
            'limit': 5
        })
    
    print(f"Found {len(templates)} product templates")
    for template in templates:
        print(f"- {template['name']} (ID: {template['id']})")
        print(f"  Code: {template.get('default_code', 'N/A')}")
        print(f"  Price: ${template.get('list_price', 0):.2f}")
except Exception as e:
    print(f"Error: {e}")