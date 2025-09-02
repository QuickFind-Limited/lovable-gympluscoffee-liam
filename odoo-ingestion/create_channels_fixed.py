#!/usr/bin/env python3
"""
Fixed Channel Creation Script - Creates additional sales channels
"""

import xmlrpc.client

def create_additional_channels():
    # Connection setup
    url = 'https://source-gym-plus-coffee.odoo.com/'
    db = 'source-gym-plus-coffee'
    username = 'admin@quickfindai.com'
    password = 'BJ62wX2J4yzjS$i'
    
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    uid = common.authenticate(db, username, password, {})
    
    # Create additional sales channels (without code field)
    new_channels = [
        {'name': 'Instagram Shop'},
        {'name': 'Amazon Store'},
        {'name': 'Corporate Sales'},
        {'name': 'Pop-up Events'},
        {'name': 'Shopify'}
    ]
    
    for channel in new_channels:
        try:
            team_id = models.execute_kw(db, uid, password, 'crm.team', 'create', [channel])
            print(f"✅ Created channel: {channel['name']} (ID: {team_id})")
        except Exception as e:
            print(f"❌ Error creating channel {channel['name']}: {e}")

if __name__ == "__main__":
    create_additional_channels()