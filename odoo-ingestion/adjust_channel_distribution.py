#!/usr/bin/env python3
"""
Channel Distribution Adjuster
Fine-tune the sales patterns to match exact channel distribution targets.
"""

import json
import random
from typing import Dict

class ChannelDistributionAdjuster:
    def __init__(self, patterns_file: str):
        """Initialize with existing patterns."""
        with open(patterns_file, 'r') as f:
            self.patterns = json.load(f)
        
        self.target_distribution = {
            'ecommerce': 0.60,      # 60%
            'retail': 0.20,         # 20%
            'b2b_wholesale': 0.20   # 20%
        }
    
    def adjust_channel_distribution(self):
        """Adjust daily patterns to match target channel distribution."""
        
        # Calculate current totals
        current_totals = {
            'ecommerce': 0,
            'retail': 0,
            'b2b_wholesale': 0
        }
        
        for day in self.patterns['daily_patterns']:
            for channel in current_totals.keys():
                if channel in day['channels']:
                    current_totals[channel] += day['channels'][channel]['total_revenue']
        
        total_revenue = sum(current_totals.values())
        
        # Calculate target revenue per channel
        target_revenues = {
            channel: total_revenue * target_pct
            for channel, target_pct in self.target_distribution.items()
        }
        
        # Calculate adjustment factors
        adjustment_factors = {
            channel: target_revenues[channel] / current_totals[channel]
            for channel in current_totals.keys()
        }
        
        print("🔧 Adjusting Channel Distribution:")
        print("=" * 50)
        for channel, factor in adjustment_factors.items():
            current_pct = current_totals[channel] / total_revenue * 100
            target_pct = self.target_distribution[channel] * 100
            print(f"{channel.replace('_', ' ').title()}: {current_pct:.1f}% → {target_pct:.1f}% (factor: {factor:.3f})")
        
        # Apply adjustments to daily patterns
        adjusted_total_revenue = 0
        adjusted_totals = {'ecommerce': 0, 'retail': 0, 'b2b_wholesale': 0}
        
        for day in self.patterns['daily_patterns']:
            day_total = 0
            
            for channel in ['ecommerce', 'retail', 'b2b_wholesale']:
                if channel in day['channels']:
                    channel_data = day['channels'][channel]
                    
                    # Adjust revenue
                    old_revenue = channel_data['total_revenue']
                    new_revenue = old_revenue * adjustment_factors[channel]
                    
                    # Adjust AOV to maintain transaction count
                    transactions = channel_data['total_transactions']
                    if transactions > 0:
                        new_aov = new_revenue / transactions
                        channel_data['average_order_value'] = round(new_aov, 2)
                    
                    channel_data['total_revenue'] = round(new_revenue, 2)
                    day_total += new_revenue
                    adjusted_totals[channel] += new_revenue
            
            day['total_daily_revenue'] = round(day_total, 2)
            adjusted_total_revenue += day_total
        
        # Update summary statistics
        total_transactions = sum(self.patterns['summary_stats']['total_transactions_by_channel'].values())
        
        self.patterns['summary_stats']['total_revenue_by_channel'] = {
            channel: round(revenue, 2) for channel, revenue in adjusted_totals.items()
        }
        
        self.patterns['summary_stats']['average_daily_revenue'] = {
            channel: round(revenue / len(self.patterns['daily_patterns']), 2)
            for channel, revenue in adjusted_totals.items()
        }
        
        self.patterns['summary_stats']['channel_revenue_distribution'] = {
            channel: revenue / adjusted_total_revenue
            for channel, revenue in adjusted_totals.items()
        }
        
        print(f"\n✅ Adjustment Complete:")
        print(f"   Total Revenue: €{adjusted_total_revenue:,.2f}")
        print(f"   Channel Distribution:")
        for channel, revenue in adjusted_totals.items():
            pct = revenue / adjusted_total_revenue * 100
            print(f"     {channel.replace('_', ' ').title()}: {pct:.1f}% (€{revenue:,.2f})")
    
    def save_adjusted_patterns(self, output_file: str):
        """Save adjusted patterns to file."""
        with open(output_file, 'w') as f:
            json.dump(self.patterns, f, indent=2, default=str)
        
        print(f"\n💾 Adjusted patterns saved to: {output_file}")

def main():
    """Adjust channel distribution and save corrected patterns."""
    
    input_file = '/workspaces/source-lovable-gympluscoffee/odoo-ingestion/sales_patterns.json'
    output_file = '/workspaces/source-lovable-gympluscoffee/odoo-ingestion/sales_patterns_adjusted.json'
    
    try:
        adjuster = ChannelDistributionAdjuster(input_file)
        adjuster.adjust_channel_distribution()
        adjuster.save_adjusted_patterns(output_file)
        
        # Validate the adjusted patterns
        print(f"\n🔍 Validating adjusted patterns...")
        from validate_sales_patterns import SalesPatternValidator
        
        validator = SalesPatternValidator(output_file)
        channel_validation = validator.validate_channel_distribution()
        
        print("\n📊 Post-Adjustment Validation:")
        for channel, data in channel_validation['target_vs_actual'].items():
            status = "✅" if data['within_tolerance'] else "❌"
            print(f"   {status} {channel.replace('_', ' ').title()}: {data['actual']} (target: {data['target']})")
        
        # Copy adjusted version over original
        import shutil
        shutil.copy2(output_file, input_file)
        print(f"\n✅ Updated main patterns file: {input_file}")
        
    except Exception as e:
        print(f"❌ Error during adjustment: {str(e)}")

if __name__ == "__main__":
    main()