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

print("=== Analyzing product_name values that might appear empty ===\n")

# Check various false-like values
false_values = ['False', 'false', 'FALSE', 'None', 'none', 'null', 'NULL', '0', '']
total_problematic = 0

for val in false_values:
    if val == '':
        # Special case for empty string
        products = models.execute_kw(db, uid, password,
            'product.supplierinfo', 'search_read',
            [['|', ['product_name', '=', ''], ['product_name', '=', False]]],
            {
                'fields': ['id', 'product_id', 'product_name', 'product_code'],
                'limit': 5
            })
        count = models.execute_kw(db, uid, password,
            'product.supplierinfo', 'search_count',
            [['|', ['product_name', '=', ''], ['product_name', '=', False]]])
    else:
        products = models.execute_kw(db, uid, password,
            'product.supplierinfo', 'search_read',
            [[['product_name', '=', val]]],
            {
                'fields': ['id', 'product_id', 'product_name', 'product_code'],
                'limit': 5
            })
        count = models.execute_kw(db, uid, password,
            'product.supplierinfo', 'search_count',
            [[['product_name', '=', val]]])
    
    if count > 0:
        total_problematic += count
        print(f"Products with product_name = '{val}': {count}")
        print("Sample products:")
        for p in products:
            product_display = p.get('product_id', ['', ''])[1] if p.get('product_id') else 'No product'
            print(f"  - Code: {p.get('product_code')}, Name: '{p.get('product_name')}', Product: {product_display}")
        print()

print(f"\nTotal problematic products: {total_problematic}")

# Let's also check unique product_name values to understand the data
print("\n=== Checking unique product_name patterns ===")
# Get a sample of products to analyze patterns
sample_products = models.execute_kw(db, uid, password,
    'product.supplierinfo', 'search_read',
    [[]],
    {
        'fields': ['product_name'],
        'limit': 1000
    })

# Analyze unique values
unique_values = {}
for p in sample_products:
    val = str(p.get('product_name', ''))
    if val in unique_values:
        unique_values[val] += 1
    else:
        unique_values[val] = 1

# Show problematic values
print("\nProblematic product_name values found:")
for val, count in sorted(unique_values.items()):
    if val in ['False', 'false', 'FALSE', 'None', 'none', 'null', 'NULL', '0', '', 'True']:
        print(f"  '{val}': {count} occurrences")