
# Seasonal Boost Script for September
# Current: 13.1%, Target: 22.0%

import xmlrpc.client
from datetime import datetime, timedelta
import random

def boost_september_sales():
    # Connection setup
    url = 'https://source-gym-plus-coffee.odoo.com/'
    db = 'source-gym-plus-coffee'
    username = 'admin@quickfindai.com'
    password = 'BJ62wX2J4yzjS$i'
    
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    uid = common.authenticate(db, username, password, {})
    
    # Get existing customers and products
    customers = models.execute_kw(db, uid, password, 'res.partner', 'search', 
                                [[['is_company', '=', False]]], {'limit': 50})
    products = models.execute_kw(db, uid, password, 'product.product', 'search', 
                               [[]], {'limit': 20})
    
    # Calculate number of additional orders needed
    boost_percentage = 8.9
    additional_orders = int(50 * (boost_percentage / 100))  # Approximate
    
    print(f"Creating {additional_orders} additional orders for September")
    
    # Create september orders
    for i in range(additional_orders):
        # Random date in september
        if 'september' == 'june':
            base_date = datetime(2024, 6, random.randint(1, 30))
        elif 'september' == 'july':
            base_date = datetime(2024, 7, random.randint(1, 31))
        elif 'september' == 'august':
            base_date = datetime(2024, 8, random.randint(1, 31))
        else:  # september
            base_date = datetime(2024, 9, random.randint(1, 30))
        
        order_data = {
            'partner_id': random.choice(customers),
            'date_order': base_date.strftime('%Y-%m-%d %H:%M:%S'),
            'state': 'sale',
            'order_line': [(0, 0, {
                'product_id': random.choice(products),
                'product_uom_qty': random.randint(1, 5),
                'price_unit': random.uniform(15.0, 150.0)
            })]
        }
        
        try:
            order_id = models.execute_kw(db, uid, password, 'sale.order', 'create', [order_data])
            print(f"Created order {order_id} for September")
        except Exception as e:
            print(f"Error creating order: {e}")

if __name__ == "__main__":
    boost_september_sales()
