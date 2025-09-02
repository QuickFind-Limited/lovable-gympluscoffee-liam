#!/usr/bin/env python3
"""
Generate realistic transactions for Gym+Coffee with corrected B2B logic
"""

from generate_65k_transactions import TransactionGenerator, OrderLine
import random

class RealisticTransactionGenerator(TransactionGenerator):
    """Enhanced generator with realistic B2B transaction logic"""
    
    def __init__(self):
        super().__init__()
        
        # Override basket size distributions with realistic values
        self.basket_sizes = {
            'online': {'min': 1, 'max': 4, 'avg': 1.8},
            'retail': {'min': 1, 'max': 3, 'avg': 1.5}, 
            'b2b': {'min': 3, 'max': 15, 'avg': 6}  # More realistic B2B sizes
        }
        
        # Override return rates to more realistic levels
        self.return_rates = {
            'online': 0.185,  # 18.5% return rate (reduced)
            'retail': 0.045,  # 4.5% return rate (reduced) 
            'b2b': 0.010     # 1.0% return rate
        }
        
        # Realistic target AOVs for Irish retail
        self.target_aovs = {
            'online': 95,    # €95 average online
            'retail': 85,    # €85 average retail
            'b2b': 450       # €450 average B2B (reasonable for wholesale)
        }
    
    def generate_basket(self, channel: str) -> List[OrderLine]:
        """Generate realistic basket with proper quantity limits"""
        basket_config = self.basket_sizes[channel]
        
        # Determine realistic basket size
        if channel == 'b2b':
            # B2B: Small to medium wholesale orders
            basket_size = random.randint(basket_config['min'], basket_config['max'])
        else:
            # Retail/Online: Favor smaller baskets
            weights = [5, 3, 2, 1]  # Heavily favor 1-2 items
            max_size = min(4, len(weights))
            basket_size = random.choices(range(1, max_size + 1), weights=weights[:max_size])[0]
        
        # Select products
        order_lines = []
        selected_products = random.choices(self.products, k=basket_size)
        
        for product in selected_products:
            # Realistic quantity based on channel
            if channel == 'b2b':
                # B2B: Wholesale quantities but reasonable for clothing
                quantity = random.choices(
                    [3, 5, 6, 10, 12, 15, 20],  
                    weights=[3, 4, 3, 2, 2, 1, 1]
                )[0]
            elif channel == 'retail':
                # Retail: Mostly single items
                quantity = random.choices([1, 2], weights=[8, 2])[0]
            else:
                # Online: Mix of single and small multiples
                quantity = random.choices([1, 2, 3], weights=[6, 3, 1])[0]
            
            # Apply realistic pricing and discounts
            unit_price = float(product.get('list_price', 0))
            
            # B2B gets wholesale pricing (20-35% off retail)
            if channel == 'b2b':
                wholesale_discount = random.uniform(0.20, 0.35)
                unit_price = unit_price * (1 - wholesale_discount)
                discount_percent = wholesale_discount * 100
            else:
                # Retail/Online small discounts only
                discount_percent = 0.0
                if quantity >= 2:
                    discount_percent = random.uniform(0.0, 5.0)
            
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
    
    def validate_transaction_realism(self, transaction_dict: dict) -> dict:
        """Validate and adjust transaction for realism"""
        channel = transaction_dict['channel']
        target_aov = self.target_aovs[channel]
        current_total = transaction_dict['total_amount']
        
        # If transaction is way over target, apply additional discount
        if current_total > target_aov * 3:  # More than 3x target
            # Apply "bulk discount" to bring it down
            adjustment_factor = target_aov * 2 / current_total
            
            # Adjust each line item
            new_subtotal = 0
            for line in transaction_dict['order_lines']:
                line['line_total'] = round(line['line_total'] * adjustment_factor, 2)
                new_subtotal += line['line_total']
            
            # Recalculate totals
            tax_amount = new_subtotal * transaction_dict['tax_rate']
            new_total = new_subtotal + tax_amount + transaction_dict['shipping_cost']
            
            transaction_dict['subtotal'] = round(new_subtotal, 2)
            transaction_dict['tax_amount'] = round(tax_amount, 2)
            transaction_dict['total_amount'] = round(new_total, 2)
        
        return transaction_dict

