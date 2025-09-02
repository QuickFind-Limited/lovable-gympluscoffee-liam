#!/usr/bin/env python3
"""Boost revenue with high-value orders"""

import xmlrpc.client
import os
import random
from datetime import datetime, timedelta
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

print("💰 REVENUE BOOSTER")
print("="*50)

# Get data
products = execute('product.product', 'search', [[]], {'limit': 50})
customers = execute('res.partner', 'search', [[['customer_rank', '>', 0]]], {'limit': 30})

print(f"✅ Products: {len(products)}, Customers: {len(customers)}")

# Generate 50 high-value orders
print("\n📈 Creating high-value orders...")
total = 0
count = 0

for i in range(50):
    try:
        # Create large orders (4-8 items)
        num_items = random.randint(4, 8)
        order_lines = []
        
        selected = random.sample(products, min(num_items, len(products)))
        for pid in selected:
            qty = random.randint(2, 5)
            order_lines.append((0, 0, {
                'product_id': pid,
                'product_uom_qty': qty
            }))
        
        # Random date in last 30 days
        days_ago = random.randint(0, 30)
        order_date = datetime.now() - timedelta(days=days_ago)
        
        # Create order
        order_id = execute('sale.order', 'create', [{
            'partner_id': random.choice(customers),
            'date_order': order_date.strftime('%Y-%m-%d'),
            'order_line': order_lines
        }])
        
        # Confirm it
        try:
            execute('sale.order', 'action_confirm', [[order_id]])
        except:
            pass
        
        # Get total
        order_data = execute('sale.order', 'search_read', 
                           [[['id', '=', order_id]]], 
                           {'fields': ['amount_total']})[0]
        
        total += order_data['amount_total']
        count += 1
        
        if count % 10 == 0:
            print(f"   Created {count} orders, Revenue: €{total:,.0f}")
            
    except:
        pass

print(f"\n{'='*50}")
print(f"✅ New orders: {count}")
print(f"💰 New revenue: €{total:,.2f}")
print(f"📊 Average: €{total/count:.2f}" if count > 0 else "")

# Check total revenue
confirmed = execute('sale.order', 'search_read',
                   [[['state', 'in', ['sale', 'done']]]], 
                   {'fields': ['amount_total'], 'limit': 2000})

total_revenue = sum(o['amount_total'] for o in confirmed)
print(f"\n📈 TOTAL REVENUE NOW: €{total_revenue:,.2f}")
print(f"   From {len(confirmed)} confirmed orders")

print("\n🎉 Revenue boosted!")