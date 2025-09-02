#!/usr/bin/env python3
"""
Revenue Generation Script for Gym Plus Coffee
==============================================

Generates €250k-400k monthly revenue through realistic sales orders with:
- Seasonality patterns for different product categories
- Proper order value distribution
- 12 months of historical data
- Salesperson set to "Shopify" for all orders

Target: 1,700+ orders/month to achieve €300k average monthly revenue.

Author: Revenue Generation Specialist
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from pathlib import Path
import logging
from typing import Dict, List, Any, Optional, Tuple
import json
import random
import math
from collections import defaultdict
import sys
import os

# Add the scripts directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

from connection_manager import OdooConnection, ConnectionConfig
from data_models import SalesOrder, SalesOrderLine
from error_handler import ErrorHandler
from progress_tracker import ProgressTracker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    handlers=[
        logging.FileHandler('revenue_generation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RevenueGenerator:
    """
    Generates high-value sales orders with seasonality patterns
    to achieve €250k-400k monthly revenue targets
    """
    
    def __init__(self, 
                 output_dir: str = "data/revenue",
                 target_monthly_revenue: float = 300000.0,
                 months_to_generate: int = 12):
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.target_monthly_revenue = target_monthly_revenue
        self.months_to_generate = months_to_generate
        
        # Initialize error handler and progress tracker
        self.error_handler = ErrorHandler()
        self.progress_tracker = ProgressTracker()
        
        # Product categories with seasonality patterns
        self.product_categories = {
            'hoodies': {
                'base_price_range': (65, 120),
                'seasonality': self._hoodie_seasonality,
                'peak_months': [10, 11, 12, 1, 2],  # Oct-Feb
                'peak_multiplier': 1.5,
                'low_multiplier': 0.5,
                'products': [
                    'Essential Hoodie Black', 'Essential Hoodie Navy', 'Essential Hoodie Grey',
                    'Premium Hoodie Charcoal', 'Premium Hoodie Forest', 'Zip Hoodie Black',
                    'Zip Hoodie Navy', 'Oversized Hoodie Cream', 'Crop Hoodie Black'
                ]
            },
            'jackets': {
                'base_price_range': (85, 150),
                'seasonality': self._hoodie_seasonality,  # Same as hoodies
                'peak_months': [10, 11, 12, 1, 2],
                'peak_multiplier': 1.5,
                'low_multiplier': 0.5,
                'products': [
                    'Bomber Jacket Black', 'Puffer Jacket Navy', 'Track Jacket Grey',
                    'Windbreaker Green', 'Denim Jacket Blue', 'Varsity Jacket Black'
                ]
            },
            'shorts': {
                'base_price_range': (35, 65),
                'seasonality': self._summer_seasonality,
                'peak_months': [5, 6, 7, 8, 9],  # May-Sep
                'peak_multiplier': 1.4,
                'low_multiplier': 0.6,
                'products': [
                    'Training Shorts Black', 'Training Shorts Navy', 'Training Shorts Grey',
                    'Running Shorts Neon', 'Swim Shorts Blue', 'Board Shorts Camo',
                    'Cycling Shorts Black', '7" Shorts Olive'
                ]
            },
            'tank_tops': {
                'base_price_range': (25, 45),
                'seasonality': self._summer_seasonality,
                'peak_months': [5, 6, 7, 8, 9],
                'peak_multiplier': 1.4,
                'low_multiplier': 0.6,
                'products': [
                    'Essential Tank Black', 'Essential Tank White', 'Essential Tank Grey',
                    'Muscle Tank Navy', 'Racerback Tank Pink', 'Crop Tank Black',
                    'Stringer Tank Charcoal', 'Performance Tank Blue'
                ]
            },
            't_shirts': {
                'base_price_range': (30, 55),
                'seasonality': self._stable_seasonality,
                'peak_months': [],
                'peak_multiplier': 1.1,
                'low_multiplier': 0.9,
                'products': [
                    'Essential Tee Black', 'Essential Tee White', 'Essential Tee Navy',
                    'Oversized Tee Grey', 'Fitted Tee Pink', 'Long Sleeve Black',
                    'Gym Tee Charcoal', 'Logo Tee Navy', 'Vintage Tee Cream'
                ]
            },
            'leggings': {
                'base_price_range': (45, 85),
                'seasonality': self._stable_seasonality,
                'peak_months': [],
                'peak_multiplier': 1.15,
                'low_multiplier': 0.85,
                'products': [
                    'High-Waist Leggings Black', 'High-Waist Leggings Navy', 
                    'Seamless Leggings Grey', 'Printed Leggings Camo',
                    'Yoga Leggings Pink', '7/8 Leggings Olive', 'Compression Leggings Black'
                ]
            },
            'accessories': {
                'base_price_range': (15, 75),
                'seasonality': self._accessories_seasonality,
                'peak_months': [11, 12],  # Nov-Dec (gifts)
                'peak_multiplier': 1.8,
                'low_multiplier': 0.7,
                'products': [
                    'Baseball Cap Black', 'Beanie Navy', 'Water Bottle Steel',
                    'Gym Bag Black', 'Protein Shaker', 'Wrist Bands', 'Gym Towel',
                    'Phone Armband', 'Lifting Straps', 'Resistance Bands',
                    'Yoga Mat Purple', 'Foam Roller', 'Gift Card €25',
                    'Gift Card €50', 'Gift Card €100'
                ]
            }
        }
        
        # Order value distribution targets
        self.order_value_distribution = {
            'small': {'range': (60, 100), 'percentage': 0.15},
            'medium': {'range': (120, 200), 'percentage': 0.60},
            'large': {'range': (200, 350), 'percentage': 0.20},
            'premium': {'range': (350, 500), 'percentage': 0.05}
        }
        
        # Customer segments for targeting
        self.customer_segments = {
            'fitness_enthusiast': {'percentage': 0.35, 'avg_order_value': 180},
            'casual_gym_goer': {'percentage': 0.40, 'avg_order_value': 140},
            'professional_athlete': {'percentage': 0.15, 'avg_order_value': 280},
            'lifestyle_buyer': {'percentage': 0.10, 'avg_order_value': 160}
        }
        
        # Generate monthly targets
        self.monthly_targets = self._calculate_monthly_targets()
        
        logger.info(f"RevenueGenerator initialized with €{target_monthly_revenue:,.0f} monthly target")
        logger.info(f"Generating {months_to_generate} months of historical data")
    
    def _hoodie_seasonality(self, month: int) -> float:
        """Seasonality multiplier for hoodies/jackets: Peak Oct-Feb (150%), Low May-Aug (50%)"""
        if month in [10, 11, 12, 1, 2]:  # Peak winter months
            return 1.5
        elif month in [5, 6, 7, 8]:  # Low summer months
            return 0.5
        else:  # Transition months
            return 0.9 if month in [3, 4, 9] else 1.0
    
    def _summer_seasonality(self, month: int) -> float:
        """Seasonality multiplier for shorts/tank tops: Peak May-Sep (140%), Low Nov-Feb (60%)"""
        if month in [5, 6, 7, 8, 9]:  # Peak summer months
            return 1.4
        elif month in [11, 12, 1, 2]:  # Low winter months
            return 0.6
        else:  # Transition months
            return 0.8 if month in [3, 4, 10] else 1.0
    
    def _stable_seasonality(self, month: int) -> float:
        """Stable seasonality for t-shirts/leggings with minor variations"""
        # Slight increase in Jan (New Year resolutions) and summer prep (Apr-May)
        if month == 1:
            return 1.15
        elif month in [4, 5]:
            return 1.1
        elif month in [11, 12]:
            return 0.9  # Slightly lower during holiday season
        else:
            return 1.0
    
    def _accessories_seasonality(self, month: int) -> float:
        """Seasonality for accessories: Peak Nov-Dec (180% for gifts)"""
        if month in [11, 12]:  # Holiday gift season
            return 1.8
        elif month == 1:  # New Year fitness resolutions
            return 1.2
        elif month in [2, 3]:  # Post-holiday drop
            return 0.7
        else:
            return 1.0
    
    def _calculate_monthly_targets(self) -> List[Dict]:
        """Calculate monthly revenue and order targets with seasonality"""
        targets = []
        current_date = datetime.now() - timedelta(days=30 * self.months_to_generate)
        
        for month_idx in range(self.months_to_generate):
            month_date = current_date + timedelta(days=30 * month_idx)
            month = month_date.month
            
            # Calculate overall seasonality multiplier
            category_multipliers = []
            for category_data in self.product_categories.values():
                multiplier = category_data['seasonality'](month)
                category_multipliers.append(multiplier)
            
            # Average seasonality across all categories
            avg_seasonality = np.mean(category_multipliers)
            
            # Apply seasonality to base target
            monthly_revenue = self.target_monthly_revenue * avg_seasonality
            
            # Calculate required orders (assuming average order value of €175)
            avg_order_value = 175
            target_orders = int(monthly_revenue / avg_order_value)
            
            targets.append({
                'month': month,
                'year': month_date.year,
                'month_name': month_date.strftime('%B'),
                'revenue_target': monthly_revenue,
                'orders_target': target_orders,
                'seasonality_multiplier': avg_seasonality,
                'date': month_date
            })
        
        return targets
    
    def generate_product_catalog(self) -> List[Dict]:
        """Generate comprehensive product catalog with proper pricing"""
        products = []
        product_id = 1000
        
        for category, category_data in self.product_categories.items():
            base_min, base_max = category_data['base_price_range']
            
            for product_name in category_data['products']:
                for size in ['XS', 'S', 'M', 'L', 'XL', 'XXL']:
                    # Skip size variations for accessories (except clothing accessories)
                    if category == 'accessories' and not any(item in product_name.lower() 
                                                           for item in ['cap', 'beanie', 'bag']):
                        if size != 'M':  # Only create one size for non-clothing accessories
                            continue
                    
                    # Generate realistic pricing with size variations
                    base_price = random.uniform(base_min, base_max)
                    
                    # Size-based price adjustments
                    size_multiplier = {
                        'XS': 0.95, 'S': 0.98, 'M': 1.0, 
                        'L': 1.02, 'XL': 1.05, 'XXL': 1.08
                    }.get(size, 1.0)
                    
                    final_price = round(base_price * size_multiplier, 2)
                    cost_price = round(final_price * 0.4, 2)  # 60% margin
                    
                    sku = f"GPC{product_id:05d}-{size}"
                    
                    products.append({
                        'sku': sku,
                        'name': f"{product_name} - {size}",
                        'category': category,
                        'size': size,
                        'list_price': final_price,
                        'standard_cost': cost_price,
                        'description': f"High-quality {category.replace('_', ' ')} from Gym Plus Coffee",
                        'status': 'active',
                        'inventory_on_hand': random.randint(50, 500),
                        'reorder_point': 20,
                        'weight': random.uniform(0.2, 2.0)
                    })
                    
                    product_id += 1
        
        logger.info(f"Generated {len(products)} products across {len(self.product_categories)} categories")
        return products
    
    def generate_customers(self, num_customers: int = 2000) -> List[Dict]:
        """Generate diverse customer base with proper segmentation"""
        customers = []
        
        # Customer demographics
        countries = [
            'Ireland', 'United Kingdom', 'Germany', 'France', 'Netherlands',
            'Spain', 'Italy', 'Belgium', 'Austria', 'Switzerland'
        ]
        
        cities_by_country = {
            'Ireland': ['Dublin', 'Cork', 'Galway', 'Limerick', 'Waterford'],
            'United Kingdom': ['London', 'Manchester', 'Birmingham', 'Edinburgh', 'Cardiff'],
            'Germany': ['Berlin', 'Munich', 'Hamburg', 'Frankfurt', 'Cologne'],
            'France': ['Paris', 'Lyon', 'Marseille', 'Toulouse', 'Nice'],
            'Netherlands': ['Amsterdam', 'Rotterdam', 'The Hague', 'Utrecht', 'Eindhoven'],
            'Spain': ['Madrid', 'Barcelona', 'Valencia', 'Seville', 'Bilbao'],
            'Italy': ['Rome', 'Milan', 'Naples', 'Turin', 'Florence'],
            'Belgium': ['Brussels', 'Antwerp', 'Ghent', 'Charleroi', 'Liège'],
            'Austria': ['Vienna', 'Graz', 'Linz', 'Salzburg', 'Innsbruck'],
            'Switzerland': ['Zurich', 'Geneva', 'Basel', 'Lausanne', 'Bern']
        }
        
        first_names = [
            'Emma', 'Liam', 'Olivia', 'Noah', 'Ava', 'Oliver', 'Isabella', 'Elijah',
            'Sophia', 'Lucas', 'Charlotte', 'Mason', 'Amelia', 'Logan', 'Mia', 'Alexander',
            'Harper', 'Ethan', 'Evelyn', 'Jacob', 'Abigail', 'Michael', 'Emily', 'Benjamin',
            'Elizabeth', 'William', 'Mila', 'James', 'Ella', 'Henry'
        ]
        
        last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
            'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
            'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson',
            'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson'
        ]
        
        for i in range(num_customers):
            country = random.choice(countries)
            city = random.choice(cities_by_country[country])
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            
            # Generate email
            email_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 
                           'icloud.com', 'protonmail.com']
            email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@{random.choice(email_domains)}"
            
            # Assign customer segment
            segment = random.choices(
                list(self.customer_segments.keys()),
                weights=[seg['percentage'] for seg in self.customer_segments.values()]
            )[0]
            
            customers.append({
                'customer_id': f"CUST{i+1:06d}",
                'name': f"{first_name} {last_name}",
                'email': email,
                'phone': f"+{random.randint(1, 99)}{random.randint(1000000, 9999999)}",
                'street': f"{random.randint(1, 999)} {random.choice(['Main', 'Oak', 'Elm', 'Park', 'High'])} {'Street' if random.random() > 0.5 else 'Avenue'}",
                'city': city,
                'country': country,
                'zip_code': f"{random.randint(10000, 99999)}",
                'segment': segment,
                'is_company': False,
                'customer_rank': random.choice(['new', 'regular', 'vip']),
                'created_date': datetime.now() - timedelta(days=random.randint(1, 730))
            })
        
        logger.info(f"Generated {len(customers)} customers across {len(countries)} countries")
        return customers
    
    def generate_monthly_orders(self, month_target: Dict, products: List[Dict], 
                              customers: List[Dict]) -> List[Dict]:
        """Generate orders for a specific month with proper seasonality"""
        orders = []
        month = month_target['month']
        year = month_target['year']
        target_orders = month_target['orders_target']
        target_revenue = month_target['revenue_target']
        
        logger.info(f"Generating {target_orders} orders for {month_target['month_name']} {year} "
                   f"(Target: €{target_revenue:,.0f})")
        
        # Calculate days in month
        if month == 2:
            days_in_month = 29 if year % 4 == 0 else 28
        elif month in [4, 6, 9, 11]:
            days_in_month = 30
        else:
            days_in_month = 31
        
        # Distribute orders across the month with realistic patterns
        daily_orders = self._distribute_orders_across_month(target_orders, days_in_month)
        
        order_id = 1
        current_revenue = 0.0
        
        for day in range(1, days_in_month + 1):
            num_orders_today = daily_orders[day - 1]
            
            for _ in range(num_orders_today):
                # Select customer
                customer = random.choice(customers)
                
                # Determine order value tier
                tier = self._select_order_value_tier()
                min_value, max_value = self.order_value_distribution[tier]['range']
                target_order_value = random.uniform(min_value, max_value)
                
                # Generate order date with realistic time distribution
                order_date = datetime(year, month, day, 
                                    hour=random.randint(6, 22),
                                    minute=random.randint(0, 59))
                
                # Select products based on seasonality
                order_lines = self._generate_order_lines(
                    products, month, target_order_value
                )
                
                # Calculate actual order total
                order_total = sum(line['price_total'] for line in order_lines)
                current_revenue += order_total
                
                # Create order
                order = {
                    'order_id': f"SO{year}{month:02d}{order_id:04d}",
                    'customer_id': customer['customer_id'],
                    'customer_name': customer['name'],
                    'customer_email': customer['email'],
                    'order_date': order_date.isoformat(),
                    'state': 'sale',  # Confirmed sale
                    'amount_untaxed': round(order_total / 1.23, 2),  # Assuming 23% VAT
                    'amount_tax': round(order_total - (order_total / 1.23), 2),
                    'amount_total': order_total,
                    'currency': 'EUR',
                    'salesperson': 'Shopify',  # As requested
                    'order_lines': order_lines,
                    'payment_term': 'immediate',
                    'delivery_method': random.choice(['standard', 'express', 'next_day']),
                    'order_tier': tier,
                    'month': month,
                    'year': year
                }
                
                orders.append(order)
                order_id += 1
                
                # Break if we've exceeded our revenue target significantly
                if current_revenue > target_revenue * 1.1:
                    break
            
            if current_revenue > target_revenue * 1.1:
                break
        
        actual_orders = len(orders)
        logger.info(f"Generated {actual_orders} orders totaling €{current_revenue:,.2f} "
                   f"for {month_target['month_name']} {year}")
        
        return orders
    
    def _distribute_orders_across_month(self, total_orders: int, days_in_month: int) -> List[int]:
        """Distribute orders across month with realistic daily patterns"""
        # Base distribution
        daily_orders = [total_orders // days_in_month] * days_in_month
        remaining = total_orders % days_in_month
        
        # Add remaining orders to random days
        for _ in range(remaining):
            day_idx = random.randint(0, days_in_month - 1)
            daily_orders[day_idx] += 1
        
        # Apply weekly patterns (higher on weekends, lower mid-week)
        for day_idx in range(days_in_month):
            day_of_week = (day_idx + 1) % 7  # Approximate day of week
            
            if day_of_week in [5, 6]:  # Weekend (Fri-Sat)
                daily_orders[day_idx] = int(daily_orders[day_idx] * 1.3)
            elif day_of_week in [1, 2]:  # Monday-Tuesday
                daily_orders[day_idx] = int(daily_orders[day_idx] * 0.8)
        
        return daily_orders
    
    def _select_order_value_tier(self) -> str:
        """Select order value tier based on target distribution"""
        tiers = list(self.order_value_distribution.keys())
        weights = [self.order_value_distribution[tier]['percentage'] 
                  for tier in tiers]
        
        return random.choices(tiers, weights=weights)[0]
    
    def _generate_order_lines(self, products: List[Dict], month: int, 
                            target_value: float) -> List[Dict]:
        """Generate order lines based on seasonality and target value"""
        order_lines = []
        current_total = 0.0
        max_items = random.randint(1, 6)  # 1-6 items per order
        
        # Filter products based on seasonality
        seasonal_products = []
        for product in products:
            category = product['category']
            seasonality_multiplier = self.product_categories[category]['seasonality'](month)
            
            # Higher chance to select seasonal products
            selection_weight = seasonality_multiplier
            if random.random() < selection_weight / 2.0:  # Normalize probability
                seasonal_products.append(product)
        
        # If no seasonal products, use all products
        if not seasonal_products:
            seasonal_products = products
        
        for item_num in range(max_items):
            if current_total >= target_value * 0.9:  # Close to target
                break
            
            # Select product
            product = random.choice(seasonal_products)
            
            # Determine quantity (mostly 1-2, occasionally 3-5)
            if random.random() < 0.7:
                quantity = random.randint(1, 2)
            else:
                quantity = random.randint(3, 5)
            
            # Calculate prices
            unit_price = product['list_price']
            
            # Apply small random discount occasionally
            if random.random() < 0.15:  # 15% chance of discount
                discount = random.uniform(0.05, 0.15)  # 5-15% discount
                unit_price = unit_price * (1 - discount)
            
            line_total = round(quantity * unit_price, 2)
            
            # Don't exceed target significantly
            if current_total + line_total > target_value * 1.2:
                # Adjust quantity to fit
                max_affordable_qty = int((target_value - current_total) / unit_price)
                if max_affordable_qty >= 1:
                    quantity = max_affordable_qty
                    line_total = round(quantity * unit_price, 2)
                else:
                    break  # Can't afford even 1 item
            
            order_lines.append({
                'product_sku': product['sku'],
                'product_name': product['name'],
                'category': product['category'],
                'quantity': quantity,
                'price_unit': round(unit_price, 2),
                'price_subtotal': line_total,
                'price_total': line_total,  # Simplified - no line-level taxes
                'discount': 0.0
            })
            
            current_total += line_total
        
        return order_lines
    
    def generate_revenue_data(self) -> Dict:
        """Generate complete revenue dataset for all months"""
        logger.info("Starting revenue data generation...")
        
        # Generate base data
        logger.info("Generating product catalog...")
        products = self.generate_product_catalog()
        
        logger.info("Generating customer base...")
        customers = self.generate_customers(2000)
        
        # Generate orders for each month
        all_orders = []
        monthly_summaries = []
        
        for month_target in self.monthly_targets:
            try:
                month_orders = self.generate_monthly_orders(
                    month_target, products, customers
                )
                all_orders.extend(month_orders)
                
                # Calculate monthly summary
                month_revenue = sum(order['amount_total'] for order in month_orders)
                month_orders_count = len(month_orders)
                avg_order_value = month_revenue / month_orders_count if month_orders_count > 0 else 0
                
                monthly_summaries.append({
                    'month': month_target['month'],
                    'year': month_target['year'],
                    'month_name': month_target['month_name'],
                    'orders_count': month_orders_count,
                    'revenue': month_revenue,
                    'avg_order_value': avg_order_value,
                    'target_revenue': month_target['revenue_target'],
                    'revenue_achievement': (month_revenue / month_target['revenue_target']) * 100,
                    'seasonality_multiplier': month_target['seasonality_multiplier']
                })
                
            except Exception as e:
                logger.error(f"Error generating orders for {month_target['month_name']}: {e}")
                continue
        
        # Calculate overall statistics
        total_revenue = sum(order['amount_total'] for order in all_orders)
        total_orders = len(all_orders)
        avg_monthly_revenue = total_revenue / self.months_to_generate
        avg_monthly_orders = total_orders / self.months_to_generate
        overall_avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        # Create comprehensive dataset
        revenue_data = {
            'generation_date': datetime.now().isoformat(),
            'summary': {
                'total_revenue': total_revenue,
                'total_orders': total_orders,
                'months_generated': self.months_to_generate,
                'avg_monthly_revenue': avg_monthly_revenue,
                'avg_monthly_orders': avg_monthly_orders,
                'overall_avg_order_value': overall_avg_order_value,
                'target_monthly_revenue': self.target_monthly_revenue,
                'revenue_achievement_overall': (avg_monthly_revenue / self.target_monthly_revenue) * 100
            },
            'monthly_breakdown': monthly_summaries,
            'products': products,
            'customers': customers,
            'orders': all_orders
        }
        
        logger.info("Revenue data generation completed successfully!")
        logger.info(f"Generated {total_orders:,} orders totaling €{total_revenue:,.2f}")
        logger.info(f"Average monthly revenue: €{avg_monthly_revenue:,.2f}")
        logger.info(f"Average order value: €{overall_avg_order_value:.2f}")
        
        return revenue_data
    
    def save_data(self, revenue_data: Dict):
        """Save revenue data to multiple formats"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save complete dataset
        complete_file = self.output_dir / f"complete_revenue_data_{timestamp}.json"
        with open(complete_file, 'w') as f:
            json.dump(revenue_data, f, indent=2, default=str)
        logger.info(f"Saved complete dataset to: {complete_file}")
        
        # Save orders for Odoo import
        orders_file = self.output_dir / f"sales_orders_{timestamp}.json"
        orders_for_import = []
        
        for order in revenue_data['orders']:
            # Convert to Odoo-compatible format
            odoo_order = {
                'name': order['order_id'],
                'partner_id': order['customer_id'],
                'date_order': order['order_date'],
                'state': order['state'],
                'amount_untaxed': order['amount_untaxed'],
                'amount_tax': order['amount_tax'],
                'amount_total': order['amount_total'],
                'currency_id': 'EUR',
                'user_id': 'Shopify',  # Salesperson
                'payment_term_id': order['payment_term'],
                'order_line': []
            }
            
            for line in order['order_lines']:
                odoo_line = {
                    'product_id': line['product_sku'],
                    'name': line['product_name'],
                    'product_uom_qty': line['quantity'],
                    'price_unit': line['price_unit'],
                    'price_subtotal': line['price_subtotal'],
                    'price_total': line['price_total']
                }
                odoo_order['order_line'].append(odoo_line)
            
            orders_for_import.append(odoo_order)
        
        with open(orders_file, 'w') as f:
            json.dump(orders_for_import, f, indent=2, default=str)
        logger.info(f"Saved Odoo-compatible orders to: {orders_file}")
        
        # Save summary report
        summary_file = self.output_dir / f"revenue_summary_{timestamp}.json"
        summary_data = {
            'generation_date': revenue_data['generation_date'],
            'summary': revenue_data['summary'],
            'monthly_breakdown': revenue_data['monthly_breakdown']
        }
        
        with open(summary_file, 'w') as f:
            json.dump(summary_data, f, indent=2, default=str)
        logger.info(f"Saved summary report to: {summary_file}")
        
        # Create CSV for easy analysis
        try:
            # Monthly summary CSV
            monthly_df = pd.DataFrame(revenue_data['monthly_breakdown'])
            monthly_csv = self.output_dir / f"monthly_revenue_{timestamp}.csv"
            monthly_df.to_csv(monthly_csv, index=False)
            logger.info(f"Saved monthly CSV to: {monthly_csv}")
            
            # Orders CSV (sample - first 1000 orders)
            orders_sample = revenue_data['orders'][:1000]
            orders_df = pd.DataFrame(orders_sample)
            orders_csv = self.output_dir / f"orders_sample_{timestamp}.csv"
            orders_df.to_csv(orders_csv, index=False)
            logger.info(f"Saved orders sample CSV to: {orders_csv}")
            
        except Exception as e:
            logger.warning(f"Could not create CSV files: {e}")
        
        return {
            'complete_file': str(complete_file),
            'orders_file': str(orders_file),
            'summary_file': str(summary_file)
        }
    
    def print_summary(self, revenue_data: Dict):
        """Print comprehensive summary of generated data"""
        summary = revenue_data['summary']
        monthly = revenue_data['monthly_breakdown']
        
        print("\n" + "="*80)
        print("🚀 REVENUE GENERATION SUMMARY")
        print("="*80)
        
        print(f"\n📊 OVERALL PERFORMANCE")
        print(f"   Total Revenue Generated: €{summary['total_revenue']:,.2f}")
        print(f"   Total Orders Generated:  {summary['total_orders']:,}")
        print(f"   Months Generated:        {summary['months_generated']}")
        print(f"   Average Monthly Revenue: €{summary['avg_monthly_revenue']:,.2f}")
        print(f"   Average Monthly Orders:  {summary['avg_monthly_orders']:,.0f}")
        print(f"   Overall Avg Order Value: €{summary['overall_avg_order_value']:.2f}")
        print(f"   Revenue Target Achievement: {summary['revenue_achievement_overall']:.1f}%")
        
        print(f"\n🎯 TARGET vs ACTUAL")
        print(f"   Monthly Revenue Target:  €{self.target_monthly_revenue:,.2f}")
        print(f"   Achievement Status:      {'✅ TARGET MET' if summary['revenue_achievement_overall'] >= 90 else '⚠️  BELOW TARGET'}")
        
        print(f"\n📅 MONTHLY BREAKDOWN")
        print("-" * 120)
        print(f"{'Month':<12} {'Orders':<8} {'Revenue (€)':<15} {'Target (€)':<15} {'Achievement':<12} {'AOV (€)':<10} {'Seasonality':<12}")
        print("-" * 120)
        
        for month_data in monthly:
            achievement = month_data['revenue_achievement']
            status_icon = "✅" if achievement >= 90 else "⚠️" if achievement >= 80 else "❌"
            
            print(f"{month_data['month_name']:<12} "
                  f"{month_data['orders_count']:<8,} "
                  f"€{month_data['revenue']:<14,.0f} "
                  f"€{month_data['target_revenue']:<14,.0f} "
                  f"{achievement:<6.1f}% {status_icon:<4} "
                  f"€{month_data['avg_order_value']:<9.2f} "
                  f"{month_data['seasonality_multiplier']:<12.2f}")
        
        print("-" * 120)
        
        # Order value distribution analysis
        order_tiers = {'small': 0, 'medium': 0, 'large': 0, 'premium': 0}
        for order in revenue_data['orders']:
            tier = order.get('order_tier', 'medium')
            order_tiers[tier] += 1
        
        total_orders = sum(order_tiers.values())
        
        print(f"\n💰 ORDER VALUE DISTRIBUTION")
        print(f"   Small Orders (€60-100):      {order_tiers['small']:,} ({order_tiers['small']/total_orders*100:.1f}%) - Target: 15%")
        print(f"   Medium Orders (€120-200):    {order_tiers['medium']:,} ({order_tiers['medium']/total_orders*100:.1f}%) - Target: 60%")
        print(f"   Large Orders (€200-350):     {order_tiers['large']:,} ({order_tiers['large']/total_orders*100:.1f}%) - Target: 20%")
        print(f"   Premium Orders (€350-500):   {order_tiers['premium']:,} ({order_tiers['premium']/total_orders*100:.1f}%) - Target: 5%")
        
        print(f"\n🎪 SEASONALITY INSIGHTS")
        winter_months = [m for m in monthly if m['month'] in [10, 11, 12, 1, 2]]
        summer_months = [m for m in monthly if m['month'] in [5, 6, 7, 8, 9]]
        
        if winter_months:
            winter_avg = np.mean([m['revenue'] for m in winter_months])
            print(f"   Winter Average (Hoodies/Jackets): €{winter_avg:,.2f}")
        
        if summer_months:
            summer_avg = np.mean([m['revenue'] for m in summer_months])
            print(f"   Summer Average (Shorts/Tanks):   €{summer_avg:,.2f}")
        
        holiday_months = [m for m in monthly if m['month'] in [11, 12]]
        if holiday_months:
            holiday_avg = np.mean([m['revenue'] for m in holiday_months])
            print(f"   Holiday Average (Accessories):   €{holiday_avg:,.2f}")
        
        print("\n" + "="*80)
        print("🎉 Revenue generation completed successfully!")
        print("   All orders have salesperson set to 'Shopify'")
        print("   Data includes 12 months of historical orders")
        print("   Ready for Odoo import!")
        print("="*80)


def main():
    """Main execution function"""
    try:
        # Initialize revenue generator
        generator = RevenueGenerator(
            target_monthly_revenue=300000.0,  # €300k monthly target
            months_to_generate=12
        )
        
        # Generate comprehensive revenue data
        revenue_data = generator.generate_revenue_data()
        
        # Save data in multiple formats
        files_saved = generator.save_data(revenue_data)
        
        # Print comprehensive summary
        generator.print_summary(revenue_data)
        
        print(f"\n📁 FILES SAVED:")
        for file_type, file_path in files_saved.items():
            print(f"   {file_type}: {file_path}")
        
        print(f"\n🚀 SUCCESS: Generated €250k-400k monthly revenue data!")
        print(f"   Target achieved: {revenue_data['summary']['revenue_achievement_overall']:.1f}%")
        print(f"   Ready for Odoo import with 'Shopify' salesperson!")
        
        return True
        
    except Exception as e:
        logger.error(f"Revenue generation failed: {e}")
        print(f"\n❌ ERROR: Revenue generation failed - {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)