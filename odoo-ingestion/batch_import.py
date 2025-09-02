#!/usr/bin/env python3
"""Batch import with progress tracking"""

import xmlrpc.client
import json
import os
from dotenv import load_dotenv

load_dotenv()

def batch_import(batch_size=50):
    # Connect
    url = os.getenv('odoo_url', 'https://source-gym-plus-coffee.odoo.com')
    db = os.getenv('db', 'source-gym-plus-coffee')
    username = os.getenv('username', 'admin@quickfindai.com')
    password = os.getenv('password', 'BJ62wX2J4yzjS$i')
    
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
    uid = common.authenticate(db, username, password, {})
    
    print(f"✅ Connected to Odoo")
    
    # Check existing
    existing = models.execute_kw(db, uid, password, 'product.template', 'search_read', 
                                 [[]], {'fields': ['default_code']})
    existing_skus = {p['default_code'] for p in existing if p.get('default_code')}
    print(f"📊 Found {len(existing_skus)} existing products")
    
    # Load data
    with open('/workspaces/source-lovable-gympluscoffee/data/gym_plus_coffee_products.json', 'r') as f:
        data = json.load(f)
    
    # Filter new products
    new_products = [p for p in data['products'] if p['sku'] not in existing_skus]
    print(f"📦 {len(new_products)} new products to import")
    
    # Import in batches
    created = 0
    for i in range(0, len(new_products), batch_size):
        batch = new_products[i:i+batch_size]
        print(f"\n⏳ Processing batch {i//batch_size + 1} ({len(batch)} products)...")
        
        for product in batch:
            try:
                models.execute_kw(db, uid, password, 'product.template', 'create', [{
                    'name': product['name'],
                    'default_code': product['sku'],
                    'list_price': product['list_price'],
                    'standard_price': product.get('standard_cost', 0)
                }])
                created += 1
            except:
                pass  # Skip errors
        
        print(f"   ✅ Batch complete. Total created: {created}")
    
    # Final count
    final_count = models.execute_kw(db, uid, password, 'product.template', 'search_count', [[]])
    print(f"\n🎉 Import complete! Total products in Odoo: {final_count}")
    
    return created

if __name__ == "__main__":
    batch_import(50)