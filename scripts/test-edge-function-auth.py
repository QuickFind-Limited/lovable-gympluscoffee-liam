#!/usr/bin/env python3
import requests
import json

# Test the odoo-test-xml edge function
url = "https://vkxoqaansgbyzcppdiii.supabase.co/functions/v1/odoo-test-xml"
anon_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE"

headers = {
    'Authorization': f'Bearer {anon_key}',
    'Content-Type': 'application/json'
}

try:
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n=== Response ===")
        print(json.dumps(data, indent=2))
        
        # Check if we got supplier IDs
        if 'supplierIds' in data:
            print(f"\nFound {len(data['supplierIds'])} supplier IDs: {data['supplierIds']}")
        
        # Check if we got supplier data
        if 'suppliers' in data:
            print(f"\nFound {len(data['suppliers'])} suppliers with details")
            for supplier in data['suppliers']:
                print(f"  - {supplier.get('name', 'Unknown')} (ID: {supplier.get('id', 'Unknown')})")
                
    else:
        print(f"\nError response: {response.text}")
except Exception as e:
    print(f"Error: {e}")