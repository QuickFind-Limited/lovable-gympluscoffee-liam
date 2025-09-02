#!/usr/bin/env python3
"""
Check minimum quantities for products in Odoo
"""

import xmlrpc.client
import os
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools/odoo_mcp/.env')
load_dotenv(env_path)

# Odoo connection details
url = os.getenv('ODOO_URL')
db = os.getenv('ODOO_DATABASE')
username = os.getenv('ODOO_USERNAME')
password = os.getenv('ODOO_PASSWORD')

print(f"Connecting to Odoo at {url}")
print(f"Database: {db}")
print(f"Username: {username}")

# Connect to Odoo
common = xmlrpc.client.ServerProxy(f'{url}xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

if not uid:
    print("Authentication failed!")
    exit(1)

print(f"✅ Authenticated successfully (UID: {uid})")

# Connect to the object endpoint
models = xmlrpc.client.ServerProxy(f'{url}xmlrpc/2/object')

print("\n🔍 Searching for product.supplierinfo records with minimum quantities...")

# Search for supplier info records
supplier_info_ids = models.execute_kw(db, uid, password,
    'product.supplierinfo', 'search',
    [[]], # No filter - get all
    {'limit': 20} # Limit to 20 for display
)

print(f"Found {len(supplier_info_ids)} supplier info records")

if supplier_info_ids:
    # Read the supplier info details
    supplier_infos = models.execute_kw(db, uid, password,
        'product.supplierinfo', 'read',
        [supplier_info_ids],
        {'fields': ['id', 'product_id', 'product_name', 'product_code', 
                   'partner_id', 'min_qty', 'price', 'delay']}
    )
    
    print("\n📊 Product Minimum Quantities from Odoo:")
    print("=" * 100)
    print(f"{'Product Name':<40} {'Code':<15} {'Supplier':<25} {'Min Qty':>10} {'Price':>10}")
    print("-" * 100)
    
    for info in supplier_infos:
        product_name = info.get('product_name', 'N/A')
        product_code = info.get('product_code', 'N/A') or 'N/A'
        supplier = info.get('partner_id', ['N/A', 'N/A'])[1] if info.get('partner_id') else 'N/A'
        min_qty = info.get('min_qty', 0)
        price = info.get('price', 0)
        
        print(f"{product_name:<40} {product_code:<15} {supplier:<25} {min_qty:>10.0f} {price:>10.2f}")

    # Get some specific examples for UI verification
    print("\n🎯 Specific Examples to Check in UI:")
    print("=" * 70)
    
    # Pick first 5 products with min_qty > 1
    examples = [info for info in supplier_infos if info.get('min_qty', 0) > 1][:5]
    
    for i, info in enumerate(examples, 1):
        print(f"\n{i}. Product: {info.get('product_name', 'N/A')}")
        print(f"   Code: {info.get('product_code', 'N/A')}")
        print(f"   Supplier: {info.get('partner_id', ['N/A', 'N/A'])[1] if info.get('partner_id') else 'N/A'}")
        print(f"   Minimum Quantity: {info.get('min_qty', 0):.0f}")
        print(f"   Price: ${info.get('price', 0):.2f}")

print("\n💡 To verify in the UI:")
print("1. Go to the Suppliers page in your application")
print("2. Look for the products listed above")
print("3. The minimum quantity should be displayed next to each product")
print("4. The UI field is typically labeled 'Min Qty' or 'Minimum Quantity'")