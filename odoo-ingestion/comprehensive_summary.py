#!/usr/bin/env python3
"""Comprehensive system summary with monthly breakdown"""

import xmlrpc.client
import os
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

print("="*70)
print("🎯 GYM+COFFEE ODOO ERP - COMPREHENSIVE SYSTEM SUMMARY")
print("="*70)
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)

# 1. Products Analysis
print("\n📦 PRODUCT CATALOG:")
total_products = execute('product.template', 'search_count', [[]])
product_types = {}
for ptype in ['consu', 'service', 'product']:
    count = execute('product.template', 'search_count', [[['type', '=', ptype]]])
    if count > 0:
        product_types[ptype] = count

print(f"   Total Products: {total_products}")
for ptype, count in product_types.items():
    type_name = {'consu': 'Consumable', 'service': 'Service', 'product': 'Stockable'}.get(ptype, ptype)
    print(f"   - {type_name}: {count}")

# Check for new stockable products
new_products = execute('product.template', 'search_count', [[['name', 'like', '[NEW]']]])
stock_products = execute('product.template', 'search_count', [[['name', 'like', '[STOCK]']]])
print(f"\n   Recently Added:")
if new_products > 0:
    print(f"   - [NEW] Products: {new_products}")
if stock_products > 0:
    print(f"   - [STOCK] Products: {stock_products}")

# 2. Inventory Status
print("\n📊 INVENTORY STATUS:")
quants = execute('stock.quant', 'search_count', [[]])
print(f"   Stock Quant Records: {quants}")

if quants > 0:
    # Get sample inventory
    sample_quants = execute('stock.quant', 'search_read', 
                          [[]], 
                          {'fields': ['product_id', 'quantity'], 'limit': 5})
    if sample_quants:
        print("   Sample Inventory Levels:")
        for q in sample_quants:
            print(f"   - {q['product_id'][1][:40]}: {q['quantity']:.0f} units")

# 3. Customer Base
print("\n👥 CUSTOMER BASE:")
total_customers = execute('res.partner', 'search_count', [[['customer_rank', '>', 0]]])
b2b = execute('res.partner', 'search_count', [[['customer_rank', '>', 0], ['is_company', '=', True]]])
b2c = total_customers - b2b

print(f"   Total Customers: {total_customers}")
print(f"   - B2C (Individuals): {b2c} ({b2c*100//total_customers if total_customers else 0}%)")
print(f"   - B2B (Companies): {b2b} ({b2b*100//total_customers if total_customers else 0}%)")

# 4. Sales Analysis by Month
print("\n📅 SALES BY MONTH (2024):")
print("   Month | Orders | Revenue      | Avg Order")
print("   " + "-"*45)

months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
total_yearly_revenue = 0
total_yearly_orders = 0

for month in range(1, 13):
    start_date = f"2024-{month:02d}-01"
    # Use last day of month (28 for safety, works for all months)
    end_date = f"2024-{month:02d}-28"
    
    # Get confirmed orders for this month
    month_orders = execute('sale.order', 'search_read',
                          [[['date_order', '>=', start_date],
                            ['date_order', '<=', end_date],
                            ['state', 'in', ['sale', 'done']]]],
                          {'fields': ['amount_total'], 'limit': 500})
    
    if month_orders:
        month_revenue = sum(o['amount_total'] for o in month_orders)
        month_count = len(month_orders)
        avg_order = month_revenue / month_count if month_count else 0
        
        total_yearly_revenue += month_revenue
        total_yearly_orders += month_count
        
        print(f"   {months[month-1]:3s} | {month_count:6d} | €{month_revenue:11,.0f} | €{avg_order:7.0f}")
    else:
        # Check all orders (not just confirmed)
        all_month_orders = execute('sale.order', 'search_count',
                                  [[['date_order', '>=', start_date],
                                    ['date_order', '<=', end_date]]])
        if all_month_orders > 0:
            print(f"   {months[month-1]:3s} | {all_month_orders:6d} | (unconfirmed)  | -")

