#!/usr/bin/env python3
"""
Comprehensive Transaction Generator for Gym+Coffee
Generates 65,000 realistic retail transactions with complete order structure.

Agent: Transaction Generator
Part of swarm coordination for realistic retail data generation.
"""

import json
import random
import datetime
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
import uuid
import math

# Coordination imports
import os
import sys

@dataclass 
class OrderLine:
    """Individual line item within an order"""
    sku: str
    product_name: str
    quantity: int
    unit_price: float
    line_total: float
    discount_percent: float = 0.0
    discount_amount: float = 0.0
    category: str = ""
    
@dataclass
class PaymentInfo:
    """Payment method and details"""
    method: str  # 'credit_card', 'debit_card', 'cash', 'bank_transfer', 'gift_card'
    last_four: str = ""
    processor: str = ""
    transaction_fee: float = 0.0
    
@dataclass
class ShippingInfo:
    """Shipping and fulfillment details"""
    method: str  # 'standard', 'express', 'overnight', 'pickup', 'bopis'
    cost: float = 0.0
    carrier: str = ""
    tracking_number: str = ""
    estimated_delivery: str = ""
    
@dataclass 
class ReturnInfo:
    """Return record if applicable"""
    return_date: str
    return_reason: str
    return_amount: float
    credit_note_number: str
    items_returned: List[Dict[str, Any]]
    
@dataclass
class Transaction:
    """Complete transaction record"""
    # Core order info
    order_id: str
    order_date: str
    order_time: str
    channel: str  # 'online', 'retail', 'b2b'
    
    # Customer info
    customer_id: int
    customer_name: str
    customer_email: str
    customer_type: str  # 'individual', 'company'
    
    # Location info
    billing_address: Dict[str, str]
    shipping_address: Dict[str, str]
    
    # Order details
    order_lines: List[OrderLine]
    subtotal: float
    tax_rate: float
    tax_amount: float
    shipping_cost: float
    total_amount: float
    
    # Payment and fulfillment
    payment: PaymentInfo
    shipping: ShippingInfo
    
    # Order status
    status: str  # 'pending', 'confirmed', 'shipped', 'delivered', 'returned'
    fulfillment_status: str
    
    # Optional fields with defaults
    store_location: str = ""
    sales_rep: str = ""
    return_info: ReturnInfo = None
    created_by: str = "system"
    source: str = "transaction_generator"

