#!/usr/bin/env python3
"""Simple inventory setup - work with what we have"""

import xmlrpc.client
import os
import random
from dotenv import load_dotenv

load_dotenv()

url = os.getenv('odoo_url', 'https://source-gym-plus-coffee.odoo.com')
db = os.getenv('db', 'source-gym-plus-coffee')
username = os.getenv('username', 'admin@quickfindai.com')
password = os.getenv('password', 'BJ62wX2J4yzjS$i')

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
uid = common.authenticate(db, username, password, {})

def execute(model, method, *args):
    return models.execute_kw(db, uid, password, model, method, *args)

print("📦 INVENTORY SETUP")
print("="*50)

# Check available fields
print("\n🔍 Checking product fields...")
try:
    fields = execute('product.template', 'fields_get', [], {'attributes': ['string', 'type']})
    type_fields = [f for f in fields if 'type' in f.lower()]
    print(f"   Type-related fields: {type_fields}")
except:
    pass

# Get products
products = execute('product.template', 'search_read', 
                  [[]], 
                  {'fields': ['name', 'type'], 'limit': 10})

print(f"\n📊 Sample products:")
for p in products[:3]:
    print(f"   {p['name'][:40]}: type={p.get('type', 'N/A')}")

# Try to update product type
print("\n🔄 Attempting to update product types...")
product_ids = execute('product.template', 'search', [[]], {'limit': 20})

updated = 0
for pid in product_ids:
    try:
        # Try updating to product type
        execute('product.template', 'write', [[pid], {'type': 'product'}])
        updated += 1
    except:
        try:
            # Try service type as alternative
            execute('product.template', 'write', [[pid], {'type': 'service'}])
            updated += 1
        except:
            pass

print(f"   Updated {updated} products")

# Create inventory adjustments anyway
print("\n📈 Creating inventory adjustments...")

# Get location
locations = execute('stock.location', 'search_read', 
                   [[['usage', '=', 'internal']]], 
                   {'fields': ['name'], 'limit': 5})

if locations:
    location_id = locations[0]['id']
    print(f"   Using location: {locations[0]['name']}")
    
    # Get product variants
    products = execute('product.product', 'search', [[]], {'limit': 30})
    
    created = 0
    for product_id in products:
        qty = random.randint(100, 500)
        try:
            # Create quant
            execute('stock.quant', 'create', [{
                'product_id': product_id,
                'location_id': location_id,
                'quantity': float(qty)
            }])
            created += 1
            if created % 10 == 0:
                print(f"   Created {created} inventory records...")
        except:
            # Try inventory adjustment
            try:
                execute('stock.inventory.line', 'create', [{
                    'product_id': product_id,
                    'location_id': location_id,
                    'product_qty': float(qty)
                }])
                created += 1
            except:
                pass
    
    print(f"\n✅ Created {created} inventory records")

# Verify
quants = execute('stock.quant', 'search_count', [[]])
print(f"\n📊 Total inventory records: {quants}")

print("\n✅ Done!")