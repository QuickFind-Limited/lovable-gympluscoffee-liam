#!/usr/bin/env python3
"""
Quick Validation Check for Gym+Coffee Odoo Data
Fast validation to ensure data meets requirements
"""

import xmlrpc.client
import json
from datetime import datetime
from collections import defaultdict

def quick_validate():
    """Run quick validation checks"""
    
    # Odoo connection
    url = 'https://source-gym-plus-coffee.odoo.com/'
    db = 'source-gym-plus-coffee'
    username = 'admin@quickfindai.com'
    password = 'BJ62wX2J4yzjS$i'
    
    print("🔌 Connecting to Odoo...")
    try:
        common = xmlrpc.client.ServerProxy(f'{url}xmlrpc/2/common')
        uid = common.authenticate(db, username, password, {})
        models = xmlrpc.client.ServerProxy(f'{url}xmlrpc/2/object')
        print("✅ Connected successfully!\n")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    results = {}
    
    # 1. Count customers
    print("👥 Checking Customers...")
    customer_count = models.execute_kw(
        db, uid, password,
        'res.partner', 'search_count',
        [[('customer_rank', '>', 0)]], {}
    )
    print(f"   Total customers: {customer_count:,}")
    
    # Get sample of customers to check geography
    customers = models.execute_kw(
        db, uid, password,
        'res.partner', 'search_read',
        [[('customer_rank', '>', 0)]],
        {'fields': ['country_id', 'city'], 'limit': 100}
    )
    
    countries = defaultdict(int)
    for c in customers:
        if c.get('country_id'):
            countries[c['country_id'][1] if isinstance(c['country_id'], list) else 'Unknown'] += 1
    
    print(f"   Geographic sample (100 customers):")
    for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"      {country}: {count}")
    
    results['customers'] = {
        'total': customer_count,
        'geographic_sample': dict(countries)
    }
    
    # 2. Count orders
    print("\n📦 Checking Orders...")
    order_count = models.execute_kw(
        db, uid, password,
        'sale.order', 'search_count',
        [[('state', 'in', ['sale', 'done'])]], {}
    )
    print(f"   Total confirmed orders: {order_count:,}")
    
    # Get sample to check channels
    orders = models.execute_kw(
        db, uid, password,
        'sale.order', 'search_read',
        [[('state', 'in', ['sale', 'done'])]],
        {'fields': ['amount_total', 'team_id', 'date_order'], 'limit': 100}
    )
    
    channels = defaultdict(int)
    total_revenue = 0
    
    for order in orders:
        total_revenue += order.get('amount_total', 0)
        if order.get('team_id'):
            channels[order['team_id'][1] if isinstance(order['team_id'], list) else 'No Channel'] += 1
        else:
            channels['No Channel'] += 1
    
    print(f"   Sample revenue (100 orders): €{total_revenue:,.2f}")
    print(f"   Average order value: €{total_revenue/len(orders) if orders else 0:,.2f}")
    print(f"   Channel distribution (sample):")
    for channel, count in sorted(channels.items(), key=lambda x: x[1], reverse=True):
        print(f"      {channel}: {count}")
    
    results['orders'] = {
        'total': order_count,
        'sample_revenue': total_revenue,
        'avg_order_value': total_revenue/len(orders) if orders else 0,
        'channels': dict(channels)
    }
    
    # 3. Check products
    print("\n🛍️ Checking Products...")
    product_count = models.execute_kw(
        db, uid, password,
        'product.product', 'search_count',
        [[('sale_ok', '=', True)]], {}
    )
    print(f"   Total saleable products: {product_count:,}")
    
    # Get products with sales
    products_with_sales = models.execute_kw(
        db, uid, password,
        'product.product', 'search_count',
        [[('sale_ok', '=', True), ('sales_count', '>', 0)]], {}
    )
    print(f"   Products with sales: {products_with_sales:,}")
    print(f"   Coverage: {products_with_sales/product_count*100 if product_count else 0:.1f}%")
    
    results['products'] = {
        'total': product_count,
        'with_sales': products_with_sales,
        'coverage_pct': products_with_sales/product_count*100 if product_count else 0
    }
    
    # 4. Check returns
    print("\n↩️ Checking Returns...")
    returns = models.execute_kw(
        db, uid, password,
        'sale.order', 'search_read',
        [[('state', 'in', ['sale', 'done'])]],
        {'fields': ['name', 'amount_total'], 'limit': 1000}
    )
    
    return_count = sum(1 for r in returns if 'RET' in r.get('name', '') or r.get('amount_total', 0) < 0)
    return_rate = return_count/len(returns)*100 if returns else 0
    
    print(f"   Returns in sample: {return_count}/{len(returns)}")
    print(f"   Return rate: {return_rate:.1f}%")
    
    results['returns'] = {
        'count': return_count,
        'sample_size': len(returns),
        'rate_pct': return_rate
    }
    
    # 5. Date range check
    print("\n📅 Checking Date Ranges...")
    date_orders = models.execute_kw(
        db, uid, password,
        'sale.order', 'search_read',
        [[('state', 'in', ['sale', 'done'])]],
        {'fields': ['date_order'], 'limit': 100, 'order': 'date_order desc'}
    )
    
    if date_orders:
        dates = [datetime.strptime(o['date_order'], '%Y-%m-%d %H:%M:%S') for o in date_orders if o.get('date_order')]
        if dates:
            print(f"   Latest order: {max(dates).strftime('%Y-%m-%d')}")
            print(f"   Earliest in sample: {min(dates).strftime('%Y-%m-%d')}")
    
    # Summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    # Check against requirements
    issues = []
    
    if customer_count < 30000:
        issues.append(f"❌ Only {customer_count:,} customers (target: 35,000)")
    else:
        print(f"✅ Customers: {customer_count:,}")
    
    if order_count < 50000:
        issues.append(f"❌ Only {order_count:,} orders (target: 65,000)")
    else:
        print(f"✅ Orders: {order_count:,}")
    
    if products_with_sales < product_count * 0.8:
        issues.append(f"❌ Only {products_with_sales/product_count*100:.1f}% product coverage")
    else:
        print(f"✅ Product coverage: {products_with_sales/product_count*100:.1f}%")
    
    if return_rate < 5 or return_rate > 30:
        issues.append(f"⚠️ Return rate {return_rate:.1f}% may need adjustment")
    else:
        print(f"✅ Return rate: {return_rate:.1f}%")
    
    if issues:
        print("\n⚠️ Issues found:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("\n✅ All validations passed!")
    
    # Save results
    results['summary'] = {
        'timestamp': datetime.now().isoformat(),
        'issues': issues,
        'status': 'PASSED' if not issues else 'NEEDS_ATTENTION'
    }
    
    with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/quick_validation_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n📄 Results saved to quick_validation_results.json")
    
    return results

if __name__ == "__main__":
    quick_validate()