class TransactionGenerator:
    """Generates realistic retail transactions for Gym+Coffee"""
    
    def __init__(self):
        self.products = []
        self.customers = []
        self.transactions = []
        
        # Load test data
        self.load_test_data()
        
        # Business rules and distributions
        self.setup_business_rules()
        
    def load_test_data(self):
        """Load product and customer data from test fixtures"""
        try:
            # Load products
            with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/tests/fixtures/generated/test-products.json', 'r') as f:
                product_data = json.load(f)
                self.products = [p for p in product_data['products'] if p.get('status') == 'active' and p.get('list_price', 0) > 0]
                
            # Load customers  
            with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/tests/fixtures/generated/test-customers.json', 'r') as f:
                customer_data = json.load(f)
                self.customers = [c for c in customer_data['customers'] if c.get('active', True) and c.get('email')]
                
            print(f"✅ Loaded {len(self.products)} products and {len(self.customers)} customers")
            
        except Exception as e:
            print(f"⚠️  Error loading test data: {e}")
            print("Using minimal fallback data...")
            self.create_fallback_data()
            
    def create_fallback_data(self):
        """Create minimal fallback data if test data unavailable"""
        self.products = [
            {
                'sku': 'GC10001-BLA-M',
                'name': 'Essential Hoodie - Black',
                'category': 'hoodies',
                'list_price': 75,
                'standard_cost': 25,
                'inventory_on_hand': 100
            },
            {
                'sku': 'GC10002-RED-L', 
                'name': 'Basic Tee - Red',
                'category': 't-shirts',
                'list_price': 35,
                'standard_cost': 12,
                'inventory_on_hand': 150
            }
        ]
        
        self.customers = [
            {
                'id': 1,
                'name': 'John Smith',
                'email': 'john.smith@email.com',
                'is_company': False,
                'city': 'Dublin',
                'country_id': [78, 'Ireland']
            },
            {
                'id': 2,
                'name': 'Gym Equipment Ltd',
                'email': 'orders@gymequipment.ie',
                'is_company': True,
                'city': 'Cork',
                'country_id': [78, 'Ireland']
            }
        ]
        
    def setup_business_rules(self):
        """Setup realistic business rules and distributions"""
        
        # Channel distribution (60% online, 20% retail, 20% B2B)
        self.channel_distribution = {
            'online': 0.60,
            'retail': 0.20,
            'b2b': 0.20
        }
        
        # Geographic distribution for Ireland focus
        self.location_distribution = {
            'Dublin': 0.35,
            'Cork': 0.15,
            'Galway': 0.10,
            'Limerick': 0.08,
            'Waterford': 0.07,
            'Other Ireland': 0.15,
            'UK': 0.06,
            'EU': 0.04
        }
        
        # Seasonal multipliers by month
        self.seasonal_multipliers = {
            1: 0.75,  # January (post-holiday low)
            2: 0.80,  # February 
            3: 0.85,  # March
            4: 0.90,  # April
            5: 1.00,  # May
            6: 1.05,  # June
            7: 1.10,  # July (summer high)
            8: 1.05,  # August  
            9: 1.00,  # September
            10: 1.10, # October (back to gym season)
            11: 1.15, # November (Black Friday)
            12: 1.20  # December (holidays)
        }
        
        # Day of week patterns (Monday = 0)
        self.daily_multipliers = {
            0: 0.90,  # Monday
            1: 0.95,  # Tuesday  
            2: 1.00,  # Wednesday
            3: 1.05,  # Thursday
            4: 1.15,  # Friday
            5: 1.25,  # Saturday
            6: 1.10   # Sunday
        }
        
        # Hour patterns for online orders
        self.hourly_online_pattern = {
            0: 0.2, 1: 0.1, 2: 0.1, 3: 0.1, 4: 0.1, 5: 0.1,
            6: 0.3, 7: 0.5, 8: 0.8, 9: 1.2, 10: 1.5, 11: 1.7,
            12: 1.8, 13: 1.6, 14: 1.4, 15: 1.3, 16: 1.2, 17: 1.1,
            18: 1.0, 19: 0.9, 20: 0.8, 21: 0.7, 22: 0.5, 23: 0.3
        }
        
        # Retail store hours (10 AM - 8 PM)
        self.retail_hours = list(range(10, 21))
        
        # Basket size distributions
        self.basket_sizes = {
            'online': {'min': 1, 'max': 4, 'avg': 1.8},
            'retail': {'min': 1, 'max': 3, 'avg': 1.5}, 
            'b2b': {'min': 5, 'max': 100, 'avg': 25}
        }
        
        # Return rates by channel
        self.return_rates = {
            'online': 0.235,  # 23.5% return rate
            'retail': 0.065,  # 6.5% return rate
            'b2b': 0.015     # 1.5% return rate
        }
        
        # Payment methods by channel
        self.payment_methods = {
            'online': {
                'credit_card': 0.65,
                'debit_card': 0.25,
                'paypal': 0.08,
                'gift_card': 0.02
            },
            'retail': {
                'credit_card': 0.45,
                'debit_card': 0.40,
                'cash': 0.15
            },
            'b2b': {
                'bank_transfer': 0.60,
                'credit_card': 0.25,
                'invoice_30': 0.15
            }
        }
        
        # Fulfillment methods  
        self.fulfillment_methods = {
            'online': {
                'standard_shipping': 0.70,
                'express_shipping': 0.18,
                'bopis': 0.07,  # Buy online pickup in store
                'click_collect': 0.05
            },
            'retail': {
                'immediate': 1.0
            },
            'b2b': {
                'warehouse_delivery': 0.80,
                'pickup': 0.20
            }
        }
        
    def generate_order_id(self) -> str:
        """Generate realistic order ID"""
        timestamp = datetime.datetime.now().strftime("%y%m%d")
        random_part = str(random.randint(10000, 99999))
        return f"GC{timestamp}{random_part}"
        
    def select_channel(self) -> str:
        """Select channel based on distribution weights"""
        rand = random.random()
        if rand < self.channel_distribution['online']:
            return 'online'
        elif rand < self.channel_distribution['online'] + self.channel_distribution['retail']:
            return 'retail'
        else:
            return 'b2b'
            
    def generate_transaction_datetime(self) -> tuple:
        """Generate realistic transaction date and time"""
        # Generate random date in 2024
        start_date = datetime.date(2024, 1, 1)
        end_date = datetime.date(2024, 12, 31)
        
        days_diff = (end_date - start_date).days
        random_days = random.randint(0, days_diff)
        
        transaction_date = start_date + datetime.timedelta(days=random_days)
        
        # Apply seasonal and daily multipliers for realistic distribution
        month_mult = self.seasonal_multipliers[transaction_date.month]
        day_mult = self.daily_multipliers[transaction_date.weekday()]
        
        # Bias random selection based on multipliers
        accept_prob = month_mult * day_mult / 1.5  # Normalize
        if random.random() > accept_prob:
            # Try again with better probability
            return self.generate_transaction_datetime()
            
        return transaction_date, self.generate_transaction_time()
        
    def generate_transaction_time(self) -> str:
        """Generate realistic transaction time based on patterns"""
        # Weight hours based on typical shopping patterns
        hours = list(range(24))
        weights = [self.hourly_online_pattern[h] for h in hours]
        
        hour = random.choices(hours, weights=weights)[0]
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        
        return f"{hour:02d}:{minute:02d}:{second:02d}"
        
    def select_customer(self, channel: str) -> Dict:
        """Select appropriate customer based on channel"""
        if channel == 'b2b':
            # Prefer company customers for B2B
            company_customers = [c for c in self.customers if c.get('is_company', False)]
            if company_customers:
                return random.choice(company_customers)
                
        # For retail/online or if no companies available
        return random.choice(self.customers)
        
    def generate_basket(self, channel: str) -> List[OrderLine]:
        """Generate realistic basket of products"""
        basket_config = self.basket_sizes[channel]
        
        # Determine basket size
        if channel == 'b2b':
            # B2B orders are larger, use normal distribution
            basket_size = max(basket_config['min'], 
                            int(random.normalvariate(basket_config['avg'], 8)))
            basket_size = min(basket_size, basket_config['max'])
        else:
            # Retail/online tend toward smaller baskets
            weights = [3, 2, 1.5, 1, 0.5]  # Favor 1-2 items
            basket_size = random.choices(range(1, min(6, len(weights) + 1)), weights=weights)[0]
            
        # Select products
        order_lines = []
        selected_products = random.choices(self.products, k=basket_size)
        
        for product in selected_products:
            # Determine quantity 
            if channel == 'b2b':
                quantity = random.choices([1, 2, 3, 5, 10, 25], weights=[1, 2, 2, 3, 4, 2])[0]
            else:
                quantity = random.choices([1, 2, 3], weights=[7, 2, 1])[0]
                
            # Apply discounts for larger quantities or B2B
            discount_percent = 0.0
            if channel == 'b2b' and quantity >= 10:
                discount_percent = random.uniform(5.0, 15.0)
            elif quantity >= 3:
                discount_percent = random.uniform(0.0, 5.0)
                
            unit_price = float(product.get('list_price', 0))
            discount_amount = unit_price * quantity * (discount_percent / 100)
            line_total = (unit_price * quantity) - discount_amount
            
            order_line = OrderLine(
                sku=product['sku'],
                product_name=product['name'],
                quantity=quantity,
                unit_price=unit_price,
                line_total=line_total,
                discount_percent=discount_percent,
                discount_amount=discount_amount,
                category=product.get('category', 'unknown')
            )
            
            order_lines.append(order_line)
            
        return order_lines
        
    def calculate_totals(self, order_lines: List[OrderLine], channel: str) -> tuple:
        """Calculate order totals including tax and shipping"""
        subtotal = sum(line.line_total for line in order_lines)
        
        # Tax rate (Ireland VAT)
        tax_rate = 0.23
        tax_amount = subtotal * tax_rate
        
        # Shipping costs
        shipping_cost = 0.0
        if channel == 'online':
            if subtotal < 50:  # Free shipping over €50
                shipping_cost = random.choice([4.95, 6.95, 9.95])
        elif channel == 'b2b':
            if subtotal < 200:  # Free delivery over €200
                shipping_cost = random.choice([15.0, 25.0, 35.0])
                
        total_amount = subtotal + tax_amount + shipping_cost
        
        return subtotal, tax_rate, tax_amount, shipping_cost, total_amount
        
    def generate_payment_info(self, channel: str, total_amount: float) -> PaymentInfo:
        """Generate payment information"""
        payment_options = self.payment_methods[channel]
        payment_method = random.choices(list(payment_options.keys()), 
                                      weights=list(payment_options.values()))[0]
        
        payment_info = PaymentInfo(method=payment_method)
        
        # Add method-specific details
        if 'card' in payment_method:
            payment_info.last_four = str(random.randint(1000, 9999))
            payment_info.processor = random.choice(['Stripe', 'Square', 'Worldpay'])
            # Transaction fee (2.9% + €0.30 for cards)
            payment_info.transaction_fee = (total_amount * 0.029) + 0.30
            
        return payment_info
        
    def generate_shipping_info(self, channel: str, shipping_cost: float) -> ShippingInfo:
        """Generate shipping and fulfillment information"""
        fulfillment_options = self.fulfillment_methods[channel]
        fulfillment_method = random.choices(list(fulfillment_options.keys()),
                                          weights=list(fulfillment_options.values()))[0]
        
        shipping_info = ShippingInfo(
            method=fulfillment_method,
            cost=shipping_cost
        )
        
        # Add method-specific details
        if channel == 'online':
            if 'shipping' in fulfillment_method:
                shipping_info.carrier = random.choice(['An Post', 'DPD', 'UPS', 'DHL'])
                shipping_info.tracking_number = f"GC{random.randint(100000000, 999999999)}"
                
                # Estimated delivery based on method
                days_to_delivery = 2 if 'express' in fulfillment_method else 5
                delivery_date = datetime.date.today() + datetime.timedelta(days=days_to_delivery)
                shipping_info.estimated_delivery = delivery_date.isoformat()
                
        return shipping_info
        
    def generate_addresses(self, customer: Dict) -> tuple:
        """Generate billing and shipping addresses"""
        # Use customer info as base
        billing_address = {
            'name': customer['name'],
            'street': customer.get('street', '123 Main Street'),
            'city': customer.get('city', 'Dublin'),
            'zip': customer.get('zip', 'D02 XY00'),
            'country': customer.get('country_id', [78, 'Ireland'])[1],
            'phone': customer.get('phone', '+353 1 234 5678')
        }
        
        # 85% of time shipping = billing
        if random.random() < 0.85:
            shipping_address = billing_address.copy()
        else:
            # Different shipping address
            locations = list(self.location_distribution.keys())
            ship_city = random.choice(locations)
            
            shipping_address = billing_address.copy()
            shipping_address['city'] = ship_city
            shipping_address['street'] = f"{random.randint(1, 999)} {random.choice(['Main', 'High', 'Church', 'Market'])} Street"
            
        return billing_address, shipping_address
        
    def should_generate_return(self, channel: str, transaction_date: datetime.date) -> bool:
        """Determine if this order should have a return"""
        # Don't generate returns for very recent orders
        days_since = (datetime.date.today() - transaction_date).days
        if days_since < 7:
            return False
            
        return random.random() < self.return_rates[channel]
        
    def generate_return_info(self, order_lines: List[OrderLine], transaction_date: datetime.date, 
                           total_amount: float) -> ReturnInfo:
        """Generate return information"""
        # Return date 5-30 days after purchase
        days_to_return = random.randint(5, 30)
        return_date = transaction_date + datetime.timedelta(days=days_to_return)
        
        # Return reasons by frequency
        return_reasons = [
            'Size/fit issues',
            'Style not as expected', 
            'Quality concerns',
            'Wrong item received',
            'Damaged in shipping',
            'Changed mind',
            'Duplicate order'
        ]
        
        reason_weights = [40, 25, 15, 8, 6, 4, 2]
        return_reason = random.choices(return_reasons, weights=reason_weights)[0]
        
        # Usually partial returns
        if len(order_lines) > 1 and random.random() < 0.3:
            # Full return
            items_returned = [asdict(line) for line in order_lines]
            return_amount = total_amount
        else:
            # Partial return - return random subset
            num_to_return = random.randint(1, len(order_lines))
            lines_to_return = random.sample(order_lines, num_to_return)
            items_returned = [asdict(line) for line in lines_to_return]
            return_amount = sum(line.line_total for line in lines_to_return)
            
        credit_note = f"CN{return_date.strftime('%y%m%d')}{random.randint(1000, 9999)}"
        
        return ReturnInfo(
            return_date=return_date.isoformat(),
            return_reason=return_reason,
            return_amount=return_amount,
            credit_note_number=credit_note,
            items_returned=items_returned
        )
        
    def generate_single_transaction(self) -> Transaction:
        """Generate a single complete transaction"""
        # Basic order info
        order_id = self.generate_order_id()
        channel = self.select_channel()
        transaction_date, transaction_time = self.generate_transaction_datetime()
        
        # Customer
        customer = self.select_customer(channel)
        
        # Generate order basket
        order_lines = self.generate_basket(channel)
        
        # Calculate totals
        subtotal, tax_rate, tax_amount, shipping_cost, total_amount = self.calculate_totals(order_lines, channel)
        
        # Payment and shipping
        payment_info = self.generate_payment_info(channel, total_amount)
        shipping_info = self.generate_shipping_info(channel, shipping_cost)
        
        # Addresses  
        billing_address, shipping_address = self.generate_addresses(customer)
        
        # Order status
        status_options = ['confirmed', 'shipped', 'delivered']
        status_weights = [0.1, 0.2, 0.7]  # Most orders are delivered
        status = random.choices(status_options, weights=status_weights)[0]
        
        fulfillment_status = 'completed' if status == 'delivered' else 'processing'
        
        # Store location for retail
        store_location = ""
        sales_rep = ""
        if channel == 'retail':
            stores = ['Dublin Grafton St', 'Cork Patrick St', 'Galway Shop St', 'Limerick O\'Connell St']
            store_location = random.choice(stores)
            sales_reps = ['Sarah Murphy', 'John O\'Brien', 'Emma Walsh', 'David Kelly', 'Lisa Ryan']
            sales_rep = random.choice(sales_reps)
            
        # Generate return if applicable
        return_info = None
        if self.should_generate_return(channel, transaction_date):
            return_info = self.generate_return_info(order_lines, transaction_date, total_amount)
            
        # Create transaction
        transaction = Transaction(
            order_id=order_id,
            order_date=transaction_date.isoformat(),
            order_time=transaction_time,
            channel=channel,
            customer_id=customer['id'],
            customer_name=customer['name'],
            customer_email=customer['email'],
            customer_type='company' if customer.get('is_company', False) else 'individual',
            billing_address=billing_address,
            shipping_address=shipping_address,
            store_location=store_location,
            sales_rep=sales_rep,
            order_lines=order_lines,
            subtotal=subtotal,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            shipping_cost=shipping_cost,
            total_amount=total_amount,
            payment=payment_info,
            shipping=shipping_info,
            status=status,
            fulfillment_status=fulfillment_status,
            return_info=return_info
        )
        
        return transaction
        
    def generate_transactions(self, count: int = 65000) -> List[Dict]:
        """Generate specified number of transactions"""
        print(f"🏁 Generating {count:,} transactions...")
        
        transactions = []
        
        # Progress tracking
        batch_size = 1000
        
        for i in range(count):
            try:
                transaction = self.generate_single_transaction()
                
                # Convert to dictionary for JSON serialization
                transaction_dict = asdict(transaction)
                
                # Convert nested dataclass objects to dicts
                transaction_dict['order_lines'] = [asdict(line) for line in transaction.order_lines]
                transaction_dict['payment'] = asdict(transaction.payment)
                transaction_dict['shipping'] = asdict(transaction.shipping)
                
                if transaction.return_info:
                    transaction_dict['return_info'] = asdict(transaction.return_info)
                    
                transactions.append(transaction_dict)
                
                # Progress update
                if (i + 1) % batch_size == 0:
                    progress = (i + 1) / count * 100
                    print(f"  📊 Progress: {i+1:,}/{count:,} ({progress:.1f}%)")
                    
            except Exception as e:
                print(f"⚠️  Error generating transaction {i+1}: {e}")
                continue
                
        print(f"✅ Generated {len(transactions):,} transactions successfully")
        return transactions
        
    def save_transactions(self, transactions: List[Dict], filename: str = None):
        """Save transactions to JSON file"""
        if not filename:
            filename = '/workspaces/source-lovable-gympluscoffee/odoo-ingestion/generated_transactions.json'
            
        # Create summary statistics
        summary = self.generate_summary_stats(transactions)
        
        output_data = {
            'metadata': {
                'generated_date': datetime.datetime.now().isoformat(),
                'generator_version': '1.0.0',
                'total_transactions': len(transactions),
                'generator_agent': 'transaction_generator',
                'coordination_session': 'gym_coffee_retail_data'
            },
            'summary_statistics': summary,
            'transactions': transactions
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(output_data, f, indent=2, default=str)
                
            print(f"💾 Transactions saved to: {filename}")
            print(f"📁 File size: {os.path.getsize(filename) / (1024*1024):.1f} MB")
            
        except Exception as e:
            print(f"❌ Error saving transactions: {e}")
            
    def generate_summary_stats(self, transactions: List[Dict]) -> Dict:
        """Generate summary statistics for the transaction dataset"""
        if not transactions:
            return {}
            
        total_revenue = sum(t['total_amount'] for t in transactions)
        total_orders = len(transactions)
        
        # Channel breakdown
        channels = {}
        for t in transactions:
            channel = t['channel']
            if channel not in channels:
                channels[channel] = {'count': 0, 'revenue': 0.0}
            channels[channel]['count'] += 1
            channels[channel]['revenue'] += t['total_amount']
            
        # Calculate percentages
        for channel_data in channels.values():
            channel_data['percentage'] = (channel_data['count'] / total_orders) * 100
            
        # Return analysis
        returns = [t for t in transactions if t.get('return_info')]
        return_rate = (len(returns) / total_orders) * 100 if total_orders > 0 else 0
        
        # AOV by channel
        aov_by_channel = {}
        for channel, data in channels.items():
            aov_by_channel[channel] = data['revenue'] / data['count'] if data['count'] > 0 else 0
            
        summary = {
            'total_orders': total_orders,
            'total_revenue': round(total_revenue, 2),
            'average_order_value': round(total_revenue / total_orders, 2) if total_orders > 0 else 0,
            'channel_breakdown': channels,
            'aov_by_channel': aov_by_channel,
            'return_analysis': {
                'total_returns': len(returns),
                'return_rate_percent': round(return_rate, 2),
                'return_value': round(sum(r['return_info']['return_amount'] for r in returns), 2)
            }
        }
        
        return summary

def main():
    """Main execution function"""
    print("🚀 Gym+Coffee Transaction Generator v1.0")
    print("=" * 50)
    
    # Initialize generator
    generator = TransactionGenerator()
    
    # Generate transactions
    transactions = generator.generate_transactions(65000)
    
    # Save to file
    generator.save_transactions(transactions)
    
    print("\n🎉 Transaction generation completed successfully!")
    print("📊 Ready for Odoo import and analysis")

if __name__ == "__main__":
    main()