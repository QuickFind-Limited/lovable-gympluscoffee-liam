#!/usr/bin/env python3
"""
Test script using the correct Odoo credentials from odoo_mcp/.env
"""
import xmlrpc.client
import os

def test_odoo_with_correct_creds():
    # Correct Odoo connection settings from odoo_mcp/.env
    ODOO_URL = 'https://source-animalfarmacy.odoo.com'
    ODOO_DB = 'source-animalfarmacy'
    ODOO_USERNAME = 'admin@quickfindai.com'
    ODOO_PASSWORD = 'BJ62wX2J4yzjS$i'
    
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
                'name': 'Check total product count',
                'domain': [],
                'fields': ['id', 'name', 'active', 'sale_ok'],
                'limit': 5
            },
            {
                'name': 'Search for products containing "acralube" (no filters)',
                'domain': [['name', 'ilike', 'acralube']],
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
                'name': 'Search for products containing "product" (should find many)',
                'domain': [['name', 'ilike', 'product']],
                'fields': ['id', 'name', 'display_name', 'active', 'sale_ok'],
                'limit': 3
            },
            {
                'name': 'Search active products only',
                'domain': [['active', '=', True]],
                'fields': ['id', 'name', 'active', 'sale_ok'],
                'limit': 3
            },
            {
                'name': 'Search sale_ok products only', 
                'domain': [['sale_ok', '=', True]],
                'fields': ['id', 'name', 'active', 'sale_ok'],
                'limit': 3
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
                        print(f"    Display Name: {result.get('display_name', 'N/A')}")
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
                
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    test_odoo_with_correct_creds()