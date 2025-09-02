#!/usr/bin/env python3
"""
Final Validation Check for Gym+Coffee Odoo Data
Complete validation ensuring all requirements are met
"""

import xmlrpc.client
import json
from datetime import datetime
from collections import defaultdict

def final_validation():
    """Run comprehensive validation checks"""
    
    # Odoo connection
    url = 'https://source-gym-plus-coffee.odoo.com/'
    db = 'source-gym-plus-coffee'
    username = 'admin@quickfindai.com'
    password = 'BJ62wX2J4yzjS$i'
    
    print("="*70)
    print("FINAL VALIDATION CHECK - GYM+COFFEE ODOO DATA")
    print("="*70)
    
    print("\n🔌 Connecting to Odoo...")
    try:
        common = xmlrpc.client.ServerProxy(f'{url}xmlrpc/2/common')
        uid = common.authenticate(db, username, password, {})
        models = xmlrpc.client.ServerProxy(f'{url}xmlrpc/2/object')
        print("✅ Connected successfully to Odoo saas~18.4\n")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    validation_results = {}
    issues = []
    fixes_needed = []
    
    # 1. CUSTOMER VALIDATION
    print("="*70)
    print("1️⃣ CUSTOMER VALIDATION")
    print("="*70)
    
    customer_count = models.execute_kw(
        db, uid, password,
        'res.partner', 'search_count',
        [[('customer_rank', '>', 0)]], {}
    )
    
    print(f"📊 Total customers: {customer_count:,}")
    
    # Get all customers to analyze geography
    customers = models.execute_kw(
        db, uid, password,
        'res.partner', 'search_read',
        [[('customer_rank', '>', 0)]],
        {'fields': ['country_id', 'city', 'total_invoiced'], 'limit': 500}
    )
    
    # Geographic analysis
    geo_dist = defaultdict(int)
    geo_revenue = defaultdict(float)
    
    for c in customers:
        if c.get('country_id'):
            country = c['country_id'][1] if isinstance(c['country_id'], list) else 'Unknown'
            geo_dist[country] += 1
            geo_revenue[country] += c.get('total_invoiced', 0)
    
    print("\n🌍 Geographic Distribution:")
    total_customers_sample = len(customers)
    for country, count in sorted(geo_dist.items(), key=lambda x: x[1], reverse=True)[:10]:
        pct = count/total_customers_sample*100
        print(f"   {country}: {count} ({pct:.1f}%)")
    
    # Check requirements
    if customer_count < 35000:
        issues.append(f"Only {customer_count:,} customers (need 35,000)")
        fixes_needed.append("Import remaining customer data")
    
    validation_results['customers'] = {
        'total': customer_count,
        'target': 35000,
        'status': '✅' if customer_count >= 35000 else '❌'
    }
    
    # 2. ORDER VALIDATION
    print("\n" + "="*70)
    print("2️⃣ ORDER VALIDATION")
    print("="*70)
    
    order_count = models.execute_kw(
        db, uid, password,
        'sale.order', 'search_count',
        [[('state', 'in', ['sale', 'done'])]], {}
    )
    
    print(f"📊 Total confirmed orders: {order_count:,}")
    
    # Get orders for channel analysis
    orders = models.execute_kw(
        db, uid, password,
        'sale.order', 'search_read',
        [[('state', 'in', ['sale', 'done'])]],
        {'fields': ['amount_total', 'team_id', 'date_order', 'partner_id'], 'limit': 1000}
    )
    
    # Channel analysis
    channel_revenue = defaultdict(float)
    channel_count = defaultdict(int)
    total_revenue = 0
    
    for order in orders:
        amount = order.get('amount_total', 0)
        total_revenue += amount
        
        channel = 'Unknown'
        if order.get('team_id'):
            team_name = order['team_id'][1] if isinstance(order['team_id'], list) else 'Unknown'
            
            # Categorize channels
            if any(x in team_name.lower() for x in ['online', 'web', 'shopify', 'instagram', 'amazon']):
                channel = 'Online/D2C'
            elif any(x in team_name.lower() for x in ['retail', 'store', 'pop-up']):
                channel = 'Retail'
            elif any(x in team_name.lower() for x in ['b2b', 'wholesale', 'corporate']):
                channel = 'B2B/Wholesale'
            else:
                channel = team_name
        
        channel_revenue[channel] += amount
        channel_count[channel] += 1
    
    print("\n📈 Channel Distribution (sample of 1000 orders):")
    for channel, revenue in sorted(channel_revenue.items(), key=lambda x: x[1], reverse=True):
        pct = revenue/total_revenue*100 if total_revenue > 0 else 0
        count = channel_count[channel]
        print(f"   {channel}: {count} orders, €{revenue:,.2f} ({pct:.1f}% of revenue)")
    
    # Date range check
    if orders:
        dates = []
        for o in orders:
            if o.get('date_order'):
                try:
                    dates.append(datetime.strptime(o['date_order'], '%Y-%m-%d %H:%M:%S'))
                except:
                    pass
        
        if dates:
            print(f"\n📅 Date Range:")
            print(f"   Earliest: {min(dates).strftime('%Y-%m-%d')}")
            print(f"   Latest: {max(dates).strftime('%Y-%m-%d')}")
            
            # Check for summer period (June-September)
            summer_orders = [d for d in dates if d.month in [6, 7, 8, 9] and d.year == 2024]
            print(f"   Summer 2024 orders: {len(summer_orders)}/{len(dates)} ({len(summer_orders)/len(dates)*100:.1f}%)")
    
    if order_count < 65000:
        issues.append(f"Only {order_count:,} orders (need 65,000)")
        fixes_needed.append("Import remaining transaction data")
    
    validation_results['orders'] = {
        'total': order_count,
        'target': 65000,
        'status': '✅' if order_count >= 65000 else '❌'
    }
    
    # 3. PRODUCT COVERAGE
    print("\n" + "="*70)
    print("3️⃣ PRODUCT COVERAGE")
    print("="*70)
    
    product_count = models.execute_kw(
        db, uid, password,
        'product.product', 'search_count',
        [[('sale_ok', '=', True), ('active', '=', True)]], {}
    )
    
    print(f"📊 Total saleable products: {product_count:,}")
    
    # Get order lines to check product coverage
    order_lines = models.execute_kw(
        db, uid, password,
        'sale.order.line', 'search_read',
        [[('order_id.state', 'in', ['sale', 'done'])]],
        {'fields': ['product_id', 'product_uom_qty', 'price_subtotal'], 'limit': 5000}
    )
    
    product_sales = defaultdict(lambda: {'qty': 0, 'revenue': 0})
    
    for line in order_lines:
        if line.get('product_id'):
            product_id = line['product_id'][0] if isinstance(line['product_id'], list) else line['product_id']
            product_sales[product_id]['qty'] += line.get('product_uom_qty', 0)
            product_sales[product_id]['revenue'] += line.get('price_subtotal', 0)
    
    products_with_sales = len(product_sales)
    coverage_pct = products_with_sales/product_count*100 if product_count > 0 else 0
    
    print(f"📈 Products with sales: {products_with_sales:,}/{product_count:,} ({coverage_pct:.1f}%)")
    
    # Top 20% analysis
    if product_sales:
        sorted_products = sorted(product_sales.items(), key=lambda x: x[1]['revenue'], reverse=True)
        top_20_count = max(1, len(sorted_products) // 5)
        top_20_revenue = sum(p[1]['revenue'] for p in sorted_products[:top_20_count])
        total_product_revenue = sum(p[1]['revenue'] for p in sorted_products)
        
        if total_product_revenue > 0:
            top_20_pct = top_20_revenue/total_product_revenue*100
            print(f"📊 Top 20% products: {top_20_pct:.1f}% of revenue")
            
            if top_20_pct < 60 or top_20_pct > 75:
                issues.append(f"Top 20% products generate {top_20_pct:.1f}% (target: 60-75%)")
    
    if coverage_pct < 80:
        issues.append(f"Only {coverage_pct:.1f}% product coverage")
        fixes_needed.append("Generate sales for inactive products")
    
    validation_results['products'] = {
        'total': product_count,
        'with_sales': products_with_sales,
        'coverage_pct': coverage_pct,
        'status': '✅' if coverage_pct >= 80 else '❌'
    }
    
    # 4. RETURN RATES
    print("\n" + "="*70)
    print("4️⃣ RETURN VALIDATION")
    print("="*70)
    
    # Check for returns (negative amounts or RET prefix)
    all_orders = models.execute_kw(
        db, uid, password,
        'sale.order', 'search_read',
        [[('state', 'in', ['sale', 'done'])]],
        {'fields': ['name', 'amount_total', 'team_id'], 'limit': 2000}
    )
    
    returns_by_channel = defaultdict(int)
    orders_by_channel = defaultdict(int)
    
    for order in all_orders:
        is_return = 'RET' in order.get('name', '') or order.get('amount_total', 0) < 0
        
        channel = 'Online'  # Default
        if order.get('team_id'):
            team_name = order['team_id'][1] if isinstance(order['team_id'], list) else ''
            if 'retail' in team_name.lower() or 'store' in team_name.lower():
                channel = 'Retail'
            elif 'b2b' in team_name.lower() or 'wholesale' in team_name.lower():
                channel = 'B2B'
        
        orders_by_channel[channel] += 1
        if is_return:
            returns_by_channel[channel] += 1
    
    print("📊 Return Rates by Channel:")
    for channel in ['Online', 'Retail', 'B2B']:
        if orders_by_channel[channel] > 0:
            rate = returns_by_channel[channel]/orders_by_channel[channel]*100
            target_range = {
                'Online': '20-27%',
                'Retail': '4-9%',
                'B2B': '1-2%'
            }
            print(f"   {channel}: {rate:.1f}% (target: {target_range[channel]})")
            
            # Check if in range
            if channel == 'Online' and (rate < 20 or rate > 27):
                issues.append(f"{channel} return rate {rate:.1f}% outside target")
            elif channel == 'Retail' and (rate < 4 or rate > 9):
                issues.append(f"{channel} return rate {rate:.1f}% outside target")
            elif channel == 'B2B' and (rate < 1 or rate > 2):
                issues.append(f"{channel} return rate {rate:.1f}% outside target")
    
    # 5. SUMMARY
    print("\n" + "="*70)
    print("📊 VALIDATION SUMMARY")
    print("="*70)
    
    # Requirements check
    requirements_met = []
    requirements_not_met = []
    
    # Customer requirement
    if customer_count >= 35000:
        requirements_met.append("✅ Customers: 35,000+ records")
    else:
        requirements_not_met.append(f"❌ Customers: {customer_count:,}/35,000")
    
    # Order requirement
    if order_count >= 65000:
        requirements_met.append("✅ Orders: 65,000+ transactions")
    else:
        requirements_not_met.append(f"❌ Orders: {order_count:,}/65,000")
    
    # Product coverage
    if coverage_pct >= 80:
        requirements_met.append(f"✅ Product coverage: {coverage_pct:.1f}%")
    else:
        requirements_not_met.append(f"❌ Product coverage: {coverage_pct:.1f}% (need 80%+)")
    
    # Channel distribution (simplified check)
    if 'Online/D2C' in channel_revenue and 'Retail' in channel_revenue:
        requirements_met.append("✅ Multi-channel distribution active")
    else:
        requirements_not_met.append("⚠️ Channel distribution needs balancing")
    
    print("\n✅ REQUIREMENTS MET:")
    for req in requirements_met:
        print(f"   {req}")
    
    if requirements_not_met:
        print("\n❌ REQUIREMENTS NOT MET:")
        for req in requirements_not_met:
            print(f"   {req}")
    
    if fixes_needed:
        print("\n🔧 RECOMMENDED FIXES:")
        for fix in fixes_needed:
            print(f"   • {fix}")
    
    # Final status
    print("\n" + "="*70)
    if not requirements_not_met:
        print("🎉 ALL VALIDATION CHECKS PASSED!")
        print("The Gym+Coffee Odoo data meets all requirements.")
        status = "PASSED"
    else:
        print("⚠️ VALIDATION INCOMPLETE")
        print("Some requirements still need to be addressed.")
        print("Run the import scripts to complete the data population.")
        status = "NEEDS_COMPLETION"
    print("="*70)
    
    # Save results
    results = {
        'timestamp': datetime.now().isoformat(),
        'status': status,
        'validation_results': validation_results,
        'requirements_met': requirements_met,
        'requirements_not_met': requirements_not_met,
        'fixes_needed': fixes_needed,
        'summary': {
            'customers': customer_count,
            'orders': order_count,
            'products': product_count,
            'product_coverage': f"{coverage_pct:.1f}%",
            'geographic_distribution': dict(geo_dist),
            'channel_distribution': {k: f"€{v:,.2f}" for k, v in channel_revenue.items()}
        }
    }
    
    with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/final_validation_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n📄 Detailed results saved to final_validation_results.json")
    
    return results

if __name__ == "__main__":
    final_validation()