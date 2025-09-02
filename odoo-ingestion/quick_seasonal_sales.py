#!/usr/bin/env python3
"""Quick generation of 12 months seasonal sales"""

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

print("📅 GENERATING 12 MONTHS OF SEASONAL SALES")
print("="*60)

# Get products and customers
products = execute('product.product', 'search', [[]], {'limit': 50})
customers = execute('res.partner', 'search', [[['customer_rank', '>', 0]]], {'limit': 50})

print(f"✅ Products: {len(products)}, Customers: {len(customers)}")

# Seasonal factors for athletic wear
seasonal = {
    1: 1.8, 2: 1.5, 3: 1.4, 4: 1.6, 5: 1.5, 6: 1.0,
    7: 0.8, 8: 0.7, 9: 1.2, 10: 1.3, 11: 1.4, 12: 1.6
}

total_orders = 0
total_revenue = 0

# Generate sales for each month
for month in range(1, 13):
    num_orders = int(30 * seasonal[month])  # Base 30 orders/month
    month_revenue = 0
    
    print(f"\nMonth {month:2d}/2024: Creating {num_orders} orders...")
    
    for i in range(num_orders):
        try:
            # Random date in month
            day = random.randint(1, 28)
            order_date = datetime(2024, month, day)
            
            # Create order with 2-5 items
            num_items = random.randint(2, 5)
            selected = random.sample(products, min(num_items, len(products)))
            
            order_lines = []
            for pid in selected:
                qty = random.randint(1, 3)
                order_lines.append((0, 0, {
                    'product_id': pid,
                    'product_uom_qty': qty
                }))
            
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
            
            total_orders += 1
            
            # Quick progress update
            if total_orders % 50 == 0:
                print(f"   Progress: {total_orders} orders created...")
                
        except:
            pass

print(f"\n{'='*60}")
print(f"✅ Created {total_orders} orders across 12 months")

# Verify distribution
print("\n📊 Verifying monthly distribution:")
for month in range(1, 13):
    start = datetime(2024, month, 1).strftime('%Y-%m-%d')
    end = datetime(2024, month, 28).strftime('%Y-%m-%d')
    
    count = execute('sale.order', 'search_count', 
                   [[['date_order', '>=', start],
                     ['date_order', '<=', end]]])
    
    if count > 0:
        print(f"   Month {month:2d}: {count} orders")

# Check total revenue
confirmed = execute('sale.order', 'search_read',
                   [[['state', 'in', ['sale', 'done']]]], 
                   {'fields': ['amount_total'], 'limit': 3000})

if confirmed:
    total = sum(o['amount_total'] for o in confirmed)
    print(f"\n💰 Total Revenue: €{total:,.0f}")
    print(f"   Monthly Average: €{total/12:,.0f}")

print("\n🎉 Seasonal sales generation complete!")