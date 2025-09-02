#!/usr/bin/env python3
"""
Automated realistic transaction generator for Gym+Coffee
"""

import json
import datetime
import random
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

from generate_65k_transactions import TransactionGenerator, OrderLine, PaymentInfo, ShippingInfo, ReturnInfo, Transaction

class AutoRealisticGenerator(TransactionGenerator):
    """Automated realistic transaction generator"""
    
    def __init__(self):
        super().__init__()
        
        # Realistic Irish retail parameters
        self.realistic_params = {
            'target_aovs': {
                'online': 85,   # €85 target AOV for online
                'retail': 75,   # €75 target AOV for retail  
                'b2b': 320      # €320 target AOV for B2B wholesale
            },
            'max_quantities': {
                'online': 4,    # Max 4 of any item online
                'retail': 3,    # Max 3 of any item retail
                'b2b': 24       # Max 24 of any item B2B
            },
            'basket_limits': {
                'online': 5,    # Max 5 different items
                'retail': 4,    # Max 4 different items
                'b2b': 12       # Max 12 different items
            }
        }
    
    def generate_realistic_basket(self, channel: str) -> List[OrderLine]:
        """Generate basket with realistic constraints"""
        params = self.realistic_params
        max_items = params['basket_limits'][channel]
        max_qty = params['max_quantities'][channel]
        
        # Determine basket size
        if channel == 'b2b':
            basket_size = random.choices([3, 4, 5, 6, 7, 8], weights=[3, 3, 2, 2, 1, 1])[0]
        elif channel == 'online':
            basket_size = random.choices([1, 2, 3], weights=[5, 3, 2])[0]
        else:  # retail
            basket_size = random.choices([1, 2], weights=[7, 3])[0]
        
        basket_size = min(basket_size, max_items, len(self.products))
        
        # Select products
        selected_products = random.sample(self.products, basket_size)
        order_lines = []
        
        for product in selected_products:
            # Realistic quantities
            if channel == 'b2b':
                quantity = random.choices([6, 8, 10, 12, 15, 18], weights=[3, 3, 2, 2, 1, 1])[0]
            elif channel == 'online':
                quantity = random.choices([1, 2, 3], weights=[7, 2, 1])[0]
            else:  # retail
                quantity = random.choices([1, 2], weights=[8, 2])[0]
            
            quantity = min(quantity, max_qty)
            
            # Pricing
            unit_price = float(product.get('list_price', 0))
            
            # B2B wholesale pricing (25-40% discount)
            discount_percent = 0.0
            if channel == 'b2b':
                discount_percent = random.uniform(25.0, 40.0)
                unit_price = unit_price * (1 - discount_percent / 100)
            elif quantity >= 2:
                discount_percent = random.uniform(0.0, 8.0)
            
            discount_amount = unit_price * quantity * (discount_percent / 100)
            line_total = (unit_price * quantity) - discount_amount
            
            order_line = OrderLine(
                sku=product['sku'],
                product_name=product['name'],
                quantity=quantity,
                unit_price=round(unit_price, 2),
                line_total=round(line_total, 2),
                discount_percent=round(discount_percent, 2),
                discount_amount=round(discount_amount, 2),
                category=product.get('category', 'unknown')
            )
            
            order_lines.append(order_line)
        
        return order_lines
    
    def apply_realistic_constraints(self, subtotal: float, channel: str) -> float:
        """Apply constraints to keep orders realistic"""
        target_aov = self.realistic_params['target_aovs'][channel]
        
        # If order is more than 4x target AOV, apply "volume discount"
        if subtotal > target_aov * 4:
            adjustment_factor = (target_aov * 2.5) / subtotal
            subtotal = subtotal * adjustment_factor
        
        return round(subtotal, 2)
    
    def generate_single_transaction(self) -> Transaction:
        """Generate single realistic transaction"""
        # Basic order info
        order_id = self.generate_order_id()
        channel = self.select_channel()
        transaction_date, transaction_time = self.generate_transaction_datetime()
        
        # Customer
        customer = self.select_customer(channel)
        
        # Generate realistic basket
        order_lines = self.generate_realistic_basket(channel)
        
        # Calculate totals with realistic constraints
        raw_subtotal = sum(line.line_total for line in order_lines)
        adjusted_subtotal = self.apply_realistic_constraints(raw_subtotal, channel)
        
        # If we adjusted subtotal, adjust line items proportionally
        if abs(adjusted_subtotal - raw_subtotal) > 0.01:
            adjustment_factor = adjusted_subtotal / raw_subtotal
            for line in order_lines:
                line.line_total = round(line.line_total * adjustment_factor, 2)
        
        # Calculate final totals
        subtotal = adjusted_subtotal
        tax_rate = 0.23
        tax_amount = subtotal * tax_rate
        
        # Shipping costs
        shipping_cost = 0.0
        if channel == 'online':
            if subtotal < 50:
                shipping_cost = random.choice([4.95, 6.95])
        elif channel == 'b2b':
            if subtotal < 200:
                shipping_cost = random.choice([15.0, 25.0])
        
        total_amount = subtotal + tax_amount + shipping_cost
        
        # Payment and shipping
        payment_info = self.generate_payment_info(channel, total_amount)
        shipping_info = self.generate_shipping_info(channel, shipping_cost)
        
        # Addresses
        billing_address, shipping_address = self.generate_addresses(customer)
        
        # Order status
        status_options = ['confirmed', 'shipped', 'delivered']
        status_weights = [0.1, 0.3, 0.6]
        status = random.choices(status_options, weights=status_weights)[0]
        fulfillment_status = 'completed' if status == 'delivered' else 'processing'
        
        # Store info for retail
        store_location = ""
        sales_rep = ""
        if channel == 'retail':
            stores = ['Dublin Grafton St', 'Cork Patrick St', 'Galway Shop St', 'Limerick O\'Connell St']
            store_location = random.choice(stores)
            sales_reps = ['Sarah Murphy', 'John O\'Brien', 'Emma Walsh', 'David Kelly']
            sales_rep = random.choice(sales_reps)
        
        # Returns (reduced rates)
        return_info = None
        return_rates = {'online': 0.12, 'retail': 0.04, 'b2b': 0.008}
        if random.random() < return_rates[channel]:
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
            order_lines=order_lines,
            subtotal=round(subtotal, 2),
            tax_rate=tax_rate,
            tax_amount=round(tax_amount, 2),
            shipping_cost=shipping_cost,
            total_amount=round(total_amount, 2),
            payment=payment_info,
            shipping=shipping_info,
            status=status,
            fulfillment_status=fulfillment_status,
            store_location=store_location,
            sales_rep=sales_rep,
            return_info=return_info
        )
        
        return transaction

