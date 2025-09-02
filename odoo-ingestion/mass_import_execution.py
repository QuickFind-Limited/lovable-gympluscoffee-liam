#!/usr/bin/env python3
"""
Mass Import Execution - Process large batches efficiently
"""

import json
import time
from datetime import datetime

# Statistics tracking
stats = {
    'customers_imported': 10,  # Already imported 10 test customers
    'transactions_imported': 0,
    'errors': 0,
    'start_time': datetime.now(),
    'last_batch_time': datetime.now()
}

def load_all_data():
    """Load all data files for processing"""
    print("Loading all data files...")
    
    # Load customers
    with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/generated_customers.json', 'r') as f:
        customers = json.load(f)
    
    # Load transactions
    with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/generated_transactions.json', 'r') as f:
        transactions_data = json.load(f)
    
    # Load product mapping
    with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/product_mapping.json', 'r') as f:
        product_mapping = json.load(f)
    
    print(f"Loaded {len(customers):,} customers")
    print(f"Loaded {len(transactions_data.get('transactions', [])):,} transactions")
    print(f"Product mapping contains {len(product_mapping.keys())} items")
    
    return {
        'customers': customers,
        'transactions': transactions_data.get('transactions', []),
        'product_mapping': product_mapping,
        'metadata': transactions_data.get('metadata', {}),
        'summary': transactions_data.get('summary_statistics', {})
    }

def create_customer_mapping_for_mcp():
    """Create customer mappings that can be used with MCP calls"""
    data = load_all_data()
    
    # Country mapping
    country_map = {'AU': 13, 'IE': 101, 'GB': 231, 'UK': 231, 'US': 233}
    
    # Process customers into batches ready for MCP
    customers = data['customers']
    
    # Skip the first 10 we already imported
    remaining_customers = customers[10:]
    
    print(f"Preparing {len(remaining_customers):,} remaining customers for import")
    print("Next batches will need to be processed using MCP tools...")
    
    # Group by countries for verification
    country_counts = {}
    for customer in customers:
        country = customer.get('country', 'UK')
        country_counts[country] = country_counts.get(country, 0) + 1
    
    print("Full dataset country distribution:")
    for country, count in sorted(country_counts.items()):
        percentage = (count / len(customers)) * 100
        print(f"  {country}: {count:,} customers ({percentage:.1f}%)")
    
    return data

def create_product_mapping():
    """Create product SKU to Odoo ID mapping"""
    with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/product_mapping.json', 'r') as f:
        mapping_data = json.load(f)
    
    # The product mapping is structured with product IDs as keys
    # We need to create a SKU -> Odoo ID mapping
    product_sku_map = {}
    
    # Look through the numbered keys (product IDs)
    for key, product in mapping_data.items():
        if key.isdigit():
            if 'default_code' in product and product['default_code']:
                sku = product['default_code']
                odoo_id = int(key)  # The key is the Odoo product ID
                product_sku_map[sku] = odoo_id
    
    print(f"Created SKU mapping for {len(product_sku_map)} products")
    if len(product_sku_map) > 0:
        sample_skus = list(product_sku_map.keys())[:5]
        print("Sample SKU mappings:")
        for sku in sample_skus:
            print(f"  {sku} -> Odoo ID {product_sku_map[sku]}")
    
    return product_sku_map

def analyze_transaction_patterns():
    """Analyze transaction patterns for import planning"""
    with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/generated_transactions.json', 'r') as f:
        data = json.load(f)
    
    transactions = data.get('transactions', [])
    summary = data.get('summary_statistics', {})
    
    print(f"\nTransaction Analysis:")
    print(f"Total transactions: {len(transactions):,}")
    
    if 'channel_breakdown' in summary:
        channels = summary['channel_breakdown']
        print("Channel distribution:")
        for channel, info in channels.items():
            print(f"  {channel.title()}: {info.get('count', 0):,} orders ({info.get('percentage', 0):.1f}%)")
    
    if 'geographic_breakdown' in summary:
        geo = summary['geographic_breakdown']
        print("Geographic distribution:")
        for country, info in geo.items():
            print(f"  {country}: {info.get('count', 0):,} orders ({info.get('percentage', 0):.1f}%)")
    
    # Sample some transactions
    print("\nSample transactions:")
    for i, tx in enumerate(transactions[:3]):
        print(f"  {i+1}. Order {tx.get('order_id', 'unknown')} - {tx.get('channel', 'unknown')} - €{tx.get('total_value', 0):.2f}")
        for item in tx.get('items', [])[:2]:  # First 2 items per order
            print(f"     - {item.get('sku', 'unknown')}: {item.get('quantity', 0)} x €{item.get('unit_price', 0):.2f}")
    
    return len(transactions)

def print_import_status():
    """Print current import status"""
    elapsed = datetime.now() - stats['start_time']
    
    print(f"\n=== IMPORT STATUS ===")
    print(f"Customers imported: {stats['customers_imported']:,}")
    print(f"Transactions imported: {stats['transactions_imported']:,}")  
    print(f"Errors: {stats['errors']}")
    print(f"Elapsed time: {elapsed}")
    print(f"Started: {stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    print("=" * 60)
    print("MASS IMPORT EXECUTION - DATA ANALYSIS")
    print("=" * 60)
    
    # Analyze the data structure
    data = create_customer_mapping_for_mcp()
    product_mapping = create_product_mapping()
    transaction_count = analyze_transaction_patterns()
    
    print_import_status()
    
    print(f"\n=== READY FOR MASS IMPORT ===")
    print(f"Next steps:")
    print(f"1. Import remaining {len(data['customers']) - 10:,} customers")
    print(f"2. Import {transaction_count:,} transactions") 
    print(f"3. Map products using {len(product_mapping)} SKU mappings")
    print(f"4. Validate distribution patterns")
    print(f"5. Generate final report")