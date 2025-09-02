#!/usr/bin/env python3
"""Create orders specifically in 2024 with seasonal distribution"""

import xmlrpc.client
import os
import random
from datetime import datetime
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

print("📅 CREATING 2024 SEASONAL ORDERS")
print("="*60)

# Get products and customers
products = execute('product.product', 'search', [[]], {'limit': 30})
customers = execute('res.partner', 'search', [[['customer_rank', '>', 0]]], {'limit': 30})

print(f"Using {len(products)} products, {len(customers)} customers")

# Seasonal factors for Gym+Coffee (athletic wear)
seasonal = {
    1: 1.8,   # January - New Year fitness
    2: 1.5,   # February 
    3: 1.4,   # March - Spring
    4: 1.6,   # April - Spring peak
    5: 1.5,   # May - Pre-summer
    6: 1.0,   # June
    7: 0.8,   # July - Summer low
    8: 0.7,   # August - Summer low
    9: 1.2,   # September - Back to fitness
    10: 1.3,  # October
    11: 1.4,  # November - Winter prep
    12: 1.6   # December - Gifts
}

total_created = 0
total_revenue = 0

print("\n📊 Creating orders for each month of 2024:")

for month in range(1, 13):
    # Number of orders based on seasonality
    base_orders = 8  # Reduced for speed
    num_orders = int(base_orders * seasonal[month])
    month_revenue = 0
    month_created = 0
    
    for i in range(num_orders):
        try:
            # Random day in month
            day = random.randint(1, 28 if month != 12 else 15)  # Earlier in December
            
            # Create order date in 2024
            order_date = datetime(2024, month, day, 
                                 random.randint(9, 18), 
                                 random.randint(0, 59))
            
            # Vary order size
            if random.random() < 0.2:  # 20% large orders
                num_items = random.randint(4, 7)
            elif random.random() < 0.5:  # 30% medium
                num_items = random.randint(2, 3)
            else:  # 50% small
                num_items = 1
            
            # Create order lines
            order_lines = []
            selected_products = random.sample(products, min(num_items, len(products)))
            
            for product_id in selected_products:
                qty = random.randint(1, 3)
                order_lines.append((0, 0, {
                    'product_id': product_id,
                    'product_uom_qty': qty
                }))
            
            # Create the order
            order_vals = {
                'partner_id': random.choice(customers),
                'date_order': order_date.strftime('%Y-%m-%d %H:%M:%S'),
                'order_line': order_lines
            }
            
            order_id = execute('sale.order', 'create', [order_vals])
            
            # Confirm the order
            try:
                execute('sale.order', 'action_confirm', [[order_id]])
            except:
                pass
            
            # Track progress
            month_created += 1
            total_created += 1
            
        except Exception as e:
            pass
    
    print(f"   Month {month:2d}/2024: Created {month_created} orders")

print(f"\n✅ Total orders created: {total_created}")

# Verify the date distribution
print("\n📊 Verifying 2024 distribution:")
for m in range(1, 13):
    start = f"2024-{m:02d}-01"
    end = f"2024-{m:02d}-28"
    
    count = execute('sale.order', 'search_count', 
                   [[['date_order', '>=', start], 
                     ['date_order', '<=', end]]])
    
    if count > 0:
        # Get revenue for this month
        month_orders = execute('sale.order', 'search_read',
                              [[['date_order', '>=', start],
                                ['date_order', '<=', end],
                                ['state', 'in', ['sale', 'done']]]],
                              {'fields': ['amount_total'], 'limit': 200})
        
        if month_orders:
            month_rev = sum(o['amount_total'] for o in month_orders)
            print(f"   Month {m:2d}: {count:3d} orders, €{month_rev:10,.0f}")
        else:
            print(f"   Month {m:2d}: {count:3d} orders (draft)")

# Final check
print("\n📈 FINAL REVENUE CHECK:")
all_2024 = execute('sale.order', 'search_read',
                  [[['date_order', '>=', '2024-01-01'],
                    ['date_order', '<=', '2024-12-31'],
                    ['state', 'in', ['sale', 'done']]]],
                  {'fields': ['amount_total'], 'limit': 2000})

if all_2024:
    total_2024 = sum(o['amount_total'] for o in all_2024)
    print(f"   2024 Total Revenue: €{total_2024:,.0f}")
    print(f"   2024 Monthly Average: €{total_2024/12:,.0f}")
    print(f"   Number of 2024 Orders: {len(all_2024)}")

print("\n✅ 2024 seasonal sales created successfully!")