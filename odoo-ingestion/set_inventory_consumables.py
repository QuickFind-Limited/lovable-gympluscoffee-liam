#!/usr/bin/env python3
"""Set inventory for consumable products using stock.quant"""

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

print("📦 Setting inventory for consumable products...")

# Get stock location
location_ids = execute('stock.location', 'search', 
                      [[['usage', '=', 'internal']]], {'limit': 1})

if not location_ids:
    print("❌ No stock location found")
    exit()

location_id = location_ids[0]
print(f"✅ Using location ID: {location_id}")

# Get first 50 products
products = execute('product.product', 'search_read',
                  [[]],
                  {'fields': ['name', 'type'], 'limit': 50})

print(f"📊 Processing {len(products)} products...")

created = 0
for product in products:
    name = product['name'].lower()
    
    # Set quantity based on product type
    if 'hoodie' in name or 'jacket' in name:
        qty = random.randint(200, 400)
    elif 'essential' in name:
        qty = random.randint(300, 500)
    elif 'limited' in name:
        qty = random.randint(50, 150)
    else:
        qty = random.randint(100, 300)
    
    try:
        # Force create stock.quant even for consumables
        execute('stock.quant', 'create', [{
            'product_id': product['id'],
            'location_id': location_id,
            'quantity': float(qty),
            'inventory_quantity': float(qty),
            'inventory_quantity_auto_apply': True
        }])
        created += 1
        if created % 10 == 0:
            print(f"   ✅ Set inventory for {created} products...")
    except:
        pass

print(f"\n✅ Inventory set for {created} products")

# Verify
quant_count = execute('stock.quant', 'search_count', [[]])
print(f"📊 Total inventory records: {quant_count}")