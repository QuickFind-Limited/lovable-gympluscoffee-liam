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

# Test simple query first
print("=== Testing simple ID search ===")
supplier_ids = models.execute_kw(db, uid, password,
    'res.partner', 'search',
    [[['supplier_rank', '>', 0]]],
    {'limit': 10})

print(f"Found supplier IDs: {supplier_ids}")

# Then read the records
if supplier_ids:
    print("\n=== Reading supplier records ===")
    suppliers = models.execute_kw(db, uid, password,
        'res.partner', 'read',
        [supplier_ids, ['id', 'name', 'email', 'phone', 'city', 'supplier_rank']])
    
    print(f"Found {len(suppliers)} suppliers")
    for supplier in suppliers[:3]:
        print(f"\nSupplier: {supplier['name']}")
        print(f"  ID: {supplier['id']}")
        print(f"  Email: {supplier.get('email', 'N/A')}")
        print(f"  City: {supplier.get('city', 'N/A')}")
        print(f"  Rank: {supplier.get('supplier_rank', 0)}")