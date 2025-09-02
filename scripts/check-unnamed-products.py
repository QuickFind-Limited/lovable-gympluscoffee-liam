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

print("=== Searching for supplier products with empty or missing product_name ===\n")

# Get all suppliers with products
suppliers = models.execute_kw(db, uid, password,
    'res.partner', 'search_read',
    [[['supplier_rank', '>', 0]]],
    {
        'fields': ['id', 'name'],
        'limit': 100
    })

total_unnamed = 0
suppliers_with_unnamed = []

for supplier in suppliers:
    supplier_id = supplier['id']
    supplier_name = supplier['name']
    
    # Get products for this supplier
    products = models.execute_kw(db, uid, password,
        'product.supplierinfo', 'search_read',
        [[['partner_id', '=', supplier_id]]],
        {
            'fields': ['id', 'product_id', 'product_name', 'product_code'],
            'limit': 1000
        })
    
    # Check for empty product names
    unnamed_products = [p for p in products if not p.get('product_name') or p.get('product_name').strip() == '']
    
    if unnamed_products:
        total_unnamed += len(unnamed_products)
        suppliers_with_unnamed.append({
            'supplier_id': supplier_id,
            'supplier_name': supplier_name,
            'unnamed_count': len(unnamed_products),
            'total_products': len(products),
            'sample_products': unnamed_products[:3]  # Show first 3 unnamed products
        })

print(f"Total suppliers checked: {len(suppliers)}")
print(f"Total unnamed products found: {total_unnamed}")
print(f"Suppliers with unnamed products: {len(suppliers_with_unnamed)}\n")

if suppliers_with_unnamed:
    print("=== Suppliers with unnamed products ===\n")
    for supplier_info in suppliers_with_unnamed:
        print(f"Supplier: {supplier_info['supplier_name']} (ID: {supplier_info['supplier_id']})")
        print(f"  Unnamed products: {supplier_info['unnamed_count']} out of {supplier_info['total_products']}")
        print("  Sample unnamed products:")
        for product in supplier_info['sample_products']:
            print(f"    - ID: {product['id']}, Product ID: {product.get('product_id', 'None')}, Code: {product.get('product_code', 'None')}")
        print()
else:
    print("No unnamed products found!")

# Let's also check the structure of product_supplierinfo fields
print("\n=== Checking available fields in product.supplierinfo ===")
fields_info = models.execute_kw(db, uid, password,
    'product.supplierinfo', 'fields_get',
    [],
    {'attributes': ['string', 'type', 'required']})

relevant_fields = ['product_name', 'product_id', 'product_tmpl_id', 'name', 'product_code']
for field in relevant_fields:
    if field in fields_info:
        print(f"{field}: {fields_info[field].get('string', '')} (type: {fields_info[field].get('type', '')})")