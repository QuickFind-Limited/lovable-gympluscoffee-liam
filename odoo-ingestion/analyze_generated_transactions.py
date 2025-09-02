#!/usr/bin/env python3
"""
Analyze the generated transactions for quality and realism
"""

import json
import statistics
from collections import defaultdict, Counter

def analyze_transactions():
    """Analyze the generated transaction dataset"""
    print("📊 Analyzing Generated Transaction Dataset")
    print("=" * 50)
    
    # Load the data
    with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/generated_transactions.json', 'r') as f:
        data = json.load(f)
    
    transactions = data['transactions']
    summary = data['summary_statistics']
    
    print(f"📈 Basic Statistics:")
    print(f"   Total Transactions: {summary['total_orders']:,}")
    print(f"   Total Revenue: €{summary['total_revenue']:,.2f}")
    print(f"   Average Order Value: €{summary['average_order_value']:.2f}")
    print(f"   Return Rate: {summary['return_analysis']['return_rate_percent']:.1f}%")
    print()
    
    # Analyze by channel
    print(f"📈 Channel Analysis:")
    for channel, stats in summary['channel_breakdown'].items():
        aov = summary['aov_by_channel'][channel]
        print(f"   {channel.title()}:")
        print(f"     Orders: {stats['count']:,} ({stats['percentage']:.1f}%)")
        print(f"     Revenue: €{stats['revenue']:,.2f}")
        print(f"     AOV: €{aov:.2f}")
        print()
    
    # Sample analysis
    print(f"🔍 Sample Transaction Analysis:")
    
    # Look at order values by channel
    channel_values = defaultdict(list)
    basket_sizes = defaultdict(list)
    
    # Analyze first 1000 transactions for performance
    sample_size = min(1000, len(transactions))
    for t in transactions[:sample_size]:
        channel = t['channel']
        channel_values[channel].append(t['total_amount'])
        basket_sizes[channel].append(len(t['order_lines']))
    
    print(f"   Sample Analysis (first {sample_size:,} transactions):")
    for channel in ['online', 'retail', 'b2b']:
        if channel in channel_values:
            values = channel_values[channel]
            baskets = basket_sizes[channel]
            
            print(f"   {channel.title()}:")
            print(f"     Count: {len(values)}")
            print(f"     AOV Range: €{min(values):.2f} - €{max(values):,.2f}")
            print(f"     AOV Median: €{statistics.median(values):.2f}")
            print(f"     Basket Size Range: {min(baskets)} - {max(baskets)} items")
            print(f"     Avg Basket Size: {statistics.mean(baskets):.1f}")
            print()
    
    # Show a few sample transactions
    print(f"🔍 Sample Transactions:")
    channels_shown = set()
    for t in transactions[:20]:  # Look at first 20
        channel = t['channel']
        if channel not in channels_shown:
            channels_shown.add(channel)
            print(f"   {channel.title()} Transaction:")
            print(f"     Order ID: {t['order_id']}")
            print(f"     Date: {t['order_date']}")
            print(f"     Customer: {t['customer_name']}")
            print(f"     Items: {len(t['order_lines'])}")
            print(f"     Total: €{t['total_amount']:.2f}")
            
            for line in t['order_lines'][:3]:  # Show first 3 items
                print(f"       - {line['quantity']}x {line['product_name']} @ €{line['unit_price']:.2f}")
            
            if len(t['order_lines']) > 3:
                print(f"       ... and {len(t['order_lines']) - 3} more items")
            print()
    
    # Identify any issues
    print(f"⚠️  Data Quality Checks:")
    
    issues = []
    
    # Check for unrealistic AOVs
    if summary['average_order_value'] > 1000:
        issues.append(f"Very high overall AOV (€{summary['average_order_value']:.2f})")
    
    # Check channel distribution
    b2b_pct = summary['channel_breakdown']['b2b']['percentage']
    if b2b_pct > 25:
        issues.append(f"High B2B percentage ({b2b_pct:.1f}%)")
    
    # Check for extreme values
    for channel, aov in summary['aov_by_channel'].items():
        if channel == 'b2b' and aov > 100000:
            issues.append(f"Extremely high B2B AOV (€{aov:.2f})")
        elif channel in ['online', 'retail'] and aov > 500:
            issues.append(f"High {channel} AOV (€{aov:.2f})")
    
    if issues:
        print("   Issues found:")
        for issue in issues:
            print(f"     ❌ {issue}")
        print("\n   💡 Recommendations:")
        print("     - Review B2B basket size generation logic")
        print("     - Consider adding maximum quantity limits")
        print("     - Adjust channel distribution weights")
    else:
        print("   ✅ No major issues detected")
    
    print(f"\n📄 File Information:")
    print(f"   File: /workspaces/source-lovable-gympluscoffee/odoo-ingestion/generated_transactions.json")
    print(f"   Size: {data.get('metadata', {}).get('total_transactions', 0):,} transactions")
    
    return transactions

if __name__ == "__main__":
    analyze_transactions()