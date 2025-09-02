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

print(f"Authenticated with UID: {uid}")

# Test the exact query the edge function is using
domain = [['supplier_rank', '>', 0]]

print(f"\n=== Testing suppliers query ===")
print(f"Domain: {domain}")

# Get suppliers
suppliers = models.execute_kw(db, uid, password,
    'res.partner', 'search_read',
    [domain],
    {
        'fields': ['id', 'name', 'email', 'phone', 'street', 'street2', 'city', 'state_id', 
                   'zip', 'country_id', 'website', 'vat', 'supplier_rank'],
        'offset': 0,
        'limit': 10
    })

print(f"\nFound {len(suppliers)} suppliers")

# Display suppliers
for i, supplier in enumerate(suppliers):
    print(f"\n--- Supplier {i+1} ---")
    print(f"ID: {supplier.get('id')}")
    print(f"Name: {supplier.get('name')}")
    print(f"Email: {supplier.get('email')}")
    print(f"Phone: {supplier.get('phone')}")
    print(f"City: {supplier.get('city')}")
    print(f"Supplier Rank: {supplier.get('supplier_rank')}")

# Count total
total_count = models.execute_kw(db, uid, password,
    'res.partner', 'search_count',
    [domain])

print(f"\nTotal suppliers with supplier_rank > 0: {total_count}")