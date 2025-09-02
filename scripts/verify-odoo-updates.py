#!/usr/bin/env python3
"""
Verify that Odoo products have been updated with metadata
"""

import xmlrpc.client
import json

# Odoo connection details
odoo_url = 'https://source-animalfarmacy.odoo.com'
db = 'source-animalfarmacy'
username = 'admin@quickfindai.com'
password = 'BJ62wX2J4yzjS$i'

def connect():
    """Connect to Odoo and authenticate"""
    common = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})
    
    if not uid:
        raise Exception("Failed to authenticate with Odoo")
    
    models = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/object')
    
    return uid, models

def verify_updates(uid, models):
    """Check supplier products for metadata"""
    print("=== Verifying Odoo Product Updates ===\n")
    
    # Get supplier products
    supplier_products = models.execute_kw(
        db, uid, password,
        'product.supplierinfo', 'search_read',
        [[['partner_id', '=', 22]]],  # Veterinary Wholesale Inc
        {
            'fields': ['id', 'product_id', 'product_name', 'product_code', 'min_qty'],
            'limit': 10
        }
    )
    
    print(f"Found {len(supplier_products)} products for Veterinary Wholesale Inc\n")
    
    has_metadata = 0
    no_metadata = 0
    
    for sp in supplier_products:
        product_name = sp.get('product_name', '')
        print(f"Product ID: {sp['id']}")
        print(f"Product Code: {sp.get('product_code', 'N/A')}")
        print(f"Product Name: {product_name[:80]}...")
        
        if '|META|' in str(product_name):
            has_metadata += 1
            print("✓ HAS METADATA")
            # Try to parse it
            try:
                parts = product_name.split('|META|')
                if len(parts) == 2:
                    metadata = json.loads(parts[1])
                    print(f"  - Pack Size: {metadata.get('pack_size', 'N/A')}")
                    print(f"  - Min Level: {metadata.get('minimum_level', 'N/A')}")
                    print(f"  - Available: {metadata.get('qty_available', 'N/A')}")
                    print(f"  - Virtual: {metadata.get('virtual_available', 'N/A')}")
            except:
                print("  ! Error parsing metadata")
        else:
            no_metadata += 1
            print("✗ NO METADATA")
        
        print("-" * 60)
        print()
    
    print(f"\nSummary:")
    print(f"  Products with metadata: {has_metadata}")
    print(f"  Products without metadata: {no_metadata}")

def main():
    try:
        uid, models = connect()
        print(f"Successfully connected to Odoo (UID: {uid})\n")
        
        verify_updates(uid, models)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()