#!/usr/bin/env python3
"""Test Odoo connection and basic operations"""

import xmlrpc.client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    """Test connection to Odoo"""
    
    # Get credentials from environment
    url = os.getenv('odoo_url', 'https://source-gym-plus-coffee.odoo.com')
    db = os.getenv('db', 'source-gym-plus-coffee')
    username = os.getenv('username', 'admin@quickfindai.com')
    password = os.getenv('password', 'BJ62wX2J4yzjS$i')
    
    print(f"🔗 Connecting to Odoo...")
    print(f"   URL: {url}")
    print(f"   Database: {db}")
    print(f"   Username: {username}")
    
    try:
        # Create connection
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
        
        # Test version
        version = common.version()
        print(f"✅ Connected to Odoo version: {version.get('server_version', 'Unknown')}")
        
        # Authenticate
        uid = common.authenticate(db, username, password, {})
        
        if uid:
            print(f"✅ Authentication successful! UID: {uid}")
            
            # Create models proxy
            models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
            
            # Test access - count existing products
            product_count = models.execute_kw(
                db, uid, password,
                'product.product', 'search_count',
                [[]]
            )
            print(f"📊 Current products in database: {product_count}")
            
            # Count customers
            customer_count = models.execute_kw(
                db, uid, password,
                'res.partner', 'search_count',
                [[['customer_rank', '>', 0]]]
            )
            print(f"👥 Current customers in database: {customer_count}")
            
            # Count sales orders
            order_count = models.execute_kw(
                db, uid, password,
                'sale.order', 'search_count',
                [[]]
            )
            print(f"📋 Current sales orders in database: {order_count}")
            
            return True
        else:
            print("❌ Authentication failed!")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

if __name__ == "__main__":
    test_connection()