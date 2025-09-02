#!/usr/bin/env python3
"""Fast revenue generator - Efficient batch processing"""

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

print("⚡ FAST REVENUE GENERATOR")
print("="*50)

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
uid = common.authenticate(db, username, password, {})

def execute(model, method, *args):
    return models.execute_kw(db, uid, password, model, method, *args)

# Quick load
products = execute('product.product', 'search', [[]], {'limit': 100})
customers = execute('res.partner', 'search', [[['customer_rank', '>', 0]]], {'limit': 50})

print(f"✅ Products: {len(products)}, Customers: {len(customers)}")

# Generate 200 quick orders
print("\n💰 Generating orders...")
total = 0
count = 0

for i in range(200):
    try:
        # Random 2-5 products per order
        num_items = random.randint(2, 5)
        order_lines = []
        
        for _ in range(num_items):
            order_lines.append((0, 0, {
                'product_id': random.choice(products),
                'product_uom_qty': random.randint(1, 3)
            }))
        
        # Create order
        order_id = execute('sale.order', 'create', [{
            'partner_id': random.choice(customers),
            'order_line': order_lines
        }])
        
        # Get total
        order_data = execute('sale.order', 'read', [order_id], ['amount_total'])[0]
        total += order_data['amount_total']
        count += 1
        
        if count % 20 == 0:
            print(f"   {count} orders created... Revenue: €{total:,.0f}")
        
        # Confirm order
        if random.random() < 0.8:
            try:
                execute('sale.order', 'action_confirm', [[order_id]])
            except:
                pass
                
    except:
        pass

print(f"\n{'='*50}")
print(f"✅ Orders: {count}")
print(f"💰 Revenue: €{total:,.2f}")
print(f"📊 AOV: €{total/count:.2f}" if count > 0 else "")
print(f"\n🎉 Done!")