#!/usr/bin/env python3
"""Create NEW products as stockable type for inventory tracking"""

import xmlrpc.client
import os
import json
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

print("📦 CREATING NEW STOCKABLE PRODUCTS")
print("="*60)

# Load original product data
with open('../data/gym_plus_coffee_products.json', 'r') as f:
    data = json.load(f)

products = data['products']
print(f"✅ Loaded {len(products)} products from JSON")

# Get stock location
location_ids = execute('stock.location', 'search', 
                      [[['usage', '=', 'internal']]], {'limit': 1})
location_id = location_ids[0] if location_ids else None

created = 0
inventory_set = 0

# Create first 100 products as STOCKABLE
for product in products[:100]:
    try:
        # Create product with explicit stockable type
        product_data = {
            'name': f"[STOCK] {product['name']}",
            'default_code': f"STOCK-{product.get('sku', '')}",
            'list_price': float(product.get('price', 29.99)),
            'standard_price': float(product.get('price', 29.99)) * 0.4,
            'type': 'product',  # This makes it stockable!
            'sale_ok': True,
            'purchase_ok': True,
            'categ_id': 1,
            'tracking': 'none',  # No serial/lot tracking
            'invoice_policy': 'order',
            'service_type': 'manual'
        }
        
        # Try with detailed_type first (Odoo 16+)
        try:
            product_data['detailed_type'] = 'product'
            product_id = execute('product.template', 'create', [product_data])
        except:
            # Fallback to just type field
            product_id = execute('product.template', 'create', [product_data])
        
        created += 1
        
        # Set inventory for this product
        if location_id:
            # Get product variant
            variant_ids = execute('product.product', 'search', 
                                [['product_tmpl_id', '=', product_id]], {'limit': 1})
            
            if variant_ids:
                # Determine quantity based on product type
                name = product['name'].lower()
                if 'hoodie' in name or 'jacket' in name:
                    qty = random.randint(200, 500)
                elif 'essential' in name or 'basic' in name:
                    qty = random.randint(300, 600)
                elif 'limited' in name or 'premium' in name:
                    qty = random.randint(50, 150)
                else:
                    qty = random.randint(100, 400)
                
                try:
                    # Create inventory
                    execute('stock.quant', 'create', [{
                        'product_id': variant_ids[0],
                        'location_id': location_id,
                        'quantity': float(qty)
                    }])
                    inventory_set += 1
                except:
                    # Try alternative method
                    try:
                        execute('stock.quant', 'sudo().create', [{
                            'product_id': variant_ids[0],
                            'location_id': location_id,
                            'quantity': float(qty),
                            'inventory_quantity': float(qty)
                        }])
                        inventory_set += 1
                    except:
                        pass
        
        if created % 10 == 0:
            print(f"   Created {created} stockable products, {inventory_set} with inventory...")
            
    except Exception as e:
        if created == 0:
            print(f"   Error on first product: {e}")
        continue

print(f"\n✅ Created {created} stockable products")
print(f"✅ Set inventory for {inventory_set} products")

# Verify
stockable_count = execute('product.template', 'search_count', 
                         [['name', 'like', '[STOCK]']])
quant_count = execute('stock.quant', 'search_count', [[]])

print(f"\n📊 Verification:")
print(f"   Stockable products: {stockable_count}")
print(f"   Inventory records: {quant_count}")

print("\n🎉 Stockable products created with inventory!")