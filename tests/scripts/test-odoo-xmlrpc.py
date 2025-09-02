#!/usr/bin/env python3
"""Test Odoo connection using XML-RPC directly"""

import xmlrpc.client
import ssl
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment
load_dotenv(Path(__file__).parent.parent / "odoo_mcp" / ".env")

# Connection details
url = os.getenv("ODOO_URL").rstrip('/')
db = os.getenv("ODOO_DATABASE")
username = os.getenv("ODOO_USERNAME")
password = os.getenv("ODOO_PASSWORD")

print(f"Connecting to {url} with database {db}...")

# Create SSL context
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

# Connect to Odoo
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', context=context)
uid = common.authenticate(db, username, password, {})

if uid:
    print(f"✅ Authenticated successfully! UID: {uid}")
    
    # Create object endpoint
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', context=context)
    
    # 1. Check product structure
    print("\n📦 Product Structure:")
    
    # Get sample products
    product_ids = models.execute_kw(db, uid, password,
        'product.product', 'search',
        [[]],
        {'limit': 5})
    
    if product_ids:
        products = models.execute_kw(db, uid, password,
            'product.product', 'read',
            [product_ids],
            {'fields': ['name', 'display_name', 'description_sale', 'list_price', 
                       'categ_id', 'qty_available', 'default_code', 'barcode',
                       'image_1920', 'product_tmpl_id', 'type']})
        
        for product in products:
            print(f"\n  Product: {product.get('display_name', 'N/A')}")
            print(f"  - ID: {product['id']}")
            print(f"  - Code: {product.get('default_code', 'N/A')}")
            print(f"  - Price: ${product.get('list_price', 0)}")
            print(f"  - Type: {product.get('type', 'N/A')}")
            print(f"  - Stock: {product.get('qty_available', 0)}")
            print(f"  - Has Image: {'Yes' if product.get('image_1920') else 'No'}")
    
    # 2. Check categories
    print("\n🗂️ Product Categories:")
    categories = models.execute_kw(db, uid, password,
        'product.category', 'search_read',
        [[]],
        {'fields': ['name', 'complete_name'], 'limit': 10})
    
    for cat in categories[:5]:
        print(f"  - {cat.get('complete_name', cat.get('name', 'N/A'))}")
    
    # 3. Test search
    print("\n🔍 Testing Multi-field Search:")
    
    # Search for products with a common term
    domain = ['|', '|', 
              ('name', 'ilike', 'dog'),
              ('description', 'ilike', 'dog'),
              ('description_sale', 'ilike', 'dog')]
    
    search_results = models.execute_kw(db, uid, password,
        'product.product', 'search_read',
        [domain],
        {'fields': ['name', 'list_price'], 'limit': 5})
    
    print(f"  Found {len(search_results)} products containing 'dog'")
    for result in search_results:
        print(f"    - {result.get('name', 'N/A')} (${result.get('list_price', 0)})")
    
    # 4. Check if we can access product attributes
    print("\n🏷️ Product Attributes:")
    try:
        # Check product.attribute model
        attributes = models.execute_kw(db, uid, password,
            'product.attribute', 'search_read',
            [[]],
            {'fields': ['name', 'display_type'], 'limit': 5})
        
        if attributes:
            print(f"  Found {len(attributes)} product attributes")
            for attr in attributes:
                print(f"    - {attr.get('name', 'N/A')}")
        else:
            print("  No product attributes found")
            
    except Exception as e:
        print(f"  Could not access product attributes: {e}")
    
    # 5. Check sale.order structure
    print("\n📝 Sale Order Structure:")
    
    # Get fields info
    so_fields = models.execute_kw(db, uid, password,
        'sale.order', 'fields_get',
        [],
        {'attributes': ['string', 'type', 'required']})
    
    important_fields = ['partner_id', 'order_line', 'state', 'amount_total']
    print("  Important sale.order fields:")
    for field in important_fields:
        if field in so_fields:
            info = so_fields[field]
            print(f"    - {field}: {info.get('string', '')} (Type: {info.get('type', '')})")
    
    print("\n✅ Odoo connection test complete!")
    
else:
    print("❌ Authentication failed!")