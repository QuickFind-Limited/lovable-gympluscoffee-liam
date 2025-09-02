#!/usr/bin/env python3
"""
Create comprehensive supplier-product relationships in Odoo (optimized batch version)
Each supplier will have 50-100 products with realistic distribution
"""

import xmlrpc.client
import random
from typing import List, Dict

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

def create_supplier_product_relationships_batch(models, uid):
    """Create comprehensive supplier-product relationships using batch operations"""
    
    # Get all suppliers
    supplier_ids = models.execute_kw(
        db, uid, password,
        'res.partner', 'search',
        [[['supplier_rank', '>', 0]]],
        {'limit': 20}
    )
    
    suppliers = models.execute_kw(
        db, uid, password,
        'res.partner', 'read',
        [supplier_ids],
        {'fields': ['id', 'name']}
    )
    
    print(f"✅ Found {len(suppliers)} suppliers")
    
    # Get all products
    product_ids = models.execute_kw(
        db, uid, password,
        'product.product', 'search',
        [[]],
        {'limit': 500}
    )
    
    products = models.execute_kw(
        db, uid, password,
        'product.product', 'read',
        [product_ids],
        {'fields': ['id', 'name', 'display_name', 'product_tmpl_id', 'list_price']}
    )
    
    print(f"✅ Found {len(products)} products")
    
    # Delete existing relationships first
    print("🗑️  Cleaning up existing relationships...")
    existing_ids = models.execute_kw(
        db, uid, password,
        'product.supplierinfo', 'search',
        [[]],
        {'limit': 5000}
    )
    
    if existing_ids:
        # Delete in smaller batches
        for i in range(0, len(existing_ids), 50):
            batch = existing_ids[i:i+50]
            models.execute_kw(
                db, uid, password,
                'product.supplierinfo', 'unlink',
                [batch]
            )
        print(f"✅ Deleted {len(existing_ids)} existing relationships")
    
    # Create relationships
    total_created = 0
    relationships_to_create = []
    
    for supplier in suppliers:
        supplier_id = supplier['id']
        supplier_name = supplier['name']
        
        # Each supplier gets 50-100 random products
        num_products = random.randint(50, 100)
        selected_products = random.sample(products, min(num_products, len(products)))
        
        print(f"\n📦 Preparing {len(selected_products)} products for {supplier_name}")
        
        for product in selected_products:
            # Get product template ID
            product_tmpl_id = product['product_tmpl_id'][0] if isinstance(product['product_tmpl_id'], list) else product['product_tmpl_id']
            
            # Generate realistic supplier data
            base_price = product.get('list_price', 50) or 50
            supplier_price = round(base_price * random.uniform(0.4, 0.7), 2)
            
            # MOQ based on price
            if supplier_price < 20:
                moq = random.choice([50, 100, 200])
            elif supplier_price < 50:
                moq = random.choice([10, 20, 50])
            else:
                moq = random.choice([1, 5, 10])
            
            # Lead time
            if 'Express' in supplier_name:
                lead_time = random.randint(1, 7)
            elif 'Global' in supplier_name:
                lead_time = random.randint(7, 21)
            else:
                lead_time = random.randint(3, 14)
            
            relationships_to_create.append({
                'partner_id': supplier_id,
                'product_tmpl_id': product_tmpl_id,
                'product_name': product['display_name'],
                'min_qty': moq,
                'price': supplier_price,
                'delay': lead_time,
            })
    
    # Create relationships in batches
    print(f"\n🏗️  Creating {len(relationships_to_create)} relationships in batches...")
    batch_size = 50
    
    for i in range(0, len(relationships_to_create), batch_size):
        batch = relationships_to_create[i:i+batch_size]
        try:
            # Create multiple records at once
            for record in batch:
                models.execute_kw(
                    db, uid, password,
                    'product.supplierinfo', 'create',
                    [record]
                )
            total_created += len(batch)
            print(f"   Created batch {i//batch_size + 1}: {total_created}/{len(relationships_to_create)}")
        except Exception as e:
            print(f"   ⚠️  Error in batch: {str(e)}")
    
    return total_created

def verify_relationships(models, uid):
    """Verify the created relationships"""
    print("\n📊 Verifying supplier-product relationships:")
    
    supplier_ids = models.execute_kw(
        db, uid, password,
        'res.partner', 'search',
        [[['supplier_rank', '>', 0]]],
        {'limit': 20}
    )
    
    suppliers = models.execute_kw(
        db, uid, password,
        'res.partner', 'read',
        [supplier_ids],
        {'fields': ['id', 'name']}
    )
    
    for supplier in suppliers:
        count = models.execute_kw(
            db, uid, password,
            'product.supplierinfo', 'search_count',
            [[['partner_id', '=', supplier['id']]]]
        )
        print(f"   {supplier['name']}: {count} products")
    
    total_count = models.execute_kw(
        db, uid, password,
        'product.supplierinfo', 'search_count',
        [[]]
    )
    
    print(f"\n📈 Total supplier-product relationships: {total_count}")
    print(f"   Average per supplier: {total_count // len(suppliers) if suppliers else 0}")

def main():
    """Main function"""
    print("🔄 Connecting to Odoo...")
    try:
        uid, models = connect_odoo()
        print(f"✅ Connected to Odoo (UID: {uid})")
        
        # Create relationships
        created = create_supplier_product_relationships_batch(models, uid)
        print(f"\n✅ Successfully created {created} supplier-product relationships")
        
        # Verify
        verify_relationships(models, uid)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()