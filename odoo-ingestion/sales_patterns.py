#!/usr/bin/env python3
"""
Gym+Coffee Sales Pattern Generator
Generates realistic sales patterns for retail data with proper seasonality,
channel distribution, and promotional effects.
"""

import json
import random
import datetime
from typing import Dict, List, Tuple
import math

class SalesPatternGenerator:
    def __init__(self):
        """Initialize the sales pattern generator with base configurations."""
        
        # Channel distribution (by revenue percentage)
        self.channel_distribution = {
            'ecommerce': 0.60,      # D2C E-commerce: 60%
            'retail': 0.20,         # Retail Stores: 20% 
            'b2b_wholesale': 0.20   # B2B Wholesale: 20%
        }
        
        # Average Order Values by channel (EUR)
        self.aov_ranges = {
            'ecommerce': (90, 120),      # €90-120 per transaction
            'retail': (70, 100),         # €70-100 per transaction
            'b2b_wholesale': (500, 2500) # €500-2,500+ per transaction
        }
        
        # Product performance distribution (Pareto principle)
        self.product_performance = {
            'top_20_percent_revenue_share': 0.70,  # Top 20% SKUs = 70% revenue
            'seasonal_boost_summer': 1.25,         # +25% for summer items
            'size_distribution': {
                'S': 0.20,   # 20% Small
                'M': 0.32,   # 32% Medium (most popular)
                'L': 0.26,   # 26% Large
                'XL': 0.15,  # 15% Extra Large
                'XXL': 0.07  # 7% XXL
            },
            'color_distribution': {
                'black': 0.25,
                'grey': 0.20,
                'navy': 0.15,
                'white': 0.12,
                'other': 0.28
            }
        }
        
        # Base transaction volumes per day
        self.base_daily_volumes = {
            'ecommerce': 180,      # Higher volume, lower AOV
            'retail': 45,          # Medium volume, medium AOV
            'b2b_wholesale': 12    # Lower volume, high AOV
        }
        
        # Hourly patterns (multipliers)
        self.hourly_patterns = {
            'ecommerce': self._generate_ecommerce_hourly(),
            'retail': self._generate_retail_hourly(),
            'b2b_wholesale': self._generate_b2b_hourly()
        }
        
        # Weekly patterns (Monday=0, Sunday=6)
        self.weekly_multipliers = {
            'ecommerce': [0.9, 0.95, 1.0, 1.05, 1.1, 1.3, 1.2],  # Sat strongest
            'retail': [0.8, 0.85, 0.9, 0.95, 1.0, 1.4, 1.1],     # Strong weekend
            'b2b_wholesale': [1.2, 1.3, 1.2, 1.1, 0.9, 0.3, 0.2] # Weekday focused
        }
        
        # Promotional events with date ranges and effects
        self.promotional_events = [
            {
                'name': 'US Independence Day Sale',
                'start_date': '2024-07-04',
                'end_date': '2024-07-07',
                'revenue_boost': 1.25,
                'volume_boost': 1.30,
                'channels': ['ecommerce', 'retail']
            },
            {
                'name': 'Global Flash Sale',
                'start_date': '2024-07-18',
                'end_date': '2024-07-20',
                'revenue_boost': 1.40,
                'volume_boost': 1.60,
                'channels': ['ecommerce']
            },
            {
                'name': 'UK Bank Holiday Weekend',
                'start_date': '2024-08-24',
                'end_date': '2024-08-26',
                'revenue_boost': 1.20,
                'volume_boost': 1.25,
                'channels': ['ecommerce', 'retail']
            },
            {
                'name': 'Labor Day Promotion',
                'start_date': '2024-09-02',
                'end_date': '2024-09-02',
                'revenue_boost': 1.15,
                'volume_boost': 1.20,
                'channels': ['ecommerce', 'retail']
            }
        ]
    
    def _generate_ecommerce_hourly(self) -> List[float]:
        """Generate 24-hour pattern for e-commerce with lunch and evening peaks."""
        pattern = []
        for hour in range(24):
            if 6 <= hour <= 8:       # Morning rise
                multiplier = 0.6 + (hour - 6) * 0.2
            elif 9 <= hour <= 12:    # Building to lunch
                multiplier = 1.0 + (hour - 9) * 0.1
            elif 13 <= hour <= 14:   # Lunch peak
                multiplier = 1.4
            elif 15 <= hour <= 18:   # Afternoon steady
                multiplier = 1.1
            elif 19 <= hour <= 22:   # Evening peak
                multiplier = 1.6 - (hour - 19) * 0.1
            elif 23 <= hour <= 24 or 0 <= hour <= 5:  # Night/early morning
                multiplier = 0.3
            else:
                multiplier = 1.0
            
            pattern.append(multiplier)
        return pattern
    
    def _generate_retail_hourly(self) -> List[float]:
        """Generate 24-hour pattern for retail stores."""
        pattern = []
        for hour in range(24):
            if 0 <= hour <= 8:       # Closed
                multiplier = 0.0
            elif 9 <= hour <= 11:    # Morning opening
                multiplier = 0.8
            elif 12 <= hour <= 14:   # Lunch rush
                multiplier = 1.5
            elif 15 <= hour <= 17:   # Afternoon steady
                multiplier = 1.0
            elif 18 <= hour <= 21:   # Evening peak
                multiplier = 1.3
            elif 22 <= hour <= 23:   # Closing time
                multiplier = 0.5
            else:
                multiplier = 0.0
            
            pattern.append(multiplier)
        return pattern
    
    def _generate_b2b_hourly(self) -> List[float]:
        """Generate 24-hour pattern for B2B wholesale."""
        pattern = []
        for hour in range(24):
            if 0 <= hour <= 7:       # Outside business hours
                multiplier = 0.1
            elif 8 <= hour <= 17:    # Business hours
                multiplier = 1.2 if 9 <= hour <= 16 else 1.0
            elif 18 <= hour <= 23:   # Evening low
                multiplier = 0.3
            else:
                multiplier = 0.1
            
            pattern.append(multiplier)
        return pattern
    
    def _get_seasonal_multiplier(self, date: datetime.date) -> float:
        """Get seasonal multiplier based on date."""
        month = date.month
        
        # Summer boost for apparel items (June-August)
        if month in [6, 7, 8]:
            return 1.15
        # Spring/Fall moderate
        elif month in [4, 5, 9, 10]:
            return 1.05
        # Winter lower for fitness apparel
        elif month in [12, 1, 2]:
            return 0.90
        # Default
        else:
            return 1.0
    
    def _get_payday_multiplier(self, date: datetime.date) -> float:
        """Get payday effect multiplier (1st-5th and 15th-19th of month)."""
        day = date.day
        
        if 1 <= day <= 5 or 15 <= day <= 19:
            return 1.12  # +12% during payday periods
        else:
            return 1.0
    
    def _get_promotional_multiplier(self, date: datetime.date, channel: str) -> Tuple[float, float]:
        """Get promotional multipliers for revenue and volume."""
        date_str = date.strftime('%Y-%m-%d')
        
        for promo in self.promotional_events:
            if (promo['start_date'] <= date_str <= promo['end_date'] 
                and channel in promo['channels']):
                return promo['revenue_boost'], promo['volume_boost']
        
        return 1.0, 1.0  # No promotion
    
    def generate_daily_patterns(self, start_date: str, end_date: str) -> Dict:
        """Generate complete daily sales patterns for date range."""
        
        start = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        
        patterns = {
            'metadata': {
                'start_date': start_date,
                'end_date': end_date,
                'generation_timestamp': datetime.datetime.now().isoformat(),
                'channel_distribution': self.channel_distribution,
                'aov_ranges': self.aov_ranges
            },
            'daily_patterns': [],
            'summary_stats': {}
        }
        
        current_date = start
        total_revenue = {'ecommerce': 0, 'retail': 0, 'b2b_wholesale': 0}
        total_transactions = {'ecommerce': 0, 'retail': 0, 'b2b_wholesale': 0}
        
        while current_date <= end:
            day_pattern = self._generate_day_pattern(current_date)
            patterns['daily_patterns'].append(day_pattern)
            
            # Accumulate totals
            for channel in ['ecommerce', 'retail', 'b2b_wholesale']:
                total_revenue[channel] += day_pattern['channels'][channel]['total_revenue']
                total_transactions[channel] += day_pattern['channels'][channel]['total_transactions']
            
            current_date += datetime.timedelta(days=1)
        
        # Generate summary statistics
        patterns['summary_stats'] = {
            'total_revenue_by_channel': total_revenue,
            'total_transactions_by_channel': total_transactions,
            'average_daily_revenue': {
                channel: total_revenue[channel] / len(patterns['daily_patterns'])
                for channel in total_revenue
            },
            'channel_revenue_distribution': {
                channel: total_revenue[channel] / sum(total_revenue.values())
                for channel in total_revenue
            }
        }
        
        return patterns
    
    def _generate_day_pattern(self, date: datetime.date) -> Dict:
        """Generate sales pattern for a single day."""
        
        day_pattern = {
            'date': date.strftime('%Y-%m-%d'),
            'day_of_week': date.weekday(),  # Monday=0, Sunday=6
            'channels': {},
            'total_daily_revenue': 0,
            'total_daily_transactions': 0
        }
        
        # Get global multipliers
        seasonal_mult = self._get_seasonal_multiplier(date)
        payday_mult = self._get_payday_multiplier(date)
        
        for channel in ['ecommerce', 'retail', 'b2b_wholesale']:
            # Base volume with random variance (±25%)
            base_volume = self.base_daily_volumes[channel]
            variance = random.uniform(0.75, 1.25)
            
            # Apply weekly multiplier
            weekly_mult = self.weekly_multipliers[channel][date.weekday()]
            
            # Apply promotional multipliers
            promo_revenue_mult, promo_volume_mult = self._get_promotional_multiplier(date, channel)
            
            # Calculate final volume
            final_volume = int(base_volume * variance * weekly_mult * seasonal_mult * payday_mult * promo_volume_mult)
            
            # Generate hourly distribution
            hourly_transactions = []
            total_transactions = 0
            
            for hour in range(24):
                hourly_mult = self.hourly_patterns[channel][hour]
                hour_transactions = int(final_volume * hourly_mult / sum(self.hourly_patterns[channel]))
                hourly_transactions.append(hour_transactions)
                total_transactions += hour_transactions
            
            # Generate revenue
            aov_min, aov_max = self.aov_ranges[channel]
            base_aov = random.uniform(aov_min, aov_max)
            
            # Apply promotional AOV boost
            final_aov = base_aov * promo_revenue_mult
            
            total_revenue = total_transactions * final_aov
            
            day_pattern['channels'][channel] = {
                'total_transactions': total_transactions,
                'total_revenue': round(total_revenue, 2),
                'average_order_value': round(final_aov, 2),
                'hourly_transactions': hourly_transactions,
                'multipliers_applied': {
                    'seasonal': seasonal_mult,
                    'weekly': weekly_mult,
                    'payday': payday_mult,
                    'promotional_revenue': promo_revenue_mult,
                    'promotional_volume': promo_volume_mult
                }
            }
            
            day_pattern['total_daily_revenue'] += total_revenue
            day_pattern['total_daily_transactions'] += total_transactions
        
        day_pattern['total_daily_revenue'] = round(day_pattern['total_daily_revenue'], 2)
        
        return day_pattern
    
    def save_patterns(self, patterns: Dict, filename: str):
        """Save patterns to JSON file."""
        with open(filename, 'w') as f:
            json.dump(patterns, f, indent=2, default=str)
        
        print(f"Sales patterns saved to {filename}")
        print(f"Generated {len(patterns['daily_patterns'])} days of data")
        print(f"Total revenue: €{sum(patterns['summary_stats']['total_revenue_by_channel'].values()):,.2f}")

