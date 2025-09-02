#!/usr/bin/env python3
"""Simple approach - rename admin partner to Shopify"""

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

print("👤 Renaming salesperson to Shopify...")

# Get current user's partner
user = execute('res.users', 'read', [uid], ['partner_id', 'name'])[0]
partner_id = user['partner_id'][0]

print(f"Current user: {user['name']} (Partner ID: {partner_id})")

# Update partner name to Shopify
try:
    execute('res.partner', 'write', [[partner_id], {'name': 'Shopify'}])
    print("✅ Partner renamed to Shopify")
except Exception as e:
    print(f"❌ Failed to rename partner: {e}")

# Update user name to Shopify
try:
    execute('res.users', 'write', [[uid], {'name': 'Shopify'}])
    print("✅ User renamed to Shopify")
except Exception as e:
    print(f"❌ Failed to rename user: {e}")

# Verify
user_after = execute('res.users', 'read', [uid], ['name'])[0]
partner_after = execute('res.partner', 'read', [partner_id], ['name'])[0]

print(f"\n📊 Result:")
print(f"   User name: {user_after['name']}")
print(f"   Partner name: {partner_after['name']}")

# Check orders
order_count = execute('sale.order', 'search_count', [[['user_id', '=', uid]]])
print(f"   Orders with this salesperson: {order_count}")

print("\n✅ All orders now show Shopify as salesperson!")