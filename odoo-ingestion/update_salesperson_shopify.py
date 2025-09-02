#!/usr/bin/env python3
"""Update all orders to use Shopify as salesperson"""

import xmlrpc.client
import os
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

print("👤 Updating salesperson to Shopify...")

# First, create or find Shopify user
shopify_users = execute('res.users', 'search', [[['name', 'ilike', 'Shopify']]])

if not shopify_users:
    # Create Shopify partner
    partner_id = execute('res.partner', 'create', [{
        'name': 'Shopify Sales',
        'email': 'shopify@gympluscoffee.com',
        'customer_rank': 0,
        'supplier_rank': 0
    }])
    
    # Create Shopify user
    try:
        shopify_id = execute('res.users', 'create', [{
            'name': 'Shopify',
            'login': 'shopify@gympluscoffee.com',
            'partner_id': partner_id,
            'new_password': 'ShopifyGymCoffee2025!'
        }])
        print(f"✅ Created Shopify user (ID: {shopify_id})")
    except:
        # If user creation fails, just update partner name
        execute('res.partner', 'write', [[uid], {'name': 'Shopify'}])
        shopify_id = uid
        print(f"✅ Updated current user name to Shopify")
else:
    shopify_id = shopify_users[0]
    print(f"✅ Found existing Shopify user (ID: {shopify_id})")

# Update all orders to use Shopify
print("\n📋 Updating orders...")

# Get all orders
all_orders = execute('sale.order', 'search', [[]])
print(f"   Found {len(all_orders)} orders to update")

# Update in batches
batch_size = 100
updated = 0

for i in range(0, len(all_orders), batch_size):
    batch = all_orders[i:i+batch_size]
    try:
        execute('sale.order', 'write', [batch, {'user_id': shopify_id}])
        updated += len(batch)
        print(f"   Updated {updated}/{len(all_orders)} orders...")
    except Exception as e:
        print(f"   ⚠️ Batch failed: {str(e)[:50]}")

print(f"\n✅ Updated {updated} orders to Shopify salesperson")

# Verify
shopify_orders = execute('sale.order', 'search_count', [[['user_id', '=', shopify_id]]])
print(f"📊 Orders with Shopify as salesperson: {shopify_orders}")