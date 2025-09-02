#!/usr/bin/env python3
"""
Fix supplier products and create purchase orders in Odoo
1. Add more supplier-product relationships
2. Create purchase orders
3. Update stock levels
"""

import xmlrpc.client
import random
from datetime import datetime, timedelta

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

def add_more_supplier_relationships(models, uid):
    """Add more supplier-product relationships"""
    print("\n📦 Adding more supplier-product relationships...")
    
    # Get all suppliers
    supplier_ids = models.execute_kw(
        db, uid, password,
        'res.partner', 'search',
        [[['supplier_rank', '>', 0]]],
        {'limit': 20}
    )
    
    # Get all products (limit to 300 for speed)
    product_ids = models.execute_kw(
        db, uid, password,
        'product.product', 'search',
        [[]],
        {'limit': 300}
    )
    
    products = models.execute_kw(
        db, uid, password,
        'product.product', 'read',
        [product_ids],
        {'fields': ['id', 'product_tmpl_id', 'display_name', 'list_price']}
    )
    
    print(f"Found {len(supplier_ids)} suppliers and {len(products)} products")
    
    created = 0
    for supplier_id in supplier_ids:
        # Check existing relationships
        existing_count = models.execute_kw(
            db, uid, password,
            'product.supplierinfo', 'search_count',
            [[['partner_id', '=', supplier_id]]]
        )
        
        if existing_count >= 50:
            print(f"Supplier {supplier_id} already has {existing_count} products, skipping")
            continue
        
        # Add products to reach 50-80 total
        target_count = random.randint(50, 80)
        needed = target_count - existing_count
        
        if needed <= 0:
            continue
        
        # Select random products
        selected_products = random.sample(products, min(needed, len(products)))
        
        print(f"Adding {len(selected_products)} products to supplier {supplier_id}")
        
        for product in selected_products:
            try:
                product_tmpl_id = product['product_tmpl_id'][0] if isinstance(product['product_tmpl_id'], list) else product['product_tmpl_id']
                base_price = product.get('list_price', 50) or 50
                
                # Check if relationship already exists
                existing = models.execute_kw(
                    db, uid, password,
                    'product.supplierinfo', 'search',
                    [[
                        ['partner_id', '=', supplier_id],
                        ['product_tmpl_id', '=', product_tmpl_id]
                    ]],
                    {'limit': 1}
                )
                
                if existing:
                    continue
                
                models.execute_kw(
                    db, uid, password,
                    'product.supplierinfo', 'create',
                    [{
                        'partner_id': supplier_id,
                        'product_tmpl_id': product_tmpl_id,
                        'product_name': product['display_name'],
                        'min_qty': random.choice([1, 5, 10, 20, 50]),
                        'price': round(base_price * random.uniform(0.4, 0.7), 2),
                        'delay': random.randint(1, 14),
                    }]
                )
                created += 1
            except Exception as e:
                pass  # Skip errors silently
    
    print(f"✅ Created {created} new supplier-product relationships")
    return created

def create_purchase_orders(models, uid):
    """Create purchase orders in Odoo"""
    print("\n📋 Creating purchase orders...")
    
    # Get suppliers with products
    supplier_ids = models.execute_kw(
        db, uid, password,
        'res.partner', 'search',
        [[['supplier_rank', '>', 0]]],
        {'limit': 10}
    )
    
    created_orders = []
    
    for supplier_id in supplier_ids:
        # Get supplier products
        supplier_products = models.execute_kw(
            db, uid, password,
            'product.supplierinfo', 'search_read',
            [[['partner_id', '=', supplier_id]]],
            {'fields': ['product_tmpl_id', 'min_qty', 'price'], 'limit': 10}
        )
        
        if not supplier_products:
            continue
        
        # Create purchase order
        order_date = datetime.now() - timedelta(days=random.randint(0, 30))
        
        try:
            order_id = models.execute_kw(
                db, uid, password,
                'purchase.order', 'create',
                [{
                    'partner_id': supplier_id,
                    'date_order': order_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'state': random.choice(['draft', 'sent', 'purchase', 'done']),
                }]
            )
            
            # Add order lines
            for sp in supplier_products[:5]:  # Max 5 products per order
                product_tmpl_id = sp['product_tmpl_id'][0] if isinstance(sp['product_tmpl_id'], list) else sp['product_tmpl_id']
                
                # Get product variant
                product_ids = models.execute_kw(
                    db, uid, password,
                    'product.product', 'search',
                    [[['product_tmpl_id', '=', product_tmpl_id]]],
                    {'limit': 1}
                )
                
                if product_ids:
                    quantity = sp['min_qty'] * random.randint(1, 5)
                    models.execute_kw(
                        db, uid, password,
                        'purchase.order.line', 'create',
                        [{
                            'order_id': order_id,
                            'product_id': product_ids[0],
                            'product_qty': quantity,
                            'price_unit': sp['price'],
                            'date_planned': (order_date + timedelta(days=7)).strftime('%Y-%m-%d'),
                        }]
                    )
            
            created_orders.append(order_id)
            print(f"   Created PO-{order_id} for supplier {supplier_id}")
            
        except Exception as e:
            print(f"   Error creating order: {str(e)}")
    
    print(f"✅ Created {len(created_orders)} purchase orders")
    return created_orders

