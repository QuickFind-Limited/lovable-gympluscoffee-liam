#!/usr/bin/env python3
"""Check current state and create working orders"""

import xmlrpc.client
import os
from dotenv import load_dotenv

load_dotenv()

# Connect
url = os.getenv('odoo_url', 'https://source-gym-plus-coffee.odoo.com')
db = os.getenv('db', 'source-gym-plus-coffee')
username = os.getenv('username', 'admin@quickfindai.com')
password = os.getenv('password', 'BJ62wX2J4yzjS$i')

print("🔍 CHECKING ODOO STATE")
print("="*50)

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
uid = common.authenticate(db, username, password, {})

def execute(model, method, *args):
    return models.execute_kw(db, uid, password, model, method, *args)

# Check counts
print("\n📊 Current Database State:")
products = execute('product.template', 'search_count', [[]])
customers = execute('res.partner', 'search_count', [[['customer_rank', '>', 0]]])
orders = execute('sale.order', 'search_count', [[]])
confirmed = execute('sale.order', 'search_count', [[['state', 'in', ['sale', 'done']]]])

print(f"   Products: {products}")
print(f"   Customers: {customers}")
print(f"   Total Orders: {orders}")
print(f"   Confirmed Orders: {confirmed}")

# Get recent orders with revenue
recent = execute('sale.order', 'search_read', 
                [[['state', 'in', ['sale', 'done']]]], 
                {'fields': ['name', 'amount_total', 'date_order', 'partner_id'],
                 'limit': 10,
                 'order': 'date_order desc'})

if recent:
    print("\n💰 Recent Confirmed Orders:")
    total = 0
    for order in recent:
        partner = order['partner_id'][1] if order['partner_id'] else 'Unknown'
        print(f"   {order['name']}: €{order['amount_total']:.2f} - {partner[:30]}")
        total += order['amount_total']
    print(f"\n   Total of last {len(recent)} orders: €{total:,.2f}")
    print(f"   Average: €{total/len(recent):.2f}")

# Calculate total revenue
all_confirmed = execute('sale.order', 'search_read',
                       [[['state', 'in', ['sale', 'done']]]], 
                       {'fields': ['amount_total'], 'limit': 1000})

if all_confirmed:
    total_revenue = sum(o['amount_total'] for o in all_confirmed)
    print(f"\n💰 Total Revenue (all confirmed): €{total_revenue:,.2f}")
    print(f"   From {len(all_confirmed)} orders")
    print(f"   Average Order Value: €{total_revenue/len(all_confirmed):.2f}")

print("\n✅ Analysis complete!")