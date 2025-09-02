#!/usr/bin/env python3
"""Import Gym+Coffee products into Odoo"""

import xmlrpc.client
import json
import os
import sys
from dotenv import load_dotenv
from datetime import datetime
import random

# Load environment variables
load_dotenv()

class GymCoffeeImporter:
    def __init__(self):
        # Get credentials
        self.url = os.getenv('odoo_url', 'https://source-gym-plus-coffee.odoo.com')
        self.db = os.getenv('db', 'source-gym-plus-coffee')
        self.username = os.getenv('username', 'admin@quickfindai.com')
        self.password = os.getenv('password', 'BJ62wX2J4yzjS$i')
        
        # Connect
        self.common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")
        
        # Authenticate
        self.uid = self.common.authenticate(self.db, self.username, self.password, {})
        if not self.uid:
            raise Exception("Authentication failed!")
        
        print(f"✅ Connected to Odoo (UID: {self.uid})")
        
        # Cache for created records
        self.created_products = {}
        self.created_customers = []
        self.created_categories = {}
        self.created_attributes = {}
        
    def execute(self, model, method, *args):
        """Execute Odoo method"""
        return self.models.execute_kw(self.db, self.uid, self.password, model, method, *args)
    
    def create_product_categories(self):
        """Create product categories from Gym+Coffee data"""
        print("\n📁 Creating product categories...")
        
        categories = [
            "hoodies", "joggers", "t-shirts", "accessories", 
            "shorts", "sports-bras", "jackets", "tops", 
            "beanies", "leggings"
        ]
        
        for cat_name in categories:
            # Check if category exists
            existing = self.execute('product.category', 'search', [
                [('name', '=', cat_name.title())]
            ])
            
            if existing:
                self.created_categories[cat_name] = existing[0]
                print(f"   Found existing category: {cat_name.title()}")
            else:
                cat_id = self.execute('product.category', 'create', [{
                    'name': cat_name.title(),
                    'parent_id': False
                }])
                self.created_categories[cat_name] = cat_id
                print(f"   ✅ Created category: {cat_name.title()}")
        
        return self.created_categories
    
    def create_product_attributes(self):
        """Create size and color attributes"""
        print("\n🎨 Creating product attributes...")
        
        # Create Size attribute
        size_attr_id = self.execute('product.attribute', 'create', [{
            'name': 'Size',
            'display_type': 'radio',
            'create_variant': 'always'
        }])
        
        # Create size values
        sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
        size_values = {}
        for size in sizes:
            val_id = self.execute('product.attribute.value', 'create', [{
                'name': size,
                'attribute_id': size_attr_id
            }])
            size_values[size] = val_id
        
        # Create Color attribute
        color_attr_id = self.execute('product.attribute', 'create', [{
            'name': 'Color',
            'display_type': 'color',
            'create_variant': 'always'
        }])
        
        # Create color values
        colors = {
            'Black': '#000000',
            'White': '#FFFFFF',
            'Navy': '#000080',
            'Grey': '#808080',
            'Blue': '#0000FF',
            'Green': '#008000',
            'Red': '#FF0000',
            'Pink': '#FFC0CB'
        }
        color_values = {}
        for color, html_color in colors.items():
            val_id = self.execute('product.attribute.value', 'create', [{
                'name': color,
                'attribute_id': color_attr_id,
                'html_color': html_color
            }])
            color_values[color] = val_id
        
        self.created_attributes = {
            'size': {'attr_id': size_attr_id, 'values': size_values},
            'color': {'attr_id': color_attr_id, 'values': color_values}
        }
        
        print(f"   ✅ Created Size attribute with {len(sizes)} values")
        print(f"   ✅ Created Color attribute with {len(colors)} values")
        
        return self.created_attributes
    
    def import_products(self, limit=20):
        """Import Gym+Coffee products"""
        print(f"\n📦 Importing Gym+Coffee products (limit: {limit})...")
        
        # Load product data
        with open('/workspaces/source-lovable-gympluscoffee/data/gym_plus_coffee_products.json', 'r') as f:
            data = json.load(f)
        
        products = data['products'][:limit]
        
        # Group products by base name (for variants)
        product_groups = {}
        for product in products:
            base_name = product['name'].rsplit(' - ', 1)[0]  # Remove color suffix
            if base_name not in product_groups:
                product_groups[base_name] = []
            product_groups[base_name].append(product)
        
        created_count = 0
        
        for base_name, variants in product_groups.items():
            # Get first variant for base info
            first = variants[0]
            
            # Get category
            cat_id = self.created_categories.get(first['category'], False)
            
            # Prepare attribute lines
            attribute_lines = []
            
            # Get unique sizes and colors from variants
            sizes = list(set([v['size'] for v in variants if 'size' in v]))
            colors = list(set([v['color'] for v in variants if 'color' in v]))
            
            if sizes and 'size' in self.created_attributes:
                size_value_ids = [self.created_attributes['size']['values'].get(s) 
                                 for s in sizes 
                                 if s in self.created_attributes['size']['values']]
                if size_value_ids:
                    attribute_lines.append((0, 0, {
                        'attribute_id': self.created_attributes['size']['attr_id'],
                        'value_ids': [(6, 0, size_value_ids)]
                    }))
            
            if colors and 'color' in self.created_attributes:
                color_value_ids = [self.created_attributes['color']['values'].get(c) 
                                  for c in colors 
                                  if c in self.created_attributes['color']['values']]
                if color_value_ids:
                    attribute_lines.append((0, 0, {
                        'attribute_id': self.created_attributes['color']['attr_id'],
                        'value_ids': [(6, 0, color_value_ids)]
                    }))
            
            # Create product template
            try:
                template_id = self.execute('product.template', 'create', [{
                    'name': base_name,
                    'detailed_type': 'product',  # Use detailed_type instead of type
                    'categ_id': cat_id if cat_id else 1,  # Default category
                    'list_price': first['list_price'],
                    'standard_price': first.get('standard_cost', 0),
                    'description_sale': first.get('description', ''),
                    'default_code': first['sku'].split('-')[0],  # Base SKU
                    'attribute_line_ids': attribute_lines if attribute_lines else False
                }])
                
                self.created_products[base_name] = template_id
                created_count += 1
                print(f"   ✅ Created: {base_name} (ID: {template_id})")
                
            except Exception as e:
                print(f"   ❌ Failed to create {base_name}: {str(e)}")
        
        print(f"\n📊 Created {created_count} product templates")
        return created_count
    
    def create_customers(self, count=10):
        """Create sample customers"""
        print(f"\n👥 Creating {count} sample customers...")
        
        # Sample data
        first_names = ['John', 'Jane', 'Michael', 'Sarah', 'David', 'Emma', 'James', 'Lisa', 'Robert', 'Mary']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
        cities = ['Dublin', 'Cork', 'Galway', 'Limerick', 'Waterford']
        
        for i in range(count):
            fname = random.choice(first_names)
            lname = random.choice(last_names)
            
            customer_data = {
                'name': f"{fname} {lname}",
                'email': f"{fname.lower()}.{lname.lower()}@example.com",
                'customer_rank': 1,  # Mark as customer
                'is_company': False,
                'street': f"{random.randint(1, 999)} Main Street",
                'city': random.choice(cities),
                'country_id': 103,  # Ireland
                'phone': f"+353 {random.randint(10000000, 99999999)}"
            }
            
            try:
                customer_id = self.execute('res.partner', 'create', [customer_data])
                self.created_customers.append(customer_id)
                print(f"   ✅ Created customer: {customer_data['name']} (ID: {customer_id})")
            except Exception as e:
                print(f"   ❌ Failed to create customer: {str(e)}")
        
        print(f"\n📊 Created {len(self.created_customers)} customers")
        return self.created_customers
    
    def create_sample_orders(self, count=5):
        """Create sample sales orders"""
        print(f"\n📋 Creating {count} sample sales orders...")
        
        if not self.created_customers:
            print("   ❌ No customers available, skipping orders")
            return []
        
        # Get product variants
        product_ids = self.execute('product.product', 'search', [
            [('product_tmpl_id', 'in', list(self.created_products.values()))]
        ], {'limit': 50})
        
        if not product_ids:
            print("   ❌ No product variants found, skipping orders")
            return []
        
        created_orders = []
        
        for i in range(min(count, len(self.created_customers))):
            customer_id = self.created_customers[i]
            
            # Create order lines (1-3 products per order)
            order_lines = []
            for _ in range(random.randint(1, 3)):
                product_id = random.choice(product_ids)
                quantity = random.randint(1, 5)
                
                order_lines.append((0, 0, {
                    'product_id': product_id,
                    'product_uom_qty': quantity
                }))
            
            # Create order
            try:
                order_id = self.execute('sale.order', 'create', [{
                    'partner_id': customer_id,
                    'order_line': order_lines,
                    'state': 'draft'
                }])
                created_orders.append(order_id)
                print(f"   ✅ Created order {order_id} with {len(order_lines)} lines")
            except Exception as e:
                print(f"   ❌ Failed to create order: {str(e)}")
        
        print(f"\n📊 Created {len(created_orders)} sales orders")
        return created_orders
    
    def run(self):
        """Run the complete import process"""
        print("\n" + "="*60)
        print("🚀 STARTING GYM+COFFEE ODOO IMPORT")
        print("="*60)
        
        # Create categories
        self.create_product_categories()
        
        # Create attributes
        self.create_product_attributes()
        
        # Import products
        self.import_products(limit=20)
        
        # Create customers
        self.create_customers(count=10)
        
        # Create sample orders
        self.create_sample_orders(count=5)
        
        print("\n" + "="*60)
        print("✅ IMPORT COMPLETE!")
        print("="*60)
        
        # Summary
        print("\n📊 SUMMARY:")
        print(f"   - Categories created: {len(self.created_categories)}")
        print(f"   - Products created: {len(self.created_products)}")
        print(f"   - Customers created: {len(self.created_customers)}")
        
        return {
            'categories': self.created_categories,
            'products': self.created_products,
            'customers': self.created_customers
        }

if __name__ == "__main__":
    try:
        importer = GymCoffeeImporter()
        results = importer.run()
        
        # Save results for verification
        with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/import_results.json', 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'product_count': len(results['products']),
                'customer_count': len(results['customers']),
                'product_ids': list(results['products'].values()),
                'customer_ids': results['customers']
            }, f, indent=2)
        
        print("\n💾 Results saved to import_results.json")
        
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        sys.exit(1)