#!/usr/bin/env python3
"""
Sales Pattern Validator
Analyzes and validates the generated sales patterns for realistic business metrics.
"""

import json
import datetime
import statistics
from typing import Dict, List

class SalesPatternValidator:
    def __init__(self, patterns_file: str):
        """Initialize validator with patterns data."""
        with open(patterns_file, 'r') as f:
            self.patterns = json.load(f)
        
        self.daily_patterns = self.patterns['daily_patterns']
        self.summary_stats = self.patterns['summary_stats']
        
    def validate_channel_distribution(self) -> Dict:
        """Validate that channel distribution matches target ratios."""
        target = {
            'ecommerce': 0.60,
            'retail': 0.20,
            'b2b_wholesale': 0.20
        }
        
        actual = self.summary_stats['channel_revenue_distribution']
        
        validation = {
            'target_vs_actual': {},
            'within_tolerance': True,
            'tolerance': 0.05  # 5% tolerance
        }
        
        for channel, target_pct in target.items():
            actual_pct = actual[channel]
            diff = abs(target_pct - actual_pct)
            validation['target_vs_actual'][channel] = {
                'target': f"{target_pct:.1%}",
                'actual': f"{actual_pct:.1%}",
                'difference': f"{diff:.1%}",
                'within_tolerance': diff <= validation['tolerance']
            }
            
            if diff > validation['tolerance']:
                validation['within_tolerance'] = False
        
        return validation
    
    def analyze_seasonal_patterns(self) -> Dict:
        """Analyze seasonal revenue patterns by month."""
        monthly_revenue = {}
        monthly_transactions = {}
        
        for day in self.daily_patterns:
            date = datetime.datetime.strptime(day['date'], '%Y-%m-%d')
            month_key = f"{date.year}-{date.month:02d}"
            
            if month_key not in monthly_revenue:
                monthly_revenue[month_key] = 0
                monthly_transactions[month_key] = 0
            
            monthly_revenue[month_key] += day['total_daily_revenue']
            monthly_transactions[month_key] += day['total_daily_transactions']
        
        # Calculate month-over-month growth
        months = sorted(monthly_revenue.keys())
        monthly_analysis = {}
        
        for i, month in enumerate(months):
            revenue = monthly_revenue[month]
            transactions = monthly_transactions[month]
            
            analysis = {
                'revenue': round(revenue, 2),
                'transactions': transactions,
                'avg_daily_revenue': round(revenue / 30, 2),  # Approximate
                'avg_aov': round(revenue / transactions if transactions > 0 else 0, 2)
            }
            
            if i > 0:
                prev_month = months[i-1]
                prev_revenue = monthly_revenue[prev_month]
                growth = ((revenue - prev_revenue) / prev_revenue) * 100
                analysis['mom_growth'] = f"{growth:+.1f}%"
            
            monthly_analysis[month] = analysis
        
        return monthly_analysis
    
    def analyze_weekly_patterns(self) -> Dict:
        """Analyze day-of-week patterns."""
        dow_revenue = [0] * 7  # Monday=0 to Sunday=6
        dow_transactions = [0] * 7
        dow_count = [0] * 7
        
        for day in self.daily_patterns:
            dow = day['day_of_week']
            dow_revenue[dow] += day['total_daily_revenue']
            dow_transactions[dow] += day['total_daily_transactions']
            dow_count[dow] += 1
        
        # Calculate averages
        dow_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekly_analysis = {}
        
        for i, day_name in enumerate(dow_names):
            if dow_count[i] > 0:
                avg_revenue = dow_revenue[i] / dow_count[i]
                avg_transactions = dow_transactions[i] / dow_count[i]
                weekly_analysis[day_name] = {
                    'avg_daily_revenue': round(avg_revenue, 2),
                    'avg_daily_transactions': round(avg_transactions, 1),
                    'avg_aov': round(avg_revenue / avg_transactions if avg_transactions > 0 else 0, 2),
                    'days_counted': dow_count[i]
                }
        
        return weekly_analysis
    
    def identify_promotional_impact(self) -> Dict:
        """Identify high-revenue days that indicate promotional events."""
        # Calculate daily revenue statistics
        daily_revenues = [day['total_daily_revenue'] for day in self.daily_patterns]
        mean_revenue = statistics.mean(daily_revenues)
        std_revenue = statistics.stdev(daily_revenues)
        
        # Identify outliers (> 1.5 standard deviations above mean)
        threshold = mean_revenue + (1.5 * std_revenue)
        
        promotional_days = []
        for day in self.daily_patterns:
            if day['total_daily_revenue'] > threshold:
                promotional_days.append({
                    'date': day['date'],
                    'revenue': day['total_daily_revenue'],
                    'transactions': day['total_daily_transactions'],
                    'multiplier': round(day['total_daily_revenue'] / mean_revenue, 2)
                })
        
        return {
            'mean_daily_revenue': round(mean_revenue, 2),
            'std_deviation': round(std_revenue, 2),
            'threshold': round(threshold, 2),
            'promotional_days': sorted(promotional_days, key=lambda x: x['revenue'], reverse=True)
        }
    
    def analyze_hourly_patterns(self) -> Dict:
        """Analyze hourly distribution patterns across channels."""
        # Sample from first week of data for hourly analysis
        sample_days = self.daily_patterns[:7]  # First week
        
        hourly_analysis = {}
        
        for channel in ['ecommerce', 'retail', 'b2b_wholesale']:
            hourly_totals = [0] * 24
            
            for day in sample_days:
                if channel in day['channels']:
                    hourly_transactions = day['channels'][channel].get('hourly_transactions', [0]*24)
                    for hour in range(24):
                        if hour < len(hourly_transactions):
                            hourly_totals[hour] += hourly_transactions[hour]
            
            # Calculate percentages
            total_transactions = sum(hourly_totals)
            hourly_percentages = []
            
            for hour_total in hourly_totals:
                pct = (hour_total / total_transactions * 100) if total_transactions > 0 else 0
                hourly_percentages.append(round(pct, 2))
            
            # Identify peak hours
            max_pct = max(hourly_percentages)
            peak_hours = [i for i, pct in enumerate(hourly_percentages) if pct == max_pct]
            
            hourly_analysis[channel] = {
                'hourly_distribution_pct': hourly_percentages,
                'peak_hours': peak_hours,
                'peak_percentage': max_pct
            }
        
        return hourly_analysis
    
    def generate_validation_report(self) -> str:
        """Generate comprehensive validation report."""
        
        print("🔍 SALES PATTERN VALIDATION REPORT")
        print("=" * 60)
        
        # Basic stats
        total_revenue = sum(self.summary_stats['total_revenue_by_channel'].values())
        total_transactions = sum(self.summary_stats['total_transactions_by_channel'].values())
        
        print(f"📊 Overall Statistics:")
        print(f"   • Total Revenue: €{total_revenue:,.2f}")
        print(f"   • Total Transactions: {total_transactions:,}")
        print(f"   • Average Daily Revenue: €{total_revenue / len(self.daily_patterns):,.2f}")
        print(f"   • Days Generated: {len(self.daily_patterns)}")
        
        # Channel distribution validation
        print(f"\n📈 Channel Distribution Validation:")
        channel_validation = self.validate_channel_distribution()
        
        for channel, data in channel_validation['target_vs_actual'].items():
            status = "✅" if data['within_tolerance'] else "❌"
            print(f"   {status} {channel.replace('_', ' ').title()}: {data['actual']} (target: {data['target']}, diff: {data['difference']})")
        
        # Seasonal analysis
        print(f"\n🗓️  Monthly Revenue Patterns:")
        monthly_analysis = self.analyze_seasonal_patterns()
        
        for month, data in list(monthly_analysis.items())[-6:]:  # Last 6 months
            growth = f" ({data['mom_growth']})" if 'mom_growth' in data else ""
            print(f"   • {month}: €{data['revenue']:,.2f}{growth}")
        
        # Weekly patterns
        print(f"\n📅 Weekly Patterns (Average Daily):")
        weekly_analysis = self.analyze_weekly_patterns()
        
        for day, data in weekly_analysis.items():
            print(f"   • {day}: €{data['avg_daily_revenue']:,.2f} ({data['avg_daily_transactions']:.0f} orders)")
        
        # Promotional events
        print(f"\n🎯 Promotional Event Detection:")
        promo_analysis = self.identify_promotional_impact()
        
        print(f"   • Daily Revenue Mean: €{promo_analysis['mean_daily_revenue']:,.2f}")
        print(f"   • High-Performance Days (>{promo_analysis['mean_daily_revenue'] * 1.5:,.0f}): {len(promo_analysis['promotional_days'])}")
        
        if promo_analysis['promotional_days']:
            print("   • Top Promotional Days:")
            for promo_day in promo_analysis['promotional_days'][:5]:  # Top 5
                print(f"     - {promo_day['date']}: €{promo_day['revenue']:,.2f} ({promo_day['multiplier']}x avg)")
        
        # Hourly patterns
        print(f"\n⏰ Peak Hours by Channel:")
        hourly_analysis = self.analyze_hourly_patterns()
        
        for channel, data in hourly_analysis.items():
            peak_hours_str = ", ".join([f"{hour}:00" for hour in data['peak_hours']])
            print(f"   • {channel.replace('_', ' ').title()}: {peak_hours_str} ({data['peak_percentage']:.1f}%)")
        
        print(f"\n✅ VALIDATION COMPLETE")
        print("=" * 60)
        
        return "Validation report generated successfully"

def main():
    """Run validation on the generated sales patterns."""
    patterns_file = '/workspaces/source-lovable-gympluscoffee/odoo-ingestion/sales_patterns.json'
    
    try:
        validator = SalesPatternValidator(patterns_file)
        validator.generate_validation_report()
    except FileNotFoundError:
        print(f"❌ Error: Could not find patterns file at {patterns_file}")
        print("   Please run sales_patterns.py first to generate the data.")
    except Exception as e:
        print(f"❌ Validation error: {str(e)}")

if __name__ == "__main__":
    main()