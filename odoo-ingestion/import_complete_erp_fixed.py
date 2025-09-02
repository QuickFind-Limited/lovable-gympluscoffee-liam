#!/usr/bin/env python3
"""Import complete ERP data - Fixed version"""

import xmlrpc.client
import json
import os
import random
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class CompleteERPImporter:
    def __init__(self):
        # Connect to Odoo
        self.url = os.getenv('odoo_url', 'https://source-gym-plus-coffee.odoo.com')
        self.db = os.getenv('db', 'source-gym-plus-coffee')
        self.username = os.getenv('username', 'admin@quickfindai.com')
        self.password = os.getenv('password', 'BJ62wX2J4yzjS$i')
        
        print("🔗 Connecting to Odoo...")
        self.common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")
        self.uid = self.common.authenticate(self.db, self.username, self.password, {})
        print(f"✅ Connected (UID: {self.uid})\n")
        
        # Track created records
        self.created_customers = []
        self.created_orders = []
        
    def execute(self, model, method, *args):
        """Execute Odoo method"""
        return self.models.execute_kw(self.db, self.uid, self.password, model, method, *args)
    
    def create_more_customers(self, count=50):
        """Create additional customers"""
        print("=" * 60)
        print(f"👥 CREATING {count} MORE CUSTOMERS")
        print("=" * 60)
        
        # Check existing
        existing_count = self.execute('res.partner', 'search_count', 
                                     [[['customer_rank', '>', 0]]])
        print(f"   Existing customers: {existing_count}")
        
        # Customer data
        first_names = ['Alice', 'Bob', 'Charlie', 'Diana', 'Edward', 'Fiona', 
                       'George', 'Helen', 'Ian', 'Julia', 'Kevin', 'Laura',
                       'Martin', 'Nancy', 'Oliver', 'Paula', 'Quinn', 'Rachel']
        
        last_names = ['O\'Brien', 'Murphy', 'Kelly', 'Sullivan', 'Walsh', 
                      'Ryan', 'Connor', 'Fitzgerald', 'McCarthy', 'O\'Neill',
                      'Burke', 'Collins', 'Campbell', 'Clarke', 'Hughes']
        
        cities = ['Dublin', 'Cork', 'Galway', 'Limerick', 'Waterford', 'Kilkenny']
        streets = ['Main Street', 'High Street', 'Church Road', 'Park Avenue']
        
        created = 0
        
        for i in range(count):
            fname = random.choice(first_names)
            lname = random.choice(last_names)
            
            customer_data = {
                'name': f"{fname} {lname}",
                'email': f"{fname.lower()}.{lname.lower().replace('\'', '')}@email.com",
                'customer_rank': 1,
                'is_company': False,
                'street': f"{random.randint(1, 999)} {random.choice(streets)}",
                'city': random.choice(cities),
                'country_id': 103,  # Ireland
                'phone': f"+353 {random.randint(10000000, 99999999)}"
            }
            
            try:
                customer_id = self.execute('res.partner', 'create', [customer_data])
                self.created_customers.append(customer_id)
                created += 1
                if created % 10 == 0:
                    print(f"   Created {created} customers...")
            except Exception as e:
                pass  # Skip errors
        
        print(f"\n✅ Created {created} additional customers")
        return created
    
    def create_more_orders(self, count=100):
        """Create more sales orders"""
        print("\n" + "=" * 60)
        print(f"📋 CREATING {count} MORE SALES ORDERS")
        print("=" * 60)
        
        # Get customers
        customer_ids = self.execute('res.partner', 'search', 
                                   [[['customer_rank', '>', 0]]])
        
        # Get products  
        product_ids = self.execute('product.product', 'search', [[]])
        
        if not customer_ids or not product_ids:
            print("   ❌ Need customers and products")
            return 0
        
        print(f"   Using {len(customer_ids)} customers and {len(product_ids)} products")
        
        created = 0
        failed = 0
        
        for i in range(count):
            try:
                # Simple order creation
                customer_id = random.choice(customer_ids)
                num_items = random.randint(1, 4)
                
                order_lines = []
                for _ in range(num_items):
                    product_id = random.choice(product_ids)
                    quantity = random.randint(1, 3)
                    
                    order_lines.append((0, 0, {
                        'product_id': product_id,
                        'product_uom_qty': quantity
                    }))
                
                # Create order WITHOUT date or state (use defaults)
                order_data = {
                    'partner_id': customer_id,
                    'order_line': order_lines
                }
                
                order_id = self.execute('sale.order', 'create', [order_data])
                self.created_orders.append(order_id)
                created += 1
                
                if created % 20 == 0:
                    print(f"   Created {created} orders...")
                    
            except Exception as e:
                failed += 1
                if failed <= 3:
                    print(f"   ⚠️ Order failed: {str(e)[:100]}")
        
        print(f"\n✅ Created {created} sales orders")
        if failed > 0:
            print(f"   ⚠️ Failed: {failed} orders")
        
        return created
    
    def set_basic_inventory(self):
        """Set basic inventory levels"""
        print("\n" + "=" * 60)
        print("📊 SETTING INVENTORY LEVELS")
        print("=" * 60)
        
        try:
            # Get products
            products = self.execute('product.product', 'search_read', 
                                   [[]], {'fields': ['id', 'name'], 'limit': 100})
            
            if not products:
                print("   ❌ No products found")
                return 0
            
            print(f"   Setting inventory for {len(products)} products...")
            
            # Try to find stock location
            location_ids = self.execute('stock.location', 'search', 
                                       [[['usage', '=', 'internal']]], {'limit': 1})
            
            if not location_ids:
                print("   ⚠️ Stock module not configured, skipping inventory")
                return 0
            
            location_id = location_ids[0]
            updated = 0
            
            for product in products[:50]:  # Just do first 50
                try:
                    quantity = random.randint(10, 100)
                    
                    # Try to create or update stock
                    existing = self.execute('stock.quant', 'search', [
                        [['product_id', '=', product['id']],
                         ['location_id', '=', location_id]]
                    ])
                    
                    if existing:
                        # Update existing
                        self.execute('stock.quant', 'write', 
                                   [existing[0], {'quantity': quantity}])
                    else:
                        # Create new
                        self.execute('stock.quant', 'create', [{
                            'product_id': product['id'],
                            'location_id': location_id,
                            'quantity': quantity
                        }])
                    
                    updated += 1
                    
                except Exception as e:
                    pass  # Skip errors
            
            print(f"\n✅ Set inventory for {updated} products")
            return updated
            
        except Exception as e:
            print(f"   ⚠️ Inventory module issue: {str(e)[:100]}")
            return 0
    
    def confirm_some_orders(self):
        """Confirm some orders"""
        print("\n" + "=" * 60)
        print("✅ CONFIRMING ORDERS")
        print("=" * 60)
        
        try:
            # Get draft orders
            draft_orders = self.execute('sale.order', 'search', 
                                       [[['state', '=', 'draft']]], {'limit': 20})
            
            if not draft_orders:
                print("   No draft orders to confirm")
                return 0
            
            confirmed = 0
            for order_id in draft_orders:
                try:
                    # Try to confirm order
                    self.execute('sale.order', 'action_confirm', [[order_id]])
                    confirmed += 1
                except:
                    pass
            
            print(f"   ✅ Confirmed {confirmed} orders")
            return confirmed
            
        except Exception as e:
            print(f"   ⚠️ Could not confirm orders: {str(e)[:50]}")
            return 0
    
    def run_complete_import(self):
        """Run the complete import"""
        print("\n🚀 " + "=" * 56 + " 🚀")
        print("    COMPLETING ERP DATA FOR GYM+COFFEE")
        print("🚀 " + "=" * 56 + " 🚀\n")
        
        start_time = time.time()
        
        # Create more customers
        customers_created = self.create_more_customers(50)
        
        # Create sales orders
        orders_created = self.create_more_orders(100)
        
        # Set inventory
        inventory_set = self.set_basic_inventory()
        
        # Confirm some orders
        orders_confirmed = self.confirm_some_orders()
        
        elapsed = time.time() - start_time
        
        # Summary
        print("\n" + "=" * 60)
        print("🎉 ERP DATA IMPORT COMPLETE!")
        print("=" * 60)
        
        print("\n📊 RESULTS:")
        print(f"   ✅ New customers: {customers_created}")
        print(f"   ✅ New orders: {orders_created}")
        print(f"   ✅ Products with inventory: {inventory_set}")
        print(f"   ✅ Orders confirmed: {orders_confirmed}")
        print(f"   ⏱️ Time: {elapsed:.1f} seconds")
        
        # Final counts
        print("\n📈 FINAL ODOO STATE:")
        
        product_count = self.execute('product.template', 'search_count', [[]])
        customer_count = self.execute('res.partner', 'search_count', 
                                     [[['customer_rank', '>', 0]]])
        order_count = self.execute('sale.order', 'search_count', [[]])
        confirmed_count = self.execute('sale.order', 'search_count', 
                                      [[['state', 'in', ['sale', 'done']]]])
        
        print(f"   📦 Products: {product_count}")
        print(f"   👥 Customers: {customer_count}")
        print(f"   📋 Total orders: {order_count}")
        print(f"   ✅ Confirmed orders: {confirmed_count}")
        
        print("\n🎊 Your Gym+Coffee Odoo ERP is ready!")
        
        return {
            'customers': customers_created,
            'orders': orders_created,
            'inventory': inventory_set,
            'confirmed': orders_confirmed
        }

if __name__ == "__main__":
    importer = CompleteERPImporter()
    importer.run_complete_import()