def auto_generate():
    """Auto-generate realistic transactions"""
    print("🎯 Auto-Generating Realistic Gym+Coffee Transactions")
    print("=" * 60)
    
    generator = AutoRealisticGenerator()
    
    # Test small batch
    print("🧪 Testing with 500 transactions...")
    test_transactions = []
    
    for i in range(500):
        transaction = generator.generate_single_transaction()
        transaction_dict = asdict(transaction)
        transaction_dict['order_lines'] = [asdict(line) for line in transaction.order_lines]
        transaction_dict['payment'] = asdict(transaction.payment)
        transaction_dict['shipping'] = asdict(transaction.shipping)
        if transaction.return_info:
            transaction_dict['return_info'] = asdict(transaction.return_info)
        test_transactions.append(transaction_dict)
    
    # Analyze test batch
    channel_stats = {}
    for t in test_transactions:
        channel = t['channel']
        if channel not in channel_stats:
            channel_stats[channel] = []
        channel_stats[channel].append(t['total_amount'])
    
    print("\n📊 Test Results:")
    realistic = True
    for channel, amounts in channel_stats.items():
        if amounts:
            avg_amount = sum(amounts) / len(amounts)
            max_amount = max(amounts)
            target = generator.realistic_params['target_aovs'][channel]
            
            print(f"   {channel.title()}: AOV €{avg_amount:.2f}, Max €{max_amount:.2f} (Target: €{target})")
            
            # Check if realistic
            if avg_amount > target * 2:
                realistic = False
                print(f"     ⚠️  AOV too high!")
    
    if not realistic:
        print("\n❌ Test failed - adjusting parameters...")
        return None
    
    print("\n✅ Test passed - generating full dataset...")
    
    # Generate full 65k dataset
    all_transactions = []
    total_target = 65000
    batch_size = 5000
    
    start_time = datetime.datetime.now()
    
    for batch_num in range(13):
        batch_start = datetime.datetime.now()
        print(f"🔄 Batch {batch_num + 1}/13...")
        
        batch_transactions = []
        for i in range(batch_size):
            transaction = generator.generate_single_transaction()
            transaction_dict = asdict(transaction)
            transaction_dict['order_lines'] = [asdict(line) for line in transaction.order_lines]
            transaction_dict['payment'] = asdict(transaction.payment)
            transaction_dict['shipping'] = asdict(transaction.shipping)
            if transaction.return_info:
                transaction_dict['return_info'] = asdict(transaction.return_info)
            batch_transactions.append(transaction_dict)
        
        all_transactions.extend(batch_transactions)
        
        batch_time = (datetime.datetime.now() - batch_start).total_seconds()
        progress = len(all_transactions) / total_target * 100
        
        print(f"   ✅ {batch_size:,} transactions in {batch_time:.1f}s - Progress: {progress:.1f}%")
    
    total_time = (datetime.datetime.now() - start_time).total_seconds()
    
    print(f"\n🎉 Generation Complete!")
    print(f"   📊 Total: {len(all_transactions):,} transactions")
    print(f"   ⏱️  Time: {total_time:.1f} seconds")
    print(f"   🚀 Rate: {len(all_transactions)/total_time:.0f} transactions/second")
    
    # Save dataset
    generator.save_transactions(all_transactions, 
                               '/workspaces/source-lovable-gympluscoffee/odoo-ingestion/generated_transactions.json')
    
    # Quick analysis
    summary = generator.generate_summary_stats(all_transactions)
    print(f"\n📈 Final Dataset Summary:")
    print(f"   Total Revenue: €{summary['total_revenue']:,.2f}")
    print(f"   Overall AOV: €{summary['average_order_value']:.2f}")
    print(f"   Return Rate: {summary['return_analysis']['return_rate_percent']:.1f}%")
    
    for channel, data in summary['channel_breakdown'].items():
        aov = summary['aov_by_channel'][channel]
        print(f"   {channel.title()}: {data['count']:,} orders, AOV €{aov:.2f}")
    
    return all_transactions

if __name__ == "__main__":
    auto_generate()