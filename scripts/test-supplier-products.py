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

if not uid:
    print("Authentication failed!")
    exit(1)

models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Test supplier ID
supplier_id = 23

print(f"\n=== Testing products for supplier ID {supplier_id} ===")

# Count total products for this supplier
count = models.execute_kw(db, uid, password,
    'product.supplierinfo', 'search_count',
    [[['partner_id', '=', supplier_id]]])

print(f"Total product.supplierinfo records for supplier {supplier_id}: {count}")

# Get first 10 supplier products
supplier_products = models.execute_kw(db, uid, password,
    'product.supplierinfo', 'search_read',
    [[['partner_id', '=', supplier_id]]],
    {
        'fields': ['id', 'product_id', 'product_name', 'product_code', 'price', 'min_qty', 'delay'],
        'offset': 0,
        'limit': 10
    })

print(f"\nFound {len(supplier_products)} supplier product records (showing first 10)")

# Display the products
for i, sp in enumerate(supplier_products):
    print(f"\n--- Product {i+1} ---")
    print(f"ID: {sp.get('id')}")
    print(f"Product ID: {sp.get('product_id')}")
    print(f"Product Name: {sp.get('product_name')}")
    print(f"Product Code: {sp.get('product_code')}")
    print(f"Price: {sp.get('price')}")
    print(f"Min Qty: {sp.get('min_qty')}")
    print(f"Delay: {sp.get('delay')}")

# Get product details for the first product ID if available
if supplier_products and supplier_products[0].get('product_id'):
    product_id = supplier_products[0]['product_id'][0]
    print(f"\n=== Getting full details for product ID {product_id} ===")
    
    products = models.execute_kw(db, uid, password,
        'product.product', 'search_read',
        [[['id', '=', product_id]]],
        {
            'fields': ['id', 'name', 'default_code', 'list_price', 'standard_price', 'qty_available'],
            'limit': 1
        })
    
    if products:
        print(f"Product details: {products[0]}")