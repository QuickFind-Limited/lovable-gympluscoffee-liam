#!/usr/bin/env python3
import xmlrpc.client
import os
from dotenv import load_dotenv
import xml.etree.ElementTree as ET

# Load environment variables
load_dotenv('../tools/odoo_mcp/.env')

# Odoo connection details
url = os.getenv('ODOO_URL', 'https://source-animalfarmacy.odoo.com')
db = os.getenv('ODOO_DB', 'source-animalfarmacy')
username = os.getenv('ODOO_USERNAME', 'admin@quickfindai.com')
password = os.getenv('ODOO_PASSWORD', 'BJ62wX2J4yzjS$i')

# Create a custom transport to capture XML
class VerboseTransport(xmlrpc.client.Transport):
    def send_content(self, connection, request_body):
        print("\n=== XML Request ===")
        print(request_body.decode('utf-8'))
        return super().send_content(connection, request_body)
    
    def parse_response(self, response):
        # Read the response
        data = response.read()
        print("\n=== XML Response (first 2000 chars) ===")
        print(data.decode('utf-8')[:2000])
        
        # Create a new response-like object for the parent to parse
        from io import BytesIO
        return super().parse_response(BytesIO(data))

# Connect to Odoo with verbose transport
transport = VerboseTransport()
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', transport=transport)
uid = common.authenticate(db, username, password, {})

if not uid:
    print("Authentication failed!")
    exit(1)

models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', transport=transport)

# Test the exact query
domain = [['supplier_rank', '>', 0]]

print(f"\n=== Testing suppliers query ===")

# Get suppliers - this will show the XML
suppliers = models.execute_kw(db, uid, password,
    'res.partner', 'search_read',
    [domain],
    {
        'fields': ['id', 'name'],
        'offset': 0,
        'limit': 1
    })

print(f"\n=== Parsed Result ===")
print(f"Found {len(suppliers)} suppliers")
if suppliers:
    print(f"First supplier: {suppliers[0]}")