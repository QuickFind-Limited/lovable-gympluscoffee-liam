#!/usr/bin/env python3
"""Test Odoo connection and explore product structure"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "odoo_mcp" / "src"))

import asyncio
from odoo_mcp.connection import OdooConnection, OdooConnectionConfig

async def explore_odoo_products():
    """Explore Odoo product structure and capabilities"""
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / "odoo_mcp" / ".env")
    
    # Get connection details
    config = OdooConnectionConfig(
        url=os.getenv("ODOO_URL"),
        database=os.getenv("ODOO_DATABASE"),
        username=os.getenv("ODOO_USERNAME"),
        password=os.getenv("ODOO_PASSWORD")
    )
    
    print(f"Connecting to Odoo at {config.url}...")
    
    # Create connection
    connection = OdooConnection(config)
    
    try:
        # Authenticate
        await connection.authenticate()
        print("✅ Successfully connected to Odoo!")
        
        # 1. Check product models
        print("\n📦 Checking Product Models...")
        
        # Get product.product fields
        product_fields = await connection.execute_kw(
            'product.product', 
            'fields_get', 
            [],
            {'attributes': ['string', 'type', 'relation']}
        )
        
        print("\nKey product.product fields:")
        important_fields = ['name', 'display_name', 'description', 'description_sale', 
                          'categ_id', 'list_price', 'standard_price', 'qty_available',
                          'image_1920', 'image_128', 'product_tmpl_id', 'attribute_value_ids']
        
        for field in important_fields:
            if field in product_fields:
                info = product_fields[field]
                print(f"  - {field}: {info.get('string', '')} ({info.get('type', '')})")
                if info.get('relation'):
                    print(f"    → Relation: {info['relation']}")
        
        # 2. Get sample products
        print("\n📋 Sample Products:")
        product_ids = await connection.execute_kw(
            'product.product',
            'search',
            [[]],
            {'limit': 5}
        )
        
        if product_ids:
            products = await connection.execute_kw(
                'product.product',
                'read',
                [product_ids],
                {'fields': ['name', 'display_name', 'description_sale', 'list_price', 
                           'categ_id', 'qty_available', 'product_tmpl_id']}
            )
            
            for product in products:
                print(f"\n  Product ID: {product['id']}")
                print(f"  Name: {product.get('name', 'N/A')}")
                print(f"  Display Name: {product.get('display_name', 'N/A')}")
                print(f"  Price: ${product.get('list_price', 0)}")
                print(f"  Category: {product.get('categ_id', ['N/A', 'N/A'])[1] if product.get('categ_id') else 'N/A'}")
                print(f"  Stock: {product.get('qty_available', 0)}")
        
        # 3. Check product categories
        print("\n🗂️ Product Categories:")
        categories = await connection.execute_kw(
            'product.category',
            'search_read',
            [[]],
            {'fields': ['name', 'complete_name', 'parent_id'], 'limit': 10}
        )
        
        for cat in categories:
            print(f"  - {cat.get('complete_name', cat.get('name', 'N/A'))}")
        
        # 4. Test search capabilities
        print("\n🔍 Testing Search Capabilities...")
        
        # Test multi-field search
        search_term = "product"  # Generic term to find something
        domain = [
            '|', '|',
            ('name', 'ilike', search_term),
            ('description', 'ilike', search_term),
            ('description_sale', 'ilike', search_term)
        ]
        
        search_results = await connection.execute_kw(
            'product.product',
            'search',
            [domain],
            {'limit': 3}
        )
        
        print(f"  Found {len(search_results)} products matching '{search_term}'")
        
        # 5. Check product images
        print("\n🖼️ Checking Product Images...")
        
        # Check if product.image model exists
        try:
            image_model_fields = await connection.execute_kw(
                'product.image',
                'fields_get',
                [],
                {'attributes': ['string', 'type']}
            )
            print("  ✅ product.image model exists")
            
            # Get sample product images
            product_images = await connection.execute_kw(
                'product.image',
                'search_read',
                [[]],
                {'fields': ['name', 'product_tmpl_id', 'image_1920'], 'limit': 3}
            )
            
            print(f"  Found {len(product_images)} product images")
            
        except Exception as e:
            print(f"  ℹ️ product.image model not found or accessible: {e}")
            print("  Products might use image fields directly (image_1920, etc.)")
        
        # 6. Check sale order model
        print("\n📝 Checking Sale Order Model...")
        sale_order_fields = await connection.execute_kw(
            'sale.order',
            'fields_get',
            [],
            {'attributes': ['string', 'type', 'relation']}
        )
        
        important_so_fields = ['name', 'partner_id', 'order_line', 'state', 
                              'amount_total', 'date_order']
        
        print("  Key sale.order fields:")
        for field in important_so_fields:
            if field in sale_order_fields:
                info = sale_order_fields[field]
                print(f"    - {field}: {info.get('string', '')} ({info.get('type', '')})")
        
        # 7. Check sale order line model
        print("\n  Key sale.order.line fields:")
        sol_fields = await connection.execute_kw(
            'sale.order.line',
            'fields_get',
            [],
            {'attributes': ['string', 'type']}
        )
        
        important_sol_fields = ['product_id', 'product_uom_qty', 'price_unit', 
                               'price_subtotal', 'name']
        
        for field in important_sol_fields:
            if field in sol_fields:
                info = sol_fields[field]
                print(f"    - {field}: {info.get('string', '')} ({info.get('type', '')})")
        
        print("\n✅ Odoo exploration complete!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await connection.close()

if __name__ == "__main__":
    asyncio.run(explore_odoo_products())