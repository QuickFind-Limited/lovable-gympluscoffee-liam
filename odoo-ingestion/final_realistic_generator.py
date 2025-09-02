#!/usr/bin/env python3
"""
Final realistic transaction generator with strict Irish retail constraints
"""

import json
import datetime
import random
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import statistics

# Import base classes
from generate_65k_transactions import TransactionGenerator, OrderLine, PaymentInfo, ShippingInfo, ReturnInfo, Transaction

class FinalRealisticGenerator(TransactionGenerator):
    """Final generator with very strict realistic constraints for Irish retail"""
    
    def __init__(self):
        super().__init__()
        
        # Very strict Irish retail constraints
        self.constraints = {
            'strict_aovs': {
                'online': {'target': 78, 'max': 250},     # Irish online average with max
                'retail': {'target': 65, 'max': 200},     # Irish retail average with max
                'b2b': {'target': 285, 'max': 800}        # B2B wholesale with max
            },
            'quantity_limits': {
                'online': [1, 1, 1, 2, 2, 3],           # Heavily favor single items
                'retail': [1, 1, 1, 1, 2, 2],           # Almost all single items
                'b2b': [3, 4, 5, 6, 8, 10, 12]          # Small wholesale quantities
            },
            'basket_patterns': {
                'online': [1, 1, 1, 1, 2, 2, 3],        # Mostly single item baskets
                'retail': [1, 1, 1, 1, 1, 2],           # Almost all single item
                'b2b': [2, 3, 3, 4, 4, 5, 6]            # Small variety B2B orders
            }
        }
        
        # Filter products to only realistic ones for clothing brand
        self.realistic_products = []
        for product in self.products:
            price = float(product.get('list_price', 0))
            if 15 <= price <= 120:  # Realistic clothing price range
                self.realistic_products.append(product)
        
        if not self.realistic_products:
            self.realistic_products = self.products  # Fallback
        
        print(f"✅ Using {len(self.realistic_products)} realistic products")
    
    def generate_constrained_basket(self, channel: str) -> List[OrderLine]:
        """Generate heavily constrained realistic basket"""
        constraints = self.constraints
        
        # Very constrained basket size
        basket_size = random.choice(constraints['basket_patterns'][channel])
        basket_size = min(basket_size, len(self.realistic_products))
        
        # Select products
        selected_products = random.sample(self.realistic_products, basket_size)
        order_lines = []
        
        for product in selected_products:
            # Very constrained quantities
            quantity = random.choice(constraints['quantity_limits'][channel])
            
            # Strict pricing
            base_price = float(product.get('list_price', 0))
            unit_price = base_price
            discount_percent = 0.0
            
            # B2B gets modest wholesale discount
            if channel == 'b2b':
                discount_percent = random.uniform(15.0, 28.0)  # Modest wholesale discount
                unit_price = base_price * (1 - discount_percent / 100)
            elif quantity >= 2 and random.random() < 0.3:
                discount_percent = random.uniform(2.0, 8.0)    # Small quantity discount
            
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
                category=product.get('category', 'clothing')
            )
            
            order_lines.append(order_line)
        
        return order_lines
    
    def enforce_aov_limits(self, order_lines: List[OrderLine], channel: str) -> List[OrderLine]:
        """Strictly enforce AOV limits"""
        subtotal = sum(line.line_total for line in order_lines)
        max_allowed = self.constraints['strict_aovs'][channel]['max']
        
        if subtotal > max_allowed:
            # Scale down proportionally
            scale_factor = max_allowed * 0.9 / subtotal  # 10% under max for safety
            
            for line in order_lines:
                line.line_total = round(line.line_total * scale_factor, 2)
                line.unit_price = round(line.unit_price * scale_factor, 2)
                if line.discount_amount > 0:
                    line.discount_amount = round(line.discount_amount * scale_factor, 2)
        
        return order_lines
    
    def generate_single_transaction(self) -> Transaction:
        """Generate single transaction with strict constraints"""
        # Basic order info
        order_id = self.generate_order_id()
        channel = self.select_channel()
        transaction_date, transaction_time = self.generate_transaction_datetime()
        
        # Customer
        customer = self.select_customer(channel)
        
        # Generate constrained basket
        order_lines = self.generate_constrained_basket(channel)
        order_lines = self.enforce_aov_limits(order_lines, channel)
        
        # Calculate totals
        subtotal = sum(line.line_total for line in order_lines)
        tax_rate = 0.23  # Irish VAT
        tax_amount = subtotal * tax_rate
        
        # Modest shipping costs
        shipping_cost = 0.0
        if channel == 'online':
            if subtotal < 50:
                shipping_cost = 4.95
        elif channel == 'b2b':
            if subtotal < 150:
                shipping_cost = 12.50
        
        total_amount = subtotal + tax_amount + shipping_cost
        
        # Payment and shipping
        payment_info = self.generate_payment_info(channel, total_amount)
        shipping_info = self.generate_shipping_info(channel, shipping_cost)
        
        # Addresses
        billing_address, shipping_address = self.generate_addresses(customer)
        
        # Order status
        status = random.choices(['confirmed', 'shipped', 'delivered'], weights=[0.15, 0.25, 0.60])[0]
        fulfillment_status = 'completed' if status == 'delivered' else 'processing'
        
        # Store info for retail
        store_location = ""
        sales_rep = ""
        if channel == 'retail':
            stores = ['Dublin Grafton St', 'Cork Patrick St', 'Galway Shop St']
            store_location = random.choice(stores)
            sales_reps = ['Sarah M.', 'John O.', 'Emma W.', 'David K.']
            sales_rep = random.choice(sales_reps)
        
        # Conservative return rates
        return_info = None
        return_rates = {'online': 0.08, 'retail': 0.03, 'b2b': 0.005}  # Very conservative
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

