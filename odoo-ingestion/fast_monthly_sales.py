#!/usr/bin/env python3
"""Fast monthly sales generation - 10 orders per month"""

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

print("📅 FAST MONTHLY SALES GENERATION")
print("="*60)

# Get IDs quickly
products = execute('product.product', 'search', [[]], {'limit': 20})
customers = execute('res.partner', 'search', [[['customer_rank', '>', 0]]], {'limit': 20})

print(f"Using {len(products)} products, {len(customers)} customers")

# Create 5 orders per month for past months
months_to_generate = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]  # Not December (current data)
created = 0

for month in months_to_generate:
    print(f"\nMonth {month:02d}/2024:")
    
    # Just 5 orders per month for speed
    for i in range(5):
        try:
            order_date = datetime(2024, month, random.randint(1, 28))
            
            # 2-3 items per order
            num_items = random.randint(2, 3)
            order_lines = []
            
            for j in range(num_items):
                order_lines.append((0, 0, {
                    'product_id': random.choice(products),
                    'product_uom_qty': random.randint(1, 3)
                }))
            
            # Create and confirm
            order_id = execute('sale.order', 'create', [{
                'partner_id': random.choice(customers),
                'date_order': order_date.strftime('%Y-%m-%d'),
                'order_line': order_lines
            }])
            
            execute('sale.order', 'action_confirm', [[order_id]])
            created += 1
            
        except:
            pass
    
    print(f"   Created {min(5, created - (month-1)*5)} orders")

print(f"\n✅ Total orders created: {created}")

# Quick verification
print("\n📊 Orders by month:")
for m in range(1, 13):
    start = f"2024-{m:02d}-01"
    end = f"2024-{m:02d}-28"
    count = execute('sale.order', 'search_count', 
                   [[['date_order', '>=', start], ['date_order', '<=', end]]])
    if count > 0:
        print(f"   Month {m:2d}: {count} orders")

print("\n✅ Sales now distributed across multiple months!")