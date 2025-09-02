#!/usr/bin/env python3
"""
Test raw XML response from Odoo for false values
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

# Enable verbose mode to see raw XML
class VerboseTransport(xmlrpc.client.Transport):
    def send_content(self, connection, request_body):
        print("Request XML:")
        print(request_body[:500])
        print()
        super().send_content(connection, request_body)
    
    def single_request(self, host, handler, request_body, verbose=0):
        response = super().single_request(host, handler, request_body, verbose)
        return response

# Connect to Odoo with verbose transport
transport = VerboseTransport()
models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object', transport=transport, verbose=True)

# First authenticate normally
common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
uid = common.authenticate(ODOO_DATABASE, ODOO_USERNAME, ODOO_PASSWORD, {})

# Get just one category to see the raw response
try:
    categories = models.execute_kw(
        ODOO_DATABASE, uid, ODOO_PASSWORD,
        'product.category', 'search_read',
        [[], ['id', 'name', 'parent_id']],
        {'limit': 1}
    )
    print(f"Result: {categories}")
except Exception as e:
    print(f"Error: {e}")