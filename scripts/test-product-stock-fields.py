#!/usr/bin/env python3
"""
Test script to fetch product stock fields from Odoo API
Tests product.product fields for available quantities and packaging info
"""

import xmlrpc.client
import json
from datetime import datetime

# Odoo connection details
odoo_url = 'https://source-animalfarmacy.odoo.com'
db = 'source-animalfarmacy'
username = 'admin@quickfindai.com'
password = 'BJ62wX2J4yzjS$i'

def connect():
    """Connect to Odoo and authenticate"""
    # Connect to common endpoint for authentication
    common = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})
    
    if not uid:
        raise Exception("Failed to authenticate with Odoo")
    
    # Connect to object endpoint for operations
    models = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/object')
    
    return uid, models

def test_product_fields(uid, models):
    """Test fetching product fields including stock quantities"""
    print("=== Testing Product Stock Fields ===\n")
    
    # First, get some supplier products
    supplier_products = models.execute_kw(
        db, uid, password,
        'product.supplierinfo', 'search_read',
        [[]], # All supplier products
        {
            'fields': ['id', 'product_id', 'product_name', 'min_qty'],
            'limit': 5
        }
    )
    
    print("Sample supplier products:")
    for sp in supplier_products:
        print(f"  - {sp['product_name']} (Product ID: {sp['product_id']})")
    
    if supplier_products and supplier_products[0]['product_id']:
        product_id = supplier_products[0]['product_id'][0] if isinstance(supplier_products[0]['product_id'], list) else supplier_products[0]['product_id']
        
        print(f"\nFetching detailed info for product ID: {product_id}")
        
        # Get product details with stock fields
        product_details = models.execute_kw(
            db, uid, password,
            'product.product', 'read',
            [[product_id]],
            {
                'fields': [
                    'name',
                    'default_code',
                    'qty_available',
                    'virtual_available',
                    'incoming_qty',
                    'outgoing_qty',
                    'free_qty',
                    'uom_id',
                    'list_price',
                    'standard_price',
                    'type',
                    'tracking',
                    'barcode'
                ]
            }
        )
        
        if product_details:
            print("\nProduct Details:")
            for key, value in product_details[0].items():
                print(f"  {key}: {value}")
    
    # Check for warehouse orderpoint (reorder rules)
    print("\n=== Testing Warehouse Orderpoint (Reorder Rules) ===")
    try:
        # First check what fields are available
        orderpoint_fields = models.execute_kw(
            db, uid, password,
            'stock.warehouse.orderpoint', 'fields_get',
            [],
            {'attributes': ['string', 'type']}
        )
        print("Available orderpoint fields:", list(orderpoint_fields.keys())[:10], "...")
        
        # Try with basic fields
        orderpoints = models.execute_kw(
            db, uid, password,
            'stock.warehouse.orderpoint', 'search_read',
            [[]],
            {
                'fields': ['product_id', 'product_min_qty', 'product_max_qty'],
                'limit': 5
            }
        )
        
        if orderpoints:
            print("\nSample reorder rules:")
            for op in orderpoints:
                print(f"  Product: {op['product_id']}")
                print(f"    Min Qty: {op['product_min_qty']}")
                print(f"    Max Qty: {op['product_max_qty']}")
        else:
            print("No reorder rules found")
    except Exception as e:
        print(f"Error accessing orderpoint: {e}")
    
    # Check for product packaging
    print("\n=== Testing Product Packaging ===")
    try:
        packagings = models.execute_kw(
            db, uid, password,
            'product.packaging', 'search_read',
            [[]],
            {
                'fields': ['name', 'product_id', 'qty'],
                'limit': 5
            }
        )
        
        if packagings:
            print("\nSample packaging configurations:")
            for pkg in packagings:
                print(f"  {pkg['name']} - Product: {pkg['product_id']}, Qty: {pkg['qty']}")
        else:
            print("No packaging configurations found")
    except Exception as e:
        print(f"Error accessing packaging: {e}")
        print("Packaging model might not be available or accessible")

def test_extended_supplier_products(uid, models):
    """Test fetching supplier products with extended fields"""
    print("\n=== Testing Extended Supplier Product Query ===")
    
    # Get supplier products with related product details
    supplier_products = models.execute_kw(
        db, uid, password,
        'product.supplierinfo', 'search_read',
        [[]],
        {
            'fields': [
                'id',
                'product_id',
                'product_name',
                'product_code',
                'min_qty',
                'price',
                'delay',
                'partner_id'
            ],
            'limit': 3
        }
    )
    
    print("\nSupplier products with stock info:")
    for sp in supplier_products:
        print(f"\nSupplier: {sp['partner_id']}")
        print(f"Product: {sp['product_name']} ({sp['product_code']})")
        print(f"MOQ: {sp['min_qty']}")
        
        # Get stock info for this product
        if sp['product_id']:
            product_id = sp['product_id'][0] if isinstance(sp['product_id'], list) else sp['product_id']
            
            product_stock = models.execute_kw(
                db, uid, password,
                'product.product', 'read',
                [[product_id]],
                {
                    'fields': ['qty_available', 'virtual_available']
                }
            )
            
            if product_stock:
                print(f"Available: {product_stock[0]['qty_available']}")
                print(f"Forecast: {product_stock[0]['virtual_available']}")

def main():
    try:
        uid, models = connect()
        print(f"Successfully connected to Odoo (UID: {uid})\n")
        
        test_product_fields(uid, models)
        test_extended_supplier_products(uid, models)
        
        print("\n=== Field Mapping Summary ===")
        print("✓ Available → product.product.qty_available")
        print("✓ Forecast → product.product.virtual_available")
        print("✓ MOQ → product.supplierinfo.min_qty (already exists)")
        print("? Minimum Level → stock.warehouse.orderpoint.product_min_qty (if configured)")
        print("? Pack Size → product.packaging.qty (if configured)")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()