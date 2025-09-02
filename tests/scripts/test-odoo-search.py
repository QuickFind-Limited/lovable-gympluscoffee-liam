#!/usr/bin/env python3
"""
Test script to debug Odoo search issues by testing different search domains
and checking if products exist with different filters.
"""
import xmlrpc.client
import os
import json

# Odoo connection settings
ODOO_URL = os.getenv('ODOO_URL', 'https://animalfarmacy.odoo.com')
ODOO_DB = os.getenv('ODOO_DB', 'animalfarmacy')
ODOO_USERNAME = os.getenv('ODOO_USERNAME', 'admin')
ODOO_PASSWORD = os.getenv('ODOO_PASSWORD', '')

def test_odoo_search():
    try:
        # Connect to Odoo
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
        
        if not uid:
            print("❌ Authentication failed")
            return
        
        print(f"✅ Successfully authenticated with UID: {uid}")
        
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
        
        # Test different search scenarios
        test_cases = [
            {
                'name': 'Search for products containing "acralube" (no filters)',
                'domain': [['name', 'ilike', 'acralube']],
                'fields': ['id', 'name', 'display_name', 'active', 'sale_ok']
            },
            {
                'name': 'Search for products containing "acralube" (active only)',
                'domain': [['active', '=', True], ['name', 'ilike', 'acralube']],
                'fields': ['id', 'name', 'display_name', 'active', 'sale_ok']
            },
            {
                'name': 'Search for products containing "acralube" (sale_ok only)',
                'domain': [['sale_ok', '=', True], ['name', 'ilike', 'acralube']],
                'fields': ['id', 'name', 'display_name', 'active', 'sale_ok']
            },
            {
                'name': 'Search for products containing "acralube" (active + sale_ok)',
                'domain': [['&'], ['active', '=', True], ['sale_ok', '=', True], ['name', 'ilike', 'acralube']],
                'fields': ['id', 'name', 'display_name', 'active', 'sale_ok']
            },
            {
                'name': 'Search any field containing "acralube" (no filters)',
                'domain': ['|', '|', '|', '|',
                          ['name', 'ilike', 'acralube'],
                          ['display_name', 'ilike', 'acralube'],
                          ['description_sale', 'ilike', 'acralube'],
                          ['default_code', 'ilike', 'acralube'],
                          ['barcode', 'ilike', 'acralube']],
                'fields': ['id', 'name', 'display_name', 'default_code', 'barcode', 'active', 'sale_ok']
            },
            {
                'name': 'Check total product count',
                'domain': [],
                'fields': ['id', 'name', 'active', 'sale_ok'],
                'limit': 5
            },
            {
                'name': 'Check active product count',
                'domain': [['active', '=', True]],
                'fields': ['id', 'name', 'active', 'sale_ok'],
                'limit': 5
            },
            {
                'name': 'Check sale_ok product count', 
                'domain': [['sale_ok', '=', True]],
                'fields': ['id', 'name', 'active', 'sale_ok'],
                'limit': 5
            }
        ]
        
        for test_case in test_cases:
            print(f"\n🔍 {test_case['name']}")
            print(f"Domain: {test_case['domain']}")
            
            try:
                limit = test_case.get('limit', 10)
                results = models.execute_kw(
                    ODOO_DB, uid, ODOO_PASSWORD,
                    'product.product', 'search_read',
                    [test_case['domain']],
                    {'fields': test_case['fields'], 'limit': limit}
                )
                
                print(f"Results count: {len(results)}")
                
                if results:
                    print("Sample results:")
                    for result in results[:3]:  # Show first 3 results
                        print(f"  - ID: {result.get('id')}, Name: {result.get('name')}")
                        print(f"    Display Name: {result.get('display_name')}")
                        print(f"    Active: {result.get('active')}, Sale OK: {result.get('sale_ok')}")
                        if result.get('default_code'):
                            print(f"    Code: {result.get('default_code')}")
                        if result.get('barcode'):
                            print(f"    Barcode: {result.get('barcode')}")
                        print()
                else:
                    print("  ❌ No results found")
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        # Also search for common product terms
        common_terms = ['product', 'medicine', 'drug', 'tablet', 'capsule']
        print(f"\n🔍 Testing common product terms...")
        
        for term in common_terms:
            try:
                results = models.execute_kw(
                    ODOO_DB, uid, ODOO_PASSWORD,
                    'product.product', 'search_read',
                    [[['name', 'ilike', term]]],
                    {'fields': ['id', 'name'], 'limit': 1}
                )
                print(f"  {term}: {len(results)} results")
                if results:
                    print(f"    Sample: {results[0].get('name')}")
            except Exception as e:
                print(f"  {term}: Error - {e}")
                
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    test_odoo_search()