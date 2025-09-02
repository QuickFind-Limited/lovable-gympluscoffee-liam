#!/usr/bin/env python3
"""Check real revenue from all confirmed orders"""

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

print("💰 CHECKING REAL REVENUE")
print("="*60)

# Get ALL confirmed orders
confirmed_orders = execute('sale.order', 'search_read',
                          [[['state', 'in', ['sale', 'done']]]],
                          {'fields': ['amount_total', 'date_order'], 'limit': 5000})

print(f"✅ Found {len(confirmed_orders)} confirmed orders")

if confirmed_orders:
    # Calculate total
    total = sum(o['amount_total'] for o in confirmed_orders)
    print(f"\n💵 TOTAL REVENUE: €{total:,.2f}")
    print(f"📊 Average Order Value: €{total/len(confirmed_orders):.2f}")
    
    # Check date distribution
    dates = [o['date_order'] for o in confirmed_orders if o['date_order']]
    if dates:
        # Parse years
        years = set()
        for date in dates:
            if isinstance(date, str):
                year = date[:4]
                years.add(year)
        
        print(f"\n📅 Orders span years: {sorted(years)}")
        
        # Count by month for 2024
        months_2024 = {}
        for order in confirmed_orders:
            if order['date_order'] and '2024' in str(order['date_order']):
                month = str(order['date_order'])[5:7]
                if month not in months_2024:
                    months_2024[month] = {'count': 0, 'revenue': 0}
                months_2024[month]['count'] += 1
                months_2024[month]['revenue'] += order['amount_total']
        
        if months_2024:
            print("\n📅 2024 Monthly Breakdown:")
            for month in sorted(months_2024.keys()):
                data = months_2024[month]
                print(f"   Month {month}: {data['count']:3d} orders, €{data['revenue']:10,.0f}")
    
    # Monthly average
    print(f"\n📈 If all in one month: €{total:,.0f}/month")
    print(f"📈 If spread over 12 months: €{total/12:,.0f}/month")
    
    # Check against targets
    if total >= 250000:
        print("\n✅ REVENUE TARGET MET!")
    else:
        print(f"\n⚠️ Need €{250000-total:,.0f} more to reach minimum target")

else:
    print("⚠️ No confirmed orders found")

# Check draft orders too
draft_orders = execute('sale.order', 'search_read',
                      [[['state', '=', 'draft']]],
                      {'fields': ['amount_total'], 'limit': 1000})

if draft_orders:
    draft_total = sum(o['amount_total'] for o in draft_orders)
    print(f"\n📝 Draft orders: {len(draft_orders)} worth €{draft_total:,.0f}")
    print(f"   If confirmed: Total would be €{total+draft_total:,.0f}")