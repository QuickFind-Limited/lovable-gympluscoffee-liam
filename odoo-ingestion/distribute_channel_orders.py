#!/usr/bin/env python3
"""
Channel Distribution Fix
Creates orders across multiple channels and geographic regions
"""

import xmlrpc.client
import random
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def distribute_orders_across_channels():
    # Connection setup
    url = 'https://source-gym-plus-coffee.odoo.com/'
    db = 'source-gym-plus-coffee'
    username = 'admin@quickfindai.com'
    password = 'BJ62wX2J4yzjS$i'
    
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    uid = common.authenticate(db, username, password, {})
    
    # Get all channels
    teams = models.execute_kw(db, uid, password, 'crm.team', 'search_read',
                             [[]], {'fields': ['id', 'name']})
    
    logger.info(f"Available channels: {[t['name'] for t in teams]}")
    
    # Get customers from different regions
    all_customers = models.execute_kw(db, uid, password, 'res.partner', 'search_read',
                                    [[['is_company', '=', False]]], 
                                    {'fields': ['id', 'name', 'city', 'state_id'], 'limit': 200})
    
    # Group customers by geography
    us_customers = [c for c in all_customers if c['city'] in ['Miami', 'Austin', 'Denver', 'Seattle', 'Boston', 'Atlanta', 'Phoenix', 'Portland']]
    irish_customers = [c for c in all_customers if c['city'] in ['Dublin', 'Galway', 'Cork', 'Limerick', 'Waterford']]
    uk_customers = [c for c in all_customers if c['city'] in ['London', 'Manchester', 'Birmingham', 'Bristol', 'Leeds']]
    
    logger.info(f"Customer distribution: US: {len(us_customers)}, Irish: {len(irish_customers)}, UK: {len(uk_customers)}")
    
    # Get products
    products = models.execute_kw(db, uid, password, 'product.product', 'search', [[]], {'limit': 50})
    
    # Channel-specific order creation
    channel_strategies = [
        {
            'team_name': 'Instagram Shop',
            'customer_pool': us_customers + irish_customers,  # Younger demographics
            'order_count': 15,
            'avg_value': 280,
            'product_count_range': (1, 3)  # Smaller, trendy orders
        },
        {
            'team_name': 'Amazon Store', 
            'customer_pool': us_customers,
            'order_count': 20,
            'avg_value': 350,
            'product_count_range': (2, 5)  # Bulk orders
        },
        {
            'team_name': 'Corporate Sales',
            'customer_pool': us_customers + uk_customers,
            'order_count': 8,
            'avg_value': 1200,
            'product_count_range': (5, 12)  # Large corporate orders
        },
        {
            'team_name': 'Pop-up Events',
            'customer_pool': irish_customers + uk_customers,
            'order_count': 12,
            'avg_value': 180,
            'product_count_range': (1, 2)  # Impulse purchases
        },
        {
            'team_name': 'Shopify',
            'customer_pool': all_customers,
            'order_count': 25,
            'avg_value': 320,
            'product_count_range': (2, 4)  # E-commerce standard
        }
    ]
    
    total_orders_created = 0
    
    for strategy in channel_strategies:
        # Find the team
        team = next((t for t in teams if t['name'] == strategy['team_name']), None)
        if not team:
            logger.warning(f"Team '{strategy['team_name']}' not found, skipping")
            continue
        
        if not strategy['customer_pool']:
            logger.warning(f"No customers available for {strategy['team_name']}, skipping")
            continue
        
        logger.info(f"Creating {strategy['order_count']} orders for {strategy['team_name']}...")
        
        channel_orders = 0
        for i in range(strategy['order_count']):
            try:
                # Random date in last 3 months
                days_ago = random.randint(1, 90)
                order_date = datetime.now() - timedelta(days=days_ago)
                
                # Select customer and products
                customer = random.choice(strategy['customer_pool'])
                num_products = random.randint(*strategy['product_count_range'])
                
                # Create order lines
                order_lines = []
                target_total = strategy['avg_value'] + random.uniform(-50, 50)
                price_per_product = target_total / num_products
                
                for j in range(num_products):
                    product_id = random.choice(products)
                    quantity = random.randint(1, 4)
                    unit_price = (price_per_product / quantity) + random.uniform(-10, 10)
                    unit_price = max(15.0, unit_price)
                    
                    order_lines.append((0, 0, {
                        'product_id': product_id,
                        'product_uom_qty': quantity,
                        'price_unit': round(unit_price, 2)
                    }))
                
                # Create order
                order_data = {
                    'partner_id': customer['id'],
                    'date_order': order_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'state': 'sale',
                    'team_id': team['id'],
                    'order_line': order_lines
                }
                
                order_id = models.execute_kw(db, uid, password, 'sale.order', 'create', [order_data])
                channel_orders += 1
                total_orders_created += 1
                
            except Exception as e:
                logger.error(f"Error creating order for {strategy['team_name']}: {e}")
                continue
        
        logger.info(f"✅ Created {channel_orders} orders for {strategy['team_name']}")
    
    logger.info(f"🎉 Channel distribution completed: {total_orders_created} orders across channels")

if __name__ == "__main__":
    distribute_orders_across_channels()