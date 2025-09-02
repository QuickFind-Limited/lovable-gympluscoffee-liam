#!/usr/bin/env python3
"""Confirm all 2024 draft orders"""

import xmlrpc.client
import os
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

print("✅ CONFIRMING 2024 DRAFT ORDERS")
print("="*60)

# Get all draft orders from 2024
draft_2024 = execute('sale.order', 'search',
                    [[['date_order', '>=', '2024-01-01'],
                      ['date_order', '<=', '2024-12-31'],
                      ['state', '=', 'draft']]],
                    {'limit': 500})

print(f"Found {len(draft_2024)} draft orders from 2024")

confirmed = 0
for order_id in draft_2024[:200]:  # Confirm up to 200
    try:
        execute('sale.order', 'action_confirm', [[order_id]])
        confirmed += 1
        if confirmed % 20 == 0:
            print(f"   Confirmed {confirmed} orders...")
    except:
        pass

print(f"\n✅ Confirmed {confirmed} orders")

# Check revenue now
confirmed_2024 = execute('sale.order', 'search_read',
                        [[['date_order', '>=', '2024-01-01'],
                          ['date_order', '<=', '2024-12-31'],
                          ['state', 'in', ['sale', 'done']]]],
                        {'fields': ['amount_total'], 'limit': 1000})

if confirmed_2024:
    total = sum(o['amount_total'] for o in confirmed_2024)
    print(f"\n💰 2024 Revenue: €{total:,.0f}")
    print(f"   Orders: {len(confirmed_2024)}")
    print(f"   Monthly Average: €{total/12:,.0f}")

print("\n✅ Done!")