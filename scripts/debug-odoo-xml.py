#!/usr/bin/env python3
import xmlrpc.client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('../tools/odoo_mcp/.env')

# Create a custom transport to capture XML
class VerboseTransport(xmlrpc.client.Transport):
    def send_content(self, connection, request_body):
        print("\n=== XML Request ===")
        print(request_body.decode('utf-8'))
        return super().send_content(connection, request_body)

# Odoo connection details
url = os.getenv('ODOO_URL', 'https://source-animalfarmacy.odoo.com')
db = os.getenv('ODOO_DB', 'source-animalfarmacy')
username = os.getenv('ODOO_USERNAME', 'admin@quickfindai.com')
password = os.getenv('ODOO_PASSWORD', 'BJ62wX2J4yzjS$i')

# Connect to Odoo with verbose transport
transport = VerboseTransport()
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', transport=transport)

# Test the exact query
print("\n=== Testing search query ===")
supplier_ids = models.execute_kw(db, uid, password,
    'res.partner', 'search',
    [[['supplier_rank', '>', 0]]],
    {'limit': 10})