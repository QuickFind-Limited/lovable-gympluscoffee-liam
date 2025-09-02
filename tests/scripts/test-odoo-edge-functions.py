E#!/usr/bin/env python3
"""
Test Odoo Edge Functions with real API calls
"""
import requests
import json
from datetime import datetime

# Supabase project configuration
SUPABASE_URL = "https://vkxoqaansgbyzcppdiii.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE"

# Test user credentials
TEST_EMAIL = "test@animalfarmacy.com"
TEST_PASSWORD = "testpassword123"

class EdgeFunctionTester:
    def __init__(self):
        self.base_url = f"{SUPABASE_URL}/functions/v1"
        self.auth_token = None
        self.headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Content-Type": "application/json"
        }
    
    def create_test_user(self):
        """Create a test user for authentication"""
        print("\n🔐 Creating test user...")
        
        # Sign up
        signup_url = f"{SUPABASE_URL}/auth/v1/signup"
        signup_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        response = requests.post(signup_url, json=signup_data, headers=self.headers)
        
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get("access_token")
            print(f"✅ Test user created/logged in successfully")
            self.headers["Authorization"] = f"Bearer {self.auth_token}"
            return True
        elif response.status_code == 400:
            # User might already exist, try to login
            return self.login_test_user()
        else:
            print(f"❌ Failed to create user: {response.status_code} - {response.text}")
            return False
    
    def login_test_user(self):
        """Login with test user"""
        print("\n🔐 Logging in test user...")
        
        login_url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
        login_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        response = requests.post(login_url, json=login_data, headers=self.headers)
        
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get("access_token")
            print(f"✅ Logged in successfully")
            self.headers["Authorization"] = f"Bearer {self.auth_token}"
            return True
        else:
            print(f"❌ Failed to login: {response.status_code} - {response.text}")
            return False
    
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
                    print(f"   - {product['name']} (${product['price']})")
            return True
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
    
    def test_odoo_products_search(self):
        """Test searching products"""
        print("\n🔍 Testing odoo-products - Search...")
        
        url = f"{self.base_url}/odoo-products"
        params = {
            "search": "hose",
            "limit": 5
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Search successful")
            print(f"   Found: {len(data.get('products', []))} products matching 'hose'")
            
            if data.get('products'):
                for product in data['products']:
                    print(f"   - {product['name']}")
            return True
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
    
    def test_odoo_products_single(self):
        """Test getting single product"""
        print("\n📦 Testing odoo-products - Get Single Product...")
        
        # First get a product ID
        list_url = f"{self.base_url}/odoo-products?limit=1"
        list_response = requests.get(list_url, headers=self.headers)
        
        if list_response.status_code == 200:
            products = list_response.json().get('products', [])
            if products:
                product_id = products[0]['id']
                print(f"   Testing with product ID: {product_id}")
                
                # Get single product
                url = f"{self.base_url}/odoo-products/{product_id}"
                response = requests.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    product = response.json()
                    print(f"✅ Successfully fetched product")
                    print(f"   Name: {product['name']}")
                    print(f"   Price: ${product['price']}")
                    print(f"   Description: {product.get('description', 'N/A')[:50]}...")
                    return True
                else:
                    print(f"❌ Failed to get product: {response.status_code} - {response.text}")
                    return False
        
        print("❌ No products available to test")
        return False
    
    def test_odoo_categories(self):
        """Test categories endpoint"""
        print("\n📁 Testing odoo-categories...")
        
        url = f"{self.base_url}/odoo-categories"
        params = {"view": "flat"}
        
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            categories = data.get('categories', [])
            print(f"✅ Successfully fetched categories")
            print(f"   Total categories: {len(categories)}")
            print(f"   View: {data.get('view')}")
            
            if categories:
                print("\n   Sample categories:")
                for cat in categories[:5]:
                    indent = "  " * cat.get('level', 0)
                    print(f"   {indent}- {cat['display_name']}")
            return True
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
    
    def test_odoo_orders_create(self):
        """Test creating an order"""
        print("\n🛒 Testing odoo-orders - Create Order...")
        
        # First get some products
        products_url = f"{self.base_url}/odoo-products?limit=2"
        products_response = requests.get(products_url, headers=self.headers)
        
        if products_response.status_code != 200:
            print("❌ Failed to get products for order")
            return False
        
        products = products_response.json().get('products', [])
        if len(products) < 1:
            print("❌ No products available for order")
            return False
        
        # Create order
        url = f"{self.base_url}/odoo-orders"
        order_data = {
            "items": [
                {
                    "product_id": products[0]['id'],
                    "quantity": 2,
                    "price": products[0]['price'],
                    "product_name": products[0]['name']
                }
            ],
            "shipping_address": {
                "street": "123 Test Street",
                "city": "Test City",
                "state": "CA",
                "zip": "12345",
                "country": "US"
            },
            "notes": "Test order from edge function"
        }
        
        if len(products) > 1:
            order_data["items"].append({
                "product_id": products[1]['id'],
                "quantity": 1,
                "price": products[1]['price'],
                "product_name": products[1]['name']
            })
        
        print(f"   Creating order with {len(order_data['items'])} items...")
        response = requests.post(url, headers=self.headers, json=order_data)
        
        if response.status_code == 201:
            order = response.json()
            print(f"✅ Order created successfully")
            print(f"   Order ID: {order['id']}")
            print(f"   Order Name: {order['name']}")
            print(f"   Total: ${order['amount_total']}")
            print(f"   State: {order['state']}")
            return True
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
    
    def test_odoo_orders_list(self):
        """Test listing orders"""
        print("\n📋 Testing odoo-orders - List Orders...")
        
        url = f"{self.base_url}/odoo-orders"
        params = {"limit": 10}
        
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            orders = data.get('orders', [])
            print(f"✅ Successfully fetched orders")
            print(f"   Total orders: {data.get('total', 0)}")
            
            if orders:
                print("\n   Recent orders:")
                for order in orders[:3]:
                    print(f"   - {order['name']} - ${order['amount_total']} ({order['state']})")
            else:
                print("   No orders found for this user")
            return True
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🧪 Starting Odoo Edge Functions Tests")
        print("=" * 50)
        
        # Setup authentication
        if not self.create_test_user():
            print("\n❌ Failed to authenticate. Cannot proceed with tests.")
            return
        
        # Track results
        results = []
        
        # Test odoo-products
        results.append(("odoo-products - List", self.test_odoo_products_list()))
        results.append(("odoo-products - Search", self.test_odoo_products_search()))
        results.append(("odoo-products - Single", self.test_odoo_products_single()))
        
        # Test odoo-categories
        results.append(("odoo-categories", self.test_odoo_categories()))
        
        # Test odoo-orders
        results.append(("odoo-orders - Create", self.test_odoo_orders_create()))
        results.append(("odoo-orders - List", self.test_odoo_orders_list()))
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 All tests passed! Edge functions are working correctly.")
        else:
            print(f"\n⚠️  {total - passed} tests failed. Please check the logs above.")

if __name__ == "__main__":
    tester = EdgeFunctionTester()
    tester.run_all_tests()