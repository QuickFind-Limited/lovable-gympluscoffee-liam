#!/usr/bin/env python3
"""Fix product types - convert from consu to product for inventory tracking"""

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

print("🔧 FIXING PRODUCT TYPES FOR INVENTORY")
print("="*60)

# First, let's check what we have
print("\n📊 Current product types:")
products = execute('product.template', 'search_read', 
                  [[]], 
                  {'fields': ['name', 'type', 'detailed_type'], 'limit': 5})

for p in products[:3]:
    print(f"   {p['name'][:40]}: type={p.get('type', 'N/A')}, detailed_type={p.get('detailed_type', 'N/A')}")

# In Odoo 17/18, we need to update detailed_type, not type
print("\n🔄 Converting products to stockable...")

# Get all consumable products
consumables = execute('product.template', 'search', 
                     [[['detailed_type', '=', 'consu']]], 
                     {'limit': 100})

print(f"   Found {len(consumables)} consumable products")

# Convert them to stockable products
converted = 0
for product_id in consumables[:50]:  # Start with 50
    try:
        # Update to stockable product
        execute('product.template', 'write', 
               [[product_id], {'detailed_type': 'product'}])
        converted += 1
        if converted % 10 == 0:
            print(f"   ✅ Converted {converted} products...")
    except Exception as e:
        # Try alternative field names
        try:
            execute('product.template', 'write', 
                   [[product_id], {'type': 'product'}])
            converted += 1
        except:
            pass

print(f"\n✅ Converted {converted} products to stockable")

# Now set inventory for these products
print("\n📦 Setting inventory levels...")

# Get stock location
location_ids = execute('stock.location', 'search', 
                      [[['usage', '=', 'internal']]], {'limit': 1})

if location_ids:
    location_id = location_ids[0]
    
    # Get stockable products
    stockable = execute('product.product', 'search_read',
                       [[['detailed_type', '=', 'product']]],
                       {'fields': ['name'], 'limit': 50})
    
    if not stockable:
        # Try with type field
        stockable = execute('product.product', 'search_read',
                           [[['type', '=', 'product']]],
                           {'fields': ['name'], 'limit': 50})
    
    print(f"   Found {len(stockable)} stockable products")
    
    inventory_set = 0
    for product in stockable[:30]:  # Set inventory for 30 products
        name = product['name'].lower()
        
        # Determine quantity
        if 'hoodie' in name or 'jacket' in name:
            qty = random.randint(200, 400)
        elif 'essential' in name:
            qty = random.randint(300, 500)
        elif 'limited' in name:
            qty = random.randint(50, 150)
        else:
            qty = random.randint(100, 300)
        
        try:
            # Create inventory adjustment
            execute('stock.quant', 'create', [{
                'product_id': product['id'],
                'location_id': location_id,
                'quantity': float(qty)
            }])
            inventory_set += 1
            if inventory_set % 10 == 0:
                print(f"   ✅ Set inventory for {inventory_set} products...")
        except:
            pass
    
    print(f"\n✅ Inventory set for {inventory_set} products")

# Verify
print("\n📈 Final verification:")
stockable_count = execute('product.template', 'search_count', 
                         [[['detailed_type', '=', 'product']]])
if stockable_count == 0:
    stockable_count = execute('product.template', 'search_count', 
                             [[['type', '=', 'product']]])

quant_count = execute('stock.quant', 'search_count', [[]])

print(f"   Stockable products: {stockable_count}")
print(f"   Inventory records: {quant_count}")

print("\n🎉 Products fixed and inventory set!")