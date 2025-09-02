#!/usr/bin/env python3
"""
Create supplier-product relationships in Odoo for testing
"""

import xmlrpc.client
import random
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

def get_suppliers(models, uid) -> List[Dict[str, Any]]:
    """Get all suppliers"""
    supplier_ids = models.execute_kw(
        db, uid, password,
        'res.partner', 'search',
        [[['supplier_rank', '>', 0]]],
        {'limit': 20}
    )
    
    if not supplier_ids:
        return []
    
    suppliers = models.execute_kw(
        db, uid, password,
        'res.partner', 'read',
        [supplier_ids],
        {'fields': ['id', 'name', 'supplier_rank']}
    )
    
    return suppliers

def get_products(models, uid, limit: int = 100) -> List[Dict[str, Any]]:
    """Get products"""
    product_ids = models.execute_kw(
        db, uid, password,
        'product.product', 'search',
        [[]],
        {'limit': limit}
    )
    
    if not product_ids:
        return []
    
    products = models.execute_kw(
        db, uid, password,
        'product.product', 'read',
        [product_ids],
        {'fields': ['id', 'name', 'product_tmpl_id', 'list_price', 'default_code']}
    )
    
    return products

def check_existing_supplierinfo(models, uid, supplier_id: int, product_tmpl_id: int) -> bool:
    """Check if supplier info already exists"""
    existing_ids = models.execute_kw(
        db, uid, password,
        'product.supplierinfo', 'search',
        [[
            ['partner_id', '=', supplier_id],
            ['product_tmpl_id', '=', product_tmpl_id]
        ]]
    )
    
    return len(existing_ids) > 0

def create_supplier_relationships(models, uid, suppliers: List[Dict], products: List[Dict]):
    """Create supplier-product relationships"""
    created_count = 0
    skipped_count = 0
    
    # Distribute products among suppliers
    products_per_supplier = len(products) // len(suppliers) if suppliers else 0
    
    if products_per_supplier < 1:
        products_per_supplier = 10  # Minimum products per supplier
    
    for i, supplier in enumerate(suppliers):
        # Assign a subset of products to each supplier
        start_idx = (i * products_per_supplier) % len(products)
        end_idx = min(start_idx + products_per_supplier, len(products))
        
        # If we've wrapped around, also include products from the beginning
        if end_idx <= start_idx:
            supplier_products = products[start_idx:] + products[:end_idx]
        else:
            supplier_products = products[start_idx:end_idx]
        
        # Add some random products for variety
        random_products = random.sample(products, min(5, len(products)))
        supplier_products.extend(random_products)
        
        # Remove duplicates
        seen = set()
        unique_products = []
        for p in supplier_products:
            if p['id'] not in seen:
                seen.add(p['id'])
                unique_products.append(p)
        
        print(f"\n📦 Assigning {len(unique_products)} products to {supplier['name']} (ID: {supplier['id']})")
        
        for product in unique_products:
            # Extract product template ID
            product_tmpl_id = product['product_tmpl_id']
            if isinstance(product_tmpl_id, list):
                product_tmpl_id = product_tmpl_id[0]
            
            # Check if relationship already exists
            if check_existing_supplierinfo(models, uid, supplier['id'], product_tmpl_id):
                print(f"  ⏭️  Skipping {product['name']} - relationship already exists")
                skipped_count += 1
                continue
            
            # Create supplier info
            try:
                # Generate realistic supplier data
                base_price = product.get('list_price', 10.0) or 10.0
                supplier_price = base_price * random.uniform(0.6, 0.9)  # Supplier price is 60-90% of list price
                min_qty = random.choice([1, 5, 10, 20, 50, 100])
                delay = random.choice([1, 3, 5, 7, 14, 21])  # Lead time in days
                
                supplier_info = {
                    'partner_id': supplier['id'],
                    'product_tmpl_id': product_tmpl_id,
                    'product_name': product['name'],
                    'product_code': product.get('default_code') or f"SUP-{product['id']}",
                    'min_qty': min_qty,
                    'price': round(supplier_price, 2),
                    'delay': delay,
                }
                
                result = models.execute_kw(
                    db, uid, password,
                    'product.supplierinfo', 'create',
                    [supplier_info]
                )
                
                if result:
                    print(f"  ✅ Created: {product['name']} - MOQ: {min_qty}, Price: ${supplier_price:.2f}, Lead: {delay}d")
                    created_count += 1
                else:
                    print(f"  ❌ Failed to create relationship for {product['name']}")
                    
            except Exception as e:
                print(f"  ❌ Error creating relationship for {product['name']}: {str(e)}")
    
    return created_count, skipped_count

def main():
    """Main function"""
    print("🔄 Connecting to Odoo...")
    try:
        uid, models = connect_odoo()
        print(f"✅ Connected to Odoo (UID: {uid})")
        
        # Get suppliers
        print("\n📋 Fetching suppliers...")
        suppliers = get_suppliers(models, uid)
        print(f"✅ Found {len(suppliers)} suppliers")
        
        if not suppliers:
            print("❌ No suppliers found. Please create suppliers first.")
            return
        
        # Get products
        print("\n📋 Fetching products...")
        products = get_products(models, uid, limit=100)
        print(f"✅ Found {len(products)} products")
        
        if not products:
            print("❌ No products found. Please create products first.")
            return
        
        # Create relationships
        print("\n🔗 Creating supplier-product relationships...")
        created, skipped = create_supplier_relationships(models, uid, suppliers, products)
        
        print(f"\n📊 Summary:")
        print(f"  ✅ Created: {created} relationships")
        print(f"  ⏭️  Skipped: {skipped} (already existed)")
        print(f"  📦 Total: {created + skipped} processed")
        
        # Verify creation
        print("\n🔍 Verifying supplier product counts...")
        for supplier in suppliers[:5]:  # Check first 5 suppliers
            count = models.execute_kw(
                db, uid, password,
                'product.supplierinfo', 'search_count',
                [[['partner_id', '=', supplier['id']]]]
            )
            print(f"  {supplier['name']}: {count} products")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()