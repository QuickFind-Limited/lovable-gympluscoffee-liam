#!/usr/bin/env python3
"""
Test Edge Functions Locally with Odoo Secrets
"""
import os
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from odoo_mcp/.env
env_path = Path(__file__).parent.parent / "odoo_mcp" / ".env"
load_dotenv(env_path)

# Get Odoo credentials from environment
ODOO_URL = os.getenv('ODOO_URL', '').rstrip('/')
ODOO_DATABASE = os.getenv('ODOO_DATABASE')
ODOO_USERNAME = os.getenv('ODOO_USERNAME')
ODOO_PASSWORD = os.getenv('ODOO_PASSWORD')

# Supabase project configuration
SUPABASE_URL = "https://vkxoqaansgbyzcppdiii.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Mzk3MTQ4MiwiZXhwIjoyMDY5NTQ3NDgyfQ.Ip7h5Xiiv9V13ihQRNSGkCJHsKRGlY-1PiGtYPrpOk0"

print("🔧 Testing Edge Functions with Local Odoo Secrets")
print("=" * 50)
print(f"Odoo URL: {ODOO_URL}")
print(f"Odoo Database: {ODOO_DATABASE}")
print(f"Odoo Username: {ODOO_USERNAME}")
print(f"Odoo Password: {'*' * len(ODOO_PASSWORD) if ODOO_PASSWORD else 'NOT SET'}")
print("=" * 50)

# First, let's verify the Odoo connection directly
print("\n🔍 Step 1: Verifying Odoo Connection Directly...")
try:
    import xmlrpc.client
    
    # Test authentication
    common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
    uid = common.authenticate(ODOO_DATABASE, ODOO_USERNAME, ODOO_PASSWORD, {})
    
    if uid:
        print(f"✅ Odoo authentication successful! UID: {uid}")
        
        # Test data access
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
        product_count = models.execute_kw(
            ODOO_DATABASE, uid, ODOO_PASSWORD,
            'product.product', 'search_count',
            [[['sale_ok', '=', True]]]
        )
        print(f"✅ Found {product_count} products in Odoo")
    else:
        print("❌ Odoo authentication failed")
        exit(1)
        
except Exception as e:
    print(f"❌ Odoo connection error: {e}")
    exit(1)

print("\n🚀 Step 2: Testing Edge Functions...")
print("\nℹ️  The edge functions need the following secrets set in Supabase:")
print(f"   ODOO_URL={ODOO_URL}")
print(f"   ODOO_DATABASE={ODOO_DATABASE}")
print(f"   ODOO_USERNAME={ODOO_USERNAME}")
print(f"   ODOO_PASSWORD={ODOO_PASSWORD}")

# Test edge functions
class EdgeFunctionTester:
    def __init__(self):
        self.base_url = f"{SUPABASE_URL}/functions/v1"
        self.headers = {
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Content-Type": "application/json"
        }
    
    def test_odoo_products_list(self):
        """Test listing products"""
        print("\n📦 Testing odoo-products - List Products...")
        
        url = f"{self.base_url}/odoo-products"
        params = {
            "limit": 5,
            "offset": 0
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Successfully fetched products")
            print(f"   Total products: {data.get('total', 0)}")
            print(f"   Returned: {len(data.get('products', []))}")
            
            if data.get('products'):
                print("\n   Sample products:")
                for product in data['products'][:3]:
                    print(f"   - {product['name']} (ID: {product['id']}, Price: ${product['price']})")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
                print(f"   Message: {error_data.get('message', 'No message')}")
            except:
                print(f"   Response: {response.text}")
            return False
    
    def run_test(self):
        """Run a single test to verify connection"""
        result = self.test_odoo_products_list()
        
        if not result:
            print("\n⚠️  Edge function test failed!")
            print("\n🔑 Please ensure these secrets are set in Supabase:")
            print("   1. Go to: https://supabase.com/dashboard/project/vkxoqaansgbyzcppdiii/settings/functions")
            print("   2. Add the following secrets:")
            print(f"      ODOO_URL={ODOO_URL}")
            print(f"      ODOO_DATABASE={ODOO_DATABASE}")
            print(f"      ODOO_USERNAME={ODOO_USERNAME}")
            print(f"      ODOO_PASSWORD={ODOO_PASSWORD}")
            print("\n   3. After adding secrets, the edge functions should work correctly")
        else:
            print("\n🎉 Edge function test passed!")
            print("   The edge functions are working correctly with Odoo")

if __name__ == "__main__":
    tester = EdgeFunctionTester()
    tester.run_test()