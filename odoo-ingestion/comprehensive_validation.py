#!/usr/bin/env python3
"""Comprehensive Data Validation for Gym+Coffee Odoo Import"""

import xmlrpc.client
import os
from datetime import datetime, timedelta
import json
from collections import defaultdict, Counter
from dotenv import load_dotenv

load_dotenv()

class DataValidator:
    def __init__(self):
        self.url = 'https://source-gym-plus-coffee.odoo.com'
        self.db = 'source-gym-plus-coffee'
        self.username = 'admin@quickfindai.com'
        self.password = 'BJ62wX2J4yzjS$i'
        
        # Connect to Odoo
        self.common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")
        self.uid = self.common.authenticate(self.db, self.username, self.password, {})
        
        self.validation_results = {
            'timestamp': datetime.now().isoformat(),
            'channel_distribution': {},
            'geographic_distribution': {},
            'business_metrics': {},
            'data_quality': {},
            'recommendations': []
        }
        
    def execute(self, model, method, *args):
        """Execute Odoo XML-RPC call"""
        return self.models.execute_kw(self.db, self.uid, self.password, model, method, *args)
    
    def validate_channel_distribution(self):
        """Validate channel distribution: D2C 60%, Retail 20%, B2B 20%"""
        print("🔍 Validating channel distribution...")
        
        # Get all sales teams (channels)
        teams = self.execute('crm.team', 'search_read', [[]], {'fields': ['name', 'id']})
        team_mapping = {team['id']: team['name'] for team in teams}
        
        # Get confirmed orders with team info
        orders = self.execute('sale.order', 'search_read', 
                            [['state', 'in', ['sale', 'done']]], 
                            {'fields': ['team_id', 'amount_total']})
        
        channel_stats = defaultdict(lambda: {'count': 0, 'revenue': 0})
        total_orders = len(orders)
        total_revenue = 0
        
        for order in orders:
            team_id = order['team_id'][0] if order['team_id'] else None
            team_name = team_mapping.get(team_id, 'Unknown')
            
            # Map to channel categories
            if 'online' in team_name.lower() or 'e-commerce' in team_name.lower() or 'website' in team_name.lower():
                channel = 'D2C E-commerce'
            elif 'retail' in team_name.lower() or 'store' in team_name.lower():
                channel = 'Retail Stores'
            elif 'b2b' in team_name.lower() or 'wholesale' in team_name.lower():
                channel = 'B2B Wholesale'
            else:
                channel = 'Other'
            
            channel_stats[channel]['count'] += 1
            channel_stats[channel]['revenue'] += order['amount_total']
            total_revenue += order['amount_total']
        
        # Calculate percentages
        for channel in channel_stats:
            channel_stats[channel]['order_pct'] = (channel_stats[channel]['count'] / total_orders * 100) if total_orders > 0 else 0
            channel_stats[channel]['revenue_pct'] = (channel_stats[channel]['revenue'] / total_revenue * 100) if total_revenue > 0 else 0
        
        # Validate against targets
        targets = {
            'D2C E-commerce': 60,
            'Retail Stores': 20,
            'B2B Wholesale': 20
        }
        
        results = {}
        for channel, target in targets.items():
            actual = channel_stats[channel]['order_pct']
            results[channel] = {
                'target_pct': target,
                'actual_pct': actual,
                'variance': abs(actual - target),
                'within_tolerance': abs(actual - target) <= 2,
                'orders': channel_stats[channel]['count'],
                'revenue': channel_stats[channel]['revenue']
            }
        
        self.validation_results['channel_distribution'] = results
        return results
    
    def validate_geographic_distribution(self):
        """Validate geographic distribution: UK 50%, US 20%, AU 20%, IE 10%"""
        print("🌍 Validating geographic distribution...")
        
        # Get customers with countries
        customers = self.execute('res.partner', 'search_read', 
                               [[['customer_rank', '>', 0]], 
                               {'fields': ['country_id']}])
        
        country_stats = Counter()
        total_customers = len(customers)
        
        for customer in customers:
            if customer['country_id']:
                country_code = customer['country_id'][1]  # Country name
                country_stats[country_code] += 1
        
        # Map to target countries (may need to adjust based on actual country names in Odoo)
        targets = {
            'United Kingdom': 50,
            'United States': 20,
            'Australia': 20,
            'Ireland': 10
        }
        
        results = {}
        for country, target in targets.items():
            actual_count = 0
            # Try to find matching country (flexible matching)
            for country_name in country_stats:
                if country.lower() in country_name.lower() or country_name.lower() in country.lower():
                    actual_count += country_stats[country_name]
            
            actual_pct = (actual_count / total_customers * 100) if total_customers > 0 else 0
            results[country] = {
                'target_pct': target,
                'actual_pct': actual_pct,
                'variance': abs(actual_pct - target),
                'within_tolerance': abs(actual_pct - target) <= 2,
                'customer_count': actual_count
            }
        
        self.validation_results['geographic_distribution'] = results
        return results
    
    def validate_business_metrics(self):
        """Validate AOV, return rates, repeat buyers, BOPIS"""
        print("📊 Validating business metrics...")
        
        # Get all confirmed orders
        orders = self.execute('sale.order', 'search_read', 
                            [[['state', 'in', ['sale', 'done']]], 
                            {'fields': ['team_id', 'amount_total', 'partner_id', 'date_order']}])
        
        # Channel-based AOV calculation
        channel_aov = defaultdict(list)
        partner_orders = defaultdict(list)
        
        teams = self.execute('crm.team', 'search_read', [[]], {'fields': ['name', 'id']})
        team_mapping = {team['id']: team['name'] for team in teams}
        
        for order in orders:
            team_id = order['team_id'][0] if order['team_id'] else None
            team_name = team_mapping.get(team_id, 'Unknown')
            
            # Map to channel
            if 'online' in team_name.lower():
                channel = 'Online'
            elif 'retail' in team_name.lower():
                channel = 'Retail'
            elif 'b2b' in team_name.lower():
                channel = 'B2B'
            else:
                channel = 'Other'
            
            channel_aov[channel].append(order['amount_total'])
            partner_orders[order['partner_id'][0]].append(order)
        
        # Calculate AOV by channel
        aov_results = {}
        aov_targets = {
            'Online': {'min': 90, 'max': 120},
            'Retail': {'min': 70, 'max': 100},
            'B2B': {'min': 500, 'max': 2500}
        }
        
        for channel, amounts in channel_aov.items():
            if amounts:
                avg = sum(amounts) / len(amounts)
                target = aov_targets.get(channel, {'min': 0, 'max': 999999})
                aov_results[channel] = {
                    'actual_aov': avg,
                    'target_min': target['min'],
                    'target_max': target['max'],
                    'within_range': target['min'] <= avg <= target['max'],
                    'order_count': len(amounts)
                }
        
        # Repeat buyer calculation
        repeat_buyers = sum(1 for orders in partner_orders.values() if len(orders) > 1)
        total_customers = len(partner_orders)
        repeat_rate = (repeat_buyers / total_customers * 100) if total_customers > 0 else 0
        
        repeat_buyer_result = {
            'actual_rate': repeat_rate,
            'target_min': 28,
            'target_max': 32,
            'within_range': 28 <= repeat_rate <= 32,
            'repeat_buyers': repeat_buyers,
            'total_customers': total_customers
        }
        
        # Store results
        self.validation_results['business_metrics'] = {
            'aov_by_channel': aov_results,
            'repeat_buyer_rate': repeat_buyer_result,
            'return_rates': {'note': 'Return rate validation requires return/refund data'},
            'bopis_orders': {'note': 'BOPIS validation requires delivery method data'}
        }
        
        return self.validation_results['business_metrics']
    
    def validate_data_quality(self):
        """Validate data quality metrics"""
        print("✅ Validating data quality...")
        
        # Check SKU sales coverage
        products = self.execute('product.template', 'search_read', 
                              [[['sale_ok', '=', True]], 
                              {'fields': ['id', 'name']}])
        
        # Check which products have sales
        order_lines = self.execute('sale.order.line', 'search_read', 
                                 [[]], {'fields': ['product_template_id']})
        
        products_with_sales = set()
        for line in order_lines:
            if line['product_template_id']:
                products_with_sales.add(line['product_template_id'][0])
        
        total_products = len(products)
        products_with_sales_count = len(products_with_sales)
        sku_coverage = (products_with_sales_count / total_products * 100) if total_products > 0 else 0
        
        # Check inventory for negative stock
        stock_quants = self.execute('stock.quant', 'search_read', 
                                  [[['quantity', '<', 0]], 
                                  {'fields': ['product_id', 'quantity']}])
        
        negative_stock_count = len(stock_quants)
        
        # Pareto analysis (top 20% products generate 60-75% revenue)
        product_revenue = defaultdict(float)
        order_lines = self.execute('sale.order.line', 'search_read', 
                                  [[]], 
                                  {'fields': ['product_template_id', 'price_subtotal']})
        for line in order_lines:
            if line['product_template_id']:
                product_revenue[line['product_template_id'][0]] += line['price_subtotal']
        
        if product_revenue:
            sorted_products = sorted(product_revenue.items(), key=lambda x: x[1], reverse=True)
            total_revenue = sum(product_revenue.values())
            top_20_percent_count = max(1, int(len(sorted_products) * 0.2))
            top_20_revenue = sum(revenue for _, revenue in sorted_products[:top_20_percent_count])
            pareto_percentage = (top_20_revenue / total_revenue * 100) if total_revenue > 0 else 0
        else:
            pareto_percentage = 0
        
        data_quality_results = {
            'sku_sales_coverage': {
                'products_with_sales': products_with_sales_count,
                'total_products': total_products,
                'coverage_pct': sku_coverage,
                'target': 100,
                'pass': sku_coverage >= 95
            },
            'negative_stock': {
                'count': negative_stock_count,
                'target': 0,
                'pass': negative_stock_count == 0
            },
            'pareto_principle': {
                'top_20_pct_revenue_share': pareto_percentage,
                'target_min': 60,
                'target_max': 75,
                'pass': 60 <= pareto_percentage <= 75
            }
        }
        
        self.validation_results['data_quality'] = data_quality_results
        return data_quality_results
    
    def generate_recommendations(self):
        """Generate recommendations based on validation results"""
        print("💡 Generating recommendations...")
        
        recommendations = []
        
        # Channel distribution recommendations
        for channel, data in self.validation_results['channel_distribution'].items():
            if not data['within_tolerance']:
                if data['actual_pct'] < data['target_pct']:
                    recommendations.append({
                        'priority': 'high',
                        'category': 'channel_distribution',
                        'issue': f"{channel} underperforming",
                        'details': f"Actual: {data['actual_pct']:.1f}%, Target: {data['target_pct']}%",
                        'recommendation': f"Increase {channel} sales activities and marketing focus"
                    })
                else:
                    recommendations.append({
                        'priority': 'medium',
                        'category': 'channel_distribution', 
                        'issue': f"{channel} overperforming",
                        'details': f"Actual: {data['actual_pct']:.1f}%, Target: {data['target_pct']}%",
                        'recommendation': f"Consider rebalancing focus from {channel} to underperforming channels"
                    })
        
        # Geographic recommendations
        for country, data in self.validation_results['geographic_distribution'].items():
            if not data['within_tolerance']:
                recommendations.append({
                    'priority': 'medium',
                    'category': 'geographic_distribution',
                    'issue': f"{country} market variance",
                    'details': f"Actual: {data['actual_pct']:.1f}%, Target: {data['target_pct']}%",
                    'recommendation': f"Review {country} market strategy and customer acquisition"
                })
        
        # Data quality recommendations
        dq = self.validation_results['data_quality']
        if not dq['sku_sales_coverage']['pass']:
            recommendations.append({
                'priority': 'high',
                'category': 'data_quality',
                'issue': 'SKUs without sales',
                'details': f"Coverage: {dq['sku_sales_coverage']['coverage_pct']:.1f}%",
                'recommendation': 'Review product catalog for inactive SKUs and update sales data'
            })
        
        if not dq['negative_stock']['pass']:
            recommendations.append({
                'priority': 'critical',
                'category': 'data_quality',
                'issue': 'Negative stock levels detected',
                'details': f"Count: {dq['negative_stock']['count']}",
                'recommendation': 'Immediate inventory reconciliation required'
            })
        
        if not dq['pareto_principle']['pass']:
            recommendations.append({
                'priority': 'medium',
                'category': 'data_quality',
                'issue': 'Pareto principle variance',
                'details': f"Top 20% products: {dq['pareto_principle']['top_20_pct_revenue_share']:.1f}% revenue",
                'recommendation': 'Review product performance and pricing strategy'
            })
        
        self.validation_results['recommendations'] = recommendations
        return recommendations
    
    def run_full_validation(self):
        """Run complete validation suite"""
        print("🚀 Starting comprehensive data validation...")
        print("="*60)
        
        # Run all validations
        self.validate_channel_distribution()
        self.validate_geographic_distribution() 
        self.validate_business_metrics()
        self.validate_data_quality()
        self.generate_recommendations()
        
        # Generate summary
        self.generate_summary_report()
        
        return self.validation_results
    
    def generate_summary_report(self):
        """Generate final validation report"""
        print("\n" + "="*60)
        print("📋 VALIDATION SUMMARY REPORT")
        print("="*60)
        
        # Channel Distribution Summary
        print("\n🎯 CHANNEL DISTRIBUTION:")
        for channel, data in self.validation_results['channel_distribution'].items():
            status = "✅ PASS" if data['within_tolerance'] else "❌ FAIL"
            print(f"   {channel}: {data['actual_pct']:.1f}% (Target: {data['target_pct']}%) {status}")
        
        # Geographic Distribution Summary  
        print("\n🌍 GEOGRAPHIC DISTRIBUTION:")
        for country, data in self.validation_results['geographic_distribution'].items():
            status = "✅ PASS" if data['within_tolerance'] else "❌ FAIL"
            print(f"   {country}: {data['actual_pct']:.1f}% (Target: {data['target_pct']}%) {status}")
        
        # Business Metrics Summary
        print("\n📊 BUSINESS METRICS:")
        bm = self.validation_results['business_metrics']
        for channel, data in bm['aov_by_channel'].items():
            status = "✅ PASS" if data['within_range'] else "❌ FAIL"
            print(f"   {channel} AOV: €{data['actual_aov']:.0f} (Target: €{data['target_min']}-{data['target_max']}) {status}")
        
        rb = bm['repeat_buyer_rate']
        status = "✅ PASS" if rb['within_range'] else "❌ FAIL"
        print(f"   Repeat Buyer Rate: {rb['actual_rate']:.1f}% (Target: {rb['target_min']}-{rb['target_max']}%) {status}")
        
        # Data Quality Summary
        print("\n✅ DATA QUALITY:")
        dq = self.validation_results['data_quality']
        for metric, data in dq.items():
            if 'pass' in data:
                status = "✅ PASS" if data['pass'] else "❌ FAIL"
                print(f"   {metric.replace('_', ' ').title()}: {status}")
        
        # Recommendations Summary
        print(f"\n💡 RECOMMENDATIONS: {len(self.validation_results['recommendations'])} items")
        critical = sum(1 for r in self.validation_results['recommendations'] if r['priority'] == 'critical')
        high = sum(1 for r in self.validation_results['recommendations'] if r['priority'] == 'high')
        medium = sum(1 for r in self.validation_results['recommendations'] if r['priority'] == 'medium')
        
        if critical > 0:
            print(f"   🔴 Critical: {critical}")
        if high > 0:
            print(f"   🟡 High: {high}")
        if medium > 0:
            print(f"   🟢 Medium: {medium}")
        
        print("\n" + "="*60)
        print("🎯 VALIDATION COMPLETE")
        print("="*60)

if __name__ == "__main__":
    validator = DataValidator()
    results = validator.run_full_validation()
    
    # Save results to file
    output_file = "/workspaces/source-lovable-gympluscoffee/odoo-ingestion/validation_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📁 Full results saved to: {output_file}")