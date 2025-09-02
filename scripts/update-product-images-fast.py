#!/usr/bin/env python3
"""
Update products in Odoo with images - Fast version
"""

import xmlrpc.client
import base64
import os
import random
from pathlib import Path

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

def update_product_images_fast(models, uid):
    """Update first 50 products with images quickly"""
    print("📸 Updating product images (fast mode)...")
    
    # Get a few sample images
    image_dir = Path('/workspaces/source-lovable-gympluscoffee/public/lovable-uploads')
    
    # Use specific images for quick update
    sample_images = [
        'a9fe6291-ad62-4a09-b635-c551a2d05dc6.png',  # Hoodie
        '90aa2a49-82df-4998-97ee-c77b558cf526.png',  # Tee
        'ee5a6158-0f47-49b2-808f-02c56bc0f8d9.png',  # Leggings
        '5b596d50-da50-4030-9d26-bf381e82a36c.png',  # Jacket
        '180d7dec-c110-4413-8c0d-580b73dffedb.png',  # Shoes
    ]
    
    # Read and encode images once
    encoded_images = []
    for img_name in sample_images:
        img_path = image_dir / img_name
        if img_path.exists():
            with open(img_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
                encoded_images.append(image_data)
                print(f"   Loaded image: {img_name}")
    
    if not encoded_images:
        print("❌ No images could be loaded")
        return
    
    # Get first 50 products without images
    product_ids = models.execute_kw(
        db, uid, password,
        'product.product', 'search',
        [[['image_1920', '=', False]]],
        {'limit': 50}
    )
    
    if not product_ids:
        print("✅ All products already have images")
        return
    
    print(f"Updating {len(product_ids)} products...")
    
    updated_count = 0
    for i, product_id in enumerate(product_ids):
        try:
            # Use a random image from our preloaded set
            image_data = encoded_images[i % len(encoded_images)]
            
            # Update the product
            models.execute_kw(
                db, uid, password,
                'product.product', 'write',
                [[product_id], {'image_1920': image_data}]
            )
            
            updated_count += 1
            
            if updated_count % 10 == 0:
                print(f"   Updated {updated_count}/{len(product_ids)} products...")
            
        except Exception as e:
            print(f"   ⚠️ Error updating product {product_id}: {str(e)}")
    
    print(f"✅ Successfully updated {updated_count} products with images")

def verify_images(models, uid):
    """Quick verification"""
    print("\n📊 Quick verification...")
    
    # Count products with images
    with_images = models.execute_kw(
        db, uid, password,
        'product.product', 'search_count',
        [[['image_1920', '!=', False]]]
    )
    
    total = models.execute_kw(
        db, uid, password,
        'product.product', 'search_count',
        [[]]
    )
    
    print(f"   Products with images: {with_images}/{total}")
    
    if with_images > 0:
        print("   ✅ Products now have images!")

def main():
    """Main function"""
    print("🔄 Connecting to Odoo...")
    try:
        uid, models = connect_odoo()
        print(f"✅ Connected to Odoo (UID: {uid})")
        
        # Update product images
        update_product_images_fast(models, uid)
        
        # Verify
        verify_images(models, uid)
        
        print("\n🎉 Operation completed!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()