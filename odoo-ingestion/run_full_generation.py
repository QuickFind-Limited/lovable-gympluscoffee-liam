#!/usr/bin/env python3
"""
Run full 65,000 transaction generation in optimized batches
"""

import json
import datetime
import os
from generate_65k_transactions import TransactionGenerator

def run_full_generation():
    """Generate all 65,000 transactions in optimized batches"""
    print("🚀 Starting full 65,000 transaction generation")
    print("=" * 60)
    
    generator = TransactionGenerator()
    all_transactions = []
    
    # Generate in smaller batches for better memory management
    batch_size = 5000
    total_target = 65000
    batches_needed = total_target // batch_size
    
    print(f"📊 Generation plan:")
    print(f"   Target transactions: {total_target:,}")
    print(f"   Batch size: {batch_size:,}")
    print(f"   Number of batches: {batches_needed}")
    print()
    
    start_time = datetime.datetime.now()
    
    for batch_num in range(batches_needed):
        batch_start = datetime.datetime.now()
        print(f"🔄 Processing batch {batch_num + 1}/{batches_needed}...")
        
        # Generate batch
        batch_transactions = generator.generate_transactions(batch_size)
        all_transactions.extend(batch_transactions)
        
        batch_time = (datetime.datetime.now() - batch_start).total_seconds()
        total_generated = len(all_transactions)
        progress_pct = (total_generated / total_target) * 100
        
        print(f"   ✅ Batch {batch_num + 1} complete: {len(batch_transactions):,} transactions in {batch_time:.1f}s")
        print(f"   📈 Total progress: {total_generated:,}/{total_target:,} ({progress_pct:.1f}%)")
        
        # Estimate remaining time
        elapsed = (datetime.datetime.now() - start_time).total_seconds()
        if total_generated > 0:
            rate = total_generated / elapsed
            remaining = (total_target - total_generated) / rate
            eta_minutes = remaining / 60
            print(f"   ⏱️  ETA: {eta_minutes:.1f} minutes remaining")
        print()
    
    total_time = (datetime.datetime.now() - start_time).total_seconds()
    
    print(f"🎉 Generation complete!")
    print(f"   📊 Total transactions: {len(all_transactions):,}")
    print(f"   ⏱️  Total time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print(f"   🚀 Rate: {len(all_transactions)/total_time:.0f} transactions/second")
    
    # Save final dataset
    print(f"\n💾 Saving final dataset...")
    generator.transactions = all_transactions  # Set for summary generation
    generator.save_transactions(all_transactions)
    
    # Generate and display summary
    summary = generator.generate_summary_stats(all_transactions)
    print(f"\n📈 Dataset Summary:")
    print(f"   Total Revenue: €{summary['total_revenue']:,.2f}")
    print(f"   Average Order Value: €{summary['average_order_value']:.2f}")
    print(f"   Return Rate: {summary['return_analysis']['return_rate_percent']:.1f}%")
    print(f"   Channels: {len(summary['channel_breakdown'])} channels")
    
    for channel, data in summary['channel_breakdown'].items():
        print(f"     - {channel.title()}: {data['count']:,} orders ({data['percentage']:.1f}%) - €{data['revenue']:,.2f}")
    
    return all_transactions

if __name__ == "__main__":
    try:
        transactions = run_full_generation()
        print("\n✅ Full transaction generation completed successfully!")
    except KeyboardInterrupt:
        print("\n⚠️ Generation interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during generation: {e}")
        import traceback
        traceback.print_exc()