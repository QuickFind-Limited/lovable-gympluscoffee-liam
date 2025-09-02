#!/usr/bin/env python3
"""Import ALL Gym+Coffee products efficiently with duplicate checking"""

import xmlrpc.client
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

def import_all_products():
    # Connect to Odoo
    url = os.getenv('odoo_url', 'https://source-gym-plus-coffee.odoo.com')
    db = os.getenv('db', 'source-gym-plus-coffee')
    username = os.getenv('username', 'admin@quickfindai.com')
    password = os.getenv('password', 'BJ62wX2J4yzjS$i')
    
    print("🔗 Connecting to Odoo...")
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
    uid = common.authenticate(db, username, password, {})
    print(f"✅ Connected (UID: {uid})\n")
    
    # Get existing products to avoid duplicates
    print("📊 Checking existing products...")
    existing = models.execute_kw(db, uid, password, 'product.template', 'search_read', 
                                 [[]], {'fields': ['default_code', 'name']})
    existing_skus = {p['default_code'] for p in existing if p.get('default_code')}
    print(f"   Found {len(existing)} existing products")
    print(f"   Unique SKUs: {len(existing_skus)}\n")
    
    # Load Gym+Coffee data
    print("📦 Loading Gym+Coffee products...")
    with open('/workspaces/source-lovable-gympluscoffee/data/gym_plus_coffee_products.json', 'r') as f:
        data = json.load(f)
    
    all_products = data['products']
    print(f"   Total products in file: {len(all_products)}")
    
    # Filter out products that already exist
    products_to_import = []
    skipped = 0
    
    for product in all_products:
        if product['sku'] in existing_skus:
            skipped += 1
        else:
            products_to_import.append(product)
    
    print(f"   Products to import: {len(products_to_import)}")
    print(f"   Skipping duplicates: {skipped}\n")
    
    if len(products_to_import) == 0:
        print("✅ All products already imported!")
        return
    
    # Import products in small batches to avoid timeout
    print("🚀 Starting import...")
    print("="*50)
    
    created = 0
    failed = 0
    batch_size = 10  # Small batch size to avoid timeouts
    
    start_time = time.time()
    
    for i in range(0, len(products_to_import), batch_size):
        batch = products_to_import[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(products_to_import) + batch_size - 1) // batch_size
        
        print(f"\n📦 Batch {batch_num}/{total_batches} ({len(batch)} products)")
        
        for product in batch:
            try:
                # Create product
                product_id = models.execute_kw(db, uid, password, 'product.template', 'create', [{
                    'name': product['name'],
                    'default_code': product['sku'],
                    'list_price': product['list_price'],
                    'standard_price': product.get('standard_cost', 0),
                    'description_sale': product.get('description', ''),
                    # Add more fields if needed
                    'sale_ok': True,
                    'purchase_ok': True,
                    'active': True
                }])
                
                created += 1
                print(f"   ✅ {product['name'][:50]} ({product['sku']})")
                
            except Exception as e:
                failed += 1
                print(f"   ❌ Failed: {product['sku']} - {str(e)[:50]}")
        
        # Progress update
        elapsed = time.time() - start_time
        rate = created / elapsed if elapsed > 0 else 0
        remaining = len(products_to_import) - (i + len(batch))
        eta = remaining / rate if rate > 0 else 0
        
        print(f"\n   Progress: {created}/{len(products_to_import)} created")
        print(f"   Rate: {rate:.1f} products/sec")
        if remaining > 0:
            print(f"   ETA: {eta/60:.1f} minutes")
    
    # Final summary
    print("\n" + "="*50)
    print("🎉 IMPORT COMPLETE!")
    print("="*50)
    
    elapsed_total = time.time() - start_time
    
    print(f"\n📊 Results:")
    print(f"   ✅ Created: {created} products")
    print(f"   ⏭️  Skipped: {skipped} duplicates")
    print(f"   ❌ Failed: {failed} products")
    print(f"   ⏱️  Time: {elapsed_total:.1f} seconds")
    
    # Verify final count
    final_count = models.execute_kw(db, uid, password, 'product.template', 'search_count', [[]])
    print(f"\n📦 Total products now in Odoo: {final_count}")
    
    # Save import log
    log = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'products_created': created,
        'products_skipped': skipped,
        'products_failed': failed,
        'total_in_odoo': final_count,
        'elapsed_time': elapsed_total
    }
    
    with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/import_log.json', 'w') as f:
        json.dump(log, f, indent=2)
    
    print("\n💾 Import log saved to import_log.json")

if __name__ == "__main__":
    import_all_products()