#!/usr/bin/env python3
"""
Test the transaction generator with a smaller batch
"""

import sys
import os

# Import the main generator
from generate_65k_transactions import TransactionGenerator

def test_small_batch():
    """Test generation with a small batch"""
    print("🧪 Testing transaction generation with 100 transactions...")
    
    generator = TransactionGenerator()
    
    # Generate small batch
    transactions = generator.generate_transactions(100)
    
    print(f"✅ Generated {len(transactions)} test transactions")
    
    # Show sample transaction
    if transactions:
        print("\n📋 Sample Transaction:")
        print("=" * 50)
        sample = transactions[0]
        print(f"Order ID: {sample['order_id']}")
        print(f"Channel: {sample['channel']}")
        print(f"Customer: {sample['customer_name']}")
        print(f"Date: {sample['order_date']} {sample['order_time']}")
        print(f"Total: €{sample['total_amount']:.2f}")
        print(f"Items: {len(sample['order_lines'])}")
        
        for line in sample['order_lines']:
            print(f"  - {line['quantity']}x {line['product_name']} @ €{line['unit_price']:.2f}")
            
        if sample.get('return_info'):
            print(f"Return: €{sample['return_info']['return_amount']:.2f} on {sample['return_info']['return_date']}")
    
    return True

if __name__ == "__main__":
    test_small_batch()