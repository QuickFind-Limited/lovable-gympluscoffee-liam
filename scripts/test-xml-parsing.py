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

# Get suppliers
print("\n=== Fetching Suppliers ===")
supplier_ids = models.execute_kw(db, uid, password,
    'res.partner', 'search',
    [[['supplier_rank', '>', 0]]],
    {'limit': 10})
print(f"Found {len(supplier_ids)} suppliers: {supplier_ids}")

# Get supplier details
suppliers = models.execute_kw(db, uid, password,
    'res.partner', 'read',
    [supplier_ids],
    {'fields': ['id', 'name', 'email', 'phone', 'city', 'supplier_rank']})

print("\nSupplier Details:")
for supplier in suppliers:
    print(f"\n- {supplier['name']} (ID: {supplier['id']})")
    print(f"  Email: {supplier.get('email', 'N/A')}")
    print(f"  Phone: {supplier.get('phone', 'N/A')}")
    print(f"  City: {supplier.get('city', 'N/A')}")
    
    # Get product count for this supplier
    product_count = models.execute_kw(db, uid, password,
        'product.supplierinfo', 'search_count',
        [[['partner_id', '=', supplier['id']]]])
    print(f"  Products: {product_count}")
    
    # Get first 3 products for this supplier
    if product_count > 0:
        product_infos = models.execute_kw(db, uid, password,
            'product.supplierinfo', 'search_read',
            [[['partner_id', '=', supplier['id']]]],
            {
                'fields': ['id', 'product_id', 'product_name', 'product_code', 'price', 'min_qty', 'delay'],
                'limit': 3
            })
        
        print("  Sample Products:")
        for prod in product_infos:
            print(f"    - {prod.get('product_name', 'Unknown')}")
            print(f"      Code: {prod.get('product_code', 'N/A')}")
            print(f"      Price: ${prod.get('price', 0):.2f}")
            print(f"      Min Qty: {prod.get('min_qty', 0)}")

print("\n\n=== Summary ===")
print(f"Total suppliers with products: {sum(1 for s in suppliers if models.execute_kw(db, uid, password, 'product.supplierinfo', 'search_count', [[['partner_id', '=', s['id']]]]) > 0)}")
print("Ready to display in UI!")