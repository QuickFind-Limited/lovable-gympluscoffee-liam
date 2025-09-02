#!/usr/bin/env python3
"""Check available fields for product.template"""

import xmlrpc.client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv('odoo_url', 'https://source-gym-plus-coffee.odoo.com')
db = os.getenv('db', 'source-gym-plus-coffee')
username = os.getenv('username', 'admin@quickfindai.com')
password = os.getenv('password', 'BJ62wX2J4yzjS$i')

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
uid = common.authenticate(db, username, password, {})

def execute(model, method, *args):
    return models.execute_kw(db, uid, password, model, method, *args)

print("🔍 CHECKING PRODUCT.TEMPLATE FIELDS")
print("="*60)

# Get all fields
fields = execute('product.template', 'fields_get', [], 
                {'attributes': ['string', 'type', 'selection', 'required']})

# Look for type-related fields
print("\n📦 Type-related fields:")
for field_name, field_info in fields.items():
    if 'type' in field_name.lower() or field_name in ['type', 'detailed_type']:
        print(f"\n   Field: {field_name}")
        print(f"   Label: {field_info.get('string', 'N/A')}")
        print(f"   Type: {field_info.get('type', 'N/A')}")
        if 'selection' in field_info:
            print(f"   Options: {field_info['selection']}")
        print(f"   Required: {field_info.get('required', False)}")

# Check existing product to see actual values
print("\n📊 Sample existing product:")
products = execute('product.template', 'search_read', 
                  [[]], 
                  {'fields': ['name', 'type'], 'limit': 1})

if products:
    product = products[0]
    print(f"   Name: {product['name']}")
    print(f"   Type: {product.get('type', 'N/A')}")
    
    # Get all fields for this product
    full_product = execute('product.template', 'read', 
                          [product['id']], 
                          ['type', 'detailed_type'] if 'detailed_type' in fields else ['type'])
    
    if full_product:
        print(f"   Full type info: {full_product[0].get('type', 'N/A')}")
        if 'detailed_type' in full_product[0]:
            print(f"   Detailed type: {full_product[0].get('detailed_type', 'N/A')}")

print("\n💡 Available product creation approach:")
print("   Based on the fields above, we can create products with:")
print("   - type = 'consu' (consumable)")
print("   - type = 'service' (service)")
print("   - type = 'product' (stockable) - if available")

# Try to create a test product
print("\n🧪 Testing product creation...")
test_vals = {
    'name': '[TEST] Stockable Product',
    'list_price': 100.0,
    'type': 'consu'  # Start with consumable
}

try:
    test_id = execute('product.template', 'create', [test_vals])
    print(f"   ✅ Created test product with type='consu'")
    
    # Now try to update to stockable
    try:
        execute('product.template', 'write', [[test_id], {'type': 'product'}])
        print(f"   ✅ Successfully updated to type='product' (stockable)!")
    except Exception as e:
        print(f"   ❌ Cannot update to stockable: {str(e)[:100]}")
    
    # Delete test product
    execute('product.template', 'unlink', [[test_id]])
    
except Exception as e:
    print(f"   ❌ Error creating test product: {str(e)[:100]}")