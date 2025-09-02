#!/usr/bin/env python3
"""Demo revenue generator - Creates a few high-value orders"""

import xmlrpc.client
import os
from dotenv import load_dotenv

load_dotenv()

# Connect
url = os.getenv('odoo_url', 'https://source-gym-plus-coffee.odoo.com')
db = os.getenv('db', 'source-gym-plus-coffee')
username = os.getenv('username', 'admin@quickfindai.com')
password = os.getenv('password', 'BJ62wX2J4yzjS$i')

print("💰 DEMO REVENUE GENERATOR")
print("="*50)

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
uid = common.authenticate(db, username, password, {})
print("✅ Connected\n")

def execute(model, method, *args):
    return models.execute_kw(db, uid, password, model, method, *args)

# Get first customer and products
customer = execute('res.partner', 'search', [[['customer_rank', '>', 0]]], {'limit': 1})[0]
products = execute('product.product', 'search', [[]], {'limit': 10})

print(f"Creating 5 demo orders...")

for i in range(5):
    try:
        # Create order with 3 products
        order_id = execute('sale.order', 'create', [{
            'partner_id': customer,
            'order_line': [
                (0, 0, {'product_id': products[0], 'product_uom_qty': 2}),
                (0, 0, {'product_id': products[1], 'product_uom_qty': 3}),
                (0, 0, {'product_id': products[2], 'product_uom_qty': 1})
            ]
        }])
        
        # Confirm it
        execute('sale.order', 'action_confirm', [[order_id]])
        
        # Get total
        order = execute('sale.order', 'read', [order_id], ['name', 'amount_total'])[0]
        print(f"   ✅ Order {order['name']}: €{order['amount_total']:.2f}")
        
    except Exception as e:
        print(f"   ❌ Failed: {str(e)[:50]}")

print("\n🎉 Demo complete! Check Odoo for the orders.")