#!/usr/bin/env python3
"""Comprehensive Data Validation for Gym+Coffee Odoo Import - FIXED"""

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
            'recommendations': [],
            'overall_status': {}
        }
        
    def execute(self, model, method, domain=None, fields=None, limit=None):
        """Execute Odoo XML-RPC call with proper format"""
        if method == 'search_read':
            if domain is None:
                domain = []
            options = {}
            if fields:
                options['fields'] = fields
            if limit:
                options['limit'] = limit
            return self.models.execute_kw(self.db, self.uid, self.password, model, method, [domain], options)
        elif method == 'search_count':
            if domain is None:
                domain = []
            return self.models.execute_kw(self.db, self.uid, self.password, model, method, [domain])
        else:
            return self.models.execute_kw(self.db, self.uid, self.password, model, method, domain or [])
    
    def validate_channel_distribution(self):
        """Validate channel distribution: D2C 60%, Retail 20%, B2B 20%"""
        print("🔍 Validating channel distribution...")
        
        try:
            # Get all sales teams (channels)
            teams = self.execute('crm.team', 'search_read', fields=['name', 'id'])
            team_mapping = {team['id']: team['name'] for team in teams}
            
            # Get confirmed orders with team info
            orders = self.execute('sale.order', 'search_read', 
                                domain=[['state', 'in', ['sale', 'done']]], 
                                fields=['team_id', 'amount_total'])
            
            channel_stats = defaultdict(lambda: {'count': 0, 'revenue': 0})
            total_orders = len(orders)
            total_revenue = 0
            
            for order in orders:
                team_id = order['team_id'][0] if order['team_id'] else None
                team_name = team_mapping.get(team_id, 'Unknown')
                
                # Map to channel categories
                if any(word in team_name.lower() for word in ['online', 'e-commerce', 'website', 'shopify']):
                    channel = 'D2C E-commerce'
                elif any(word in team_name.lower() for word in ['retail', 'store', 'shop']):
                    channel = 'Retail Stores'
                elif any(word in team_name.lower() for word in ['b2b', 'wholesale', 'business']):
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
            print(f"   Processed {total_orders} orders across {len(teams)} teams")
            return results
            
        except Exception as e:
            print(f"   ❌ Channel validation failed: {e}")
            self.validation_results['channel_distribution'] = {'error': str(e)}
            return {}
    
    def validate_geographic_distribution(self):
        """Validate geographic distribution: UK 50%, US 20%, AU 20%, IE 10%"""
        print("🌍 Validating geographic distribution...")
        
        try:
            # Get customers with countries
            customers = self.execute('res.partner', 'search_read', 
                                   domain=[['customer_rank', '>', 0]], 
                                   fields=['country_id'])
            
            country_stats = Counter()
            total_customers = len(customers)
            
            for customer in customers:
                if customer['country_id']:
                    country_name = customer['country_id'][1]  # Country name
                    country_stats[country_name] += 1
            
            # Map to target countries with flexible matching
            targets = {
                'United Kingdom': 50,
                'United States': 20,
                'Australia': 20,
                'Ireland': 10
            }
            
            results = {}
            for target_country, target_pct in targets.items():
                actual_count = 0
                # Find matching countries with flexible matching
                for country_name, count in country_stats.items():
                    if (target_country.lower() in country_name.lower() or 
                        country_name.lower() in target_country.lower() or
                        (target_country == 'United Kingdom' and any(uk in country_name.lower() for uk in ['uk', 'britain', 'england'])) or
                        (target_country == 'United States' and any(us in country_name.lower() for us in ['usa', 'america'])) or
                        (target_country == 'Australia' and 'australia' in country_name.lower()) or
                        (target_country == 'Ireland' and 'ireland' in country_name.lower())):
                        actual_count += count
                
                actual_pct = (actual_count / total_customers * 100) if total_customers > 0 else 0
                results[target_country] = {
                    'target_pct': target_pct,
                    'actual_pct': actual_pct,
                    'variance': abs(actual_pct - target_pct),
                    'within_tolerance': abs(actual_pct - target_pct) <= 2,
                    'customer_count': actual_count
                }
            
            self.validation_results['geographic_distribution'] = results
            print(f"   Processed {total_customers} customers across {len(country_stats)} countries")
            return results
            
        except Exception as e:
            print(f"   ❌ Geographic validation failed: {e}")
            self.validation_results['geographic_distribution'] = {'error': str(e)}
            return {}
    
    def validate_business_metrics(self):
        """Validate AOV, return rates, repeat buyers, BOPIS"""
        print("📊 Validating business metrics...")
        
        try:
            # Get all confirmed orders
            orders = self.execute('sale.order', 'search_read', 
                                domain=[['state', 'in', ['sale', 'done']]], 
                                fields=['team_id', 'amount_total', 'partner_id', 'date_order'])
            
            # Get team mapping
            teams = self.execute('crm.team', 'search_read', fields=['name', 'id'])
            team_mapping = {team['id']: team['name'] for team in teams}
            
            # Channel-based AOV calculation
            channel_aov = defaultdict(list)
            partner_orders = defaultdict(list)
            
            for order in orders:
                team_id = order['team_id'][0] if order['team_id'] else None
                team_name = team_mapping.get(team_id, 'Unknown')
                
                # Map to channel
                if any(word in team_name.lower() for word in ['online', 'website', 'shopify']):
                    channel = 'Online'
                elif any(word in team_name.lower() for word in ['retail', 'store']):
                    channel = 'Retail'
                elif any(word in team_name.lower() for word in ['b2b', 'wholesale']):
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
            repeat_buyers = sum(1 for orders_list in partner_orders.values() if len(orders_list) > 1)
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
            
            print(f"   Processed {len(orders)} orders, {total_customers} unique customers")
            return self.validation_results['business_metrics']
            
        except Exception as e:
            print(f"   ❌ Business metrics validation failed: {e}")
            self.validation_results['business_metrics'] = {'error': str(e)}
            return {}
    
    def validate_data_quality(self):
        """Validate data quality metrics"""
        print("✅ Validating data quality...")
        
        try:
            # Check SKU sales coverage
            products = self.execute('product.template', 'search_read', 
                                  domain=[['sale_ok', '=', True]], 
                                  fields=['id', 'name'])
            
            # Check which products have sales
            order_lines = self.execute('sale.order.line', 'search_read', 
                                     fields=['product_template_id'])
            
            products_with_sales = set()
            for line in order_lines:
                if line['product_template_id']:
                    products_with_sales.add(line['product_template_id'][0])
            
            total_products = len(products)
            products_with_sales_count = len(products_with_sales)
            sku_coverage = (products_with_sales_count / total_products * 100) if total_products > 0 else 0
            
            # Check inventory for negative stock
            negative_stock = self.execute('stock.quant', 'search_count', 
                                        domain=[['quantity', '<', 0]])
            
            # Pareto analysis (top 20% products generate 60-75% revenue)
            product_revenue = defaultdict(float)
            revenue_lines = self.execute('sale.order.line', 'search_read', 
                                       fields=['product_template_id', 'price_subtotal'])
            for line in revenue_lines:
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
                    'count': negative_stock,
                    'target': 0,
                    'pass': negative_stock == 0
                },
                'pareto_principle': {
                    'top_20_pct_revenue_share': pareto_percentage,
                    'target_min': 60,
                    'target_max': 75,
                    'pass': 60 <= pareto_percentage <= 75
                }
            }
            
            self.validation_results['data_quality'] = data_quality_results
            print(f"   Analyzed {total_products} products, {len(order_lines)} order lines")
            return data_quality_results
            
        except Exception as e:
            print(f"   ❌ Data quality validation failed: {e}")
            self.validation_results['data_quality'] = {'error': str(e)}
            return {}
    
    def generate_recommendations(self):
        """Generate recommendations based on validation results"""
        print("💡 Generating recommendations...")
        
        recommendations = []
        
        # Channel distribution recommendations
        if 'channel_distribution' in self.validation_results and not isinstance(self.validation_results['channel_distribution'].get('error'), str):
            for channel, data in self.validation_results['channel_distribution'].items():
                if isinstance(data, dict) and 'within_tolerance' in data and not data['within_tolerance']:
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
        
        # Add more recommendations based on other validations...
        self.validation_results['recommendations'] = recommendations
        return recommendations
    
    def generate_overall_status(self):
        """Generate overall validation status"""
        total_tests = 0
        passed_tests = 0
        
        # Count channel distribution tests
        if 'channel_distribution' in self.validation_results and not self.validation_results['channel_distribution'].get('error'):
            for channel, data in self.validation_results['channel_distribution'].items():
                if isinstance(data, dict) and 'within_tolerance' in data:
                    total_tests += 1
                    if data['within_tolerance']:
                        passed_tests += 1
        
        # Count geographic distribution tests
        if 'geographic_distribution' in self.validation_results and not self.validation_results['geographic_distribution'].get('error'):
            for country, data in self.validation_results['geographic_distribution'].items():
                if isinstance(data, dict) and 'within_tolerance' in data:
                    total_tests += 1
                    if data['within_tolerance']:
                        passed_tests += 1
        
        # Count data quality tests
        if 'data_quality' in self.validation_results and not self.validation_results['data_quality'].get('error'):
            for metric, data in self.validation_results['data_quality'].items():
                if isinstance(data, dict) and 'pass' in data:
                    total_tests += 1
                    if data['pass']:
                        passed_tests += 1
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.validation_results['overall_status'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': success_rate,
            'overall_result': 'PASS' if success_rate >= 80 else 'FAIL'
        }
    
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
        self.generate_overall_status()
        
        # Generate summary
        self.generate_summary_report()
        
        return self.validation_results
    
    def generate_summary_report(self):
        """Generate final validation report"""
        print("\n" + "="*60)
        print("📋 VALIDATION SUMMARY REPORT")
        print("="*60)
        
        # Overall Status
        overall = self.validation_results.get('overall_status', {})
        if overall:
            print(f"\n🎯 OVERALL RESULT: {overall.get('overall_result', 'UNKNOWN')}")
            print(f"   Success Rate: {overall.get('success_rate', 0):.1f}%")
            print(f"   Tests: {overall.get('passed_tests', 0)}/{overall.get('total_tests', 0)} passed")
        
        # Channel Distribution Summary
        print("\n🎯 CHANNEL DISTRIBUTION:")
        cd = self.validation_results.get('channel_distribution', {})
        if cd and not cd.get('error'):
            for channel, data in cd.items():
                if isinstance(data, dict) and 'actual_pct' in data:
                    status = "✅ PASS" if data.get('within_tolerance') else "❌ FAIL"
                    print(f"   {channel}: {data['actual_pct']:.1f}% (Target: {data['target_pct']}%) {status}")
        elif cd.get('error'):
            print(f"   ❌ Error: {cd['error']}")
        
        # Geographic Distribution Summary  
        print("\n🌍 GEOGRAPHIC DISTRIBUTION:")
        gd = self.validation_results.get('geographic_distribution', {})
        if gd and not gd.get('error'):
            for country, data in gd.items():
                if isinstance(data, dict) and 'actual_pct' in data:
                    status = "✅ PASS" if data.get('within_tolerance') else "❌ FAIL"
                    print(f"   {country}: {data['actual_pct']:.1f}% (Target: {data['target_pct']}%) {status}")
        elif gd.get('error'):
            print(f"   ❌ Error: {gd['error']}")
        
        # Business Metrics Summary
        print("\n📊 BUSINESS METRICS:")
        bm = self.validation_results.get('business_metrics', {})
        if bm and not bm.get('error'):
            aov_data = bm.get('aov_by_channel', {})
            for channel, data in aov_data.items():
                if isinstance(data, dict) and 'actual_aov' in data:
                    status = "✅ PASS" if data.get('within_range') else "❌ FAIL"
                    print(f"   {channel} AOV: €{data['actual_aov']:.0f} (Target: €{data['target_min']}-{data['target_max']}) {status}")
            
            rb = bm.get('repeat_buyer_rate', {})
            if rb and 'actual_rate' in rb:
                status = "✅ PASS" if rb.get('within_range') else "❌ FAIL"
                print(f"   Repeat Buyer Rate: {rb['actual_rate']:.1f}% (Target: {rb['target_min']}-{rb['target_max']}%) {status}")
        elif bm.get('error'):
            print(f"   ❌ Error: {bm['error']}")
        
        # Data Quality Summary
        print("\n✅ DATA QUALITY:")
        dq = self.validation_results.get('data_quality', {})
        if dq and not dq.get('error'):
            for metric, data in dq.items():
                if isinstance(data, dict) and 'pass' in data:
                    status = "✅ PASS" if data['pass'] else "❌ FAIL"
                    metric_name = metric.replace('_', ' ').title()
                    print(f"   {metric_name}: {status}")
        elif dq.get('error'):
            print(f"   ❌ Error: {dq['error']}")
        
        # Recommendations Summary
        recommendations = self.validation_results.get('recommendations', [])
        print(f"\n💡 RECOMMENDATIONS: {len(recommendations)} items")
        critical = sum(1 for r in recommendations if r.get('priority') == 'critical')
        high = sum(1 for r in recommendations if r.get('priority') == 'high')
        medium = sum(1 for r in recommendations if r.get('priority') == 'medium')
        
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
    print("🔍 Gym+Coffee Data Validation System")
    print("🔗 Connecting to Odoo instance...")
    
    validator = DataValidator()
    
    if not validator.uid:
        print("❌ Failed to authenticate with Odoo")
        exit(1)
    
    print("✅ Connected successfully")
    results = validator.run_full_validation()
    
    # Save results to file
    output_file = "/workspaces/source-lovable-gympluscoffee/odoo-ingestion/validation_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📁 Full results saved to: {output_file}")