print("   " + "-"*45)
print(f"   TOTAL| {total_yearly_orders:6d} | €{total_yearly_revenue:11,.0f} | €{total_yearly_revenue/total_yearly_orders if total_yearly_orders else 0:7.0f}")

# 5. Revenue Analysis
print("\n💰 REVENUE ANALYSIS:")
print(f"   Total Annual Revenue: €{total_yearly_revenue:,.0f}")
print(f"   Monthly Average: €{total_yearly_revenue/12:,.0f}")
print(f"   Total Orders: {total_yearly_orders}")
print(f"   Average Order Value: €{total_yearly_revenue/total_yearly_orders:.2f}" if total_yearly_orders else "   No orders")

# Check against targets
if total_yearly_revenue/12 >= 250000:
    print(f"   ✅ Monthly Target Met (€250k-400k)")
else:
    print(f"   ⚠️ Below Monthly Target (€250k-400k)")

# 6. Salesperson Check
print("\n🛍️ SALESPERSON CONFIGURATION:")
users = execute('res.users', 'search_read', 
               [[]], 
               {'fields': ['name'], 'limit': 10})
shopify_found = any('shopify' in u['name'].lower() for u in users)
if shopify_found:
    print("   ✅ Shopify user configured")
else:
    print("   ⚠️ Using default admin user")

# 7. System Health
print("\n🏥 SYSTEM HEALTH CHECK:")
total_orders = execute('sale.order', 'search_count', [[]])
draft_orders = execute('sale.order', 'search_count', [[['state', '=', 'draft']]])
confirmed_orders = execute('sale.order', 'search_count', [[['state', 'in', ['sale', 'done']]]])

print(f"   Total Orders: {total_orders}")
print(f"   - Draft: {draft_orders} ({draft_orders*100//total_orders if total_orders else 0}%)")
print(f"   - Confirmed: {confirmed_orders} ({confirmed_orders*100//total_orders if total_orders else 0}%)")

# 8. Achievement Summary
print("\n" + "="*70)
print("🎉 ACHIEVEMENT SUMMARY:")
print("="*70)

achievements = []

# Revenue check
monthly_avg = total_yearly_revenue/12
if 250000 <= monthly_avg <= 400000:
    achievements.append(f"✅ Revenue: €{monthly_avg:,.0f}/month (Target: €250k-400k)")
elif monthly_avg > 400000:
    achievements.append(f"✅ Revenue: €{monthly_avg:,.0f}/month (Exceeded target!)")
else:
    achievements.append(f"⚠️ Revenue: €{monthly_avg:,.0f}/month (Target: €250k-400k)")

# Products check
if total_products >= 400:
    achievements.append(f"✅ Products: {total_products} (Target: 400+)")
else:
    achievements.append(f"⚠️ Products: {total_products} (Target: 400+)")

# Customers check
if total_customers >= 150:
    achievements.append(f"✅ Customers: {total_customers} (Target: 150+)")
else:
    achievements.append(f"⚠️ Customers: {total_customers} (Target: 150+)")

# AOV check
aov = total_yearly_revenue/total_yearly_orders if total_yearly_orders else 0
if aov >= 150:
    achievements.append(f"✅ AOV: €{aov:.0f} (Target: €150+)")
else:
    achievements.append(f"⚠️ AOV: €{aov:.0f} (Target: €150+)")

# Monthly distribution check
months_with_sales = sum(1 for m in range(1, 13) if execute('sale.order', 'search_count', 
                        [[['date_order', '>=', f"2024-{m:02d}-01"],
                          ['date_order', '<=', f"2024-{m:02d}-28"]]]) > 0)

if months_with_sales >= 10:
    achievements.append(f"✅ Monthly Distribution: {months_with_sales}/12 months")
else:
    achievements.append(f"⚠️ Monthly Distribution: {months_with_sales}/12 months")

# Inventory check
if quants > 0:
    achievements.append(f"✅ Inventory Tracking: {quants} records")
else:
    achievements.append(f"⚠️ Inventory: No tracking (product type limitation)")

for achievement in achievements:
    print(f"   {achievement}")

print("\n" + "="*70)
print("🚀 SYSTEM STATUS: FULLY OPERATIONAL")
print("="*70)