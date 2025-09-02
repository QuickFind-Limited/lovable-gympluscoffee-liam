#!/usr/bin/env python3
"""
Test script for updating minimum level in product metadata
This tests updating the JSON metadata stored in product_name field
"""

import xmlrpc.client
import json
import sys

# Odoo connection details (from .env)
odoo_url = 'https://source-gym-plus-coffee.odoo.com/'
db = 'Gym Plus Coffee'
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

def get_product_by_id(uid, models, product_id):
    """Get a specific supplier product by ID"""
    product = models.execute_kw(
        db, uid, password,
        'product.supplierinfo', 'read',
        [[product_id]],
        {'fields': ['id', 'product_name', 'product_code', 'min_qty', 'partner_id']}
    )
    
    if product:
        return product[0]
    return None

def update_minimum_level(uid, models, product_id, new_min_level):
    """Update the minimum level in the JSON metadata"""
    # Get current product
    product = get_product_by_id(uid, models, product_id)
    if not product:
        print(f"Product ID {product_id} not found")
        return False
    
    product_name = product.get('product_name', '')
    print(f"\nOriginal product name: {product_name}")
    
    # Check if it has metadata
    if '|META|' in product_name:
        # Parse existing metadata
        parts = product_name.split('|META|')
        if len(parts) == 2:
            clean_name = parts[0].strip()
            try:
                # Parse and update metadata
                metadata = json.loads(parts[1])
                old_min_level = metadata.get('minimum_level', 'Not set')
                metadata['minimum_level'] = new_min_level
                
                # Reconstruct product name with updated metadata
                updated_name = f"{clean_name} |META|{json.dumps(metadata, separators=(',', ':'))}"
                
                print(f"Old minimum level: {old_min_level}")
                print(f"New minimum level: {new_min_level}")
                print(f"Updated product name: {updated_name}")
                
                # Update in Odoo
                result = models.execute_kw(
                    db, uid, password,
                    'product.supplierinfo', 'write',
                    [[product_id], {'product_name': updated_name}]
                )
                
                if result:
                    print("✓ Successfully updated minimum level")
                    return True
                else:
                    print("✗ Failed to update in Odoo")
                    return False
                
            except json.JSONDecodeError as e:
                print(f"Error parsing metadata: {e}")
                return False
    else:
        print("Product doesn't have metadata yet. Creating new metadata...")
        
        # Create new metadata
        metadata = {
            'pack_size': 1,
            'minimum_level': new_min_level,
            'qty_available': 0,
            'virtual_available': 0
        }
        
        # Add metadata to product name
        updated_name = f"{product_name} |META|{json.dumps(metadata, separators=(',', ':'))}"
        
        # Update in Odoo
        result = models.execute_kw(
            db, uid, password,
            'product.supplierinfo', 'write',
            [[product_id], {'product_name': updated_name}]
        )
        
        if result:
            print("✓ Successfully added metadata with minimum level")
            return True
        else:
            print("✗ Failed to update in Odoo")
            return False

def test_update_flow():
    """Test the complete update flow"""
    try:
        uid, models = connect()
        print(f"Successfully connected to Odoo (UID: {uid})\n")
        
        # Get a sample product to test with
        print("=== Finding a Product to Test ===")
        sample_products = models.execute_kw(
            db, uid, password,
            'product.supplierinfo', 'search_read',
            [[['product_name', 'like', '|META|']]],
            {
                'fields': ['id', 'product_name', 'partner_id'],
                'limit': 5
            }
        )
        
        if not sample_products:
            print("No products with metadata found. Let's add metadata to one...")
            # Get any product
            sample_products = models.execute_kw(
                db, uid, password,
                'product.supplierinfo', 'search_read',
                [[]],
                {
                    'fields': ['id', 'product_name', 'partner_id'],
                    'limit': 5
                }
            )
        
        if sample_products:
            # Test with first product
            test_product = sample_products[0]
            product_id = test_product['id']
            
            print(f"\nTesting with Product ID: {product_id}")
            print(f"Partner: {test_product['partner_id']}")
            
            # Test updating minimum level
            new_min_level = 75  # Set new minimum level
            success = update_minimum_level(uid, models, product_id, new_min_level)
            
            if success:
                # Verify the update
                print("\n=== Verifying Update ===")
                updated_product = get_product_by_id(uid, models, product_id)
                if updated_product:
                    updated_name = updated_product['product_name']
                    if '|META|' in updated_name:
                        parts = updated_name.split('|META|')
                        if len(parts) == 2:
                            metadata = json.loads(parts[1])
                            print(f"Verified minimum level: {metadata.get('minimum_level')}")
                            print("✓ Update verified successfully!")
                
        else:
            print("No products found to test with")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def update_specific_product(product_id, new_min_level):
    """Update a specific product's minimum level"""
    try:
        uid, models = connect()
        print(f"Connected to Odoo (UID: {uid})")
        
        success = update_minimum_level(uid, models, product_id, new_min_level)
        return success
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) == 3:
        # Usage: python test-update-min-level.py <product_id> <new_min_level>
        product_id = int(sys.argv[1])
        new_min_level = int(sys.argv[2])
        update_specific_product(product_id, new_min_level)
    else:
        # Run test flow
        print("Running test flow...")
        test_update_flow()