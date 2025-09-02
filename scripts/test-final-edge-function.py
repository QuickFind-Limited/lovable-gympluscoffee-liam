#!/usr/bin/env python3
import requests
import json

# Test the odoo-suppliers-final edge function
url = "https://vkxoqaansgbyzcppdiii.supabase.co/functions/v1/odoo-suppliers-final"
anon_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE"

headers = {
    'Authorization': f'Bearer {anon_key}',
    'Content-Type': 'application/json'
}

# Test 1: Get suppliers with products
print("=== Testing supplier fetch with products ===")
params = {
    'withProducts': 'true',
    'limit': '10'
}

try:
    response = requests.get(url, headers=headers, params=params)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        if 'suppliers' in data:
            print(f"\nFound {len(data['suppliers'])} suppliers")
            for supplier in data['suppliers']:
                print(f"\n- {supplier.get('name', 'Unknown')} (ID: {supplier.get('id', 'Unknown')})")
                print(f"  Email: {supplier.get('email', 'N/A')}")
                print(f"  Phone: {supplier.get('phone', 'N/A')}")
                print(f"  City: {supplier.get('city', 'N/A')}")
                print(f"  Product Count: {supplier.get('product_count', 0)}")
        else:
            print("\nNo suppliers key in response")
            print(json.dumps(data, indent=2))
    else:
        print(f"\nError response: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")

# Test 2: Get products for a specific supplier (ID 23 - European Pet Distributors)
print("\n\n=== Testing product fetch for supplier ID 23 ===")
params = {
    'supplierId': '23',
    'limit': '5'
}

try:
    response = requests.get(url, headers=headers, params=params)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        if 'data' in data:
            print(f"\nFound {len(data['data'])} products")
            print(f"Total products: {data.get('total', 'Unknown')}")
            
            for product in data['data']:
                print(f"\n- {product.get('product_name', 'Unknown')}")
                print(f"  Code: {product.get('product_code', 'N/A')}")
                print(f"  Price: ${product.get('price', 0):.2f}")
                print(f"  Min Qty: {product.get('min_qty', 0)}")
                print(f"  Lead Time: {product.get('delay', 0)} days")
        else:
            print("\nNo data key in response")
            print(json.dumps(data, indent=2))
    else:
        print(f"\nError response: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")