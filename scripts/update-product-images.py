#!/usr/bin/env python3
"""
Update products in Odoo with images from the public/lovable-uploads folder
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

def get_image_files():
    """Get list of available image files"""
    image_dir = Path('/workspaces/source-lovable-gympluscoffee/public/lovable-uploads')
    image_files = list(image_dir.glob('*.png'))
    return image_files

def update_product_images(models, uid):
    """Update products with images"""
    print("📸 Updating product images...")
    
    # Get available images
    image_files = get_image_files()
    if not image_files:
        print("❌ No image files found")
        return
    
    print(f"Found {len(image_files)} image files")
    
    # Get all products
    product_ids = models.execute_kw(
        db, uid, password,
        'product.product', 'search',
        [[]],
        {'limit': 500}  # Update more products
    )
    
    products = models.execute_kw(
        db, uid, password,
        'product.product', 'read',
        [product_ids],
        {'fields': ['id', 'name', 'display_name', 'image_1920']}
    )
    
    # Filter products without images
    products_without_images = [p for p in products if not p.get('image_1920')]
    
    print(f"Found {len(products_without_images)} products without images")
    
    if not products_without_images:
        print("✅ All products already have images")
        return
    
    # Map product types to specific images for consistency
    image_mapping = {
        'hoodie': ['a9fe6291-ad62-4a09-b635-c551a2d05dc6.png', '5b596d50-da50-4030-9d26-bf381e82a36c.png'],
        'tee': ['90aa2a49-82df-4998-97ee-c77b558cf526.png', '49d56a4d-3453-48c6-bd26-2ba59b436142.png'],
        'leggings': ['ee5a6158-0f47-49b2-808f-02c56bc0f8d9.png', 'a25deb07-bdcd-40e4-a79f-6afecbdd777e.png'],
        'shorts': ['98ffbd50-bb80-442b-9d2f-47db14c682e5.png', '003574a6-9c3e-4ef7-b388-4787c2f0f6a2.png'],
        'jacket': ['46a8e3e8-6d0d-4697-81bf-aebb8b79a19e.png', '180d7dec-c110-4413-8c0d-580b73dffedb.png'],
        'beanie': ['5e5d8252-fe38-4b94-b7b1-3d8a89600a54.png', '269b1c3e-0693-4bd7-843e-e853d37b3e0a.png'],
        'cap': ['1b305c23-bc7d-4fb1-94d3-1732379b25dd.png', '2286e440-2796-4957-8be7-2795bd630d1d.png'],
        'bottle': ['6ea6ab0b-4930-4303-80da-a1685b15c2f3.png', '706d6769-061e-4b18-91ab-25c377db66f6.png'],
        'socks': ['253f7914-95dc-4817-a80e-b1ece852d561.png', '554cd914-e6c8-4a99-a2d7-d4b44a96cfe9.png'],
        'bag': ['c01d99aa-e83d-4d4b-baf5-c451a0d3ac4d.png', 'd24004d6-3d5f-4eda-8981-c91f8e91904b.png'],
        'default': []  # Will use random images
    }
    
    # Create a list of all available image names
    all_image_names = [f.name for f in image_files]
    
    updated_count = 0
    batch_size = 10
    
    for i, product in enumerate(products_without_images):
        try:
            product_name_lower = product['display_name'].lower()
            
            # Determine which image to use based on product name
            selected_image = None
            
            # Check product type and select appropriate image
            for product_type, image_list in image_mapping.items():
                if product_type in product_name_lower and image_list:
                    # Use the appropriate image for this product type
                    selected_image_name = random.choice(image_list)
                    selected_image = Path('/workspaces/source-lovable-gympluscoffee/public/lovable-uploads') / selected_image_name
                    break
            
            # If no specific mapping found, use a random image
            if not selected_image:
                selected_image = random.choice(image_files)
            
            # Read and encode the image
            with open(selected_image, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Update the product with the image
            models.execute_kw(
                db, uid, password,
                'product.product', 'write',
                [[product['id']], {'image_1920': image_data}]
            )
            
            updated_count += 1
            
            # Print progress every batch_size products
            if (i + 1) % batch_size == 0:
                print(f"   Updated {updated_count}/{len(products_without_images)} products...")
            
        except Exception as e:
            print(f"   ⚠️ Error updating product {product['id']}: {str(e)}")
    
    print(f"✅ Successfully updated {updated_count} products with images")
    
    # Also update product templates
    print("\n📸 Updating product templates...")
    
    # Get product templates without images
    template_ids = models.execute_kw(
        db, uid, password,
        'product.template', 'search',
        [[['image_1920', '=', False]]],
        {'limit': 500}
    )
    
    if template_ids:
        templates = models.execute_kw(
            db, uid, password,
            'product.template', 'read',
            [template_ids],
            {'fields': ['id', 'name']}
        )
        
        template_updated = 0
        for template in templates:
            try:
                # Use similar logic for templates
                template_name_lower = template['name'].lower()
                selected_image = None
                
                for product_type, image_list in image_mapping.items():
                    if product_type in template_name_lower and image_list:
                        selected_image_name = random.choice(image_list)
                        selected_image = Path('/workspaces/source-lovable-gympluscoffee/public/lovable-uploads') / selected_image_name
                        break
                
                if not selected_image:
                    selected_image = random.choice(image_files)
                
                with open(selected_image, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                
                models.execute_kw(
                    db, uid, password,
                    'product.template', 'write',
                    [[template['id']], {'image_1920': image_data}]
                )
                
                template_updated += 1
                
            except Exception as e:
                pass  # Silently skip errors for templates
        
        print(f"✅ Updated {template_updated} product templates with images")

def verify_images(models, uid):
    """Verify that products now have images"""
    print("\n📊 Verifying product images...")
    
    # Check products with images
    products_with_images = models.execute_kw(
        db, uid, password,
        'product.product', 'search_count',
        [[['image_1920', '!=', False]]]
    )
    
    total_products = models.execute_kw(
        db, uid, password,
        'product.product', 'search_count',
        [[]]
    )
    
    print(f"   Products with images: {products_with_images}/{total_products}")
    
    # Check templates with images
    templates_with_images = models.execute_kw(
        db, uid, password,
        'product.template', 'search_count',
        [[['image_1920', '!=', False]]]
    )
    
    total_templates = models.execute_kw(
        db, uid, password,
        'product.template', 'search_count',
        [[]]
    )
    
    print(f"   Templates with images: {templates_with_images}/{total_templates}")
    
    # Sample some products to show
    sample_ids = models.execute_kw(
        db, uid, password,
        'product.product', 'search',
        [[['image_1920', '!=', False]]],
        {'limit': 5}
    )
    
    if sample_ids:
        samples = models.execute_kw(
            db, uid, password,
            'product.product', 'read',
            [sample_ids],
            {'fields': ['name']}
        )
        
        print("\n   Sample products with images:")
        for sample in samples:
            print(f"      ✅ {sample['name']}")

def main():
    """Main function"""
    print("🔄 Connecting to Odoo...")
    try:
        uid, models = connect_odoo()
        print(f"✅ Connected to Odoo (UID: {uid})")
        
        # Update product images
        update_product_images(models, uid)
        
        # Verify
        verify_images(models, uid)
        
        print("\n🎉 All operations completed successfully!")
        print("   Products should now display with images in the application.")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()