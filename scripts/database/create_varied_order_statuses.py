#!/usr/bin/env python3
"""
Create varied order statuses in Odoo by properly transitioning through workflows
"""
import xmlrpc.client
import ssl
import sys
from datetime import datetime, timedelta
import random

# Disable SSL verification for development
ssl._create_default_https_context = ssl._create_unverified_context

# Odoo connection details
ODOO_URL = "https://source-animalfarmacy.odoo.com/"
ODOO_DB = "source-animalfarmacy"
ODOO_USERNAME = "admin@quickfindai.com"
ODOO_PASSWORD = "BJ62wX2J4yzjS$i"

def connect_odoo():
    """Connect to Odoo and authenticate"""
    try:
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}xmlrpc/2/common')
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
        
        if not uid:
            print("Authentication failed!")
            return None, None
            
        print(f"✓ Connected to Odoo (UID: {uid})")
        
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}xmlrpc/2/object')
        return uid, models
        
    except Exception as e:
        print(f"Connection failed: {e}")
        return None, None

def create_new_orders_with_varied_status(uid, models):
    """Create new orders in different states for demonstration"""
    try:
        # Get suppliers and products
        suppliers = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
            'res.partner', 'search_read',
            [[['supplier_rank', '>', 0]]],
            {'fields': ['id', 'name'], 'limit': 10}
        )
        
        products = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
            'product.product', 'search_read',
            [[['purchase_ok', '=', True]]],
            {'fields': ['id', 'name', 'standard_price'], 'limit': 20}
        )
        
        if not suppliers or not products:
            print("No suppliers or products found!")
            return
        
        print(f"\nFound {len(suppliers)} suppliers and {len(products)} products")
        
        # Create a few new orders in different states
        order_configs = [
            {'supplier_idx': 0, 'target_state': 'sent', 'name': 'Demo RFQ Order'},
            {'supplier_idx': 1, 'target_state': 'done', 'name': 'Demo Completed Order'},
            {'supplier_idx': 2, 'target_state': 'cancel', 'name': 'Demo Cancelled Order'},
        ]
        
        for config in order_configs:
            try:
                supplier = suppliers[config['supplier_idx'] % len(suppliers)]
                print(f"\nCreating order for {supplier['name']} - Target: {config['target_state']}")
                
                # Create order
                order_vals = {
                    'partner_id': supplier['id'],
                    'order_line': []
                }
                
                # Add 2-3 random products
                num_products = random.randint(2, 3)
                selected_products = random.sample(products, min(num_products, len(products)))
                
                for product in selected_products:
                    line_vals = [0, 0, {
                        'product_id': product['id'],
                        'name': product['name'],
                        'product_uom_qty': random.randint(5, 20),
                        'price_unit': product['standard_price'] or random.uniform(10, 100),
                        'date_planned': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }]
                    order_vals['order_line'].append(line_vals)
                
                # Create the order
                order_id = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                    'purchase.order', 'create',
                    [order_vals]
                )
                
                print(f"  ✓ Created order ID: {order_id}")
                
                # Process to target state
                if config['target_state'] == 'sent':
                    # Send RFQ - this might not change state visibly but marks it as sent
                    try:
                        models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                            'purchase.order', 'action_rfq_send',
                            [[order_id]]
                        )
                        print(f"  ✓ Sent RFQ")
                    except:
                        # If action_rfq_send doesn't work, just leave as draft
                        pass
                
                elif config['target_state'] == 'done':
                    # First confirm the order
                    models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'purchase.order', 'button_confirm',
                        [[order_id]]
                    )
                    print(f"  ✓ Confirmed order")
                    
                    # Try to mark as done by receiving products
                    try:
                        # Get the associated pickings
                        order_data = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                            'purchase.order', 'read',
                            [[order_id]],
                            {'fields': ['picking_ids']}
                        )
                        
                        if order_data and order_data[0]['picking_ids']:
                            picking_id = order_data[0]['picking_ids'][0]
                            
                            # Get stock moves
                            moves = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                                'stock.move', 'search_read',
                                [[['picking_id', '=', picking_id]]],
                                {'fields': ['id', 'product_uom_qty']}
                            )
                            
                            # Set done quantities
                            for move in moves:
                                models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                                    'stock.move', 'write',
                                    [[move['id']], {'quantity_done': move['product_uom_qty']}]
                                )
                            
                            # Validate picking
                            models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                                'stock.picking', 'button_validate',
                                [[picking_id]]
                            )
                            print(f"  ✓ Received products - Order should be done")
                    except Exception as e:
                        print(f"  ⚠ Could not complete reception: {str(e)[:50]}")
                
                elif config['target_state'] == 'cancel':
                    # Cancel the order
                    models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'purchase.order', 'button_cancel',
                        [[order_id]]
                    )
                    print(f"  ✓ Cancelled order")
                
            except Exception as e:
                print(f"  ✗ Error creating order: {str(e)[:100]}")
    
    except Exception as e:
        print(f"Error creating new orders: {e}")

