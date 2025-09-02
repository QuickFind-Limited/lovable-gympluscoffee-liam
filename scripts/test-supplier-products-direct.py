#!/usr/bin/env python3
"""
Test fetching supplier products directly from Odoo
"""

import xmlrpc.client
import json
from typing import List, Dict, Any

# Odoo connection details
url = 'https://source-gym-plus-coffee.odoo.com'
db = 'source-gym-plus-coffee'
username = 'admin@quickfindai.com'
password = 'BJ62wX2J4yzjS$i'

def connect_odoo():
    """Connect to Odoo and return required objects"""
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})
    
    if not uid:
        raise Exception("Failed to authenticate with Odoo")
    
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    
    return uid, models

def test_supplier_products(models, uid, supplier_id: int = 144):
    """Test fetching products for a specific supplier"""
    print(f"\n🔍 Testing supplier ID: {supplier_id}")
    
    # Test different field combinations
    test_cases = [
        {
            'name': 'minimal',
            'fields': ['id']
        },
        {
            'name': 'basic',
            'fields': ['id', 'product_name', 'product_code']
        },
        {
            'name': 'with_price',
            'fields': ['id', 'product_name', 'product_code', 'price', 'min_qty']
        },
        {
            'name': 'with_delay',
            'fields': ['id', 'product_name', 'product_code', 'price', 'min_qty', 'delay']
        },
        {
            'name': 'with_product_id',
            'fields': ['id', 'product_id', 'product_name', 'product_code', 'price', 'min_qty', 'delay']
        },
        {
            'name': 'with_product_tmpl_id',
            'fields': ['id', 'product_tmpl_id', 'product_name', 'product_code', 'price', 'min_qty', 'delay']
        },
        {
            'name': 'all_fields',
            'fields': ['id', 'product_id', 'product_tmpl_id', 'product_name', 'product_code', 'price', 'min_qty', 'delay']
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📊 Test case: {test_case['name']}")
        print(f"   Fields: {test_case['fields']}")
        
        try:
            # Search for supplier products
            products = models.execute_kw(
                db, uid, password,
                'product.supplierinfo', 'search_read',
                [[['partner_id', '=', supplier_id]]],
                {'fields': test_case['fields'], 'limit': 3}
            )
            
            print(f"   ✅ Success! Found {len(products)} products")
            
            if products:
                print(f"   📦 First product:")
                for key, value in products[0].items():
                    print(f"      - {key}: {value}")
                    
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            import traceback
            print(f"   Stack trace: {traceback.format_exc()}")

def test_all_suppliers(models, uid):
    """Test fetching all suppliers and their product counts"""
    print("\n🏢 Testing all suppliers")
    
    # Get all suppliers
    supplier_ids = models.execute_kw(
        db, uid, password,
        'res.partner', 'search',
        [[['supplier_rank', '>', 0]]],
        {'limit': 5}
    )
    
    if not supplier_ids:
        print("❌ No suppliers found")
        return
    
    suppliers = models.execute_kw(
        db, uid, password,
        'res.partner', 'read',
        [supplier_ids],
        {'fields': ['id', 'name', 'supplier_rank']}
    )
    
    print(f"✅ Found {len(suppliers)} suppliers")
    
    for supplier in suppliers:
        # Count products for this supplier
        product_count = models.execute_kw(
            db, uid, password,
            'product.supplierinfo', 'search_count',
            [[['partner_id', '=', supplier['id']]]]
        )
        
        print(f"   - {supplier['name']} (ID: {supplier['id']}): {product_count} products")

def test_product_template_relationship(models, uid, supplier_id: int = 144):
    """Test fetching product template information"""
    print(f"\n🔗 Testing product template relationship for supplier {supplier_id}")
    
    # Get supplier products with product_tmpl_id
    supplier_products = models.execute_kw(
        db, uid, password,
        'product.supplierinfo', 'search_read',
        [[['partner_id', '=', supplier_id]]],
        {'fields': ['id', 'product_tmpl_id', 'product_name', 'min_qty', 'price'], 'limit': 3}
    )
    
    if not supplier_products:
        print("❌ No products found for supplier")
        return
    
    print(f"✅ Found {len(supplier_products)} supplier products")
    
    # Extract template IDs
    template_ids = []
    for sp in supplier_products:
        if sp.get('product_tmpl_id'):
            # product_tmpl_id is returned as [id, name]
            template_id = sp['product_tmpl_id'][0] if isinstance(sp['product_tmpl_id'], list) else sp['product_tmpl_id']
            template_ids.append(template_id)
            print(f"   📦 Supplier product: {sp['product_name']} -> Template ID: {template_id}")
    
    if template_ids:
        print(f"\n🔍 Fetching product details for {len(template_ids)} templates")
        
        # Get product.product records for these templates
        product_ids = models.execute_kw(
            db, uid, password,
            'product.product', 'search',
            [[['product_tmpl_id', 'in', template_ids]]]
        )
        
        if product_ids:
            products = models.execute_kw(
                db, uid, password,
                'product.product', 'read',
                [product_ids],
                {'fields': ['id', 'name', 'display_name', 'default_code', 'qty_available', 'virtual_available']}
            )
            
            print(f"✅ Found {len(products)} product details")
            for product in products[:3]:
                print(f"   📦 Product: {product['display_name']}")
                print(f"      - ID: {product['id']}")
                print(f"      - Code: {product.get('default_code', 'N/A')}")
                print(f"      - Stock: {product.get('qty_available', 0)}")
                print(f"      - Virtual: {product.get('virtual_available', 0)}")

def main():
    """Main function"""
    print("🔄 Connecting to Odoo...")
    try:
        uid, models = connect_odoo()
        print(f"✅ Connected to Odoo (UID: {uid})")
        
        # Test all suppliers first
        test_all_suppliers(models, uid)
        
        # Test specific supplier products with different field combinations
        test_supplier_products(models, uid, supplier_id=144)
        
        # Test product template relationships
        test_product_template_relationship(models, uid, supplier_id=144)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()