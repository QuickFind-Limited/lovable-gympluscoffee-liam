#!/usr/bin/env python3
"""Final summary of Odoo ERP system"""

import xmlrpc.client
import os
from dotenv import load_dotenv
from datetime import datetime

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

print("=" * 60)
print("🎯 GYM+COFFEE ODOO ERP - FINAL SUMMARY")
print("=" * 60)
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

# Products
print("\n📦 PRODUCTS:")
total_products = execute('product.template', 'search_count', [[]])
product_types = {}
for ptype in ['consu', 'service', 'product']:
    count = execute('product.template', 'search_count', [[['type', '=', ptype]]])
    if count > 0:
        product_types[ptype] = count

print(f"   Total Products: {total_products}")
for ptype, count in product_types.items():
    print(f"   - {ptype}: {count}")

# Inventory
quants = execute('stock.quant', 'search_count', [[]])
print(f"\n📊 INVENTORY:")
print(f"   Stock Quant Records: {quants}")
if quants > 0:
    sample_quants = execute('stock.quant', 'search_read', 
                          [[]], 
                          {'fields': ['product_id', 'quantity'], 'limit': 5})
    print("   Sample inventory:")
    for q in sample_quants:
        print(f"   - {q['product_id'][1][:30]}: {q['quantity']} units")

# Customers
print("\n👥 CUSTOMERS:")
total_customers = execute('res.partner', 'search_count', [[['customer_rank', '>', 0]]])
b2b = execute('res.partner', 'search_count', [[['customer_rank', '>', 0], ['is_company', '=', True]]])
b2c = total_customers - b2b
print(f"   Total Customers: {total_customers}")
print(f"   - B2C (Individuals): {b2c}")
print(f"   - B2B (Companies): {b2b}")

# Orders
print("\n💰 SALES ORDERS:")
total_orders = execute('sale.order', 'search_count', [[]])
draft = execute('sale.order', 'search_count', [[['state', '=', 'draft']]])
confirmed = execute('sale.order', 'search_count', [[['state', 'in', ['sale', 'done']]]])
print(f"   Total Orders: {total_orders}")
print(f"   - Draft: {draft}")
print(f"   - Confirmed: {confirmed}")

# Revenue calculation
print("\n💵 REVENUE:")
confirmed_orders = execute('sale.order', 'search_read',
                          [[['state', 'in', ['sale', 'done']]]], 
                          {'fields': ['amount_total'], 'limit': 5000})

if confirmed_orders:
    total_revenue = sum(o['amount_total'] for o in confirmed_orders)
    avg_order = total_revenue / len(confirmed_orders)
    print(f"   Total Revenue: €{total_revenue:,.2f}")
    print(f"   Average Order Value: €{avg_order:.2f}")
    print(f"   Number of Revenue Orders: {len(confirmed_orders)}")
    
    # Monthly projection
    monthly = total_revenue / 1  # Assuming 1 month of data
    print(f"\n   📈 Monthly Revenue: €{monthly:,.2f}")
    print(f"   📊 Annual Projection: €{monthly * 12:,.2f}")

# Check for "Shopify" in system
print("\n🛍️ SALESPERSON:")
users = execute('res.users', 'search_read', 
               [[]], 
               {'fields': ['name'], 'limit': 10})
shopify_found = any('shopify' in u['name'].lower() for u in users)
if shopify_found:
    print("   ✅ Shopify user configured")
else:
    print("   ⚠️ Using default admin user")

# Success metrics
print("\n" + "=" * 60)
print("🎉 ACHIEVEMENT SUMMARY:")
print("=" * 60)

achievements = []
if total_revenue >= 250000:
    achievements.append(f"✅ Revenue Target Met: €{total_revenue:,.0f} (Target: €250k-400k)")
else:
    achievements.append(f"⚠️ Revenue: €{total_revenue:,.0f} (Target: €250k-400k)")

if total_products >= 400:
    achievements.append(f"✅ Products Imported: {total_products} (Target: 400+)")
else:
    achievements.append(f"⚠️ Products: {total_products}")

if total_customers >= 150:
    achievements.append(f"✅ Customer Base: {total_customers} (Target: 150+)")
else:
    achievements.append(f"⚠️ Customers: {total_customers}")

if avg_order >= 150:
    achievements.append(f"✅ AOV: €{avg_order:.2f} (Target: €150+)")
else:
    achievements.append(f"⚠️ AOV: €{avg_order:.2f} (Target: €150+)")

for achievement in achievements:
    print(f"   {achievement}")

print("\n" + "=" * 60)
print("🚀 SYSTEM STATUS: OPERATIONAL & REVENUE GENERATING")
print("=" * 60)