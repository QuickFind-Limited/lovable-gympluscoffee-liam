#!/usr/bin/env python3
"""
Test Odoo Edge Functions using Service Role Key
"""
import requests
import json
from datetime import datetime

# Supabase project configuration
SUPABASE_URL = "https://vkxoqaansgbyzcppdiii.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Mzk3MTQ4MiwiZXhwIjoyMDY5NTQ3NDgyfQ.Ip7h5Xiiv9V13ihQRNSGkCJHsKRGlY-1PiGtYPrpOk0"

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
                    print(f"   - {product['name']} (ID: {product['id']})")
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
                    print(f"   Description: {product.get('description', 'N/A')[:100]}...")
                    if product.get('category_name'):
                        print(f"   Category: {product['category_name']}")
                    return True
                else:
                    print(f"❌ Failed to get product: {response.status_code} - {response.text}")
                    return False
        
        print("❌ No products available to test")
        return False
    
    def test_odoo_categories(self):
        """Test categories endpoint"""
        print("\n📁 Testing odoo-categories...")
        
        # Test flat view
        url = f"{self.base_url}/odoo-categories"
        params = {"view": "flat"}
        
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            categories = data.get('categories', [])
            print(f"✅ Successfully fetched categories (flat view)")
            print(f"   Total categories: {len(categories)}")
            print(f"   View: {data.get('view')}")
            
            if categories:
                print("\n   Sample categories:")
                for cat in categories[:5]:
                    indent = "  " * cat.get('level', 0)
                    print(f"   {indent}- {cat['display_name']} (ID: {cat['id']})")
            
            # Test tree view
            tree_response = requests.get(f"{self.base_url}/odoo-categories?view=tree", headers=self.headers)
            if tree_response.status_code == 200:
                tree_data = tree_response.json()
                print(f"\n✅ Tree view also working")
                print(f"   Root categories: {len(tree_data.get('categories', []))}")
            
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
            "notes": "Test order from edge function integration test"
        }
        
        if len(products) > 1:
            order_data["items"].append({
                "product_id": products[1]['id'],
                "quantity": 1,
                "price": products[1]['price'],
                "product_name": products[1]['name']
            })
        
        print(f"   Creating order with {len(order_data['items'])} items:")
        for item in order_data['items']:
            print(f"   - {item['quantity']}x {item['product_name']} @ ${item['price']}")
        
        response = requests.post(url, headers=self.headers, json=order_data)
        
        if response.status_code == 201:
            order = response.json()
            print(f"✅ Order created successfully!")
            print(f"   Order ID: {order['id']}")
            print(f"   Order Name: {order['name']}")
            print(f"   Total: ${order['amount_total']}")
            print(f"   State: {order['state']}")
            print(f"   Partner: {order.get('partner_name', 'N/A')}")
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
                    print(f"   - {order['name']} - ${order['amount_total']} ({order['state']}) - {order['date_order'][:10]}")
            else:
                print("   No orders found (this is normal if no orders have been created)")
            return True
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
    
    def test_odoo_orders_single(self):
        """Test getting single order with details"""
        print("\n📄 Testing odoo-orders - Get Single Order...")
        
        # First list orders to get an ID
        list_url = f"{self.base_url}/odoo-orders?limit=1"
        list_response = requests.get(list_url, headers=self.headers)
        
        if list_response.status_code == 200:
            orders = list_response.json().get('orders', [])
            if orders:
                order_id = orders[0]['id']
                print(f"   Testing with order ID: {order_id}")
                
                # Get single order
                url = f"{self.base_url}/odoo-orders/{order_id}"
                response = requests.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    order = response.json()
                    print(f"✅ Successfully fetched order details")
                    print(f"   Order: {order['name']}")
                    print(f"   Total: ${order['amount_total']}")
                    print(f"   State: {order['state']}")
                    
                    if order.get('order_lines'):
                        print(f"   Order lines: {len(order['order_lines'])}")
                        for line in order['order_lines']:
                            print(f"     - {line['name']} x{line['product_uom_qty']} @ ${line['price_unit']}")
                    return True
                else:
                    print(f"❌ Failed to get order: {response.status_code} - {response.text}")
                    return False
        
        print("   No orders available to test single order endpoint")
        return True  # Not a failure if no orders exist
    
    def run_all_tests(self):
        """Run all tests"""
        print("🧪 Starting Odoo Edge Functions Tests (Service Role)")
        print("=" * 50)
        print(f"🔗 Testing against: {SUPABASE_URL}")
        print(f"🔑 Using service role authentication")
        
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
        results.append(("odoo-orders - Single", self.test_odoo_orders_single()))
        
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
            print("\n🎉 All tests passed! Edge functions are working correctly with Odoo.")
        else:
            print(f"\n⚠️  {total - passed} tests failed. Please check the logs above.")
        
        # Additional information
        print("\n📝 Notes:")
        print("- All functions require authentication (service role key used for testing)")
        print("- Products are fetched from live Odoo instance")
        print("- Orders are created as draft orders in Odoo")
        print("- Categories show the full hierarchy from Odoo")

if __name__ == "__main__":
    tester = EdgeFunctionTester()
    tester.run_all_tests()