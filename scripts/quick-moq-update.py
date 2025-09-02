#!/usr/bin/env python3
"""
Quick MOQ update - update first 100 products to demonstrate the change
"""

import xmlrpc.client
import random

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

def main():
    try:
        uid, models = connect()
        print(f"Successfully connected to Odoo (UID: {uid})\n")
        
        print("=== Quick MOQ Update (First 100 Products) ===\n")
        
        # MOQ options: 12, 18, 24, 30, 36, 42, 48
        moq_options = [12, 18, 24, 30, 36, 42, 48]
        weights = [30, 25, 20, 10, 8, 5, 2]  # Higher weight for lower MOQs
        
        # Get first 100 supplier products across different vendors
        vendor_ids = [21, 22, 23, 24, 25, 26, 20]  # All vendor IDs
        
        total_updated = 0
        
        for vendor_id in vendor_ids:
            print(f"\nUpdating vendor ID {vendor_id}...")
            
            # Get products for this vendor
            supplier_products = models.execute_kw(
                db, uid, password,
                'product.supplierinfo', 'search_read',
                [[['partner_id', '=', vendor_id]]],
                {
                    'fields': ['id', 'product_name', 'min_qty'],
                    'limit': 15  # Update 15 products per vendor
                }
            )
            
            for sp in supplier_products:
                try:
                    # Select a random MOQ from the options
                    new_moq = random.choices(moq_options, weights=weights, k=1)[0]
                    
                    # Update the min_qty field
                    models.execute_kw(
                        db, uid, password,
                        'product.supplierinfo', 'write',
                        [[sp['id']], {'min_qty': new_moq}]
                    )
                    
                    total_updated += 1
                    
                    # Show first few updates
                    if total_updated <= 5:
                        product_name = sp.get('product_name', 'Unknown')
                        if '|META|' in str(product_name):
                            product_name = product_name.split('|META|')[0].strip()[:40]
                        print(f"  Updated: {product_name}... MOQ: {sp['min_qty']} → {new_moq}")
                        
                except Exception as e:
                    print(f"  Error: {e}")
                    continue
        
        print(f"\n✓ Successfully updated {total_updated} products")
        print("\nMOQ values now range from 12 to 48 in multiples of 6")
        print("The Suppliers page will now show these updated MOQ values")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()