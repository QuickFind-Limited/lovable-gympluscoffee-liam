#!/usr/bin/env python3
"""Convert products from consumable to stockable and set inventory"""

import xmlrpc.client
import os
import random
from dotenv import load_dotenv

load_dotenv()

# Connect
url = os.getenv('odoo_url', 'https://source-gym-plus-coffee.odoo.com')
db = os.getenv('db', 'source-gym-plus-coffee')
username = os.getenv('username', 'admin@quickfindai.com')
password = os.getenv('password', 'BJ62wX2J4yzjS$i')

print("🔄 CONVERTING PRODUCTS TO STOCKABLE & SETTING INVENTORY")
print("="*60)

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
uid = common.authenticate(db, username, password, {})
print(f"✅ Connected to Odoo\n")

def execute(model, method, *args):
    return models.execute_kw(db, uid, password, model, method, *args)

# Get all consumable products
print("📦 Fetching products...")
products = execute('product.template', 'search_read', 
                  [[['type', '=', 'consu']]], 
                  {'fields': ['name', 'type'], 'limit': 500})

print(f"   Found {len(products)} consumable products\n")

# Convert to stockable (product type)
print("🔄 Converting to stockable products...")
converted = 0
failed = 0

for product in products[:100]:  # Start with first 100
    try:
        # Update product type to 'product' (stockable)
        execute('product.template', 'write', 
                [[product['id']], {'type': 'product'}])
        converted += 1
        
        if converted % 20 == 0:
            print(f"   Converted {converted} products...")
    except Exception as e:
        failed += 1
        if failed <= 3:
            print(f"   ❌ Failed: {product['name'][:30]} - {str(e)[:50]}")

print(f"\n✅ Converted {converted} products to stockable")
if failed > 0:
    print(f"   ⚠️ Failed: {failed} products")

# Now set inventory levels
print("\n📊 Setting inventory levels...")

# Get stock location
location_ids = execute('stock.location', 'search', 
                      [[['usage', '=', 'internal']]], {'limit': 1})

if not location_ids:
    print("   ❌ No stock location found")
else:
    location_id = location_ids[0]
    print(f"   Using location ID: {location_id}")
    
    # Get product variants (product.product)
    stockable_products = execute('product.product', 'search_read',
                                [[['type', '=', 'product']]],
                                {'fields': ['name', 'product_tmpl_id'], 'limit': 200})
    
    print(f"   Found {len(stockable_products)} stockable product variants")
    
    inventory_set = 0
    
    for product in stockable_products:
        name = product['name'].lower()
        
        # Set inventory based on product type
        if 'limited' in name or 'special' in name:
            quantity = random.randint(50, 150)
        elif 'essential' in name or 'basic' in name:
            quantity = random.randint(400, 800)
        elif any(x in name for x in ['hoodie', 'jacket', 'sweatshirt']):
            quantity = random.randint(200, 500)
        elif any(x in name for x in ['shorts', 'tank', 't-shirt']):
            quantity = random.randint(150, 400)
        elif any(x in name for x in ['bag', 'bottle', 'socks', 'beanie']):
            quantity = random.randint(100, 300)
        else:
            quantity = random.randint(100, 250)
        
        try:
            # Check if quant exists
            existing = execute('stock.quant', 'search', [
                [['product_id', '=', product['id']],
                 ['location_id', '=', location_id]]
            ])
            
            if existing:
                # Update existing
                execute('stock.quant', 'write', 
                       [existing[0], {'quantity': quantity}])
            else:
                # Create new
                execute('stock.quant', 'create', [{
                    'product_id': product['id'],
                    'location_id': location_id,
                    'quantity': quantity
                }])
            
            inventory_set += 1
            
            if inventory_set % 20 == 0:
                print(f"   Set inventory for {inventory_set} products...")
                
        except Exception as e:
            pass  # Skip errors

    print(f"\n✅ Set inventory for {inventory_set} products")

# Verify
print("\n📈 Verification:")
stockable_count = execute('product.template', 'search_count', 
                         [[['type', '=', 'product']]])
quant_count = execute('stock.quant', 'search_count', [[]])

print(f"   Stockable products: {stockable_count}")
print(f"   Inventory records: {quant_count}")

print("\n🎉 Done! Products are now stockable with inventory levels.")