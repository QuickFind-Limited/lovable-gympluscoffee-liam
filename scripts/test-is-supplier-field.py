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

# Test 1: Search with supplier_rank > 0
print("\n=== Testing supplier_rank > 0 ===")
supplier_ids_rank = models.execute_kw(db, uid, password,
    'res.partner', 'search',
    [[['supplier_rank', '>', 0]]],
    {'limit': 10})
print(f"Found {len(supplier_ids_rank)} suppliers with supplier_rank > 0: {supplier_ids_rank}")

# Test 2: Search with is_supplier = True
print("\n=== Testing is_supplier = True ===")
supplier_ids_bool = models.execute_kw(db, uid, password,
    'res.partner', 'search',
    [[['is_supplier', '=', True]]],
    {'limit': 10})
print(f"Found {len(supplier_ids_bool)} suppliers with is_supplier = True: {supplier_ids_bool}")

# Check if the field exists
print("\n=== Checking fields on res.partner ===")
fields = models.execute_kw(db, uid, password,
    'res.partner', 'fields_get',
    [],
    {'attributes': ['string', 'help', 'type']})

if 'is_supplier' in fields:
    print("✓ is_supplier field exists:")
    print(f"  - Type: {fields['is_supplier']['type']}")
    print(f"  - String: {fields['is_supplier'].get('string', 'N/A')}")
else:
    print("✗ is_supplier field NOT found")

if 'supplier_rank' in fields:
    print("\n✓ supplier_rank field exists:")
    print(f"  - Type: {fields['supplier_rank']['type']}")
    print(f"  - String: {fields['supplier_rank'].get('string', 'N/A')}")

# Get details of suppliers
if supplier_ids_rank:
    print(f"\n=== Details of first supplier (using supplier_rank) ===")
    supplier = models.execute_kw(db, uid, password,
        'res.partner', 'read',
        [[supplier_ids_rank[0]]],
        {'fields': ['name', 'supplier_rank', 'is_supplier'] if 'is_supplier' in fields else ['name', 'supplier_rank']})
    print(supplier[0])