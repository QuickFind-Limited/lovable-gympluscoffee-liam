#!/usr/bin/env python3
"""
Create comprehensive supplier-product relationships in Odoo
Each supplier will have 50-150 products with realistic distribution
"""

import xmlrpc.client
import random
from typing import List, Dict, Tuple

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

def delete_existing_relationships(models, uid):
    """Delete existing supplier-product relationships"""
    print("🗑️  Deleting existing supplier-product relationships...")
    
    # Find all existing relationships
    existing_ids = models.execute_kw(
        db, uid, password,
        'product.supplierinfo', 'search',
        [[]],
        {'limit': 10000}
    )
    
    if existing_ids:
        # Delete in batches
        batch_size = 100
        for i in range(0, len(existing_ids), batch_size):
            batch = existing_ids[i:i+batch_size]
            models.execute_kw(
                db, uid, password,
                'product.supplierinfo', 'unlink',
                [batch]
            )
            print(f"   Deleted batch {i//batch_size + 1}/{(len(existing_ids) + batch_size - 1)//batch_size}")
    
    print(f"✅ Deleted {len(existing_ids)} existing relationships")
    return len(existing_ids)

def create_supplier_product_relationships(models, uid):
    """Create comprehensive supplier-product relationships"""
    
    # Get all suppliers
    supplier_ids = models.execute_kw(
        db, uid, password,
        'res.partner', 'search',
        [[['supplier_rank', '>', 0]]],
        {'limit': 100}
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
    
    # Get all products
    product_ids = models.execute_kw(
        db, uid, password,
        'product.product', 'search',
        [[]],
        {'limit': 1000}
    )
    
    if not product_ids:
        print("❌ No products found")
        return
    
    # Get product details including templates
    products = models.execute_kw(
        db, uid, password,
        'product.product', 'read',
        [product_ids],
        {'fields': ['id', 'name', 'display_name', 'product_tmpl_id', 'list_price', 'standard_price']}
    )
    
    print(f"✅ Found {len(products)} products")
    
    # Define supplier specializations (some overlap is realistic)
    supplier_specializations = {
        'Apparel': ['Hoodie', 'T-Shirt', 'Shirt', 'Jacket', 'Coat', 'Sweater', 'Cardigan', 'Vest', 'Tank', 'Blouse'],
        'Fashion': ['Dress', 'Skirt', 'Pants', 'Jeans', 'Shorts', 'Leggings', 'Jumpsuit', 'Romper', 'Suit', 'Blazer'],
        'Athletic': ['Sports', 'Performance', 'Training', 'Running', 'Yoga', 'Gym', 'Fitness', 'Athletic', 'Workout', 'Exercise'],
        'Sports Equipment': ['Ball', 'Racket', 'Net', 'Goal', 'Equipment', 'Gear', 'Helmet', 'Pads', 'Gloves', 'Shoes'],
        'Textile': ['Fabric', 'Cotton', 'Wool', 'Silk', 'Polyester', 'Linen', 'Denim', 'Canvas', 'Fleece', 'Jersey'],
        'Clothing Factory': ['Basic', 'Essential', 'Classic', 'Standard', 'Regular', 'Plain', 'Simple', 'Everyday', 'Casual', 'Formal']
    }
    
    # Categorize suppliers
    supplier_categories = {}
    for supplier in suppliers:
        name = supplier['name'].lower()
        categories = []
        for category, keywords in supplier_specializations.items():
            if any(keyword.lower() in name for keyword in category.split()):
                categories.append(category)
        if not categories:
            # Default category for uncategorized suppliers
            categories = ['Clothing Factory']
        supplier_categories[supplier['id']] = categories
    
    # Categorize products
    product_categories = {}
    for product in products:
        name = product['display_name'].lower()
        categories = []
        for category, keywords in supplier_specializations.items():
            if any(keyword.lower() in name for keyword in keywords):
                categories.append(category)
        if not categories:
            # Default category
            categories = ['Clothing Factory']
        product_categories[product['id']] = categories
    
    created_count = 0
    
    for supplier in suppliers:
        supplier_id = supplier['id']
        supplier_name = supplier['name']
        supplier_cats = supplier_categories[supplier_id]
        
        # Select products that match supplier's specialization
        matching_products = []
        partial_matching_products = []
        other_products = []
        
        for product in products:
            product_cats = product_categories[product['id']]
            # Check for category overlap
            overlap = set(supplier_cats) & set(product_cats)
            if overlap:
                matching_products.append(product)
            elif any(cat in ['Clothing Factory', 'Textile'] for cat in supplier_cats):
                # These suppliers can carry more diverse products
                partial_matching_products.append(product)
            else:
                other_products.append(product)
        
        # Determine number of products for this supplier (50-150)
        num_products = random.randint(50, 150)
        
        # Build product list with priority to matching products
        selected_products = []
        
        # First add all matching products (up to limit)
        if matching_products:
            selected_products.extend(matching_products[:num_products])
        
        # If we need more, add partial matches
        if len(selected_products) < num_products and partial_matching_products:
            remaining = num_products - len(selected_products)
            selected_products.extend(random.sample(
                partial_matching_products, 
                min(remaining, len(partial_matching_products))
            ))
        
        # If still need more, add random other products
        if len(selected_products) < num_products and other_products:
            remaining = num_products - len(selected_products)
            selected_products.extend(random.sample(
                other_products,
                min(remaining, len(other_products))
            ))
        
        print(f"\n📦 Creating relationships for {supplier_name}:")
        print(f"   Categories: {', '.join(supplier_cats)}")
        print(f"   Products to add: {len(selected_products)}")
        
        # Create supplier info for selected products
        for product in selected_products:
            # Get product template ID
            product_tmpl_id = product['product_tmpl_id'][0] if isinstance(product['product_tmpl_id'], list) else product['product_tmpl_id']
            
            # Generate realistic supplier data
            base_price = product.get('list_price', 50) or 50
            
            # Supplier price is typically 40-70% of list price (wholesale)
            supplier_price = round(base_price * random.uniform(0.4, 0.7), 2)
            
            # MOQ based on price (cheaper items have higher MOQ)
            if supplier_price < 20:
                moq_options = [50, 100, 200, 500]
            elif supplier_price < 50:
                moq_options = [10, 20, 50, 100]
            elif supplier_price < 100:
                moq_options = [5, 10, 20, 50]
            else:
                moq_options = [1, 5, 10, 20]
            
            moq = random.choice(moq_options)
            
            # Lead time based on supplier type and MOQ
            if 'Express' in supplier_name:
                lead_time = random.randint(1, 7)  # Express suppliers are faster
            elif 'Global' in supplier_name:
                lead_time = random.randint(7, 21)  # Global suppliers take longer
            else:
                lead_time = random.randint(3, 14)  # Standard lead time
            
            # Create the supplier info
            try:
                supplier_info_id = models.execute_kw(
                    db, uid, password,
                    'product.supplierinfo', 'create',
                    [{
                        'partner_id': supplier_id,
                        'product_tmpl_id': product_tmpl_id,
                        'product_name': product['display_name'],
                        'min_qty': moq,
                        'price': supplier_price,
                        'delay': lead_time,
                    }]
                )
                created_count += 1
            except Exception as e:
                print(f"   ⚠️  Error creating relationship for product {product['id']}: {str(e)}")
        
        print(f"   ✅ Created {len(selected_products)} relationships")
    
    return created_count

def verify_relationships(models, uid):
    """Verify the created relationships"""
    print("\n📊 Verifying supplier-product relationships:")
    
    # Get all suppliers
    supplier_ids = models.execute_kw(
        db, uid, password,
        'res.partner', 'search',
        [[['supplier_rank', '>', 0]]],
        {'limit': 100}
    )
    
    suppliers = models.execute_kw(
        db, uid, password,
        'res.partner', 'read',
        [supplier_ids],
        {'fields': ['id', 'name']}
    )
    
    total_relationships = 0
    min_products = float('inf')
    max_products = 0
    
    for supplier in suppliers[:20]:  # Check first 20 suppliers
        count = models.execute_kw(
            db, uid, password,
            'product.supplierinfo', 'search_count',
            [[['partner_id', '=', supplier['id']]]]
        )
        total_relationships += count
        min_products = min(min_products, count)
        max_products = max(max_products, count)
        print(f"   {supplier['name']}: {count} products")
    
    # Get total count
    total_count = models.execute_kw(
        db, uid, password,
        'product.supplierinfo', 'search_count',
        [[]]
    )
    
    print(f"\n📈 Summary:")
    print(f"   Total supplier-product relationships: {total_count}")
    print(f"   Average products per supplier: {total_count // len(suppliers) if suppliers else 0}")
    print(f"   Min products per supplier: {min_products}")
    print(f"   Max products per supplier: {max_products}")

def main():
    """Main function"""
    print("🔄 Connecting to Odoo...")
    try:
        uid, models = connect_odoo()
        print(f"✅ Connected to Odoo (UID: {uid})")
        
        # Delete existing relationships
        deleted = delete_existing_relationships(models, uid)
        
        # Create comprehensive relationships
        print("\n🏗️  Creating comprehensive supplier-product relationships...")
        created = create_supplier_product_relationships(models, uid)
        
        print(f"\n✅ Successfully created {created} supplier-product relationships")
        
        # Verify the results
        verify_relationships(models, uid)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()