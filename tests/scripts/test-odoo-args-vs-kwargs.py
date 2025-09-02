#!/usr/bin/env python3
"""
Test if Odoo accepts options as part of args or as kwargs
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

print("Testing Odoo execute_kw args vs kwargs...")
print("=" * 50)

# Connect to Odoo
common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
uid = common.authenticate(ODOO_DATABASE, ODOO_USERNAME, ODOO_PASSWORD, {})
models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')

print(f"Connected to Odoo (UID: {uid})")
print()

# Test 1: Direct method call
print("Test 1: Direct search_read on models")
try:
    # Try calling search_read directly on the proxy object
    result = models.search_read(
        ODOO_DATABASE, uid, ODOO_PASSWORD,
        'product.product',
        [['sale_ok', '=', True]],
        ['id', 'name', 'list_price'],
        0,  # offset
        2   # limit
    )
    print(f"✅ Success: Got {len(result)} products")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# Test 2: execute_kw with offset/limit as separate args
print("Test 2: execute_kw with offset/limit as separate positional args")
try:
    result = models.execute_kw(
        ODOO_DATABASE, uid, ODOO_PASSWORD,
        'product.product', 'search_read',
        [[['sale_ok', '=', True]], ['id', 'name', 'list_price']],
        {'offset': 0, 'limit': 2}  # As a separate parameter
    )
    print(f"✅ Success: Got {len(result)} products")
    for product in result:
        print(f"   - {product['name']}")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# Test 3: Test with empty options dict
print("Test 3: execute_kw with empty options dict")
try:
    result = models.execute_kw(
        ODOO_DATABASE, uid, ODOO_PASSWORD,
        'product.product', 'search_read',
        [[['sale_ok', '=', True]], ['id', 'name', 'list_price']],
        {}  # Empty dict
    )
    print(f"✅ Success: Got {len(result)} products (should be all)")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# Test 4: search_read with no third parameter
print("Test 4: execute_kw with no options parameter")
try:
    result = models.execute_kw(
        ODOO_DATABASE, uid, ODOO_PASSWORD,
        'product.product', 'search_read',
        [[['sale_ok', '=', True]], ['id', 'name', 'list_price']]
        # No third parameter
    )
    print(f"✅ Success: Got {len(result)} products (should be all)")
    print(f"   Total returned: {len(result)}")
except Exception as e:
    print(f"❌ Error: {e}")