#!/usr/bin/env python3
"""Generate high revenue orders with seasonal patterns - Works with consumable products"""

import xmlrpc.client
import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Connect
url = os.getenv('odoo_url', 'https://source-gym-plus-coffee.odoo.com')
db = os.getenv('db', 'source-gym-plus-coffee')
username = os.getenv('username', 'admin@quickfindai.com')
password = os.getenv('password', 'BJ62wX2J4yzjS$i')

print("💰 HIGH REVENUE ORDER GENERATOR - GYM+COFFEE")
print("="*60)
print("Target: €250k-400k monthly revenue")
print("="*60)

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
uid = common.authenticate(db, username, password, {})
print(f"✅ Connected to Odoo\n")

def execute(model, method, *args):
    return models.execute_kw(db, uid, password, model, method, *args)

# Get or create Shopify user
print("👤 Setting up Shopify salesperson...")
shopify_users = execute('res.users', 'search', [[['name', '=', 'Shopify']]])

if not shopify_users:
    try:
        # Create a partner first
        shopify_partner_id = execute('res.partner', 'create', [{
            'name': 'Shopify Integration',
            'email': 'shopify@gympluscoffee.com',
            'is_company': False
        }])
        
        # Create user
        shopify_user_id = execute('res.users', 'create', [{
            'name': 'Shopify',
            'login': 'shopify',
            'partner_id': shopify_partner_id
        }])
        print(f"   ✅ Created Shopify user (ID: {shopify_user_id})")
    except:
        shopify_user_id = uid
        print(f"   ⚠️ Using admin as salesperson")
else:
    shopify_user_id = shopify_users[0]
    print(f"   Found Shopify user (ID: {shopify_user_id})")

# Load products and customers
print("\n📦 Loading data...")
products = execute('product.product', 'search_read', 
                  [[]], 
                  {'fields': ['name', 'list_price'], 'limit': 500})

customers = execute('res.partner', 'search', 
                   [[['customer_rank', '>', 0]]])

print(f"   Products: {len(products)}")
print(f"   Customers: {len(customers)}")

# Categorize products for seasonality
winter_products = []
summer_products = []
all_season_products = []

for p in products:
    name = p['name'].lower()
    if any(x in name for x in ['hoodie', 'jacket', 'sweatshirt', 'beanie', 'winter']):
        winter_products.append(p)
    elif any(x in name for x in ['shorts', 'tank', 'summer', 'tank top']):
        summer_products.append(p)
    else:
        all_season_products.append(p)

print(f"   Winter products: {len(winter_products)}")
print(f"   Summer products: {len(summer_products)}")
print(f"   All-season products: {len(all_season_products)}")

def get_seasonal_products(month):
    """Get products based on season"""
    if month in [11, 12, 1, 2]:  # Winter
        pool = winter_products * 3 + all_season_products
    elif month in [5, 6, 7, 8]:  # Summer
        pool = summer_products * 3 + all_season_products
    else:  # Spring/Fall
        pool = all_season_products + winter_products + summer_products
    
    return pool if pool else products

def create_order(date, customer_id, order_type='medium'):
    """Create a single order"""
    month = date.month
    seasonal_products = get_seasonal_products(month)
    
    # Determine order size based on type
    if order_type == 'small':
        num_items = random.randint(1, 2)
        target_value = random.uniform(60, 100)
    elif order_type == 'medium':
        num_items = random.randint(2, 4)
        target_value = random.uniform(120, 200)
    elif order_type == 'large':
        num_items = random.randint(3, 6)
        target_value = random.uniform(200, 350)
    else:  # premium
        num_items = random.randint(4, 8)
        target_value = random.uniform(350, 500)
    
    # Select products
    order_lines = []
    order_total = 0
    
    selected = random.sample(seasonal_products, 
                           min(num_items, len(seasonal_products)))
    
    for product in selected:
        quantity = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]
        price = product['list_price'] or 75.0
        
        order_lines.append((0, 0, {
            'product_id': product['id'],
            'product_uom_qty': quantity,
            'price_unit': price
        }))
        order_total += price * quantity
    
    # Create order
    order_data = {
        'partner_id': customer_id,
        'date_order': date.strftime('%Y-%m-%d %H:%M:%S'),
        'user_id': shopify_user_id,
        'order_line': order_lines
    }
    
    try:
        order_id = execute('sale.order', 'create', [order_data])
        
        # Confirm 85% of orders
        if random.random() < 0.85:
            try:
                execute('sale.order', 'action_confirm', [[order_id]])
            except:
                pass
        
        return order_total, True
    except Exception as e:
        return 0, False

# Generate orders for last 30 days
print("\n💰 Generating high-revenue orders...")
print("   Distribution: 15% small, 60% medium, 20% large, 5% premium")

total_revenue = 0
orders_created = 0
orders_failed = 0

# Daily target: €10,000 (for €300k/month)
daily_target = 10000

for days_ago in range(30, 0, -1):
    date = datetime.now() - timedelta(days=days_ago)
    daily_revenue = 0
    daily_orders = 0
    
    # Vary daily target by day of week (higher on weekdays)
    if date.weekday() < 5:  # Monday-Friday
        day_target = daily_target * random.uniform(1.0, 1.2)
    else:  # Weekend
        day_target = daily_target * random.uniform(0.7, 0.9)
    
    while daily_revenue < day_target and daily_orders < 100:  # Max 100 orders per day
        # Order type distribution
        rand = random.random()
        if rand < 0.15:
            order_type = 'small'
        elif rand < 0.75:
            order_type = 'medium'
        elif rand < 0.95:
            order_type = 'large'
        else:
            order_type = 'premium'
        
        customer_id = random.choice(customers)
        revenue, success = create_order(date, customer_id, order_type)
        
        if success:
            daily_revenue += revenue
            daily_orders += 1
            orders_created += 1
            total_revenue += revenue
        else:
            orders_failed += 1
    
    print(f"   Day -{days_ago:2d}: {daily_orders:3d} orders, €{daily_revenue:8,.0f}")

# Summary
print("\n" + "="*60)
print("📊 REVENUE GENERATION COMPLETE")
print("="*60)
print(f"✅ Orders created: {orders_created}")
print(f"❌ Orders failed: {orders_failed}")
print(f"💰 Total revenue: €{total_revenue:,.2f}")
print(f"📈 Daily average: €{total_revenue/30:,.2f}")
print(f"🛒 Average order value: €{total_revenue/orders_created:.2f}" if orders_created > 0 else "")
print(f"📅 Monthly projection: €{total_revenue:,.2f}")

# Update any existing orders to use Shopify salesperson
print("\n🔄 Updating existing orders to Shopify salesperson...")
try:
    admin_orders = execute('sale.order', 'search', 
                          [[['user_id', '=', uid]]], {'limit': 100})
    
    if admin_orders:
        execute('sale.order', 'write', 
               [admin_orders, {'user_id': shopify_user_id}])
        print(f"   ✅ Updated {len(admin_orders)} orders")
except:
    print("   ⚠️ Could not update existing orders")

print("\n🎉 Check your Odoo dashboard for the new revenue!")