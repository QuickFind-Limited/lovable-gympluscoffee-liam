#!/usr/bin/env python3
"""Verify existing data and import all products without duplicates"""

import xmlrpc.client
import json
import os
from dotenv import load_dotenv
from collections import defaultdict

# Load environment variables
load_dotenv()

class CompleteImporter:
    def __init__(self):
        # Connect to Odoo
        self.url = os.getenv('odoo_url', 'https://source-gym-plus-coffee.odoo.com')
        self.db = os.getenv('db', 'source-gym-plus-coffee')
        self.username = os.getenv('username', 'admin@quickfindai.com')
        self.password = os.getenv('password', 'BJ62wX2J4yzjS$i')
        
        self.common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")
        
        self.uid = self.common.authenticate(self.db, self.username, self.password, {})
        print(f"✅ Connected to Odoo (UID: {self.uid})")
        
    def execute(self, model, method, *args):
        """Execute Odoo method"""
        return self.models.execute_kw(self.db, self.uid, self.password, model, method, *args)
    
    def verify_existing_data(self):
        """Check what's already in Odoo"""
        print("\n" + "="*60)
        print("📊 VERIFYING EXISTING DATA IN ODOO")
        print("="*60)
        
        # Count products
        product_count = self.execute('product.template', 'search_count', [[]])
        print(f"📦 Products in database: {product_count}")
        
        # Get existing product SKUs to avoid duplicates
        existing_products = self.execute('product.template', 'search_read', 
                                        [[]],
                                        {'fields': ['name', 'default_code', 'list_price']})
        
        existing_skus = set()
        for p in existing_products:
            if p.get('default_code'):
                existing_skus.add(p['default_code'])
                
        print(f"   - Unique SKUs: {len(existing_skus)}")
        
        # Sample of existing products
        if existing_products:
            print("\n   Sample products:")
            for p in existing_products[:5]:
                print(f"   - {p['name']} (SKU: {p.get('default_code', 'N/A')}, Price: ${p['list_price']})")
        
        # Count customers
        customer_count = self.execute('res.partner', 'search_count', 
                                     [[['customer_rank', '>', 0]]])
        print(f"\n👥 Customers in database: {customer_count}")
        
        # Count orders
        order_count = self.execute('sale.order', 'search_count', [[]])
        print(f"📋 Sales orders in database: {order_count}")
        
        # Get order details
        if order_count > 0:
            orders = self.execute('sale.order', 'search_read', 
                                [[]], 
                                {'fields': ['name', 'partner_id', 'amount_total', 'state'],
                                 'limit': 5})
            print("\n   Sample orders:")
            for o in orders:
                partner_name = o['partner_id'][1] if o['partner_id'] else 'N/A'
                print(f"   - {o['name']}: {partner_name}, Total: ${o['amount_total']}, State: {o['state']}")
        
        # Count categories
        category_count = self.execute('product.category', 'search_count', [[]])
        print(f"\n📁 Product categories: {category_count}")
        
        return existing_skus
    
    def import_all_products(self, existing_skus):
        """Import all products avoiding duplicates"""
        print("\n" + "="*60)
        print("📦 IMPORTING ALL GYM+COFFEE PRODUCTS")
        print("="*60)
        
        # Load product data
        with open('/workspaces/source-lovable-gympluscoffee/data/gym_plus_coffee_products.json', 'r') as f:
            data = json.load(f)
        
        total_products = len(data['products'])
        print(f"📊 Total products to process: {total_products}")
        print(f"📋 Existing SKUs to skip: {len(existing_skus)}")
        
        # Group by base product name for better organization
        product_groups = defaultdict(list)
        for product in data['products']:
            # Skip if SKU already exists
            if product['sku'] in existing_skus:
                continue
                
            # Group by base name (without size/color)
            base_name = product['name'].split(' - ')[0]
            product_groups[base_name].append(product)
        
        print(f"🎯 Unique product groups to import: {len(product_groups)}")
        
        created_count = 0
        skipped_count = len(existing_skus)
        failed_count = 0
        
        # Import products
        for base_name, variants in product_groups.items():
            # For now, create each variant as a separate product
            # In production, you'd create templates with proper variants
            for product in variants:
                try:
                    product_data = {
                        'name': product['name'],
                        'default_code': product['sku'],
                        'list_price': product['list_price'],
                        'standard_price': product.get('standard_cost', 0),
                        'description_sale': product.get('description', ''),
                    }
                    
                    # Add category if exists
                    if product.get('category'):
                        # Try to find category
                        cat_ids = self.execute('product.category', 'search', 
                                             [[['name', '=', product['category'].title()]]])
                        if cat_ids:
                            product_data['categ_id'] = cat_ids[0]
                    
                    # Create product
                    product_id = self.execute('product.template', 'create', [product_data])
                    created_count += 1
                    
                    if created_count % 10 == 0:
                        print(f"   Progress: {created_count} products created...")
                        
                except Exception as e:
                    failed_count += 1
                    if failed_count <= 5:  # Only show first 5 errors
                        print(f"   ❌ Failed: {product['name']} - {str(e)[:50]}")
        
        print(f"\n✅ Import Complete!")
        print(f"   - Created: {created_count} products")
        print(f"   - Skipped (duplicates): {skipped_count} products")
        print(f"   - Failed: {failed_count} products")
        
        return created_count
    
    def generate_sample_orders(self, count=10):
        """Generate more realistic orders using DataCo patterns"""
        print("\n" + "="*60)
        print("📋 GENERATING SAMPLE ORDERS")
        print("="*60)
        
        # Get all customers
        customer_ids = self.execute('res.partner', 'search', 
                                   [[['customer_rank', '>', 0]]])
        
        # Get all product variants
        product_ids = self.execute('product.product', 'search', 
                                  [[]], {'limit': 100})
        
        if not customer_ids or not product_ids:
            print("❌ Need customers and products to create orders")
            return 0
        
        import random
        created_orders = 0
        
        for i in range(min(count, len(customer_ids))):
            try:
                # Random customer
                customer_id = customer_ids[i % len(customer_ids)]
                
                # Random 1-5 products per order (DataCo average is 2.5)
                num_products = random.randint(1, 5)
                order_lines = []
                
                for _ in range(num_products):
                    product_id = random.choice(product_ids)
                    quantity = random.randint(1, 3)
                    
                    order_lines.append((0, 0, {
                        'product_id': product_id,
                        'product_uom_qty': quantity
                    }))
                
                # Create order
                order_id = self.execute('sale.order', 'create', [{
                    'partner_id': customer_id,
                    'order_line': order_lines
                }])
                
                created_orders += 1
                
            except Exception as e:
                print(f"   ❌ Failed to create order: {str(e)[:50]}")
        
        print(f"✅ Created {created_orders} orders")
        return created_orders
    
    def run(self):
        """Run complete import and verification"""
        # First verify what's already there
        existing_skus = self.verify_existing_data()
        
        # Import all products (avoiding duplicates)
        products_created = self.import_all_products(existing_skus)
        
        # Generate some sample orders if products were created
        if products_created > 0 or len(existing_skus) > 0:
            self.generate_sample_orders(10)
        
        # Final verification
        print("\n" + "="*60)
        print("📊 FINAL DATABASE STATE")
        print("="*60)
        
        final_product_count = self.execute('product.template', 'search_count', [[]])
        final_customer_count = self.execute('res.partner', 'search_count', 
                                           [[['customer_rank', '>', 0]]])
        final_order_count = self.execute('sale.order', 'search_count', [[]])
        
        print(f"📦 Total products: {final_product_count}")
        print(f"👥 Total customers: {final_customer_count}")
        print(f"📋 Total orders: {final_order_count}")
        
        # Save summary
        summary = {
            'products': final_product_count,
            'customers': final_customer_count,
            'orders': final_order_count,
            'products_created_this_run': products_created
        }
        
        with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/import_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        print("\n💾 Summary saved to import_summary.json")
        
        return summary

if __name__ == "__main__":
    importer = CompleteImporter()
    importer.run()