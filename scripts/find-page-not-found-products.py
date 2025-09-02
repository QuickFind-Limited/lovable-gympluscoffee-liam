#!/usr/bin/env python3
"""
Find all products that have "Page not found" or similar error messages as their name
"""

import os
import asyncio
from supabase import create_client, Client

# Get Supabase credentials from environment
url = os.getenv('SUPABASE_URL', 'https://kkykmtxtcgrdqiqxfhhr.supabase.co')
anon_key = os.getenv('SUPABASE_ANON_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtreWttdHh0Y2dyZHFpcXhmaGhyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjY1MTQ3OTAsImV4cCI6MjA0MjA5MDc5MH0.ZqMRhh8qindvPmqGlVexDVBYGVhY3rGJA3yIBDmXSfg')

# Create Supabase client
supabase: Client = create_client(url, anon_key)

async def check_odoo_suppliers():
    """Call the odoo-suppliers-final edge function to check for problematic product names"""
    
    headers = {
        'Authorization': f'Bearer {anon_key}',
        'Content-Type': 'application/json'
    }
    
    # Get suppliers with products
    response = supabase.functions.invoke(
        "odoo-suppliers-final",
        invoke_options={
            "body": {
                "method": "search_read",
                "model": "res.partner",
                "domain": [["is_company", "=", True], ["supplier_rank", ">", 0]],
                "fields": ["id", "name"],
                "limit": 100,
                "offset": 0,
                "with_products": True
            },
            "headers": headers
        }
    )
    
    if response.get('error'):
        print(f"Error calling edge function: {response['error']}")
        return
    
    data = response.get('data', {})
    suppliers = data.get('suppliers', [])
    
    print(f"Found {len(suppliers)} suppliers")
    
    # Check each supplier's products
    problematic_products = []
    
    for supplier in suppliers:
        products = supplier.get('products', [])
        
        for product in products:
            product_name = product.get('product_name', '')
            product_id = product.get('product_id', '')
            product_code = product.get('product_code', '')
            
            # Check if product name contains error-like text
            error_patterns = ['Page not found', 'Error', '404', 'Not Found', 'undefined', 'null']
            
            for pattern in error_patterns:
                if isinstance(product_name, str) and pattern.lower() in str(product_name).lower():
                    problematic_products.append({
                        'supplier': supplier['name'],
                        'supplier_id': supplier['id'],
                        'product_code': product_code,
                        'product_name': product_name,
                        'product_id': product_id,
                        'pattern_matched': pattern
                    })
                    break
            
            # Also check if product_id contains the error pattern
            if isinstance(product_id, list) and len(product_id) > 1:
                for pattern in error_patterns:
                    if pattern.lower() in str(product_id[1]).lower():
                        problematic_products.append({
                            'supplier': supplier['name'],
                            'supplier_id': supplier['id'],
                            'product_code': product_code,
                            'product_name': product_name,
                            'product_id': product_id,
                            'pattern_matched': f"{pattern} (in product_id)"
                        })
                        break
    
    # Display results
    if problematic_products:
        print(f"\nFound {len(problematic_products)} products with error-like names:")
        print("="*80)
        
        for prod in problematic_products:
            print(f"\nSupplier: {prod['supplier']} (ID: {prod['supplier_id']})")
            print(f"Product Code: {prod['product_code']}")
            print(f"Product Name: {prod['product_name']}")
            print(f"Product ID: {prod['product_id']}")
            print(f"Pattern Matched: {prod['pattern_matched']}")
            
        # Group by pattern
        print("\n" + "="*80)
        print("Summary by pattern:")
        pattern_counts = {}
        for prod in problematic_products:
            pattern = prod['pattern_matched']
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {pattern}: {count} products")
            
        # Find EUR-ANF-8904 specifically
        print("\n" + "="*80)
        eur_anf_8904 = [p for p in problematic_products if p['product_code'] == 'EUR-ANF-8904']
        if eur_anf_8904:
            print("Found EUR-ANF-8904:")
            for prod in eur_anf_8904:
                print(f"  Supplier: {prod['supplier']}")
                print(f"  Product Name: {prod['product_name']}")
                print(f"  Product ID: {prod['product_id']}")
    else:
        print("\nNo products found with error-like names")

# Run the async function
asyncio.run(check_odoo_suppliers())