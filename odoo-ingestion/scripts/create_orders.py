#!/usr/bin/env python3
"""
Sales Order Creation Script Using DataCo Patterns

This script generates realistic sales orders based on DataCo supply chain patterns.
It creates orders with proper customer relationships, product selections, pricing,
and shipping data that maintains referential integrity.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from pathlib import Path
import logging
from typing import Dict, List, Any, Optional, Tuple
import json
import random
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SalesOrderGenerator:
    """Generates realistic sales orders based on DataCo patterns"""
    
    def __init__(self, 
                 dataco_file: str,
                 customers_file: str,
                 products_file: str,
                 output_dir: str = "data/transformed",
                 num_orders: int = 2000):
        
        self.dataco_file = Path(dataco_file)
        self.customers_file = Path(customers_file)
        self.products_file = Path(products_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.num_orders = num_orders
        
        # Load reference data
        self.customers_df = None
        self.products_df = None
        self.dataco_patterns = None
        
        # Order patterns from DataCo
        self.order_statuses = ['COMPLETE', 'PENDING', 'CLOSED', 'PROCESSING', 'CANCELED']
        self.shipping_modes = ['Standard Class', 'First Class', 'Second Class', 'Same Day']
        self.payment_types = ['DEBIT', 'CASH', 'TRANSFER', 'PAYMENT']
        
        # Seasonal patterns for fitness apparel
        self.seasonal_patterns = self._create_seasonal_patterns()
        
        # Load data
        self._load_reference_data()
    
    def _create_seasonal_patterns(self) -> Dict[int, Dict[str, float]]:
        """Create seasonal buying patterns for fitness apparel"""
        return {
            1: {'hoodies': 1.3, 'jackets': 1.4, 't-shirts': 0.8, 'shorts': 0.6, 'leggings': 1.2},  # Jan
            2: {'hoodies': 1.2, 'jackets': 1.3, 't-shirts': 0.9, 'shorts': 0.7, 'leggings': 1.1},  # Feb
            3: {'hoodies': 1.0, 'jackets': 1.1, 't-shirts': 1.1, 'shorts': 1.2, 'leggings': 1.0},  # Mar
            4: {'hoodies': 0.8, 'jackets': 0.9, 't-shirts': 1.2, 'shorts': 1.4, 'leggings': 1.1},  # Apr
            5: {'hoodies': 0.7, 'jackets': 0.7, 't-shirts': 1.3, 'shorts': 1.5, 'leggings': 1.0},  # May
            6: {'hoodies': 0.6, 'jackets': 0.6, 't-shirts': 1.4, 'shorts': 1.6, 'leggings': 0.9},  # Jun
            7: {'hoodies': 0.5, 'jackets': 0.5, 't-shirts': 1.5, 'shorts': 1.7, 'leggings': 0.8},  # Jul
            8: {'hoodies': 0.6, 'jackets': 0.6, 't-shirts': 1.4, 'shorts': 1.6, 'leggings': 0.9},  # Aug
            9: {'hoodies': 0.8, 'jackets': 0.9, 't-shirts': 1.2, 'shorts': 1.3, 'leggings': 1.1},  # Sep
            10: {'hoodies': 1.0, 'jackets': 1.1, 't-shirts': 1.0, 'shorts': 1.0, 'leggings': 1.2}, # Oct
            11: {'hoodies': 1.2, 'jackets': 1.3, 't-shirts': 0.9, 'shorts': 0.8, 'leggings': 1.3}, # Nov
            12: {'hoodies': 1.4, 'jackets': 1.5, 't-shirts': 0.8, 'shorts': 0.7, 'leggings': 1.2}, # Dec
        }
    
    def _load_reference_data(self) -> None:
        """Load customers, products, and DataCo pattern data"""
        try:
            # Load customers
            if self.customers_file.exists():
                self.customers_df = pd.read_csv(self.customers_file)
                logger.info(f"Loaded {len(self.customers_df)} customers")
            else:
                logger.warning(f"Customer file not found: {self.customers_file}")
                self.customers_df = pd.DataFrame()
            
            # Load products
            if self.products_file.exists():
                self.products_df = pd.read_csv(self.products_file)
                logger.info(f"Loaded {len(self.products_df)} products")
            else:
                logger.warning(f"Products file not found: {self.products_file}")
                self.products_df = pd.DataFrame()
            
            # Load DataCo patterns
            if self.dataco_file.exists():
                self.dataco_patterns = pd.read_csv(self.dataco_file, encoding='latin-1')
                logger.info(f"Loaded {len(self.dataco_patterns)} DataCo records")
                self._analyze_order_patterns()
            else:
                logger.warning(f"DataCo file not found: {self.dataco_file}")
                self._create_fallback_patterns()
                
        except Exception as e:
            logger.error(f"Error loading reference data: {e}")
            self._create_fallback_patterns()
    
    def _analyze_order_patterns(self) -> None:
        """Analyze order patterns from DataCo data"""
        try:
            df = self.dataco_patterns
            
            # Order status distribution
            self.status_distribution = df['Order Status'].value_counts(normalize=True).to_dict()
            
            # Shipping mode preferences by customer segment
            self.shipping_by_segment = {}
            for segment in df['Customer Segment'].unique():
                if pd.notna(segment):
                    segment_data = df[df['Customer Segment'] == segment]
                    self.shipping_by_segment[segment] = segment_data['Shipping Mode'].value_counts(normalize=True).to_dict()
            
            # Quantity patterns
            self.quantity_stats = {
                'mean': df['Order Item Quantity'].mean(),
                'std': df['Order Item Quantity'].std(),
                'min': df['Order Item Quantity'].min(),
                'max': df['Order Item Quantity'].max()
            }
            
            # Discount patterns
            if 'Order Item Discount Rate' in df.columns:
                self.discount_stats = {
                    'mean': df['Order Item Discount Rate'].mean(),
                    'std': df['Order Item Discount Rate'].std(),
                    'rate': (df['Order Item Discount Rate'] > 0).mean()  # Probability of discount
                }
            
            # Seasonal patterns from order dates
            if 'order date (DateOrders)' in df.columns:
                df['order_month'] = pd.to_datetime(df['order date (DateOrders)']).dt.month
                self.monthly_order_distribution = df['order_month'].value_counts(normalize=True).sort_index().to_dict()
            
            logger.info("DataCo order patterns analyzed successfully")
            
        except Exception as e:
            logger.warning(f"Error analyzing DataCo patterns: {e}")
            self._create_fallback_patterns()
    
    def _create_fallback_patterns(self) -> None:
        """Create fallback patterns when DataCo analysis fails"""
        self.status_distribution = {
            'COMPLETE': 0.65,
            'PENDING': 0.15,
            'PROCESSING': 0.12,
            'CLOSED': 0.05,
            'CANCELED': 0.03
        }
        
        self.shipping_by_segment = {
            'Consumer': {'Standard Class': 0.6, 'First Class': 0.3, 'Second Class': 0.1},
            'Corporate': {'Standard Class': 0.4, 'First Class': 0.4, 'Same Day': 0.2},
            'Home Office': {'Standard Class': 0.7, 'First Class': 0.2, 'Second Class': 0.1}
        }
        
        self.quantity_stats = {'mean': 2.5, 'std': 1.8, 'min': 1, 'max': 15}
        self.discount_stats = {'mean': 0.08, 'std': 0.12, 'rate': 0.3}
        self.monthly_order_distribution = {i: 1/12 for i in range(1, 13)}
        
        logger.info("Using fallback order patterns")
    
    def generate_orders(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Generate sales orders with line items"""
        logger.info(f"Generating {self.num_orders} sales orders")
        
        if self.customers_df.empty or self.products_df.empty:
            logger.error("Cannot generate orders without customer and product data")
            return pd.DataFrame(), pd.DataFrame()
        
        orders = []
        order_lines = []
        
        for order_num in range(1, self.num_orders + 1):
            # Generate order header
            order_data = self._generate_order_header(order_num)
            
            # Generate order lines
            lines = self._generate_order_lines(order_data['external_id'], order_data)
            
            # Update order totals
            order_data.update(self._calculate_order_totals(lines))
            
            orders.append(order_data)
            order_lines.extend(lines)
        
        orders_df = pd.DataFrame(orders)
        order_lines_df = pd.DataFrame(order_lines)
        
        logger.info(f"Generated {len(orders_df)} orders with {len(order_lines_df)} line items")
        return orders_df, order_lines_df
    
    def _generate_order_header(self, order_num: int) -> Dict[str, Any]:
        """Generate sales order header"""
        
        # Select customer based on segment probabilities
        customer = self._select_customer()
        customer_segment = self._get_customer_segment(customer)
        
        # Generate order date with seasonal patterns
        order_date = self._generate_order_date()
        
        # Determine shipping method based on customer segment
        shipping_mode = self._select_shipping_mode(customer_segment)
        
        # Calculate delivery dates
        delivery_days = self._calculate_delivery_days(shipping_mode)
        expected_delivery = order_date + timedelta(days=delivery_days['scheduled'])
        actual_delivery = order_date + timedelta(days=delivery_days['actual'])
        
        # Determine order status
        status = self._select_order_status(order_date)
        
        # Payment method
        payment_type = random.choice(self.payment_types)
        
        order_data = {
            'external_id': f'gym_coffee_order_{order_num:06d}',
            'name': f'SO-{order_num:06d}',
            'partner_id': customer['external_id'],
            'partner_shipping_id': customer['external_id'],  # Same as billing for now
            'partner_invoice_id': customer['external_id'],
            
            # Dates
            'date_order': order_date.isoformat(),
            'confirmation_date': order_date.isoformat() if status != 'PENDING' else '',
            'expected_date': expected_delivery.isoformat(),
            'commitment_date': expected_delivery.isoformat(),
            
            # Status and workflow
            'state': self._map_status_to_odoo_state(status),
            'dataco_status': status,  # Keep original status for analysis
            'invoice_status': self._get_invoice_status(status),
            'delivery_status': self._get_delivery_status(status, order_date, actual_delivery),
            
            # Commercial fields
            'pricelist_id': 'gym_coffee_pricelist_default',
            'currency_id': 'USD',
            'payment_term_id': self._get_payment_terms(customer_segment),
            
            # Shipping
            'carrier_id': self._map_shipping_mode(shipping_mode),
            'delivery_method': shipping_mode,
            'incoterm': 'EXW',  # Ex Works
            
            # Other fields
            'company_id': 1,
            'team_id': 1,  # Sales team
            'user_id': random.randint(1, 5),  # Salesperson
            'client_order_ref': f'CUST-REF-{order_num}',
            'origin': 'Website',
            'note': f'Order generated from DataCo patterns - Segment: {customer_segment}',
            
            # Analytics
            'customer_segment': customer_segment,
            'order_month': order_date.month,
            'order_quarter': f"Q{((order_date.month - 1) // 3) + 1}",
            'order_year': order_date.year,
            'payment_type': payment_type,
            
            # Will be calculated after lines
            'amount_untaxed': 0,
            'amount_tax': 0,
            'amount_total': 0,
            'margin': 0,
            'margin_percent': 0
        }
        
        return order_data
    
    def _generate_order_lines(self, order_id: str, order_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate order line items"""
        
        lines = []
        order_date = datetime.fromisoformat(order_data['date_order'].replace('Z', '+00:00'))
        order_month = order_date.month
        
        # Determine number of line items (influenced by customer segment)
        customer_segment = order_data['customer_segment']
        if customer_segment == 'Corporate':
            num_lines = max(1, int(np.random.normal(4, 2)))  # Corporate orders tend to be larger
        elif customer_segment == 'Home Office':
            num_lines = max(1, int(np.random.normal(2.5, 1.5)))
        else:  # Consumer
            num_lines = max(1, int(np.random.normal(2, 1)))
        
        num_lines = min(num_lines, 8)  # Cap at 8 items
        
        # Select products with seasonal bias
        selected_products = self._select_products_for_order(num_lines, order_month)
        
        for line_seq, product in enumerate(selected_products, 1):
            # Quantity based on DataCo patterns
            quantity = max(1, int(np.random.normal(self.quantity_stats['mean'], self.quantity_stats['std'])))
            quantity = min(quantity, 10)  # Cap at 10 per line
            
            # Pricing
            unit_price = float(product.get('list_price', 0))
            
            # Apply discount based on patterns
            discount_percent = self._calculate_discount(customer_segment, unit_price, quantity)
            discount_amount = unit_price * quantity * (discount_percent / 100)
            
            # Calculate line totals
            price_subtotal = unit_price * quantity - discount_amount
            price_total = price_subtotal * 1.08  # Assume 8% tax
            
            # Margin calculation
            standard_cost = float(product.get('standard_price', 0))
            margin_amount = price_subtotal - (standard_cost * quantity)
            margin_percent = (margin_amount / price_subtotal * 100) if price_subtotal > 0 else 0
            
            line = {
                'external_id': f'gym_coffee_line_{order_id}_{line_seq:02d}',
                'order_id': order_id,
                'sequence': line_seq * 10,
                'product_id': product['external_id'],
                'product_template_id': product.get('product_tmpl_id', ''),
                'name': product.get('name', 'Unknown Product'),
                'product_uom_qty': quantity,
                'product_uom': 'uom_unit',
                'qty_delivered': quantity if order_data['state'] in ['sale', 'done'] else 0,
                'qty_invoiced': quantity if order_data['invoice_status'] == 'invoiced' else 0,
                
                # Pricing
                'price_unit': unit_price,
                'discount': discount_percent,
                'price_subtotal': round(price_subtotal, 2),
                'price_tax': round(price_total - price_subtotal, 2),
                'price_total': round(price_total, 2),
                
                # Analytics
                'purchase_price': standard_cost,
                'margin': round(margin_amount, 2),
                'margin_percent': round(margin_percent, 2),
                
                # Product details for analysis
                'product_category': product.get('category', ''),
                'product_color': product.get('color_value', ''),
                'product_size': product.get('size_value', ''),
                
                # Status
                'state': order_data['state'],
                'invoice_status': 'to invoice' if order_data['state'] == 'sale' and order_data['invoice_status'] != 'invoiced' else 'no',
                'qty_to_invoice': quantity if order_data['state'] == 'sale' and order_data['invoice_status'] != 'invoiced' else 0,
                
                # Delivery
                'route_id': 'stock_route_warehouse0_mto',  # Make to Order
                'move_ids': f'stock_move_{order_id}_{line_seq:02d}'
            }
            
            lines.append(line)
        
        return lines
    
    def _select_customer(self) -> Dict[str, Any]:
        """Select customer based on segment distribution"""
        # Weight customers by their expected spend and recency
        customers_with_weights = []
        
        for _, customer in self.customers_df.iterrows():
            # Base weight on expected spend
            weight = customer.get('expected_annual_spend', 250)
            
            # Adjust for recency (newer customers more likely to order)
            if 'create_date' in customer:
                try:
                    create_date = datetime.fromisoformat(customer['create_date'].replace('Z', '+00:00'))
                    days_since_creation = (datetime.now() - create_date).days
                    recency_multiplier = max(0.1, 1 - (days_since_creation / 365))
                    weight *= recency_multiplier
                except:
                    pass
            
            customers_with_weights.append((customer, weight))
        
        # Select customer based on weights
        total_weight = sum(weight for _, weight in customers_with_weights)
        r = random.uniform(0, total_weight)
        
        cumulative_weight = 0
        for customer, weight in customers_with_weights:
            cumulative_weight += weight
            if r <= cumulative_weight:
                return customer
        
        # Fallback to random selection
        return self.customers_df.iloc[random.randint(0, len(self.customers_df) - 1)]
    
    def _get_customer_segment(self, customer: Dict[str, Any]) -> str:
        """Get customer segment from customer data"""
        category_id = customer.get('category_id', '')
        
        if 'corporate' in category_id.lower():
            return 'Corporate'
        elif 'home_office' in category_id.lower():
            return 'Home Office'
        else:
            return 'Consumer'
    
    def _generate_order_date(self) -> datetime:
        """Generate order date with seasonal patterns"""
        # Generate date within last 18 months with seasonal bias
        days_back = int(np.random.exponential(180))  # Exponential favors recent dates
        days_back = min(days_back, 540)  # Cap at 18 months
        
        base_date = datetime.now() - timedelta(days=days_back)
        
        # Apply monthly distribution bias
        month = base_date.month
        monthly_prob = self.monthly_order_distribution.get(month, 1/12)
        
        # Adjust date based on monthly probability
        if monthly_prob < (1/12 * 0.8):  # If month is below average
            # Try again with higher probability for better months
            if random.random() < 0.3:
                better_months = [m for m, p in self.monthly_order_distribution.items() if p > (1/12 * 1.1)]
                if better_months:
                    target_month = random.choice(better_months)
                    base_date = base_date.replace(month=target_month)
        
        # Add some random hour/minute
        base_date = base_date.replace(
            hour=random.randint(8, 20),
            minute=random.randint(0, 59),
            second=random.randint(0, 59)
        )
        
        return base_date
    
    def _select_products_for_order(self, num_products: int, order_month: int) -> List[Dict[str, Any]]:
        """Select products for order with seasonal bias"""
        seasonal_weights = self.seasonal_patterns.get(order_month, {})
        
        # Create weighted product list
        weighted_products = []
        for _, product in self.products_df.iterrows():
            category = product.get('product_category', product.get('category', ''))
            weight = seasonal_weights.get(category, 1.0)
            
            # Adjust weight based on inventory
            qty_available = product.get('qty_available', 0)
            if qty_available <= 0:
                weight *= 0.1  # Much less likely to order out-of-stock items
            elif qty_available < 5:
                weight *= 0.5  # Less likely for low stock
            
            weighted_products.append((product, weight))
        
        # Select products without replacement
        selected_products = []
        available_products = weighted_products.copy()
        
        for _ in range(min(num_products, len(available_products))):
            if not available_products:
                break
            
            # Calculate total weight
            total_weight = sum(weight for _, weight in available_products)
            if total_weight <= 0:
                # Fall back to random selection
                product, _ = random.choice(available_products)
                selected_products.append(product)
                available_products.remove((product, _))
                continue
            
            # Weighted random selection
            r = random.uniform(0, total_weight)
            cumulative_weight = 0
            
            for i, (product, weight) in enumerate(available_products):
                cumulative_weight += weight
                if r <= cumulative_weight:
                    selected_products.append(product)
                    available_products.pop(i)
                    break
        
        return selected_products
    
    def _calculate_discount(self, customer_segment: str, unit_price: float, quantity: int) -> float:
        """Calculate discount based on DataCo patterns and business rules"""
        # Base discount probability from patterns
        discount_probability = self.discount_stats.get('rate', 0.3)
        
        # Adjust probability by segment
        segment_multipliers = {
            'Corporate': 1.5,
            'Home Office': 1.2,
            'Consumer': 1.0
        }
        discount_probability *= segment_multipliers.get(customer_segment, 1.0)
        
        # Adjust by quantity (volume discounts)
        if quantity >= 5:
            discount_probability *= 1.3
        elif quantity >= 3:
            discount_probability *= 1.1
        
        # Adjust by price (higher priced items more likely to have discounts)
        if unit_price > 100:
            discount_probability *= 1.2
        elif unit_price > 50:
            discount_probability *= 1.1
        
        # Apply discount
        if random.random() < discount_probability:
            base_discount = max(0, np.random.normal(
                self.discount_stats.get('mean', 0.08) * 100,
                self.discount_stats.get('std', 0.12) * 100
            ))
            
            # Cap discounts
            max_discount = {'Corporate': 25, 'Home Office': 15, 'Consumer': 10}
            return min(base_discount, max_discount.get(customer_segment, 10))
        
        return 0
    
    def _calculate_order_totals(self, lines: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate order totals from line items"""
        amount_untaxed = sum(line['price_subtotal'] for line in lines)
        amount_tax = sum(line['price_tax'] for line in lines)
        amount_total = sum(line['price_total'] for line in lines)
        margin = sum(line['margin'] for line in lines)
        
        margin_percent = (margin / amount_untaxed * 100) if amount_untaxed > 0 else 0
        
        return {
            'amount_untaxed': round(amount_untaxed, 2),
            'amount_tax': round(amount_tax, 2),
            'amount_total': round(amount_total, 2),
            'margin': round(margin, 2),
            'margin_percent': round(margin_percent, 2)
        }
    
    def _select_shipping_mode(self, customer_segment: str) -> str:
        """Select shipping mode based on customer segment"""
        segment_prefs = self.shipping_by_segment.get(customer_segment, {})
        
        if not segment_prefs:
            return random.choice(self.shipping_modes)
        
        modes = list(segment_prefs.keys())
        weights = list(segment_prefs.values())
        
        return np.random.choice(modes, p=weights)
    
    def _calculate_delivery_days(self, shipping_mode: str) -> Dict[str, int]:
        """Calculate delivery days based on shipping mode"""
        base_days = {
            'Same Day': 1,
            'First Class': 2,
            'Second Class': 4,
            'Standard Class': 6
        }
        
        scheduled = base_days.get(shipping_mode, 6)
        
        # Add variability for actual delivery
        if random.random() < 0.15:  # 15% chance of delay
            actual = scheduled + random.randint(1, 3)
        elif random.random() < 0.05:  # 5% chance of early delivery
            actual = max(1, scheduled - 1)
        else:
            actual = scheduled
        
        return {'scheduled': scheduled, 'actual': actual}
    
    def _select_order_status(self, order_date: datetime) -> str:
        """Select order status based on date and patterns"""
        days_since_order = (datetime.now() - order_date).days
        
        # Recent orders more likely to be pending/processing
        if days_since_order <= 1:
            statuses = ['PENDING', 'PROCESSING']
            weights = [0.7, 0.3]
        elif days_since_order <= 7:
            statuses = ['PENDING', 'PROCESSING', 'COMPLETE']
            weights = [0.3, 0.4, 0.3]
        else:
            # Use normal distribution for older orders
            statuses = list(self.status_distribution.keys())
            weights = list(self.status_distribution.values())
        
        return np.random.choice(statuses, p=weights)
    
    def _map_status_to_odoo_state(self, dataco_status: str) -> str:
        """Map DataCo status to Odoo sale order state"""
        mapping = {
            'PENDING': 'draft',
            'PROCESSING': 'sent',
            'COMPLETE': 'sale',
            'CLOSED': 'done',
            'CANCELED': 'cancel'
        }
        return mapping.get(dataco_status, 'draft')
    
    def _get_invoice_status(self, order_status: str) -> str:
        """Get invoice status based on order status"""
        if order_status in ['COMPLETE', 'CLOSED']:
            return 'invoiced' if random.random() < 0.8 else 'to invoice'
        elif order_status == 'PROCESSING':
            return 'to invoice' if random.random() < 0.3 else 'no'
        else:
            return 'no'
    
    def _get_delivery_status(self, order_status: str, order_date: datetime, delivery_date: datetime) -> str:
        """Get delivery status"""
        if order_status == 'CANCELED':
            return 'Shipping canceled'
        elif order_status in ['PENDING', 'PROCESSING']:
            return 'Pending'
        else:
            # Check if delivery was on time
            scheduled_days = self._calculate_delivery_days('Standard Class')['scheduled']
            expected_delivery = order_date + timedelta(days=scheduled_days)
            
            if delivery_date <= expected_delivery:
                if delivery_date < expected_delivery:
                    return 'Advance shipping'
                else:
                    return 'Shipping on time'
            else:
                return 'Late delivery'
    
    def _get_payment_terms(self, customer_segment: str) -> str:
        """Get payment terms based on customer segment"""
        terms_map = {
            'Consumer': 'gym_coffee_terms_immediate',
            'Home Office': 'gym_coffee_terms_net15',
            'Corporate': 'gym_coffee_terms_net30'
        }
        return terms_map.get(customer_segment, 'gym_coffee_terms_immediate')
    
    def _map_shipping_mode(self, shipping_mode: str) -> str:
        """Map shipping mode to Odoo carrier"""
        mapping = {
            'Standard Class': 'gym_coffee_carrier_standard',
            'First Class': 'gym_coffee_carrier_express',
            'Second Class': 'gym_coffee_carrier_economy',
            'Same Day': 'gym_coffee_carrier_same_day'
        }
        return mapping.get(shipping_mode, 'gym_coffee_carrier_standard')
    
    def create_stock_moves(self, order_lines_df: pd.DataFrame) -> pd.DataFrame:
        """Create stock movements for order lines"""
        stock_moves = []
        
        for _, line in order_lines_df.iterrows():
            if line.get('state') in ['sale', 'done'] and line.get('qty_delivered', 0) > 0:
                move = {
                    'external_id': line['move_ids'],
                    'name': f"Move: {line['name']}",
                    'product_id': line['product_id'],
                    'product_uom_qty': line['qty_delivered'],
                    'product_uom': 'uom_unit',
                    'location_id': 'stock_location_stock',
                    'location_dest_id': 'stock_location_customers',
                    'partner_id': '',  # Will be filled from order
                    'origin': line['order_id'],
                    'state': 'done' if line['state'] == 'done' else 'assigned',
                    'date': datetime.now().isoformat(),
                    'date_expected': datetime.now().isoformat(),
                    'company_id': 1,
                    'reference': f"SO {line['order_id']}"
                }
                stock_moves.append(move)
        
        return pd.DataFrame(stock_moves)
    
    def export_to_csv(self, orders_df: pd.DataFrame, order_lines_df: pd.DataFrame, stock_moves_df: pd.DataFrame) -> None:
        """Export order data to CSV files"""
        
        # Export orders
        orders_file = self.output_dir / 'odoo_sales_orders.csv'
        orders_df.to_csv(orders_file, index=False)
        logger.info(f"Exported {len(orders_df)} sales orders to {orders_file}")
        
        # Export order lines
        lines_file = self.output_dir / 'odoo_order_lines.csv'
        order_lines_df.to_csv(lines_file, index=False)
        logger.info(f"Exported {len(order_lines_df)} order lines to {lines_file}")
        
        # Export stock moves
        moves_file = self.output_dir / 'odoo_stock_moves.csv'
        stock_moves_df.to_csv(moves_file, index=False)
        logger.info(f"Exported {len(stock_moves_df)} stock moves to {moves_file}")
    
    def run_generation(self) -> None:
        """Run the complete order generation process"""
        logger.info("Starting sales order generation based on DataCo patterns")
        
        # Generate orders
        orders_df, order_lines_df = self.generate_orders()
        
        if orders_df.empty:
            logger.error("Order generation failed")
            return
        
        # Generate stock movements
        stock_moves_df = self.create_stock_moves(order_lines_df)
        
        # Export data
        self.export_to_csv(orders_df, order_lines_df, stock_moves_df)
        
        # Create analytics summary
        summary = {
            'generation_date': datetime.now().isoformat(),
            'total_orders': len(orders_df),
            'total_order_lines': len(order_lines_df),
            'total_stock_moves': len(stock_moves_df),
            'total_revenue': float(orders_df['amount_total'].sum()),
            'average_order_value': float(orders_df['amount_total'].mean()),
            'orders_by_status': orders_df['dataco_status'].value_counts().to_dict(),
            'orders_by_segment': orders_df['customer_segment'].value_counts().to_dict(),
            'top_products': order_lines_df.groupby('product_category').size().to_dict(),
            'monthly_distribution': orders_df['order_month'].value_counts().sort_index().to_dict(),
            'average_margin_percent': float(orders_df['margin_percent'].mean())
        }
        
        summary_file = self.output_dir / 'orders_generation_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info("Order generation completed successfully")
        logger.info(f"Summary: Generated {summary['total_orders']} orders worth ${summary['total_revenue']:,.2f}")


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate sales orders based on DataCo patterns')
    parser.add_argument('--dataco', default='../data/dataco/DataCoSupplyChainDataset.csv',
                       help='DataCo dataset file path')
    parser.add_argument('--customers', default='../data/transformed/odoo_customers.csv',
                       help='Generated customers CSV file')
    parser.add_argument('--products', default='../data/transformed/odoo_product_variants.csv',
                       help='Generated products CSV file')
    parser.add_argument('--output', default='../data/transformed',
                       help='Output directory for generated files')
    parser.add_argument('--count', type=int, default=2000,
                       help='Number of orders to generate')
    
    args = parser.parse_args()
    
    # Create generator and run
    generator = SalesOrderGenerator(
        args.dataco, 
        args.customers, 
        args.products, 
        args.output, 
        args.count
    )
    generator.run_generation()


if __name__ == "__main__":
    main()