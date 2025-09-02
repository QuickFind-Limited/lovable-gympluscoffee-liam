#!/usr/bin/env python3
"""Quick revenue generator - Creates high-value orders efficiently"""

import xmlrpc.client
import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Connect to Odoo
url = os.getenv('odoo_url', 'https://source-gym-plus-coffee.odoo.com')
db = os.getenv('db', 'source-gym-plus-coffee')
username = os.getenv('username', 'admin@quickfindai.com')
password = os.getenv('password', 'BJ62wX2J4yzjS$i')

print("🔗 Connecting to Odoo...")
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
uid = common.authenticate(db, username, password, {})
print(f"✅ Connected\n")

def execute(model, method, *args):
    return models.execute_kw(db, uid, password, model, method, *args)

# Get products and customers
print("📦 Loading data...")
products = execute('product.product', 'search', [[]], {'limit': 100})
customers = execute('res.partner', 'search', [[['customer_rank', '>', 0]]])
print(f"   Products: {len(products)}, Customers: {len(customers)}")

# Create or get Shopify user
print("\n👤 Setting up Shopify user...")
shopify_users = execute('res.users', 'search', [[['name', '=', 'Shopify']]])
if shopify_users:
    shopify_id = shopify_users[0]
else:
    shopify_id = uid  # Use current user
print(f"   Shopify user ID: {shopify_id}")

# Generate high-value orders
print("\n💰 Generating high-revenue orders...")
print("   Target: €300k/month = €10k/day average")

total_revenue = 0
orders_created = 0

# Generate orders for last 30 days
for days_ago in range(30, 0, -1):
    order_date = datetime.now() - timedelta(days=days_ago)
    
    # Daily target: €10k (varying by day)
    daily_target = random.uniform(8000, 12000)
    daily_revenue = 0
    daily_orders = 0
    
    # Create orders until daily target reached
    while daily_revenue < daily_target:
        # Order size distribution for high AOV
        rand = random.random()
        if rand < 0.10:  # 10% small
            num_items = random.randint(1, 2)
            target_value = random.uniform(60, 100)
        elif rand < 0.50:  # 40% medium  
            num_items = random.randint(2, 4)
            target_value = random.uniform(150, 250)
        elif rand < 0.85:  # 35% large
            num_items = random.randint(3, 6)
            target_value = random.uniform(250, 400)
        else:  # 15% premium
            num_items = random.randint(5, 10)
            target_value = random.uniform(400, 600)
        
        # Build order
        order_lines = []
        order_value = 0
        
        for _ in range(num_items):
            product_id = random.choice(products)
            quantity = random.randint(1, 3)
            
            # Get product price
            product_data = execute('product.product', 'read', 
                                  [product_id], ['list_price'])[0]
            price = product_data['list_price']
            
            order_lines.append((0, 0, {
                'product_id': product_id,
                'product_uom_qty': quantity,
                'price_unit': price
            }))
            order_value += price * quantity
        
        # Create order
        try:
            order_data = {
                'partner_id': random.choice(customers),
                'date_order': order_date.strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': shopify_id,
                'order_line': order_lines
            }
            
            order_id = execute('sale.order', 'create', [order_data])
            
            # Confirm most orders
            if random.random() < 0.85:
                try:
                    execute('sale.order', 'action_confirm', [[order_id]])
                except:
                    pass
            
            daily_revenue += order_value
            daily_orders += 1
            orders_created += 1
            total_revenue += order_value
            
        except Exception as e:
            print(f"      ❌ Order failed: {str(e)[:30]}")
    
    print(f"   Day -{days_ago}: {daily_orders} orders, €{daily_revenue:,.0f}")

# Summary
print("\n" + "="*60)
print("📊 REVENUE GENERATION COMPLETE")
print("="*60)
print(f"✅ Orders created: {orders_created}")
print(f"💰 Total revenue: €{total_revenue:,.2f}")
print(f"📈 Daily average: €{total_revenue/30:,.2f}")
print(f"🛒 Average order value: €{total_revenue/orders_created:.2f}" if orders_created > 0 else "N/A")

# Update existing orders' salesperson
print("\n🔄 Updating existing orders to Shopify...")
try:
    existing_orders = execute('sale.order', 'search', 
                             [[['user_id', '!=', shopify_id]]], {'limit': 100})
    
    if existing_orders:
        execute('sale.order', 'write', 
               [existing_orders, {'user_id': shopify_id}])
        print(f"   ✅ Updated {len(existing_orders)} orders to Shopify salesperson")
except:
    print("   ⚠️ Could not update existing orders")

print("\n🎉 Done! Check your Odoo for the new high-revenue orders.")