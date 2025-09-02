#!/usr/bin/env python3
"""
Test Odoo search_read method signature
"""
import xmlrpc.client
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / "odoo_mcp" / ".env"
load_dotenv(env_path)

# Get Odoo credentials
ODOO_URL = os.getenv('ODOO_URL', '').rstrip('/')
ODOO_DATABASE = os.getenv('ODOO_DATABASE')
ODOO_USERNAME = os.getenv('ODOO_USERNAME')
ODOO_PASSWORD = os.getenv('ODOO_PASSWORD')

print("Testing Odoo search_read method signatures...")
print("=" * 50)

# Connect to Odoo
common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
uid = common.authenticate(ODOO_DATABASE, ODOO_USERNAME, ODOO_PASSWORD, {})
models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')

print(f"Connected to Odoo (UID: {uid})")
print()

# Test 1: Basic search_read with domain only
print("Test 1: Basic search_read with domain only")
try:
    result = models.execute_kw(
        ODOO_DATABASE, uid, ODOO_PASSWORD,
        'product.product', 'search_read',
        [[['sale_ok', '=', True]]]
    )
    print(f"✅ Success: Got {len(result)} products")
    if result:
        print(f"   Fields returned: {list(result[0].keys())}")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# Test 2: search_read with domain and fields list
print("Test 2: search_read with domain and fields list")
try:
    result = models.execute_kw(
        ODOO_DATABASE, uid, ODOO_PASSWORD,
        'product.product', 'search_read',
        [
            [['sale_ok', '=', True]],
            ['id', 'name', 'list_price']
        ]
    )
    print(f"✅ Success: Got {len(result)} products")
    if result:
        print(f"   Fields returned: {list(result[0].keys())}")
        print(f"   Sample: {result[0]}")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# Test 3: search_read with all parameters
print("Test 3: search_read with domain, fields, offset, limit, order")
try:
    result = models.execute_kw(
        ODOO_DATABASE, uid, ODOO_PASSWORD,
        'product.product', 'search_read',
        [
            [['sale_ok', '=', True]],
            ['id', 'name', 'list_price']
        ],
        {
            'offset': 0,
            'limit': 2,
            'order': 'name'
        }
    )
    print(f"✅ Success: Got {len(result)} products")
    if result:
        for product in result:
            print(f"   - {product['name']} (${product.get('list_price', 0)})")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# Test 4: search_read with kwargs style
print("Test 4: search_read with keyword arguments (limit, offset)")
try:
    # In Odoo 18, these might be passed as keyword arguments
    result = models.execute_kw(
        ODOO_DATABASE, uid, ODOO_PASSWORD,
        'product.product', 'search_read',
        [
            [['sale_ok', '=', True]],
            ['id', 'name', 'list_price']
        ],
        {'limit': 3, 'offset': 0}
    )
    print(f"✅ Success: Got {len(result)} products")
except Exception as e:
    print(f"❌ Error: {e}")