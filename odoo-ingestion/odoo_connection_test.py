#!/usr/bin/env python3
"""
Test Odoo connection and setup instance for MCP tools
"""

import xmlrpc.client
import json
import sys

def test_odoo_connection():
    """Test connection to Odoo instance"""
    
    # Connection parameters
    url = "https://source-gym-plus-coffee.odoo.com/"
    db = "source-gym-plus-coffee"
    username = "admin@quickfindai.com"
    password = "BJ62wX2J4yzjS$i"
    
    print(f"🔗 Testing connection to: {url}")
    print(f"📊 Database: {db}")
    print(f"👤 Username: {username}")
    
    try:
        # Test common endpoint (version info)
        common = xmlrpc.client.ServerProxy(f'{url}xmlrpc/2/common')
        version = common.version()
        
        print(f"✅ Connection successful!")
        print(f"📋 Server version: {version}")
        
        # Test authentication
        uid = common.authenticate(db, username, password, {})
        
        if uid:
            print(f"✅ Authentication successful! User ID: {uid}")
            
            # Test model access
            models = xmlrpc.client.ServerProxy(f'{url}xmlrpc/2/object')
            
            # Check access to partners model
            partner_count = models.execute_kw(
                db, uid, password,
                'res.partner', 'search_count', [[]]
            )
            
            print(f"✅ Model access successful!")
            print(f"📊 Total partners in database: {partner_count}")
            
            # Get some sample partner data
            partner_ids = models.execute_kw(
                db, uid, password,
                'res.partner', 'search', [[]], {'limit': 5}
            )
            
            partners = models.execute_kw(
                db, uid, password,
                'res.partner', 'read', [partner_ids], {'fields': ['name', 'email']}
            )
            
            print(f"🔍 Sample partners:")
            for partner in partners:
                print(f"  - {partner['name']} ({partner.get('email', 'no email')})")
            
            return {
                'success': True,
                'url': url,
                'db': db,
                'uid': uid,
                'partner_count': partner_count
            }
        else:
            print("❌ Authentication failed!")
            return {'success': False, 'error': 'Authentication failed'}
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return {'success': False, 'error': str(e)}

def create_sample_customer():
    """Create a sample customer to test the full workflow"""
    
    url = "https://source-gym-plus-coffee.odoo.com/"
    db = "source-gym-plus-coffee"
    username = "admin@quickfindai.com"
    password = "BJ62wX2J4yzjS$i"
    
    try:
        common = xmlrpc.client.ServerProxy(f'{url}xmlrpc/2/common')
        uid = common.authenticate(db, username, password, {})
        models = xmlrpc.client.ServerProxy(f'{url}xmlrpc/2/object')
        
        # Create sample customer
        customer_data = {
            'name': 'Test Import Customer',
            'email': 'testimport@example.com', 
            'phone': '+1-555-TEST',
            'street': '123 Test Street',
            'city': 'Test City',
            'zip': '12345',
            'country_id': 233,  # United States
            'is_company': False,
            'customer_rank': 1
        }
        
        print(f"\n🧪 Creating test customer...")
        
        # Check if customer already exists
        existing = models.execute_kw(
            db, uid, password,
            'res.partner', 'search', [
                [['email', '=', customer_data['email']]]
            ]
        )
        
        if existing:
            print(f"⚠️ Test customer already exists (ID: {existing[0]})")
            return existing[0]
        
        # Create customer
        customer_id = models.execute_kw(
            db, uid, password,
            'res.partner', 'create', [customer_data]
        )
        
        print(f"✅ Test customer created successfully! ID: {customer_id}")
        
        # Verify creation
        created_customer = models.execute_kw(
            db, uid, password,
            'res.partner', 'read', [customer_id], 
            {'fields': ['name', 'email', 'phone', 'city']}
        )
        
        print(f"✅ Verification successful:")
        print(f"   Name: {created_customer['name']}")
        print(f"   Email: {created_customer['email']}")
        print(f"   Phone: {created_customer['phone']}")
        print(f"   City: {created_customer['city']}")
        
        return customer_id
        
    except Exception as e:
        print(f"❌ Failed to create test customer: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Odoo Connection Test Starting...")
    
    # Test connection
    result = test_odoo_connection()
    
    if result['success']:
        print(f"\n🎉 Connection test passed!")
        
        # Create sample customer
        customer_id = create_sample_customer()
        
        if customer_id:
            print(f"\n🎯 Ready to proceed with mass import!")
            print(f"✅ Connection verified")
            print(f"✅ Authentication verified")
            print(f"✅ Model access verified")
            print(f"✅ Create operations verified")
            
        else:
            print(f"\n⚠️ Connection works but creation failed")
    else:
        print(f"\n❌ Connection test failed: {result.get('error')}")
        sys.exit(1)