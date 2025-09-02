#!/usr/bin/env python3
"""
Create more purchase orders in Odoo
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

def create_purchase_orders(models, uid, count=20):
    """Create multiple purchase orders"""
    print(f"📋 Creating {count} purchase orders...")
    
    # Get suppliers
    supplier_ids = models.execute_kw(
        db, uid, password,
        'res.partner', 'search',
        [[['supplier_rank', '>', 0]]],
        {'limit': 50}
    )
    
    if not supplier_ids:
        print("❌ No suppliers found")
        return []
    
    suppliers = models.execute_kw(
        db, uid, password,
        'res.partner', 'read',
        [supplier_ids],
        {'fields': ['id', 'name']}
    )
    
    # Get products
    product_ids = models.execute_kw(
        db, uid, password,
        'product.product', 'search',
        [[['purchase_ok', '=', True]]],
        {'limit': 200}
    )
    
    if not product_ids:
        # If no purchasable products, get any products
        product_ids = models.execute_kw(
            db, uid, password,
            'product.product', 'search',
            [[]],
            {'limit': 200}
        )
    
    products = models.execute_kw(
        db, uid, password,
        'product.product', 'read',
        [product_ids],
        {'fields': ['id', 'name', 'list_price', 'standard_price']}
    )
    
    print(f"Found {len(suppliers)} suppliers and {len(products)} products")
    
    created_orders = []
    statuses = ['draft', 'sent', 'purchase', 'done', 'cancel']
    
    for i in range(count):
        try:
            # Random supplier
            supplier = random.choice(suppliers)
            supplier_id = supplier['id']
            supplier_name = supplier['name']
            
            # Random date in the last 60 days
            days_ago = random.randint(0, 60)
            order_date = datetime.now() - timedelta(days=days_ago)
            
            # Random status with weighted probability
            status_weights = [30, 25, 25, 15, 5]  # draft, sent, purchase, done, cancel
            status = random.choices(statuses, weights=status_weights)[0]
            
            # Create purchase order
            order_vals = {
                'partner_id': supplier_id,
                'date_order': order_date.strftime('%Y-%m-%d %H:%M:%S'),
                'state': 'draft',  # Always create as draft first
            }
            
            order_id = models.execute_kw(
                db, uid, password,
                'purchase.order', 'create',
                [order_vals]
            )
            
            # Add order lines (2-8 products per order)
            num_products = random.randint(2, 8)
            selected_products = random.sample(products, min(num_products, len(products)))
            
            total_amount = 0
            for product in selected_products:
                quantity = random.randint(5, 100)
                # Use standard_price if available, otherwise use list_price * 0.6
                price = product.get('standard_price', 0) or (product.get('list_price', 10) * 0.6)
                
                line_vals = {
                    'order_id': order_id,
                    'product_id': product['id'],
                    'name': product['name'],
                    'product_qty': quantity,
                    'price_unit': round(price, 2),
                    'date_planned': (order_date + timedelta(days=7)).strftime('%Y-%m-%d'),
                }
                
                models.execute_kw(
                    db, uid, password,
                    'purchase.order.line', 'create',
                    [line_vals]
                )
                
                total_amount += quantity * price
            
            # Update order state if needed
            if status != 'draft':
                try:
                    if status in ['sent', 'purchase', 'done']:
                        # Confirm the order
                        models.execute_kw(
                            db, uid, password,
                            'purchase.order', 'button_confirm',
                            [[order_id]]
                        )
                    
                    if status == 'done':
                        # Try to mark as done (may not work depending on workflow)
                        models.execute_kw(
                            db, uid, password,
                            'purchase.order', 'button_done',
                            [[order_id]]
                        )
                except:
                    # If state transition fails, leave it as is
                    pass
            
            # Get the created order details
            order_data = models.execute_kw(
                db, uid, password,
                'purchase.order', 'read',
                [[order_id]],
                {'fields': ['name', 'state', 'amount_total']}
            )[0]
            
            print(f"   ✅ Created {order_data['name']} for {supplier_name}: "
                  f"${order_data.get('amount_total', total_amount):.2f} "
                  f"(Status: {order_data['state']})")
            
            created_orders.append(order_id)
            
        except Exception as e:
            print(f"   ⚠️ Error creating order: {str(e)}")
    
    return created_orders

def verify_orders(models, uid):
    """Verify the purchase orders"""
    print("\n📊 Verifying purchase orders...")
    
    # Count total purchase orders
    total_count = models.execute_kw(
        db, uid, password,
        'purchase.order', 'search_count',
        [[]]
    )
    
    print(f"   Total purchase orders: {total_count}")
    
    # Count by status
    for status in ['draft', 'sent', 'purchase', 'done', 'cancel']:
        count = models.execute_kw(
            db, uid, password,
            'purchase.order', 'search_count',
            [[['state', '=', status]]]
        )
        print(f"   {status.capitalize()}: {count}")
    
    # Get recent orders
    recent_ids = models.execute_kw(
        db, uid, password,
        'purchase.order', 'search',
        [[]],
        {'limit': 5, 'order': 'create_date desc'}
    )
    
    if recent_ids:
        recent_orders = models.execute_kw(
            db, uid, password,
            'purchase.order', 'read',
            [recent_ids],
            {'fields': ['name', 'partner_id', 'amount_total', 'state']}
        )
        
        print("\n   Recent orders:")
        for order in recent_orders:
            partner_name = order['partner_id'][1] if isinstance(order['partner_id'], list) else 'Unknown'
            print(f"      {order['name']}: {partner_name} - "
                  f"${order.get('amount_total', 0):.2f} ({order['state']})")

def main():
    """Main function"""
    print("🔄 Connecting to Odoo...")
    try:
        uid, models = connect_odoo()
        print(f"✅ Connected to Odoo (UID: {uid})")
        
        # Create purchase orders
        created_orders = create_purchase_orders(models, uid, count=30)
        
        print(f"\n✅ Successfully created {len(created_orders)} purchase orders")
        
        # Verify
        verify_orders(models, uid)
        
        print("\n🎉 All operations completed successfully!")
        print("   The Orders page should now show more purchase orders.")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()