#!/usr/bin/env python3
import xmlrpc.client
import os

# Odoo connection
url = 'https://source-animalfarmacy.odoo.com'
db = 'source-animalfarmacy'
username = 'admin@quickfindai.com'
password = 'BJ62wX2J4yzjS$i'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Search for EUR-ANF-00423
print('=== Testing EUR-ANF-00423 ===')
products = models.execute_kw(db, uid, password,
    'product.supplierinfo', 'search_read',
    [[['product_code', '=', 'EUR-ANF-00423']]],
    {
        'fields': ['id', 'product_id', 'product_name', 'product_code', 'partner_id'],
        'limit': 1
    })

if products:
    p = products[0]
    print(f"\nRaw data from Odoo:")
    print(f"  ID: {p.get('id')}")
    print(f"  Product ID: {p.get('product_id')}")
    print(f"  Product Name: '{p.get('product_name')}'")
    print(f"  Product Name Type: {type(p.get('product_name'))}")
    print(f"  Product Name == 'False': {p.get('product_name') == 'False'}")
    print(f"  Product Name == False: {p.get('product_name') == False}")
    print(f"  Product Code: {p.get('product_code')}")
    print(f"  Partner: {p.get('partner_id')}")
    
    # Test the JavaScript logic in Python
    product_name = p.get('product_name')
    product_id = p.get('product_id')
    
    print(f"\nTesting display logic:")
    print(f"  product_name truthy: {bool(product_name)}")
    print(f"  product_name != 'False': {product_name != 'False'}")
    print(f"  product_name != 'false': {product_name != 'false'}")
    
    if product_name and product_name != 'False' and product_name != 'false':
        display = product_name
    elif product_id and isinstance(product_id, list) and len(product_id) > 1:
        display = product_id[1]
    else:
        display = 'Unnamed Product'
    
    print(f"\nFinal display value: '{display}'")
else:
    print("Product not found!")