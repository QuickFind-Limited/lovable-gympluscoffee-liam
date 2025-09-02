#!/usr/bin/env python3
"""Create high revenue orders - Simple and efficient"""

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

print("🚀 HIGH REVENUE GENERATOR FOR GYM+COFFEE")
print("="*50)

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
uid = common.authenticate(db, username, password, {})

def execute(model, method, *args):
    return models.execute_kw(db, uid, password, model, method, *args)

# Get data
products = execute('product.product', 'search_read', 
                  [[]], {'fields': ['list_price'], 'limit': 200})
customers = execute('res.partner', 'search', [[['customer_rank', '>', 0]]])

print(f"✅ Found {len(products)} products and {len(customers)} customers\n")

# Generate orders
print("💰 Creating high-value orders...")
total = 0
count = 0

# Create 500 orders quickly
for i in range(500):
    # High value orders
    num_items = random.choices([2, 3, 4, 5, 6], 
                               weights=[0.2, 0.3, 0.3, 0.15, 0.05])[0]
    
    order_lines = []
    order_total = 0
    
    # Add products
    selected = random.sample(products, min(num_items, len(products)))
    for p in selected:
        qty = random.randint(1, 3)
        price = p['list_price'] or 75  # Default €75
        order_lines.append((0, 0, {
            'product_id': p['id'],
            'product_uom_qty': qty,
            'price_unit': price
        }))
        order_total += price * qty
    
    # Create order
    try:
        days_ago = random.randint(0, 30)
        order_date = datetime.now() - timedelta(days=days_ago)
        
        order_id = execute('sale.order', 'create', [{
            'partner_id': random.choice(customers),
            'date_order': order_date.strftime('%Y-%m-%d'),
            'order_line': order_lines
        }])
        
        # Confirm 80% of orders
        if random.random() < 0.8:
            try:
                execute('sale.order', 'action_confirm', [[order_id]])
            except:
                pass
        
        total += order_total
        count += 1
        
        if count % 50 == 0:
            print(f"   Created {count} orders... Revenue: €{total:,.0f}")
            
    except Exception as e:
        pass

# Summary
print(f"\n{'='*50}")
print(f"✅ COMPLETE!")
print(f"   Orders: {count}")
print(f"   Revenue: €{total:,.2f}")
print(f"   AOV: €{total/count:.2f}" if count > 0 else "N/A")
print(f"   Monthly projection: €{total:,.2f}")

print("\n🎉 Check Odoo for your new high-revenue orders!")