def update_product_stock_levels(models, uid):
    """Update stock levels for products"""
    print("\n📊 Updating product stock levels...")
    
    # Get products (limit for speed)
    product_ids = models.execute_kw(
        db, uid, password,
        'product.product', 'search',
        [[]],
        {'limit': 100}
    )
    
    # Get default stock location
    location_ids = models.execute_kw(
        db, uid, password,
        'stock.location', 'search',
        [[['usage', '=', 'internal']]],
        {'limit': 1}
    )
    
    if not location_ids:
        print("❌ No stock location found")
        return 0
    
    location_id = location_ids[0]
    updated = 0
    
    for product_id in product_ids:
        try:
            # Create stock quant (inventory)
            qty = random.randint(0, 500)
            
            # Check if quant exists
            existing_quant = models.execute_kw(
                db, uid, password,
                'stock.quant', 'search',
                [[
                    ['product_id', '=', product_id],
                    ['location_id', '=', location_id]
                ]],
                {'limit': 1}
            )
            
            if existing_quant:
                # Update existing
                models.execute_kw(
                    db, uid, password,
                    'stock.quant', 'write',
                    [existing_quant, {'quantity': qty}]
                )
            else:
                # Create new
                models.execute_kw(
                    db, uid, password,
                    'stock.quant', 'create',
                    [{
                        'product_id': product_id,
                        'location_id': location_id,
                        'quantity': qty,
                    }]
                )
            
            updated += 1
            
        except Exception as e:
            pass  # Skip errors
    
    print(f"✅ Updated stock levels for {updated} products")
    return updated

def verify_data(models, uid):
    """Verify the data"""
    print("\n📊 Verifying data...")
    
    # Check supplier products
    supplier_ids = models.execute_kw(
        db, uid, password,
        'res.partner', 'search',
        [[['supplier_rank', '>', 0]]],
        {'limit': 5}
    )
    
    for supplier_id in supplier_ids:
        count = models.execute_kw(
            db, uid, password,
            'product.supplierinfo', 'search_count',
            [[['partner_id', '=', supplier_id]]]
        )
        supplier = models.execute_kw(
            db, uid, password,
            'res.partner', 'read',
            [supplier_id],
            {'fields': ['name']}
        )[0]
        print(f"   {supplier['name']}: {count} products")
    
    # Check purchase orders
    po_count = models.execute_kw(
        db, uid, password,
        'purchase.order', 'search_count',
        [[]]
    )
    print(f"\n   Total purchase orders: {po_count}")
    
    # Check products with stock
    products_with_stock = models.execute_kw(
        db, uid, password,
        'stock.quant', 'search_count',
        [[['quantity', '>', 0]]]
    )
    print(f"   Products with stock: {products_with_stock}")

def main():
    """Main function"""
    print("🔄 Connecting to Odoo...")
    try:
        uid, models = connect_odoo()
        print(f"✅ Connected to Odoo (UID: {uid})")
        
        # Add more supplier relationships
        add_more_supplier_relationships(models, uid)
        
        # Create purchase orders
        create_purchase_orders(models, uid)
        
        # Update stock levels
        update_product_stock_levels(models, uid)
        
        # Verify
        verify_data(models, uid)
        
        print("\n✅ All operations completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()