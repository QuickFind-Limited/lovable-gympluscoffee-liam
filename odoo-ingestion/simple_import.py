#!/usr/bin/env python3
"""Simplified import script for Gym+Coffee products"""

import xmlrpc.client
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def simple_import():
    # Connect to Odoo
    url = os.getenv('odoo_url', 'https://source-gym-plus-coffee.odoo.com')
    db = os.getenv('db', 'source-gym-plus-coffee')
    username = os.getenv('username', 'admin@quickfindai.com')
    password = os.getenv('password', 'BJ62wX2J4yzjS$i')
    
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
    
    uid = common.authenticate(db, username, password, {})
    print(f"✅ Connected to Odoo (UID: {uid})")
    
    # Load product data
    with open('/workspaces/source-lovable-gympluscoffee/data/gym_plus_coffee_products.json', 'r') as f:
        data = json.load(f)
    
    products_created = []
    
    # Create simple products (first 10)
    for product in data['products'][:10]:
        try:
            # Create as simple product without variants
            product_id = models.execute_kw(
                db, uid, password,
                'product.template', 'create', [{
                    'name': product['name'],
                    'list_price': product['list_price'],
                    'standard_price': product.get('standard_cost', 0),
                    'default_code': product['sku']
                }]
            )
            products_created.append(product_id)
            print(f"✅ Created product: {product['name']} (ID: {product_id})")
        except Exception as e:
            print(f"❌ Failed to create {product['name']}: {str(e)[:100]}")
    
    print(f"\n📊 Created {len(products_created)} products")
    
    # Create a simple sales order
    if products_created:
        try:
            # Get the first customer
            customer_ids = models.execute_kw(
                db, uid, password,
                'res.partner', 'search', [
                    [['customer_rank', '>', 0]]
                ], {'limit': 1}
            )
            
            if customer_ids:
                # Get product variants for the created templates
                variant_ids = models.execute_kw(
                    db, uid, password,
                    'product.product', 'search', [
                        [['product_tmpl_id', 'in', products_created[:3]]]
                    ]
                )
                
                if variant_ids:
                    # Create order
                    order_id = models.execute_kw(
                        db, uid, password,
                        'sale.order', 'create', [{
                            'partner_id': customer_ids[0],
                            'order_line': [(0, 0, {
                                'product_id': variant_ids[0],
                                'product_uom_qty': 2
                            })]
                        }]
                    )
                    print(f"✅ Created sales order ID: {order_id}")
        except Exception as e:
            print(f"❌ Failed to create order: {str(e)[:100]}")
    
    return products_created

if __name__ == "__main__":
    simple_import()