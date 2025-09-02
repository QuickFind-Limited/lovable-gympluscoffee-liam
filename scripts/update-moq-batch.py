#!/usr/bin/env python3
"""
Update MOQ (min_qty) values for all supplier products to range from 12 to 48 in multiples of 6
Batch version for better performance
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

def update_moq_by_vendor(uid, models, vendor_id, vendor_name):
    """Update MOQ values for a specific vendor"""
    # Get all supplier products for this vendor
    supplier_products = models.execute_kw(
        db, uid, password,
        'product.supplierinfo', 'search_read',
        [[['partner_id', '=', vendor_id]]],
        {
            'fields': ['id', 'min_qty'],
            'limit': 500
        }
    )
    
    print(f"\nUpdating {len(supplier_products)} products for {vendor_name}")
    
    # MOQ options: 12, 18, 24, 30, 36, 42, 48
    moq_options = [12, 18, 24, 30, 36, 42, 48]
    weights = [30, 25, 20, 10, 8, 5, 2]  # Higher weight for lower MOQs
    
    updated_count = 0
    
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
            
            updated_count += 1
                
        except Exception as e:
            print(f"  Error updating product {sp['id']}: {e}")
            continue
    
    print(f"  ✓ Updated {updated_count} products")
    return updated_count

def main():
    try:
        uid, models = connect()
        print(f"Successfully connected to Odoo (UID: {uid})\n")
        
        print("=== Updating MOQ Values by Vendor ===")
        
        # Get all suppliers
        suppliers = models.execute_kw(
            db, uid, password,
            'res.partner', 'search_read',
            [[['supplier_rank', '>', 0]]],
            {
                'fields': ['id', 'name'],
                'limit': 20
            }
        )
        
        print(f"Found {len(suppliers)} suppliers")
        
        total_updated = 0
        
        # Process each supplier
        for supplier in suppliers:
            vendor_id = supplier['id']
            vendor_name = supplier['name']
            
            updated = update_moq_by_vendor(uid, models, vendor_id, vendor_name)
            total_updated += updated
        
        print("\n" + "="*60)
        print("=== SUMMARY ===")
        print(f"✓ Updated {total_updated} products across {len(suppliers)} vendors")
        print("\nMOQ Values:")
        print("  - Range: 12 to 48 units")
        print("  - Multiples of 6 (12, 18, 24, 30, 36, 42, 48)")
        print("  - Most products have MOQ of 12-24 (common items)")
        print("  - Some products have MOQ of 30-36 (specialty items)")
        print("  - Few products have MOQ of 42-48 (bulk/premium items)")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()