def main():
    """Generate sales patterns for the specified date range."""
    
    generator = SalesPatternGenerator()
    
    # Generate for current focus period (June 2024 - May 2025)
    # This covers both historical data (Dec 2023 - May 2024) and future projections
    patterns = generator.generate_daily_patterns('2023-12-01', '2024-11-30')
    
    # Save to the specified location
    output_file = '/workspaces/source-lovable-gympluscoffee/odoo-ingestion/sales_patterns.json'
    generator.save_patterns(patterns, output_file)
    
    # Print key insights
    stats = patterns['summary_stats']
    print("\n📊 Sales Pattern Summary:")
    print("=" * 50)
    print(f"📅 Date Range: {patterns['metadata']['start_date']} to {patterns['metadata']['end_date']}")
    print(f"💰 Total Revenue: €{sum(stats['total_revenue_by_channel'].values()):,.2f}")
    print(f"🛒 Total Transactions: {sum(stats['total_transactions_by_channel'].values()):,}")
    
    print("\n📈 Channel Performance:")
    for channel, revenue in stats['total_revenue_by_channel'].items():
        transactions = stats['total_transactions_by_channel'][channel]
        avg_aov = revenue / transactions if transactions > 0 else 0
        percentage = stats['channel_revenue_distribution'][channel] * 100
        print(f"  {channel.replace('_', ' ').title()}: €{revenue:,.2f} ({percentage:.1f}%) | {transactions:,} orders | €{avg_aov:.2f} AOV")
    
    print(f"\n✅ Patterns saved to: {output_file}")

if __name__ == "__main__":
    main()