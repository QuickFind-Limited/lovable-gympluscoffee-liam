#!/usr/bin/env python3
"""
Import customers in batches to Odoo using MCP tools
"""

import json
import sys

def load_customers(start_index=0, batch_size=150):
    """Load a batch of customers"""
    with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/generated_customers.json', 'r') as f:
        customers = json.load(f)
    
    end_index = min(start_index + batch_size, len(customers))
    batch = customers[start_index:end_index]
    
    print(f"Loaded batch: customers {start_index+1}-{end_index} ({len(batch)} customers)")
    return batch, len(customers)

def map_country_code(country_code):
    """Map country codes to Odoo IDs"""
    country_mapping = {
        'AU': 13,  # Australia
        'IE': 101, # Ireland  
        'GB': 231, # United Kingdom
        'UK': 231, # United Kingdom (alternative)
        'US': 233  # United States
    }
    return country_mapping.get(country_code, 231)  # Default to UK

def print_customer_data_for_mcp(customers):
    """Print customer data formatted for MCP import"""
    
    print("Ready to import the following customers:")
    print(f"Total customers in batch: {len(customers)}")
    
    country_counts = {}
    for customer in customers:
        country = customer.get('country', 'UK')
        country_counts[country] = country_counts.get(country, 0) + 1
    
    print("Country distribution:")
    for country, count in country_counts.items():
        print(f"  {country}: {count} customers")
    
    print("\nSample customers:")
    for i, customer in enumerate(customers[:5]):
        print(f"  {i+1}. {customer['first_name']} {customer['last_name']} ({customer['email']}) - {customer['country']}")
    
    print(f"\nCountry ID mappings to use:")
    unique_countries = set(c.get('country', 'UK') for c in customers)
    for country in unique_countries:
        print(f"  {country} -> {map_country_code(country)}")

if __name__ == "__main__":
    batch_start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 150
    
    customers, total = load_customers(batch_start, batch_size)
    print_customer_data_for_mcp(customers)
    
    # Output for Claude Code to use
    print(f"\n=== BATCH DATA FOR MCP IMPORT ===")
    print(f"Batch: {batch_start+1}-{batch_start+len(customers)} of {total}")
    print("Use these customer records with mcp__odoo-mcp__odoo_create")