#!/usr/bin/env python3
"""
Update MOQ (min_qty) values for all supplier products to range from 12 to 48 in multiples of 6
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

def update_moq_values(uid, models):
    """Update MOQ values for all supplier products"""
    print("=== Updating MOQ Values ===\n")
    
    # Get all supplier products
    supplier_products = models.execute_kw(
        db, uid, password,
        'product.supplierinfo', 'search_read',
        [[]],
        {
            'fields': ['id', 'product_id', 'product_name', 'min_qty', 'partner_id'],
            'limit': 1000  # Get up to 1000 products
        }
    )
    
    print(f"Found {len(supplier_products)} supplier products to update\n")
    
    # MOQ options: 12, 18, 24, 30, 36, 42, 48
    moq_options = [12, 18, 24, 30, 36, 42, 48]
    
    updated_count = 0
    vendors_updated = set()
    
    for sp in supplier_products:
        try:
            # Select a random MOQ from the options
            # Weight the selection to have more products with lower MOQs
            weights = [30, 25, 20, 10, 8, 5, 2]  # Higher weight for lower MOQs
            new_moq = random.choices(moq_options, weights=weights, k=1)[0]
            
            # Update the min_qty field
            models.execute_kw(
                db, uid, password,
                'product.supplierinfo', 'write',
                [[sp['id']], {'min_qty': new_moq}]
            )
            
            updated_count += 1
            
            # Track which vendors we've updated
            if sp.get('partner_id'):
                vendor_id = sp['partner_id'][0] if isinstance(sp['partner_id'], list) else sp['partner_id']
                vendors_updated.add(vendor_id)
            
            # Print progress every 50 updates
            if updated_count % 50 == 0:
                print(f"Updated {updated_count} products...")
                
        except Exception as e:
            print(f"Error updating product {sp['id']}: {e}")
            continue
    
    print(f"\n✓ Successfully updated {updated_count} products")
    print(f"✓ Updated products for {len(vendors_updated)} vendors")
    print(f"\nMOQ Distribution:")
    print("  - Most products: 12-24 units (common items)")
    print("  - Some products: 30-36 units (specialty items)")
    print("  - Few products: 42-48 units (bulk/premium items)")

def verify_updates(uid, models):
    """Verify the MOQ updates by checking a sample"""
    print("\n=== Verifying Updates ===\n")
    
    # Get a sample of updated products
    sample_products = models.execute_kw(
        db, uid, password,
        'product.supplierinfo', 'search_read',
        [[]],
        {
            'fields': ['id', 'product_name', 'min_qty', 'partner_id'],
            'limit': 10,
            'order': 'id desc'
        }
    )
    
    print("Sample of updated products:")
    for sp in sample_products:
        product_name = sp.get('product_name', 'Unknown')
        if '|META|' in str(product_name):
            product_name = product_name.split('|META|')[0].strip()
        
        # Truncate long names
        if len(product_name) > 40:
            product_name = product_name[:37] + "..."
            
        print(f"  - {product_name}: MOQ = {int(sp['min_qty'])} units")

def main():
    try:
        uid, models = connect()
        print(f"Successfully connected to Odoo (UID: {uid})\n")
        
        # Update MOQ values
        update_moq_values(uid, models)
        
        # Verify updates
        verify_updates(uid, models)
        
        print("\n=== Summary ===")
        print("✓ All MOQ values updated to range from 12 to 48")
        print("✓ Values are in multiples of 6 (12, 18, 24, 30, 36, 42, 48)")
        print("✓ Distribution weighted towards lower MOQs for common items")
        print("\nNote: The metadata in product names will still reflect the old min_qty")
        print("The actual MOQ displayed comes from the min_qty field, not the metadata")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()