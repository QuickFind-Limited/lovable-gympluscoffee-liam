#!/usr/bin/env python3
"""
Complete Revenue System Implementation for Gym+Coffee
Target: €250k-400k monthly revenue with seasonality
"""

import xmlrpc.client
import json
import os
import random
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import math

load_dotenv()

class RevenueSystemImplementer:
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
        
        # Load products
        self.load_products()
        
        # Track statistics
        self.total_revenue = 0
        self.orders_created = 0
        self.monthly_stats = {}
        
    def execute(self, model, method, *args):
        """Execute Odoo method"""
        return self.models.execute_kw(self.db, self.uid, self.password, model, method, *args)
    
    def load_products(self):
        """Load all products from Odoo"""
        print("📦 Loading products...")
        self.products = self.execute('product.product', 'search_read', 
                                    [[]], 
                                    {'fields': ['name', 'list_price', 'default_code']})
        
        # Categorize products for seasonality
        self.winter_products = []
        self.summer_products = []
        self.all_season_products = []
        self.accessories = []
        
        for product in self.products:
            name = product['name'].lower()
            if any(x in name for x in ['hoodie', 'jacket', 'sweatshirt', 'beanie']):
                self.winter_products.append(product)
            elif any(x in name for x in ['shorts', 'tank', 'summer']):
                self.summer_products.append(product)
            elif any(x in name for x in ['bag', 'bottle', 'socks', 'cap', 'tote']):
                self.accessories.append(product)
            else:
                self.all_season_products.append(product)
        
        print(f"   Loaded {len(self.products)} products")
        print(f"   Winter: {len(self.winter_products)}, Summer: {len(self.summer_products)}")
        print(f"   All-season: {len(self.all_season_products)}, Accessories: {len(self.accessories)}\n")
    
    def get_seasonal_multiplier(self, month):
        """Get seasonal multiplier for the month"""
        # Athletic wear seasonality
        seasonal_patterns = {
            1: 1.10,  # Jan - New Year resolutions
            2: 1.05,  # Feb - Winter gear
            3: 1.15,  # Mar - Spring prep
            4: 1.20,  # Apr - Spring active
            5: 1.25,  # May - Summer prep
            6: 1.20,  # Jun - Summer active
            7: 0.85,  # Jul - Summer slowdown
            8: 0.85,  # Aug - Late summer
            9: 1.00,  # Sep - Back to routine
            10: 1.20, # Oct - Fall active
            11: 1.35, # Nov - Holiday shopping starts
            12: 1.40  # Dec - Peak holiday
        }
        return seasonal_patterns.get(month, 1.0)
    
    def get_product_mix(self, month):
        """Get product mix based on season"""
        # Determine seasonal product weights
        if month in [11, 12, 1, 2, 3]:  # Winter months
            winter_weight = 0.50
            summer_weight = 0.05
            all_season_weight = 0.35
            accessories_weight = 0.10
        elif month in [5, 6, 7, 8]:  # Summer months
            winter_weight = 0.10
            summer_weight = 0.45
            all_season_weight = 0.35
            accessories_weight = 0.10
        else:  # Transition months
            winter_weight = 0.25
            summer_weight = 0.25
            all_season_weight = 0.40
            accessories_weight = 0.10
        
        return {
            'winter': winter_weight,
            'summer': summer_weight,
            'all_season': all_season_weight,
            'accessories': accessories_weight
        }
    
    def select_products_for_order(self, month, order_value_category):
        """Select products based on season and target order value"""
        product_mix = self.get_product_mix(month)
        
        # Determine number of items based on order category
        if order_value_category == 'small':
            target_value = random.uniform(60, 100)
            num_items = random.randint(1, 2)
        elif order_value_category == 'medium':
            target_value = random.uniform(120, 200)
            num_items = random.randint(2, 4)
        elif order_value_category == 'large':
            target_value = random.uniform(200, 350)
            num_items = random.randint(3, 6)
        else:  # premium
            target_value = random.uniform(350, 500)
            num_items = random.randint(4, 8)
        
        selected_products = []
        current_value = 0
        
        for _ in range(num_items):
            # Select category based on weights
            rand = random.random()
            if rand < product_mix['winter'] and self.winter_products:
                product_pool = self.winter_products
            elif rand < product_mix['winter'] + product_mix['summer'] and self.summer_products:
                product_pool = self.summer_products
            elif rand < product_mix['winter'] + product_mix['summer'] + product_mix['all_season'] and self.all_season_products:
                product_pool = self.all_season_products
            elif self.accessories:
                product_pool = self.accessories
            else:
                product_pool = self.all_season_products or self.products
            
            if product_pool:
                product = random.choice(product_pool)
                quantity = random.choices([1, 2, 3], weights=[0.7, 0.25, 0.05])[0]
                selected_products.append((product, quantity))
                current_value += product['list_price'] * quantity
        
        return selected_products, current_value
    
    def create_shopify_user(self):
        """Create or get Shopify user"""
        print("👤 Setting up Shopify salesperson...")
        
        # Search for existing Shopify user
        shopify_users = self.execute('res.users', 'search', 
                                    [[['login', '=', 'shopify@gympluscoffee.com']]])
        
        if shopify_users:
            self.shopify_user_id = shopify_users[0]
            print(f"   Found existing Shopify user (ID: {self.shopify_user_id})")
        else:
            # Create Shopify user
            try:
                self.shopify_user_id = self.execute('res.users', 'create', [{
                    'name': 'Shopify',
                    'login': 'shopify@gympluscoffee.com',
                    'email': 'shopify@gympluscoffee.com',
                    'groups_id': [(6, 0, [self.execute('res.groups', 'search', 
                                                      [[['name', '=', 'Sales / User: All Documents']]])[0]])]
                }])
                print(f"   ✅ Created Shopify user (ID: {self.shopify_user_id})")
            except:
                # If can't create user, use admin
                self.shopify_user_id = self.uid
                print(f"   ⚠️ Using current user as salesperson")
        
        return self.shopify_user_id
    
    def generate_monthly_orders(self, year, month, target_revenue):
        """Generate orders for a specific month"""
        month_name = datetime(year, month, 1).strftime('%B %Y')
        print(f"\n📅 Generating orders for {month_name}")
        print(f"   Target revenue: €{target_revenue:,.2f}")
        
        # Get seasonal multiplier
        seasonal_mult = self.get_seasonal_multiplier(month)
        adjusted_target = target_revenue * seasonal_mult
        print(f"   Seasonal adjustment: {seasonal_mult:.1%} = €{adjusted_target:,.2f}")
        
        # Calculate number of orders needed
        avg_order_value = 175  # Target AOV
        num_orders = int(adjusted_target / avg_order_value)
        
        # Order value distribution
        order_distribution = {
            'small': int(num_orders * 0.15),    # 15%
            'medium': int(num_orders * 0.60),   # 60%
            'large': int(num_orders * 0.20),    # 20%
            'premium': int(num_orders * 0.05)   # 5%
        }
        
        print(f"   Orders to create: {num_orders}")
        print(f"   Distribution: Small:{order_distribution['small']}, " +
              f"Medium:{order_distribution['medium']}, " +
              f"Large:{order_distribution['large']}, " +
              f"Premium:{order_distribution['premium']}")
        
        # Get customers
        customers = self.execute('res.partner', 'search', 
                                [[['customer_rank', '>', 0]]])
        
        if not customers:
            print("   ❌ No customers found!")
            return 0
        
        monthly_revenue = 0
        monthly_orders = 0
        
        # Generate orders throughout the month
        days_in_month = 30
        orders_per_day = num_orders / days_in_month
        
        for day in range(1, days_in_month + 1):
            # Calculate orders for this day
            daily_orders = int(orders_per_day)
            if random.random() < (orders_per_day - daily_orders):
                daily_orders += 1
            
            for _ in range(daily_orders):
                # Determine order value category
                rand = random.random()
                if rand < 0.15:
                    category = 'small'
                elif rand < 0.75:
                    category = 'medium'
                elif rand < 0.95:
                    category = 'large'
                else:
                    category = 'premium'
                
                # Select products
                products, order_value = self.select_products_for_order(month, category)
                
                if not products:
                    continue
                
                # Create order
                try:
                    order_date = datetime(year, month, day, 
                                        random.randint(8, 20), 
                                        random.randint(0, 59))
                    
                    # Build order lines
                    order_lines = []
                    for product, quantity in products:
                        order_lines.append((0, 0, {
                            'product_id': product['id'],
                            'product_uom_qty': quantity,
                            'price_unit': product['list_price']
                        }))
                    
                    # Create order
                    order_data = {
                        'partner_id': random.choice(customers),
                        'date_order': order_date.strftime('%Y-%m-%d %H:%M:%S'),
                        'user_id': self.shopify_user_id,  # Set Shopify as salesperson
                        'team_id': 1,  # Default sales team
                        'order_line': order_lines
                    }
                    
                    order_id = self.execute('sale.order', 'create', [order_data])
                    
                    # Confirm order (80% chance)
                    if random.random() < 0.80:
                        try:
                            self.execute('sale.order', 'action_confirm', [[order_id]])
                        except:
                            pass  # Some orders might not confirm due to stock
                    
                    monthly_revenue += order_value
                    monthly_orders += 1
                    
                except Exception as e:
                    print(f"      ❌ Order failed: {str(e)[:50]}")
        
        print(f"   ✅ Created {monthly_orders} orders")
        print(f"   💰 Revenue: €{monthly_revenue:,.2f}")
        
        self.monthly_stats[month_name] = {
            'orders': monthly_orders,
            'revenue': monthly_revenue,
            'target': adjusted_target,
            'achievement': (monthly_revenue / adjusted_target * 100) if adjusted_target > 0 else 0
        }
        
        return monthly_revenue
    
    def set_inventory_levels(self):
        """Set proper inventory levels for all products"""
        print("\n📦 Setting inventory levels...")
        
        # Get stock location
        location_ids = self.execute('stock.location', 'search', 
                                   [[['usage', '=', 'internal']]], {'limit': 1})
        
        if not location_ids:
            print("   ❌ No stock location found")
            return
        
        location_id = location_ids[0]
        
        # Set inventory for each product category
        for product in self.products:
            name = product['name'].lower()
            
            # Determine stock level based on product type
            if 'limited' in name or 'special' in name:
                stock_level = random.randint(50, 200)
            elif 'essential' in name or 'basic' in name:
                stock_level = random.randint(500, 1000)
            elif any(x in name for x in ['hoodie', 'jacket', 't-shirt', 'joggers']):
                stock_level = random.randint(300, 600)
            elif any(x in name for x in ['bag', 'bottle', 'socks', 'cap']):
                stock_level = random.randint(300, 600)
            else:
                stock_level = random.randint(200, 500)
            
            try:
                # Check if stock exists
                existing = self.execute('stock.quant', 'search', [
                    [['product_id', '=', product['id']],
                     ['location_id', '=', location_id]]
                ])
                
                if existing:
                    # Update existing
                    self.execute('stock.quant', 'write', 
                               [existing[0], {'quantity': stock_level}])
                else:
                    # Create new
                    self.execute('stock.quant', 'create', [{
                        'product_id': product['id'],
                        'location_id': location_id,
                        'quantity': stock_level
                    }])
            except:
                pass  # Skip if stock module issues
        
        print("   ✅ Inventory levels set")
    
    def generate_full_year_revenue(self):
        """Generate 12 months of revenue data"""
        print("\n" + "="*60)
        print("💰 GENERATING 12 MONTHS OF REVENUE DATA")
        print("="*60)
        
        # Create Shopify user
        self.create_shopify_user()
        
        # Set inventory levels first
        self.set_inventory_levels()
        
        # Target monthly revenue
        base_monthly_revenue = 300000  # €300k
        
        # Generate orders for each month (last 12 months)
        current_date = datetime.now()
        
        for months_ago in range(11, -1, -1):
            # Calculate month and year
            order_date = current_date - timedelta(days=months_ago * 30)
            year = order_date.year
            month = order_date.month
            
            # Generate orders for this month
            monthly_revenue = self.generate_monthly_orders(year, month, base_monthly_revenue)
            self.total_revenue += monthly_revenue
            self.orders_created += self.monthly_stats.get(
                datetime(year, month, 1).strftime('%B %Y'), {}
            ).get('orders', 0)
        
        # Final summary
        print("\n" + "="*60)
        print("📊 FINAL REVENUE SUMMARY")
        print("="*60)
        
        print("\n💰 Monthly Performance:")
        total_target = 0
        for month, stats in self.monthly_stats.items():
            print(f"   {month}: €{stats['revenue']:,.2f} ({stats['achievement']:.1f}% of target)")
            total_target += stats['target']
        
        print(f"\n🎯 Overall Results:")
        print(f"   Total Revenue: €{self.total_revenue:,.2f}")
        print(f"   Total Orders: {self.orders_created:,}")
        print(f"   Average Order Value: €{self.total_revenue/self.orders_created:.2f}" if self.orders_created > 0 else "N/A")
        print(f"   Monthly Average: €{self.total_revenue/12:,.2f}")
        print(f"   Target Achievement: {(self.total_revenue/total_target*100):.1f}%")
        
        # Verify in Odoo
        print("\n✅ Verifying in Odoo...")
        total_orders = self.execute('sale.order', 'search_count', [[]])
        shopify_orders = self.execute('sale.order', 'search_count', 
                                     [[['user_id', '=', self.shopify_user_id]]])
        
        print(f"   Total orders in Odoo: {total_orders}")
        print(f"   Shopify orders: {shopify_orders}")
        
        print("\n🎉 Revenue generation complete!")
        
        return self.total_revenue

if __name__ == "__main__":
    implementer = RevenueSystemImplementer()
    implementer.generate_full_year_revenue()