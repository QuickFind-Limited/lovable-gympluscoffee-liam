#!/usr/bin/env python3
"""
Master Validation and Fix Script for Gym+Coffee Odoo Data
Ensures all imported data meets requirements and fixes issues automatically
"""

import xmlrpc.client
import json
import random
from datetime import datetime, timedelta
from collections import defaultdict
import logging
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/master_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OdooMasterValidator:
    def __init__(self):
        """Initialize Odoo connection and validation parameters"""
        self.url = 'https://source-gym-plus-coffee.odoo.com/'
        self.db = 'source-gym-plus-coffee'
        self.username = 'admin@quickfindai.com'
        self.password = 'BJ62wX2J4yzjS$i'
        
        # Target requirements
        self.requirements = {
            'channel_distribution': {'online': 0.60, 'retail': 0.20, 'b2b': 0.20, 'tolerance': 0.03},
            'geographic_distribution': {'UK': 0.50, 'US': 0.20, 'AU': 0.20, 'IE': 0.10, 'tolerance': 0.02},
            'return_rates': {
                'online': {'min': 0.20, 'max': 0.27},
                'retail': {'min': 0.04, 'max': 0.09},
                'b2b': {'min': 0.01, 'max': 0.02}
            },
            'customer_segments': {
                'VIP': 0.05, 'Loyal': 0.15, 'Regular': 0.30, 'One-time': 0.50
            },
            'aov_ranges': {
                'online': {'min': 90, 'max': 120},
                'retail': {'min': 70, 'max': 100},
                'b2b': {'min': 500, 'max': 2500}
            },
            'seasonal_distribution': {
                'june': {'min': 0.20, 'max': 0.23},
                'july': {'min': 0.24, 'max': 0.27},
                'august': {'min': 0.27, 'max': 0.31},
                'september': {'min': 0.22, 'max': 0.26}
            }
        }
        
        self.validation_results = {}
        self.fixes_applied = []
        self.issues_found = []
        
        # Connect to Odoo
        self.connect()
    
    def connect(self):
        """Establish connection to Odoo"""
        try:
            self.common = xmlrpc.client.ServerProxy(f'{self.url}xmlrpc/2/common')
            self.uid = self.common.authenticate(self.db, self.username, self.password, {})
            self.models = xmlrpc.client.ServerProxy(f'{self.url}xmlrpc/2/object')
            logger.info("✅ Successfully connected to Odoo")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to Odoo: {e}")
            return False
    
    def execute_kw(self, model, method, args, kwargs=None):
        """Execute Odoo method with error handling"""
        try:
            return self.models.execute_kw(
                self.db, self.uid, self.password,
                model, method, args, kwargs or {}
            )
        except Exception as e:
            logger.error(f"Error executing {model}.{method}: {e}")
            return None
    
    def validate_channel_distribution(self):
        """Validate and fix channel distribution"""
        logger.info("\n📊 Validating Channel Distribution...")
        
        # Get all orders
        orders = self.execute_kw('sale.order', 'search_read', 
            [[('state', 'in', ['sale', 'done'])]], 
            {'fields': ['id', 'amount_total', 'team_id', 'partner_id']})
        
        if not orders:
            logger.warning("No orders found")
            return False
        
        # Calculate current distribution
        channel_revenue = defaultdict(float)
        total_revenue = 0
        unassigned_orders = []
        
        for order in orders:
            total_revenue += order['amount_total']
            if order.get('team_id'):
                team = self.execute_kw('crm.team', 'read', 
                    [[order['team_id'][0]]], {'fields': ['name']})
                if team:
                    channel_name = team[0]['name'].lower()
                    if 'online' in channel_name or 'web' in channel_name:
                        channel_revenue['online'] += order['amount_total']
                    elif 'retail' in channel_name or 'store' in channel_name:
                        channel_revenue['retail'] += order['amount_total']
                    elif 'b2b' in channel_name or 'wholesale' in channel_name:
                        channel_revenue['b2b'] += order['amount_total']
                    else:
                        unassigned_orders.append(order)
            else:
                unassigned_orders.append(order)
        
        # Fix unassigned orders
        if unassigned_orders:
            logger.info(f"Found {len(unassigned_orders)} orders without channel assignment")
            self.fix_channel_attribution(unassigned_orders, channel_revenue, total_revenue)
        
        # Calculate percentages
        channel_pct = {}
        for channel in ['online', 'retail', 'b2b']:
            channel_pct[channel] = channel_revenue[channel] / total_revenue if total_revenue > 0 else 0
        
        # Validate against requirements
        valid = True
        for channel, target in [('online', 0.60), ('retail', 0.20), ('b2b', 0.20)]:
            actual = channel_pct.get(channel, 0)
            diff = abs(actual - target)
            if diff > self.requirements['channel_distribution']['tolerance']:
                valid = False
                logger.warning(f"❌ {channel.upper()}: {actual:.1%} (target: {target:.0%}, diff: {diff:.1%})")
            else:
                logger.info(f"✅ {channel.upper()}: {actual:.1%} (target: {target:.0%})")
        
        self.validation_results['channel_distribution'] = {
            'valid': valid,
            'actual': channel_pct,
            'target': {'online': 0.60, 'retail': 0.20, 'b2b': 0.20}
        }
        
        return valid
    
    def fix_channel_attribution(self, unassigned_orders, channel_revenue, total_revenue):
        """Fix orders without channel attribution"""
        logger.info("🔧 Fixing channel attribution...")
        
        # Create or get sales teams
        teams = {}
        for channel in ['Online', 'Retail', 'B2B']:
            team = self.execute_kw('crm.team', 'search', 
                [[('name', 'ilike', channel)]], {'limit': 1})
            if not team:
                # Create team if it doesn't exist
                team_id = self.execute_kw('crm.team', 'create', [{
                    'name': f'{channel} Sales',
                    'use_quotations': True,
                    'use_invoices': True
                }])
                teams[channel.lower()] = team_id
                logger.info(f"Created sales team: {channel} Sales")
            else:
                teams[channel.lower()] = team[0]
        
        # Assign orders based on AOV patterns
        fixed_count = 0
        for order in unassigned_orders:
            aov = order['amount_total']
            
            # Determine channel based on AOV
            if aov >= 500:  # High value = B2B
                channel = 'b2b'
            elif aov >= 90 and aov <= 120:  # Mid range = Online
                channel = 'online'
            else:  # Lower range = Retail
                channel = 'retail'
            
            # Check if assignment would maintain distribution
            target = self.requirements['channel_distribution'][channel]
            current = channel_revenue[channel] / total_revenue if total_revenue > 0 else 0
            
            if current < target + self.requirements['channel_distribution']['tolerance']:
                # Update order
                self.execute_kw('sale.order', 'write', 
                    [[order['id']], {'team_id': teams[channel]}])
                channel_revenue[channel] += aov
                fixed_count += 1
        
        logger.info(f"✅ Fixed channel attribution for {fixed_count} orders")
        self.fixes_applied.append(f"Fixed channel attribution for {fixed_count} orders")
    
    def validate_geographic_distribution(self):
        """Validate and fix geographic distribution"""
        logger.info("\n🌍 Validating Geographic Distribution...")
        
        # Get all customers with orders
        customers = self.execute_kw('res.partner', 'search_read',
            [[('sale_order_count', '>', 0)]], 
            {'fields': ['id', 'country_id', 'city', 'sale_order_count', 'total_invoiced']})
        
        if not customers:
            logger.warning("No customers with orders found")
            return False
        
        # Calculate distribution
        geo_revenue = defaultdict(float)
        total_revenue = 0
        unassigned_customers = []
        
        country_mapping = {
            'United Kingdom': 'UK',
            'United States': 'US',
            'Australia': 'AU',
            'Ireland': 'IE'
        }
        
        for customer in customers:
            revenue = customer.get('total_invoiced', 0)
            total_revenue += revenue
            
            if customer.get('country_id'):
                country = self.execute_kw('res.country', 'read',
                    [[customer['country_id'][0]]], {'fields': ['name']})
                if country:
                    country_name = country[0]['name']
                    country_code = country_mapping.get(country_name, 'Other')
                    geo_revenue[country_code] += revenue
            else:
                unassigned_customers.append(customer)
        
        # Fix unassigned customers
        if unassigned_customers:
            logger.info(f"Found {len(unassigned_customers)} customers without country")
            self.fix_geographic_assignment(unassigned_customers, geo_revenue, total_revenue)
        
        # Calculate percentages
        geo_pct = {}
        for country in ['UK', 'US', 'AU', 'IE']:
            geo_pct[country] = geo_revenue[country] / total_revenue if total_revenue > 0 else 0
        
        # Validate
        valid = True
        for country, target in [('UK', 0.50), ('US', 0.20), ('AU', 0.20), ('IE', 0.10)]:
            actual = geo_pct.get(country, 0)
            diff = abs(actual - target)
            if diff > self.requirements['geographic_distribution']['tolerance']:
                valid = False
                logger.warning(f"❌ {country}: {actual:.1%} (target: {target:.0%}, diff: {diff:.1%})")
            else:
                logger.info(f"✅ {country}: {actual:.1%} (target: {target:.0%})")
        
        self.validation_results['geographic_distribution'] = {
            'valid': valid,
            'actual': geo_pct,
            'target': {'UK': 0.50, 'US': 0.20, 'AU': 0.20, 'IE': 0.10}
        }
        
        return valid
    
    def fix_geographic_assignment(self, unassigned_customers, geo_revenue, total_revenue):
        """Fix customers without geographic data"""
        logger.info("🔧 Fixing geographic assignment...")
        
        # Get country IDs
        countries = {}
        for name, code in [('United Kingdom', 'UK'), ('United States', 'US'), 
                           ('Australia', 'AU'), ('Ireland', 'IE')]:
            country = self.execute_kw('res.country', 'search', 
                [[('name', '=', name)]], {'limit': 1})
            if country:
                countries[code] = country[0]
        
        # Cities by country
        cities = {
            'UK': ['London', 'Manchester', 'Birmingham', 'Liverpool', 'Bristol'],
            'US': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'],
            'AU': ['Sydney', 'Melbourne', 'Brisbane', 'Perth', 'Adelaide'],
            'IE': ['Dublin', 'Cork', 'Limerick', 'Galway', 'Waterford']
        }
        
        fixed_count = 0
        for customer in unassigned_customers:
            # Determine country based on distribution needs
            for country_code, target in [('UK', 0.50), ('US', 0.20), ('AU', 0.20), ('IE', 0.10)]:
                current = geo_revenue[country_code] / total_revenue if total_revenue > 0 else 0
                
                if current < target:
                    # Assign to this country
                    city = random.choice(cities[country_code])
                    self.execute_kw('res.partner', 'write',
                        [[customer['id']], {
                            'country_id': countries[country_code],
                            'city': city
                        }])
                    geo_revenue[country_code] += customer.get('total_invoiced', 0)
                    fixed_count += 1
                    break
        
        logger.info(f"✅ Fixed geographic data for {fixed_count} customers")
        self.fixes_applied.append(f"Fixed geographic data for {fixed_count} customers")
    
    def validate_return_rates(self):
        """Validate return rates by channel"""
        logger.info("\n📦 Validating Return Rates...")
        
        # Get returns (negative quantity orders or credit notes)
        returns = self.execute_kw('sale.order', 'search_read',
            [[('state', 'in', ['sale', 'done'])]], 
            {'fields': ['id', 'amount_total', 'team_id', 'name']})
        
        # Count returns vs regular orders by channel
        channel_orders = defaultdict(int)
        channel_returns = defaultdict(int)
        
        for order in returns:
            is_return = 'RET' in order.get('name', '') or order.get('amount_total', 0) < 0
            
            channel = 'online'  # Default
            if order.get('team_id'):
                team = self.execute_kw('crm.team', 'read',
                    [[order['team_id'][0]]], {'fields': ['name']})
                if team:
                    team_name = team[0]['name'].lower()
                    if 'retail' in team_name or 'store' in team_name:
                        channel = 'retail'
                    elif 'b2b' in team_name or 'wholesale' in team_name:
                        channel = 'b2b'
            
            if is_return:
                channel_returns[channel] += 1
            channel_orders[channel] += 1
        
        # Calculate return rates
        return_rates = {}
        valid = True
        
        for channel in ['online', 'retail', 'b2b']:
            if channel_orders[channel] > 0:
                rate = channel_returns[channel] / channel_orders[channel]
                return_rates[channel] = rate
                
                min_rate = self.requirements['return_rates'][channel]['min']
                max_rate = self.requirements['return_rates'][channel]['max']
                
                if rate < min_rate or rate > max_rate:
                    logger.warning(f"❌ {channel.upper()} return rate: {rate:.1%} (target: {min_rate:.0%}-{max_rate:.0%})")
                    valid = False
                else:
                    logger.info(f"✅ {channel.upper()} return rate: {rate:.1%} (target: {min_rate:.0%}-{max_rate:.0%})")
        
        self.validation_results['return_rates'] = {
            'valid': valid,
            'actual': return_rates,
            'target': self.requirements['return_rates']
        }
        
        # Fix if needed
        if not valid:
            self.fix_return_rates(channel_orders, channel_returns)
        
        return valid
    
    def fix_return_rates(self, channel_orders, channel_returns):
        """Create returns to meet target rates"""
        logger.info("🔧 Creating returns to meet target rates...")
        
        created_returns = 0
        
        for channel in ['online', 'retail', 'b2b']:
            if channel_orders[channel] == 0:
                continue
                
            current_rate = channel_returns[channel] / channel_orders[channel]
            target_rate = (self.requirements['return_rates'][channel]['min'] + 
                          self.requirements['return_rates'][channel]['max']) / 2
            
            if current_rate < target_rate:
                # Need to create more returns
                needed_returns = int(target_rate * channel_orders[channel]) - channel_returns[channel]
                
                # Get recent orders from this channel
                team_name = f'{channel} Sales'
                team = self.execute_kw('crm.team', 'search',
                    [[('name', 'ilike', team_name)]], {'limit': 1})
                
                if team:
                    orders = self.execute_kw('sale.order', 'search_read',
                        [[('team_id', '=', team[0]), ('state', 'in', ['sale', 'done']),
                          ('amount_total', '>', 0)]], 
                        {'limit': needed_returns, 'fields': ['id', 'partner_id', 'amount_total']})
                    
                    for order in orders[:needed_returns]:
                        # Create return order
                        return_vals = {
                            'partner_id': order['partner_id'][0],
                            'team_id': team[0],
                            'state': 'sale',
                            'note': f"Return for order {order['id']}",
                            'amount_total': -order['amount_total'] * 0.8  # 80% refund
                        }
                        
                        try:
                            self.execute_kw('sale.order', 'create', [return_vals])
                            created_returns += 1
                        except:
                            pass
        
        if created_returns > 0:
            logger.info(f"✅ Created {created_returns} return orders")
            self.fixes_applied.append(f"Created {created_returns} return orders")
    
    def validate_product_coverage(self):
        """Ensure all active products have sales"""
        logger.info("\n📦 Validating Product Coverage...")
        
        # Get all active products
        products = self.execute_kw('product.product', 'search_read',
            [[('active', '=', True), ('sale_ok', '=', True)]], 
            {'fields': ['id', 'name', 'list_price', 'sales_count']})
        
        if not products:
            logger.warning("No active products found")
            return False
        
        # Find products without sales
        no_sales_products = [p for p in products if p.get('sales_count', 0) == 0]
        
        if no_sales_products:
            logger.warning(f"Found {len(no_sales_products)} products without sales")
            self.fix_product_coverage(no_sales_products)
        else:
            logger.info(f"✅ All {len(products)} products have sales")
        
        # Check revenue distribution (top 20% should generate 60-75%)
        products_sorted = sorted(products, key=lambda x: x.get('sales_count', 0), reverse=True)
        top_20_count = max(1, len(products) // 5)
        
        # Calculate revenue distribution (simplified)
        top_20_sales = sum(p.get('sales_count', 0) for p in products_sorted[:top_20_count])
        total_sales = sum(p.get('sales_count', 0) for p in products_sorted)
        
        if total_sales > 0:
            top_20_pct = top_20_sales / total_sales
            if 0.60 <= top_20_pct <= 0.75:
                logger.info(f"✅ Top 20% products generate {top_20_pct:.0%} of sales")
                valid = True
            else:
                logger.warning(f"❌ Top 20% products generate {top_20_pct:.0%} of sales (target: 60-75%)")
                valid = False
        else:
            valid = False
        
        self.validation_results['product_coverage'] = {
            'valid': valid and len(no_sales_products) == 0,
            'products_without_sales': len(no_sales_products),
            'total_products': len(products),
            'top_20_revenue_share': top_20_pct if total_sales > 0 else 0
        }
        
        return valid and len(no_sales_products) == 0
    
    def fix_product_coverage(self, no_sales_products):
        """Create minimal sales for products without any"""
        logger.info("🔧 Creating sales for products without coverage...")
        
        # Get a sample customer
        customer = self.execute_kw('res.partner', 'search',
            [[('customer_rank', '>', 0)]], {'limit': 1})
        
        if not customer:
            logger.error("No customers found to create orders")
            return
        
        created_orders = 0
        
        for product in no_sales_products[:50]:  # Limit to 50 products
            # Create a simple order
            order_vals = {
                'partner_id': customer[0],
                'state': 'sale',
                'order_line': [(0, 0, {
                    'product_id': product['id'],
                    'product_uom_qty': random.randint(1, 3),
                    'price_unit': product.get('list_price', 100)
                })]
            }
            
            try:
                self.execute_kw('sale.order', 'create', [order_vals])
                created_orders += 1
            except Exception as e:
                logger.debug(f"Could not create order for product {product['name']}: {e}")
        
        if created_orders > 0:
            logger.info(f"✅ Created {created_orders} orders for products without sales")
            self.fixes_applied.append(f"Created {created_orders} orders for product coverage")
    
    def validate_data_volatility(self):
        """Check for realistic week-to-week variance"""
        logger.info("\n📈 Validating Data Volatility...")
        
        # Get orders by week
        orders = self.execute_kw('sale.order', 'search_read',
            [[('state', 'in', ['sale', 'done']),
              ('date_order', '>=', '2024-06-01'),
              ('date_order', '<=', '2024-09-30')]], 
            {'fields': ['date_order', 'amount_total']})
        
        if not orders:
            logger.warning("No orders found in summer period")
            return False
        
        # Group by week
        weekly_revenue = defaultdict(float)
        for order in orders:
            if order.get('date_order'):
                date = datetime.strptime(order['date_order'], '%Y-%m-%d %H:%M:%S')
                week = date.isocalendar()[1]
                weekly_revenue[week] += order['amount_total']
        
        # Calculate week-to-week variance
        weeks = sorted(weekly_revenue.keys())
        variances = []
        
        for i in range(1, len(weeks)):
            prev_week = weekly_revenue[weeks[i-1]]
            curr_week = weekly_revenue[weeks[i]]
            if prev_week > 0:
                variance = abs(curr_week - prev_week) / prev_week
                variances.append(variance)
        
        if variances:
            avg_variance = sum(variances) / len(variances)
            
            if avg_variance >= 0.20:
                logger.info(f"✅ Average week-to-week variance: {avg_variance:.0%}")
                valid = True
            else:
                logger.warning(f"❌ Average week-to-week variance: {avg_variance:.0%} (target: ≥20%)")
                valid = False
                self.fix_data_volatility(orders)
        else:
            valid = False
        
        self.validation_results['data_volatility'] = {
            'valid': valid,
            'average_variance': avg_variance if variances else 0,
            'target': 0.20
        }
        
        return valid
    
    def fix_data_volatility(self, orders):
        """Add variance to create more realistic patterns"""
        logger.info("🔧 Adding variance to sales data...")
        
        # Add random promotional orders
        promo_dates = [
            ('2024-07-04', 'Independence Day Sale'),
            ('2024-07-15', 'Mid-Summer Flash Sale'),
            ('2024-08-26', 'Bank Holiday Sale'),
            ('2024-09-02', 'Labor Day Sale')
        ]
        
        customer = self.execute_kw('res.partner', 'search',
            [[('customer_rank', '>', 0)]], {'limit': 1})
        
        if not customer:
            return
        
        created_promos = 0
        
        for date_str, promo_name in promo_dates:
            # Create 5-10 orders for each promo
            for _ in range(random.randint(5, 10)):
                order_vals = {
                    'partner_id': customer[0],
                    'date_order': f"{date_str} 14:00:00",
                    'state': 'sale',
                    'note': promo_name
                }
                
                try:
                    self.execute_kw('sale.order', 'create', [order_vals])
                    created_promos += 1
                except:
                    pass
        
        if created_promos > 0:
            logger.info(f"✅ Created {created_promos} promotional orders")
            self.fixes_applied.append(f"Created {created_promos} promotional orders for variance")
    
    def generate_final_report(self):
        """Generate comprehensive validation report"""
        logger.info("\n" + "="*60)
        logger.info("FINAL VALIDATION REPORT")
        logger.info("="*60)
        
        # Overall status
        all_valid = all(result.get('valid', False) for result in self.validation_results.values())
        
        if all_valid:
            logger.info("\n✅ ALL VALIDATIONS PASSED!")
        else:
            logger.info("\n⚠️ SOME VALIDATIONS NEED ATTENTION")
        
        # Detailed results
        logger.info("\nValidation Results:")
        for check, result in self.validation_results.items():
            status = "✅" if result.get('valid') else "❌"
            logger.info(f"{status} {check.replace('_', ' ').title()}")
        
        # Fixes applied
        if self.fixes_applied:
            logger.info(f"\n🔧 Fixes Applied ({len(self.fixes_applied)}):")
            for fix in self.fixes_applied:
                logger.info(f"  - {fix}")
        
        # Save report
        report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'PASSED' if all_valid else 'NEEDS_ATTENTION',
            'validation_results': self.validation_results,
            'fixes_applied': self.fixes_applied,
            'issues_found': self.issues_found
        }
        
        report_path = '/workspaces/source-lovable-gympluscoffee/odoo-ingestion/master_validation_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\n📄 Full report saved to: {report_path}")
        
        return all_valid
    
    def run_all_validations(self):
        """Run all validations and fixes"""
        logger.info("Starting Master Validation and Fix Process...")
        logger.info("="*60)
        
        # Run all validation checks
        checks = [
            self.validate_channel_distribution,
            self.validate_geographic_distribution,
            self.validate_return_rates,
            self.validate_product_coverage,
            self.validate_data_volatility
        ]
        
        for check in checks:
            try:
                check()
            except Exception as e:
                logger.error(f"Error in {check.__name__}: {e}")
                self.validation_results[check.__name__.replace('validate_', '')] = {
                    'valid': False,
                    'error': str(e)
                }
        
        # Generate final report
        all_valid = self.generate_final_report()
        
        return all_valid


def main():
    """Main execution"""
    validator = OdooMasterValidator()
    
    # Run all validations
    success = validator.run_all_validations()
    
    if success:
        logger.info("\n🎉 All data validations passed successfully!")
        sys.exit(0)
    else:
        logger.info("\n⚠️ Some validations need attention. Check the report for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()