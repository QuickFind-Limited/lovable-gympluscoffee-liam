#!/usr/bin/env python3
"""
Test fetching categories from Odoo
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

print("Testing Odoo categories...")
print("=" * 50)

# Connect to Odoo
common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
uid = common.authenticate(ODOO_DATABASE, ODOO_USERNAME, ODOO_PASSWORD, {})
models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')

print(f"Connected to Odoo (UID: {uid})")
print()

# Test 1: Get all categories
print("Test 1: Get all product categories")
try:
    categories = models.execute_kw(
        ODOO_DATABASE, uid, ODOO_PASSWORD,
        'product.category', 'search_read',
        [[], ['id', 'name', 'parent_id', 'child_id', 'product_count']],
        {'limit': 10}
    )
    print(f"✅ Success: Got {len(categories)} categories")
    for cat in categories[:5]:
        parent = cat.get('parent_id')
        if isinstance(parent, list):
            parent_str = f"{parent[1]} ({parent[0]})" if parent else "None"
        else:
            parent_str = str(parent)
        print(f"   - [{cat['id']}] {cat['name']} (parent: {parent_str})")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# Test 2: Count total categories
print("Test 2: Count total categories")
try:
    count = models.execute_kw(
        ODOO_DATABASE, uid, ODOO_PASSWORD,
        'product.category', 'search_count',
        [[]]
    )
    print(f"✅ Total categories: {count}")
except Exception as e:
    print(f"❌ Error: {e}")
    
print()

# Test 3: Check if product_count field exists
print("Test 3: Check available fields on product.category")
try:
    fields = models.execute_kw(
        ODOO_DATABASE, uid, ODOO_PASSWORD,
        'product.category', 'fields_get',
        [],
        {'attributes': ['string', 'type']}
    )
    print(f"✅ Found {len(fields)} fields")
    # Check for relevant fields
    relevant_fields = ['product_count', 'child_id', 'parent_id', 'display_name']
    for field in relevant_fields:
        if field in fields:
            print(f"   - {field}: {fields[field]['type']}")
        else:
            print(f"   - {field}: NOT FOUND")
except Exception as e:
    print(f"❌ Error: {e}")