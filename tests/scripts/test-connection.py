#!/usr/bin/env python3
"""
Simple test to check if we can connect to Odoo and verify basic functionality
"""
import requests
import json
import os

def test_odoo_basic():
    # Odoo connection settings
    odoo_url = os.getenv('ODOO_URL', 'https://animalfarmacy.odoo.com')
    
    print(f"Testing connection to: {odoo_url}")
    
    # Try to reach the main Odoo URL
    try:
        response = requests.get(odoo_url, timeout=10)
        print(f"✅ HTTP connection successful: {response.status_code}")
        print(f"   Response headers: {dict(list(response.headers.items())[:5])}")
        
        # Try the XML-RPC endpoint
        xmlrpc_url = f"{odoo_url}/xmlrpc/2/common"
        print(f"\nTrying XML-RPC endpoint: {xmlrpc_url}")
        
        response2 = requests.get(xmlrpc_url, timeout=10)
        print(f"XML-RPC endpoint status: {response2.status_code}")
        
        if response2.status_code == 405:
            print("✅ 405 Method Not Allowed is expected for XML-RPC GET request")
            print("   This means the endpoint exists but requires POST")
        
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    test_odoo_basic()