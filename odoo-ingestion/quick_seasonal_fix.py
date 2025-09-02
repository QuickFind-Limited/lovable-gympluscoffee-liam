#!/usr/bin/env python3
"""
Quick Seasonal Distribution Fix
Creates a smaller number of high-value orders to balance the seasonal distribution
"""

import xmlrpc.client
import random
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_high_value_seasonal_orders():
    # Connection setup
    url = 'https://source-gym-plus-coffee.odoo.com/'
    db = 'source-gym-plus-coffee'
    username = 'admin@quickfindai.com'
    password = 'BJ62wX2J4yzjS$i'
    
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    uid = common.authenticate(db, username, password, {})
    
    # Get reference data
    customers = models.execute_kw(db, uid, password, 'res.partner', 'search', 
                                [[['is_company', '=', False]]], {'limit': 50})
    products = models.execute_kw(db, uid, password, 'product.product', 'search', 
                               [[]], {'limit': 20})
    teams = models.execute_kw(db, uid, password, 'crm.team', 'search', [[]])
    
    # Create high-value orders for underperforming months
    seasonal_fixes = [
        # June orders - need ~$165k additional (current: $7k, target: 21.5% of ~$800k = $172k)
        {'month': 6, 'year': 2024, 'count': 25, 'avg_value': 6000, 'name': 'June'},
        
        # July orders - need ~$182k additional (current: $22k, target: 25.5% of ~$800k = $204k) 
        {'month': 7, 'year': 2024, 'count': 30, 'avg_value': 6000, 'name': 'July'},
        
        # September orders - need ~$192k (current: ~$165, target: 24% of ~$800k = $192k)
        {'month': 9, 'year': 2024, 'count': 32, 'avg_value': 6000, 'name': 'September'}
    ]
    
    total_created = 0
    
    for fix in seasonal_fixes:
        logger.info(f"Creating {fix['count']} high-value orders for {fix['name']}...")
        
        month_orders = 0
        for i in range(fix['count']):
            try:
                # Random date in month
                day = random.randint(1, 28)  # Safe range for all months
                order_date = datetime(fix['year'], fix['month'], day, 
                                    random.randint(9, 18), random.randint(0, 59))
                
                # Create high-value order with multiple products
                num_products = random.randint(8, 15)  # Many products for high value
                order_lines = []
                target_value = fix['avg_value'] + random.uniform(-1000, 1000)
                price_per_item = target_value / num_products
                
                for j in range(num_products):
                    product_id = random.choice(products)
                    quantity = random.randint(2, 8)  # Higher quantities
                    unit_price = price_per_item / quantity + random.uniform(-20, 20)
                    unit_price = max(15.0, unit_price)  # Minimum reasonable price
                    
                    order_lines.append((0, 0, {
                        'product_id': product_id,
                        'product_uom_qty': quantity,
                        'price_unit': round(unit_price, 2)
                    }))
                
                # Create order
                order_data = {
                    'partner_id': random.choice(customers),
                    'date_order': order_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'state': 'sale',
                    'team_id': random.choice(teams) if teams else False,
                    'order_line': order_lines
                }
                
                order_id = models.execute_kw(db, uid, password, 'sale.order', 'create', [order_data])
                month_orders += 1
                total_created += 1
                
                if month_orders % 5 == 0:
                    logger.info(f"  Created {month_orders}/{fix['count']} orders for {fix['name']}")
                    
            except Exception as e:
                logger.error(f"Error creating order for {fix['name']}: {e}")
                continue
        
        logger.info(f"✅ Completed {fix['name']}: {month_orders} orders created")
    
    logger.info(f"🎉 Total seasonal fix completed: {total_created} high-value orders created")

if __name__ == "__main__":
    create_high_value_seasonal_orders()