def run_realistic_generation():
    """Generate realistic transactions with proper validation"""
    print("🎯 Generating Realistic Gym+Coffee Transactions")
    print("=" * 50)
    
    generator = RealisticTransactionGenerator()
    
    # Generate in smaller test batch first
    print("🧪 Testing with 1,000 transactions first...")
    test_transactions = []
    
    for i in range(1000):
        transaction = generator.generate_single_transaction()
        transaction_dict = {
            'order_id': transaction.order_id,
            'order_date': transaction.order_date,
            'order_time': transaction.order_time,
            'channel': transaction.channel,
            'customer_id': transaction.customer_id,
            'customer_name': transaction.customer_name,
            'customer_email': transaction.customer_email,
            'customer_type': transaction.customer_type,
            'billing_address': transaction.billing_address,
            'shipping_address': transaction.shipping_address,
            'store_location': transaction.store_location,
            'sales_rep': transaction.sales_rep,
            'order_lines': [vars(line) for line in transaction.order_lines],
            'subtotal': transaction.subtotal,
            'tax_rate': transaction.tax_rate,
            'tax_amount': transaction.tax_amount,
            'shipping_cost': transaction.shipping_cost,
            'total_amount': transaction.total_amount,
            'payment': vars(transaction.payment),
            'shipping': vars(transaction.shipping),
            'status': transaction.status,
            'fulfillment_status': transaction.fulfillment_status,
            'return_info': vars(transaction.return_info) if transaction.return_info else None,
            'created_by': transaction.created_by,
            'source': transaction.source
        }
        
        # Validate realism
        transaction_dict = generator.validate_transaction_realism(transaction_dict)
        test_transactions.append(transaction_dict)
    
    # Analyze test batch
    channel_stats = {}
    for t in test_transactions:
        channel = t['channel']
        if channel not in channel_stats:
            channel_stats[channel] = []
        channel_stats[channel].append(t['total_amount'])
    
    print("\n📊 Test Batch Analysis:")
    for channel, amounts in channel_stats.items():
        if amounts:
            avg_amount = sum(amounts) / len(amounts)
            min_amount = min(amounts)
            max_amount = max(amounts)
            
            print(f"   {channel.title()}:")
            print(f"     Count: {len(amounts)}")
            print(f"     AOV: €{avg_amount:.2f}")
            print(f"     Range: €{min_amount:.2f} - €{max_amount:.2f}")
    
    # If test looks good, generate full dataset
    proceed = input("\nProceed with full 65,000 transaction generation? (y/n): ").lower().strip()
    if proceed != 'y':
        print("Generation cancelled.")
        return test_transactions
    
    print("\n🚀 Generating full 65,000 transaction dataset...")
    
    # Generate full dataset using the working logic
    all_transactions = []
    batch_size = 5000
    
    for batch_num in range(13):  # 13 batches of 5k = 65k
        print(f"🔄 Processing batch {batch_num + 1}/13...")
        
        batch_transactions = []
        for i in range(batch_size):
            transaction = generator.generate_single_transaction()
            transaction_dict = {
                'order_id': transaction.order_id,
                'order_date': transaction.order_date,
                'order_time': transaction.order_time,
                'channel': transaction.channel,
                'customer_id': transaction.customer_id,
                'customer_name': transaction.customer_name,
                'customer_email': transaction.customer_email,
                'customer_type': transaction.customer_type,
                'billing_address': transaction.billing_address,
                'shipping_address': transaction.shipping_address,
                'store_location': transaction.store_location,
                'sales_rep': transaction.sales_rep,
                'order_lines': [vars(line) for line in transaction.order_lines],
                'subtotal': transaction.subtotal,
                'tax_rate': transaction.tax_rate,
                'tax_amount': transaction.tax_amount,
                'shipping_cost': transaction.shipping_cost,
                'total_amount': transaction.total_amount,
                'payment': vars(transaction.payment),
                'shipping': vars(transaction.shipping),
                'status': transaction.status,
                'fulfillment_status': transaction.fulfillment_status,
                'return_info': vars(transaction.return_info) if transaction.return_info else None,
                'created_by': transaction.created_by,
                'source': transaction.source
            }
            
            transaction_dict = generator.validate_transaction_realism(transaction_dict)
            batch_transactions.append(transaction_dict)
        
        all_transactions.extend(batch_transactions)
        progress = len(all_transactions) / 65000 * 100
        print(f"   ✅ Progress: {len(all_transactions):,}/65,000 ({progress:.1f}%)")
    
    # Save final dataset
    generator.transactions = all_transactions
    generator.save_transactions(all_transactions, 
                               '/workspaces/source-lovable-gympluscoffee/odoo-ingestion/realistic_transactions.json')
    
    return all_transactions

if __name__ == "__main__":
    run_realistic_generation()