def run_final_generation():
    """Run final realistic generation with validation"""
    print("🎯 Final Realistic Gym+Coffee Transaction Generation")
    print("=" * 60)
    
    generator = FinalRealisticGenerator()
    
    # Test with small batch and validate
    print("🧪 Testing with 200 transactions...")
    test_transactions = []
    
    for i in range(200):
        transaction = generator.generate_single_transaction()
        transaction_dict = asdict(transaction)
        transaction_dict['order_lines'] = [asdict(line) for line in transaction.order_lines]
        transaction_dict['payment'] = asdict(transaction.payment)
        transaction_dict['shipping'] = asdict(transaction.shipping)
        if transaction.return_info:
            transaction_dict['return_info'] = asdict(transaction.return_info)
        test_transactions.append(transaction_dict)
    
    # Validate test results
    channel_stats = {}
    for t in test_transactions:
        channel = t['channel']
        if channel not in channel_stats:
            channel_stats[channel] = []
        channel_stats[channel].append(t['total_amount'])
    
    print("\n📊 Validation Results:")
    validation_passed = True
    
    for channel, amounts in channel_stats.items():
        if amounts:
            avg = statistics.mean(amounts)
            median = statistics.median(amounts)
            max_val = max(amounts)
            target = generator.constraints['strict_aovs'][channel]['target']
            max_allowed = generator.constraints['strict_aovs'][channel]['max']
            
            print(f"   {channel.title()}: n={len(amounts)}, avg=€{avg:.2f}, median=€{median:.2f}, max=€{max_val:.2f}")
            print(f"     Target: €{target}, Max allowed: €{max_allowed}")
            
            if max_val > max_allowed:
                print(f"     ❌ FAILED: Exceeded maximum")
                validation_passed = False
            elif avg > target * 1.5:
                print(f"     ⚠️  WARNING: Average high")
            else:
                print(f"     ✅ PASSED")
    
    if not validation_passed:
        print("\n❌ Validation failed. Please review constraints.")
        return None
    
    print(f"\n✅ Validation passed! Generating full 65,000 transactions...")
    
    # Generate full dataset
    all_transactions = []
    total_target = 65000
    batch_size = 5000
    
    start_time = datetime.datetime.now()
    
    for batch_num in range(13):
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
        progress = len(all_transactions) / total_target * 100
        print(f"   ✅ Progress: {len(all_transactions):,}/{total_target:,} ({progress:.1f}%)")
    
    total_time = (datetime.datetime.now() - start_time).total_seconds()
    
    print(f"\n🎉 Generation Complete!")
    print(f"   📊 Total: {len(all_transactions):,} transactions")
    print(f"   ⏱️  Time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    
    # Save the final realistic dataset
    print(f"\n💾 Saving final dataset...")
    generator.save_transactions(all_transactions)
    
    # Generate final analysis
    summary = generator.generate_summary_stats(all_transactions)
    print(f"\n📈 Final Dataset Analysis:")
    print(f"   Total Revenue: €{summary['total_revenue']:,.2f}")
    print(f"   Overall AOV: €{summary['average_order_value']:.2f}")
    print(f"   Return Rate: {summary['return_analysis']['return_rate_percent']:.1f}%")
    
    print(f"\n📊 Channel Performance:")
    for channel, data in summary['channel_breakdown'].items():
        aov = summary['aov_by_channel'][channel]
        target = generator.constraints['strict_aovs'][channel]['target']
        variance = ((aov - target) / target) * 100
        
        print(f"   {channel.title()}:")
        print(f"     Orders: {data['count']:,} ({data['percentage']:.1f}%)")
        print(f"     Revenue: €{data['revenue']:,.2f}")
        print(f"     AOV: €{aov:.2f} (target: €{target}, variance: {variance:+.1f}%)")
    
    return all_transactions

if __name__ == "__main__":
    run_final_generation()