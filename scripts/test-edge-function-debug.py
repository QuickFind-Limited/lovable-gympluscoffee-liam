#!/usr/bin/env python3
import requests
import json

# Test the odoo-test-xml edge function
url = "https://jxqigmykrtnphxbtwyew.supabase.co/functions/v1/odoo-test-xml"

# Note: We need the anon key for this to work
# For now, let's try without auth to see what happens
headers = {
    'Content-Type': 'application/json'
}

try:
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        data = response.json()
        print("\nResponse:")
        print(json.dumps(data, indent=2))
    else:
        print(f"\nError response: {response.text}")
except Exception as e:
    print(f"Error: {e}")