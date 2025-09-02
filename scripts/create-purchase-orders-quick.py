#!/usr/bin/env python3
"""
Quickly create purchase orders in Odoo to fix the Orders page
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

def create_purchase_orders(models, uid):
    """Create a few purchase orders quickly"""
    print("📋 Creating purchase orders...")
    
    # Get first 5 suppliers
    supplier_ids = models.execute_kw(
        db, uid, password,
        'res.partner', 'search',
        [[['supplier_rank', '>', 0]]],
        {'limit': 5}
    )
    
    suppliers = models.execute_kw(
        db, uid, password,
        'res.partner', 'read',
        [supplier_ids],
        {'fields': ['id', 'name']}
    )
    
    # Get some products
    product_ids = models.execute_kw(
        db, uid, password,
        'product.product', 'search',
        [[]],
        {'limit': 20}
    )
    
    products = models.execute_kw(
        db, uid, password,
        'product.product', 'read',
        [product_ids],
        {'fields': ['id', 'name', 'list_price']}
    )
    
    created_orders = []
    
    for supplier in suppliers[:3]:  # Create 3 orders
        supplier_id = supplier['id']
        supplier_name = supplier['name']
        
        # Create purchase order
        order_date = datetime.now() - timedelta(days=random.randint(0, 15))
        
        try:
            # Create the order
            order_vals = {
                'partner_id': supplier_id,
                'date_order': order_date.strftime('%Y-%m-%d %H:%M:%S'),
            }
            
            order_id = models.execute_kw(
                db, uid, password,
                'purchase.order', 'create',
                [order_vals]
            )
            
            print(f"   Created order {order_id} for {supplier_name}")
            
            # Add 3-5 order lines
            selected_products = random.sample(products, min(5, len(products)))
            
            for product in selected_products[:3]:
                try:
                    line_vals = {
                        'order_id': order_id,
                        'product_id': product['id'],
                        'name': product['name'],
                        'product_qty': random.randint(10, 100),
                        'price_unit': product.get('list_price', 50) * 0.6,
                        'date_planned': (order_date + timedelta(days=7)).strftime('%Y-%m-%d'),
                    }
                    
                    models.execute_kw(
                        db, uid, password,
                        'purchase.order.line', 'create',
                        [line_vals]
                    )
                    print(f"      Added {product['name']}")
                    
                except Exception as e:
                    print(f"      Error adding line: {str(e)}")
            
            # Confirm some orders
            if random.choice([True, False]):
                try:
                    models.execute_kw(
                        db, uid, password,
                        'purchase.order', 'button_confirm',
                        [[order_id]]
                    )
                    print(f"   Confirmed order {order_id}")
                except:
                    pass
            
            created_orders.append(order_id)
            
        except Exception as e:
            print(f"   Error creating order for {supplier_name}: {str(e)}")
    
    print(f"✅ Created {len(created_orders)} purchase orders")
    
    # Verify orders
    total_orders = models.execute_kw(
        db, uid, password,
        'purchase.order', 'search_count',
        [[]]
    )
    
    print(f"📊 Total purchase orders in system: {total_orders}")
    
    return created_orders

def main():
    """Main function"""
    print("🔄 Connecting to Odoo...")
    try:
        uid, models = connect_odoo()
        print(f"✅ Connected to Odoo (UID: {uid})")
        
        # Create purchase orders
        create_purchase_orders(models, uid)
        
        print("\n✅ Purchase orders created successfully!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()