def update_existing_orders(uid, models):
    """Update existing draft orders to create more variety"""
    try:
        # Get draft orders
        draft_orders = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
            'purchase.order', 'search_read',
            [[['state', '=', 'draft']]],
            {'fields': ['id', 'name', 'order_line'], 'limit': 10}
        )
        
        # Filter orders with lines
        orders_with_lines = [o for o in draft_orders if o['order_line']]
        
        if orders_with_lines:
            print(f"\nUpdating {len(orders_with_lines[:3])} existing draft orders...")
            
            # Cancel one order
            if len(orders_with_lines) > 0:
                try:
                    models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'purchase.order', 'button_cancel',
                        [[orders_with_lines[0]['id']]]
                    )
                    print(f"  ✓ Cancelled {orders_with_lines[0]['name']}")
                except Exception as e:
                    print(f"  ✗ Failed to cancel: {str(e)[:50]}")
            
            # Send RFQ for another
            if len(orders_with_lines) > 1:
                try:
                    # First confirm to get it out of draft
                    models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'purchase.order', 'button_confirm',
                        [[orders_with_lines[1]['id']]]
                    )
                    print(f"  ✓ Confirmed {orders_with_lines[1]['name']} -> purchase")
                except Exception as e:
                    print(f"  ✗ Failed to process: {str(e)[:50]}")
            
            # Try to complete one more
            if len(orders_with_lines) > 2:
                try:
                    order_id = orders_with_lines[2]['id']
                    order_name = orders_with_lines[2]['name']
                    
                    # Confirm first
                    models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'purchase.order', 'button_confirm',
                        [[order_id]]
                    )
                    
                    # Try to receive products
                    order_data = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'purchase.order', 'read',
                        [[order_id]],
                        {'fields': ['picking_ids']}
                    )
                    
                    if order_data and order_data[0]['picking_ids']:
                        picking_id = order_data[0]['picking_ids'][0]
                        
                        # Process reception
                        picking_data = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                            'stock.picking', 'read',
                            [[picking_id]],
                            {'fields': ['move_lines']}
                        )
                        
                        if picking_data and picking_data[0]['move_lines']:
                            # Mark all moves as done
                            for move_id in picking_data[0]['move_lines']:
                                move_data = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                                    'stock.move', 'read',
                                    [[move_id]],
                                    {'fields': ['product_uom_qty']}
                                )
                                if move_data:
                                    models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                                        'stock.move', 'write',
                                        [[move_id], {'quantity_done': move_data[0]['product_uom_qty']}]
                                    )
                            
                            # Validate
                            models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                                'stock.picking', 'button_validate',
                                [[picking_id]]
                            )
                            print(f"  ✓ Completed reception for {order_name} -> done")
                except Exception as e:
                    print(f"  ✗ Failed to complete: {str(e)[:50]}")
    
    except Exception as e:
        print(f"Error updating existing orders: {e}")

def show_final_status(uid, models):
    """Show final status distribution"""
    try:
        print("\n" + "="*50)
        print("FINAL ORDER STATUS DISTRIBUTION")
        print("="*50)
        
        all_orders = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
            'purchase.order', 'search_read',
            [[]],
            {'fields': ['id', 'name', 'state', 'partner_id'], 'limit': 50, 'order': 'id desc'}
        )
        
        # Count statuses
        status_count = {}
        status_examples = {}
        
        for order in all_orders:
            state = order['state']
            status_count[state] = status_count.get(state, 0) + 1
            
            # Keep example of each status
            if state not in status_examples:
                partner_name = order['partner_id'][1] if order['partner_id'] else 'No partner'
                status_examples[state] = f"{order['name']} ({partner_name})"
        
        # Display status mapping
        print("\nStatus Mapping (Odoo -> UI):")
        print("  - draft     → Pending")
        print("  - sent      → Processed")
        print("  - purchase  → With Supplier")
        print("  - done      → Delivered")
        print("  - cancel    → Pending (Cancelled)")
        
        print("\nCurrent Distribution:")
        for state in ['draft', 'sent', 'purchase', 'done', 'cancel']:
            if state in status_count:
                ui_status = {
                    'draft': 'Pending',
                    'sent': 'Processed',
                    'purchase': 'With Supplier',
                    'done': 'Delivered',
                    'cancel': 'Cancelled'
                }.get(state, state)
                
                print(f"  - {ui_status:20} : {status_count[state]:3} orders  (e.g., {status_examples[state]})")
        
        print("\nSample of recent orders:")
        for order in all_orders[:15]:
            partner_name = order['partner_id'][1] if order['partner_id'] else 'No partner'
            print(f"  - {order['name']:10} : {order['state']:10} ({partner_name})")
            
    except Exception as e:
        print(f"Error showing status: {e}")

def main():
    """Main function"""
    print("Creating varied order statuses in Odoo...")
    uid, models = connect_odoo()
    
    if uid and models:
        # Create new orders with varied statuses
        create_new_orders_with_varied_status(uid, models)
        
        # Update some existing orders
        update_existing_orders(uid, models)
        
        # Show final status distribution
        show_final_status(uid, models)
    else:
        print("Failed to connect to Odoo")
        sys.exit(1)

if __name__ == "__main__":
    main()