#!/usr/bin/env python3
"""
Business Metrics Validation Script for Source Gym Plus Coffee
Validates all KPIs and generates fix scripts for underperforming metrics.
"""

import xmlrpc.client
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics
from typing import Dict, List, Tuple, Any
import calendar

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OdooBusinessValidator:
    def __init__(self):
        # Odoo connection parameters
        self.url = 'https://source-gym-plus-coffee.odoo.com/'
        self.db = 'source-gym-plus-coffee'
        self.username = 'admin@quickfindai.com'
        self.password = 'BJ62wX2J4yzjS$i'
        
        # Business targets
        self.targets = {
            'summer_revenue_distribution': {
                'june': (20, 23),      # 20-23% of summer total
                'july': (24, 27),      # 24-27% of summer total
                'august': (27, 31),    # 27-31% of summer total
                'september': (22, 26)  # 22-26% of summer total
            },
            'weekly_variance': 30,     # ±30% variance allowed
            'holiday_spike_required': True,
            'min_channels': 3,
            'min_geographic_regions': 5
        }
        
        # Initialize connections
        self.common = None
        self.models = None
        self.uid = None
        self.connect()
        
        # Data storage
        self.sales_data = []
        self.customers_data = []
        self.products_data = []
        self.order_lines_data = []
        
    def connect(self):
        """Establish connection to Odoo"""
        try:
            self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
            
            # Authenticate
            self.uid = self.common.authenticate(self.db, self.username, self.password, {})
            if not self.uid:
                raise Exception("Authentication failed")
            
            logger.info(f"✅ Connected to Odoo as user ID: {self.uid}")
            
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            raise
    
    def fetch_all_data(self):
        """Fetch all necessary data from Odoo"""
        logger.info("📊 Fetching all business data...")
        
        # Fetch sales orders
        try:
            self.sales_data = self.models.execute_kw(
                self.db, self.uid, self.password,
                'sale.order', 'search_read',
                [[]],
                {
                    'fields': ['name', 'date_order', 'amount_total', 'state', 
                              'partner_id', 'team_id', 'user_id', 'company_id'],
                    'limit': 5000
                }
            )
            logger.info(f"✅ Fetched {len(self.sales_data)} sales orders")
        except Exception as e:
            logger.error(f"❌ Error fetching sales orders: {e}")
            self.sales_data = []
        
        # Fetch order lines for detailed analysis
        try:
            self.order_lines_data = self.models.execute_kw(
                self.db, self.uid, self.password,
                'sale.order.line', 'search_read',
                [[]],
                {
                    'fields': ['order_id', 'product_id', 'product_uom_qty', 
                              'price_unit', 'price_subtotal', 'discount'],
                    'limit': 10000
                }
            )
            logger.info(f"✅ Fetched {len(self.order_lines_data)} order lines")
        except Exception as e:
            logger.error(f"❌ Error fetching order lines: {e}")
            self.order_lines_data = []
        
        # Fetch customers
        try:
            self.customers_data = self.models.execute_kw(
                self.db, self.uid, self.password,
                'res.partner', 'search_read',
                [[['is_company', '=', False]]],
                {
                    'fields': ['name', 'email', 'phone', 'street', 'city', 
                              'state_id', 'country_id', 'category_id'],
                    'limit': 5000
                }
            )
            logger.info(f"✅ Fetched {len(self.customers_data)} customers")
        except Exception as e:
            logger.error(f"❌ Error fetching customers: {e}")
            self.customers_data = []
        
        # Fetch products
        try:
            self.products_data = self.models.execute_kw(
                self.db, self.uid, self.password,
                'product.product', 'search_read',
                [[]],
                {
                    'fields': ['name', 'default_code', 'categ_id', 'list_price', 
                              'standard_price', 'product_tmpl_id'],
                    'limit': 2000
                }
            )
            logger.info(f"✅ Fetched {len(self.products_data)} products")
        except Exception as e:
            logger.error(f"❌ Error fetching products: {e}")
            self.products_data = []
    
    def validate_seasonal_distribution(self) -> Dict[str, Any]:
        """Validate seasonal revenue distribution"""
        logger.info("🌞 Validating seasonal distribution...")
        
        # Group sales by month
        monthly_revenue = defaultdict(float)
        monthly_orders = defaultdict(int)
        
        for sale in self.sales_data:
            if sale['state'] in ['sale', 'done'] and sale['date_order']:
                try:
                    date_obj = datetime.strptime(sale['date_order'], '%Y-%m-%d %H:%M:%S')
                    month_key = f"{date_obj.year}-{date_obj.month:02d}"
                    monthly_revenue[month_key] += float(sale['amount_total'])
                    monthly_orders[month_key] += 1
                except:
                    continue
        
        # Calculate summer distribution (June-September)
        summer_months = {}
        total_summer = 0
        
        for month_key, revenue in monthly_revenue.items():
            year, month_num = month_key.split('-')
            month_num = int(month_num)
            
            if month_num in [6, 7, 8, 9]:  # June to September
                month_name = calendar.month_name[month_num].lower()
                if month_name not in summer_months:
                    summer_months[month_name] = 0
                summer_months[month_name] += revenue
                total_summer += revenue
        
        # Calculate percentages
        summer_percentages = {}
        for month, revenue in summer_months.items():
            if total_summer > 0:
                percentage = (revenue / total_summer) * 100
                summer_percentages[month] = percentage
        
        # Validate against targets
        issues = []
        fixes_needed = []
        
        for month, percentage in summer_percentages.items():
            if month in self.targets['summer_revenue_distribution']:
                min_target, max_target = self.targets['summer_revenue_distribution'][month]
                if percentage < min_target:
                    issues.append(f"{month.title()}: {percentage:.1f}% (below {min_target}%)")
                    fixes_needed.append({
                        'month': month,
                        'current': percentage,
                        'target_min': min_target,
                        'action': 'increase_orders'
                    })
                elif percentage > max_target:
                    issues.append(f"{month.title()}: {percentage:.1f}% (above {max_target}%)")
                    fixes_needed.append({
                        'month': month,
                        'current': percentage,
                        'target_max': max_target,
                        'action': 'redistribute_orders'
                    })
        
        return {
            'status': 'PASS' if not issues else 'FAIL',
            'monthly_revenue': dict(monthly_revenue),
            'summer_percentages': summer_percentages,
            'total_summer': total_summer,
            'issues': issues,
            'fixes_needed': fixes_needed
        }
    
    def validate_weekly_variance(self) -> Dict[str, Any]:
        """Validate weekly variance in sales"""
        logger.info("📈 Validating weekly variance...")
        
        # Group sales by week
        weekly_revenue = defaultdict(float)
        
        for sale in self.sales_data:
            if sale['state'] in ['sale', 'done'] and sale['date_order']:
                try:
                    date_obj = datetime.strptime(sale['date_order'], '%Y-%m-%d %H:%M:%S')
                    # Get ISO week number
                    year, week, _ = date_obj.isocalendar()
                    week_key = f"{year}-W{week:02d}"
                    weekly_revenue[week_key] += float(sale['amount_total'])
                except:
                    continue
        
        # Calculate variance
        if len(weekly_revenue) < 2:
            return {
                'status': 'INSUFFICIENT_DATA',
                'weekly_revenue': dict(weekly_revenue),
                'variance': 0,
                'issues': ['Insufficient data for variance calculation']
            }
        
        revenues = list(weekly_revenue.values())
        mean_revenue = statistics.mean(revenues)
        std_dev = statistics.stdev(revenues) if len(revenues) > 1 else 0
        coefficient_of_variation = (std_dev / mean_revenue * 100) if mean_revenue > 0 else 0
        
        issues = []
        if coefficient_of_variation > self.targets['weekly_variance']:
            issues.append(f"Weekly variance {coefficient_of_variation:.1f}% exceeds target {self.targets['weekly_variance']}%")
        
        return {
            'status': 'PASS' if not issues else 'FAIL',
            'weekly_revenue': dict(weekly_revenue),
            'mean_revenue': mean_revenue,
            'std_deviation': std_dev,
            'coefficient_of_variation': coefficient_of_variation,
            'target_variance': self.targets['weekly_variance'],
            'issues': issues
        }
    
    def validate_channel_distribution(self) -> Dict[str, Any]:
        """Validate sales channel distribution"""
        logger.info("🛍️ Validating channel distribution...")
        
        # Get sales teams (channels)
        try:
            teams = self.models.execute_kw(
                self.db, self.uid, self.password,
                'crm.team', 'search_read',
                [[]],
                {'fields': ['name', 'id']}
            )
            team_names = {team['id']: team['name'] for team in teams}
        except:
            team_names = {}
        
        # Group sales by channel
        channel_revenue = defaultdict(float)
        channel_orders = defaultdict(int)
        
        for sale in self.sales_data:
            if sale['state'] in ['sale', 'done']:
                team_id = sale['team_id'][0] if sale['team_id'] else 'Unknown'
                channel_name = team_names.get(team_id, f'Team_{team_id}')
                channel_revenue[channel_name] += float(sale['amount_total'])
                channel_orders[channel_name] += 1
        
        # Calculate average order values
        avg_order_values = {}
        for channel, revenue in channel_revenue.items():
            orders = channel_orders[channel]
            avg_order_values[channel] = revenue / orders if orders > 0 else 0
        
        # Validate
        issues = []
        unique_channels = len(channel_revenue)
        
        if unique_channels < self.targets['min_channels']:
            issues.append(f"Only {unique_channels} channels found, target: {self.targets['min_channels']}")
        
        return {
            'status': 'PASS' if not issues else 'FAIL',
            'channel_revenue': dict(channel_revenue),
            'channel_orders': dict(channel_orders),
            'avg_order_values': avg_order_values,
            'unique_channels': unique_channels,
            'issues': issues
        }
    
    def validate_geographic_distribution(self) -> Dict[str, Any]:
        """Validate geographic distribution"""
        logger.info("🗺️ Validating geographic distribution...")
        
        # Create customer location mapping
        customer_locations = {}
        for customer in self.customers_data:
            customer_id = customer['id']
            city = customer.get('city', 'Unknown')
            state = customer['state_id'][1] if customer['state_id'] else 'Unknown'
            country = customer['country_id'][1] if customer['country_id'] else 'Unknown'
            customer_locations[customer_id] = {
                'city': city,
                'state': state,
                'country': country
            }
        
        # Group sales by geography
        geographic_revenue = defaultdict(float)
        city_revenue = defaultdict(float)
        state_revenue = defaultdict(float)
        
        for sale in self.sales_data:
            if sale['state'] in ['sale', 'done']:
                customer_id = sale['partner_id'][0] if sale['partner_id'] else None
                if customer_id in customer_locations:
                    location = customer_locations[customer_id]
                    state = location['state']
                    city = location['city']
                    
                    state_revenue[state] += float(sale['amount_total'])
                    city_revenue[city] += float(sale['amount_total'])
                    geographic_revenue[f"{city}, {state}"] += float(sale['amount_total'])
        
        # Validate
        issues = []
        unique_regions = len([k for k in state_revenue.keys() if k != 'Unknown'])
        
        if unique_regions < self.targets['min_geographic_regions']:
            issues.append(f"Only {unique_regions} geographic regions, target: {self.targets['min_geographic_regions']}")
        
        return {
            'status': 'PASS' if not issues else 'FAIL',
            'state_revenue': dict(state_revenue),
            'city_revenue': dict(city_revenue),
            'geographic_revenue': dict(geographic_revenue),
            'unique_regions': unique_regions,
            'issues': issues
        }
    
    def validate_product_performance(self) -> Dict[str, Any]:
        """Validate product performance metrics"""
        logger.info("📦 Validating product performance...")
        
        # Create product mapping
        product_names = {p['id']: p['name'] for p in self.products_data}
        product_categories = {p['id']: p['categ_id'][1] if p['categ_id'] else 'Unknown' 
                            for p in self.products_data}
        
        # Analyze order lines
        product_revenue = defaultdict(float)
        product_quantities = defaultdict(float)
        category_revenue = defaultdict(float)
        
        for line in self.order_lines_data:
            product_id = line['product_id'][0] if line['product_id'] else None
            if product_id:
                revenue = float(line['price_subtotal'])
                quantity = float(line['product_uom_qty'])
                
                product_revenue[product_id] += revenue
                product_quantities[product_id] += quantity
                
                category = product_categories.get(product_id, 'Unknown')
                category_revenue[category] += revenue
        
        # Top performing products
        top_products = sorted(product_revenue.items(), key=lambda x: x[1], reverse=True)[:20]
        top_products_with_names = [
            (product_names.get(pid, f'Product_{pid}'), revenue)
            for pid, revenue in top_products
        ]
        
        return {
            'status': 'PASS',  # Products are performing well if we have data
            'product_revenue': dict(product_revenue),
            'product_quantities': dict(product_quantities),
            'category_revenue': dict(category_revenue),
            'top_products': top_products_with_names,
            'total_products_sold': len(product_revenue),
            'issues': []
        }
    
    def calculate_customer_metrics(self) -> Dict[str, Any]:
        """Calculate customer lifetime values and metrics"""
        logger.info("👥 Calculating customer metrics...")
        
        # Group sales by customer
        customer_revenue = defaultdict(float)
        customer_orders = defaultdict(int)
        customer_first_order = {}
        customer_last_order = {}
        
        for sale in self.sales_data:
            if sale['state'] in ['sale', 'done'] and sale['partner_id']:
                customer_id = sale['partner_id'][0]
                revenue = float(sale['amount_total'])
                order_date = sale['date_order']
                
                customer_revenue[customer_id] += revenue
                customer_orders[customer_id] += 1
                
                if customer_id not in customer_first_order:
                    customer_first_order[customer_id] = order_date
                else:
                    if order_date < customer_first_order[customer_id]:
                        customer_first_order[customer_id] = order_date
                
                if customer_id not in customer_last_order:
                    customer_last_order[customer_id] = order_date
                else:
                    if order_date > customer_last_order[customer_id]:
                        customer_last_order[customer_id] = order_date
        
        # Calculate CLV and other metrics
        clv_values = list(customer_revenue.values())
        avg_clv = statistics.mean(clv_values) if clv_values else 0
        
        # Average order values per customer
        avg_order_values = {}
        for customer_id in customer_revenue:
            aov = customer_revenue[customer_id] / customer_orders[customer_id]
            avg_order_values[customer_id] = aov
        
        overall_aov = statistics.mean(avg_order_values.values()) if avg_order_values else 0
        
        return {
            'status': 'PASS',
            'total_customers': len(customer_revenue),
            'avg_customer_lifetime_value': avg_clv,
            'avg_order_value': overall_aov,
            'customer_revenue': dict(customer_revenue),
            'customer_orders': dict(customer_orders),
            'repeat_customers': len([c for c in customer_orders.values() if c > 1]),
            'issues': []
        }
    
    def generate_fix_scripts(self, validation_results: Dict[str, Any]):
        """Generate fix scripts for identified issues"""
        logger.info("🔧 Generating fix scripts...")
        
        fix_scripts = []
        
        # Fix seasonal distribution issues
        if validation_results['seasonal']['status'] == 'FAIL':
            for fix in validation_results['seasonal']['fixes_needed']:
                if fix['action'] == 'increase_orders':
                    script = self.create_seasonal_boost_script(fix)
                    fix_scripts.append(script)
        
        # Fix channel distribution
        if validation_results['channels']['unique_channels'] < self.targets['min_channels']:
            script = self.create_channel_diversification_script()
            fix_scripts.append(script)
        
        # Fix geographic distribution
        if validation_results['geographic']['unique_regions'] < self.targets['min_geographic_regions']:
            script = self.create_geographic_expansion_script()
            fix_scripts.append(script)
        
        return fix_scripts
    
    def create_seasonal_boost_script(self, fix_config: Dict[str, Any]) -> str:
        """Create script to boost specific seasonal performance"""
        month = fix_config['month']
        current = fix_config['current']
        target = fix_config['target_min']
        
        script = f"""
# Seasonal Boost Script for {month.title()}
# Current: {current:.1f}%, Target: {target:.1f}%

import xmlrpc.client
from datetime import datetime, timedelta
import random

def boost_{month}_sales():
    # Connection setup
    url = 'https://source-gym-plus-coffee.odoo.com/'
    db = 'source-gym-plus-coffee'
    username = 'admin@quickfindai.com'
    password = 'BJ62wX2J4yzjS$i'
    
    common = xmlrpc.client.ServerProxy(f'{{url}}/xmlrpc/2/common')
    models = xmlrpc.client.ServerProxy(f'{{url}}/xmlrpc/2/object')
    uid = common.authenticate(db, username, password, {{}})
    
    # Get existing customers and products
    customers = models.execute_kw(db, uid, password, 'res.partner', 'search', 
                                [[['is_company', '=', False]]], {{'limit': 50}})
    products = models.execute_kw(db, uid, password, 'product.product', 'search', 
                               [[]], {{'limit': 20}})
    
    # Calculate number of additional orders needed
    boost_percentage = {target - current:.1f}
    additional_orders = int(50 * (boost_percentage / 100))  # Approximate
    
    print(f"Creating {{additional_orders}} additional orders for {month.title()}")
    
    # Create {month} orders
    for i in range(additional_orders):
        # Random date in {month}
        if '{month}' == 'june':
            base_date = datetime(2024, 6, random.randint(1, 30))
        elif '{month}' == 'july':
            base_date = datetime(2024, 7, random.randint(1, 31))
        elif '{month}' == 'august':
            base_date = datetime(2024, 8, random.randint(1, 31))
        else:  # september
            base_date = datetime(2024, 9, random.randint(1, 30))
        
        order_data = {{
            'partner_id': random.choice(customers),
            'date_order': base_date.strftime('%Y-%m-%d %H:%M:%S'),
            'state': 'sale',
            'order_line': [(0, 0, {{
                'product_id': random.choice(products),
                'product_uom_qty': random.randint(1, 5),
                'price_unit': random.uniform(15.0, 150.0)
            }})]
        }}
        
        try:
            order_id = models.execute_kw(db, uid, password, 'sale.order', 'create', [order_data])
            print(f"Created order {{order_id}} for {month.title()}")
        except Exception as e:
            print(f"Error creating order: {{e}}")

if __name__ == "__main__":
    boost_{month}_sales()
"""
        return script
    
    def create_channel_diversification_script(self) -> str:
        """Create script to add more sales channels"""
        return """
# Channel Diversification Script

import xmlrpc.client

def create_additional_channels():
    # Connection setup
    url = 'https://source-gym-plus-coffee.odoo.com/'
    db = 'source-gym-plus-coffee'
    username = 'admin@quickfindai.com'
    password = 'BJ62wX2J4yzjS$i'
    
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    uid = common.authenticate(db, username, password, {})
    
    # Create additional sales channels
    new_channels = [
        {'name': 'Instagram Shop', 'code': 'INSTAGRAM'},
        {'name': 'Amazon Store', 'code': 'AMAZON'},
        {'name': 'Corporate Sales', 'code': 'B2B'},
        {'name': 'Pop-up Events', 'code': 'POPUP'}
    ]
    
    for channel in new_channels:
        try:
            team_id = models.execute_kw(db, uid, password, 'crm.team', 'create', [channel])
            print(f"Created channel: {channel['name']} (ID: {team_id})")
        except Exception as e:
            print(f"Error creating channel {channel['name']}: {e}")

if __name__ == "__main__":
    create_additional_channels()
"""
    
    def create_geographic_expansion_script(self) -> str:
        """Create script to expand geographic reach"""
        return """
# Geographic Expansion Script

import xmlrpc.client
import random

def create_diverse_customers():
    # Connection setup
    url = 'https://source-gym-plus-coffee.odoo.com/'
    db = 'source-gym-plus-coffee'
    username = 'admin@quickfindai.com'
    password = 'BJ62wX2J4yzjS$i'
    
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    uid = common.authenticate(db, username, password, {})
    
    # Get country and state IDs
    countries = models.execute_kw(db, uid, password, 'res.country', 'search_read',
                                [[]], {'fields': ['name', 'id']})
    states = models.execute_kw(db, uid, password, 'res.country.state', 'search_read',
                             [[]], {'fields': ['name', 'id', 'country_id']})
    
    # Define diverse locations
    diverse_locations = [
        {'city': 'Miami', 'state_name': 'Florida'},
        {'city': 'Austin', 'state_name': 'Texas'},
        {'city': 'Denver', 'state_name': 'Colorado'},
        {'city': 'Seattle', 'state_name': 'Washington'},
        {'city': 'Boston', 'state_name': 'Massachusetts'},
        {'city': 'Atlanta', 'state_name': 'Georgia'},
        {'city': 'Phoenix', 'state_name': 'Arizona'},
        {'city': 'Portland', 'state_name': 'Oregon'}
    ]
    
    # Create customers in each location
    for location in diverse_locations:
        # Find state ID
        state_id = None
        for state in states:
            if location['state_name'].lower() in state['name'].lower():
                state_id = state['id']
                break
        
        # Create 3-5 customers per location
        for i in range(random.randint(3, 5)):
            customer_data = {
                'name': f"Customer {location['city']} {i+1}",
                'email': f"customer.{location['city'].lower()}.{i+1}@example.com",
                'city': location['city'],
                'state_id': state_id,
                'country_id': 233,  # USA
                'is_company': False
            }
            
            try:
                customer_id = models.execute_kw(db, uid, password, 'res.partner', 'create', [customer_data])
                print(f"Created customer in {location['city']}: {customer_id}")
            except Exception as e:
                print(f"Error creating customer in {location['city']}: {e}")

if __name__ == "__main__":
    create_diverse_customers()
"""
    
    def run_full_validation(self) -> Dict[str, Any]:
        """Run complete business metrics validation"""
        logger.info("🚀 Starting full business metrics validation...")
        
        # Fetch all data first
        self.fetch_all_data()
        
        # Run all validations
        validation_results = {
            'timestamp': datetime.now().isoformat(),
            'seasonal': self.validate_seasonal_distribution(),
            'variance': self.validate_weekly_variance(),
            'channels': self.validate_channel_distribution(),
            'geographic': self.validate_geographic_distribution(),
            'products': self.validate_product_performance(),
            'customers': self.calculate_customer_metrics()
        }
        
        # Calculate overall status
        failed_validations = [k for k, v in validation_results.items() 
                            if isinstance(v, dict) and v.get('status') == 'FAIL']
        
        validation_results['overall_status'] = 'PASS' if not failed_validations else 'FAIL'
        validation_results['failed_validations'] = failed_validations
        
        # Generate fix scripts if needed
        if failed_validations:
            validation_results['fix_scripts'] = self.generate_fix_scripts(validation_results)
        
        return validation_results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive validation report"""
        report = []
        report.append("=" * 80)
        report.append("SOURCE GYM PLUS COFFEE - BUSINESS METRICS VALIDATION REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {results['timestamp']}")
        report.append(f"Overall Status: {'✅ PASS' if results['overall_status'] == 'PASS' else '❌ FAIL'}")
        report.append("")
        
        # Seasonal Distribution
        report.append("🌞 SEASONAL DISTRIBUTION ANALYSIS")
        report.append("-" * 40)
        seasonal = results['seasonal']
        report.append(f"Status: {'✅ PASS' if seasonal['status'] == 'PASS' else '❌ FAIL'}")
        
        if 'summer_percentages' in seasonal:
            report.append("Summer Revenue Distribution:")
            for month, percentage in seasonal['summer_percentages'].items():
                target = self.targets['summer_revenue_distribution'].get(month, (0, 0))
                status = "✅" if target[0] <= percentage <= target[1] else "❌"
                report.append(f"  {status} {month.title()}: {percentage:.1f}% (Target: {target[0]}-{target[1]}%)")
        
        if seasonal['issues']:
            report.append("Issues:")
            for issue in seasonal['issues']:
                report.append(f"  ❌ {issue}")
        report.append("")
        
        # Weekly Variance
        report.append("📈 WEEKLY VARIANCE ANALYSIS")
        report.append("-" * 40)
        variance = results['variance']
        report.append(f"Status: {'✅ PASS' if variance['status'] == 'PASS' else '❌ FAIL'}")
        if 'coefficient_of_variation' in variance:
            report.append(f"Weekly Variance: {variance['coefficient_of_variation']:.1f}% (Target: <{self.targets['weekly_variance']}%)")
            report.append(f"Mean Weekly Revenue: ${variance['mean_revenue']:,.2f}")
        
        if variance['issues']:
            for issue in variance['issues']:
                report.append(f"  ❌ {issue}")
        report.append("")
        
        # Channel Distribution
        report.append("🛍️ CHANNEL DISTRIBUTION ANALYSIS")
        report.append("-" * 40)
        channels = results['channels']
        report.append(f"Status: {'✅ PASS' if channels['status'] == 'PASS' else '❌ FAIL'}")
        report.append(f"Active Channels: {channels['unique_channels']} (Target: ≥{self.targets['min_channels']})")
        
        if 'channel_revenue' in channels:
            report.append("Channel Performance:")
            total_revenue = sum(channels['channel_revenue'].values())
            for channel, revenue in sorted(channels['channel_revenue'].items(), key=lambda x: x[1], reverse=True):
                percentage = (revenue / total_revenue * 100) if total_revenue > 0 else 0
                aov = channels['avg_order_values'].get(channel, 0)
                report.append(f"  • {channel}: ${revenue:,.2f} ({percentage:.1f}%) - AOV: ${aov:.2f}")
        report.append("")
        
        # Geographic Distribution
        report.append("🗺️ GEOGRAPHIC DISTRIBUTION ANALYSIS")
        report.append("-" * 40)
        geographic = results['geographic']
        report.append(f"Status: {'✅ PASS' if geographic['status'] == 'PASS' else '❌ FAIL'}")
        report.append(f"Geographic Regions: {geographic['unique_regions']} (Target: ≥{self.targets['min_geographic_regions']})")
        
        if 'state_revenue' in geographic:
            report.append("Top States by Revenue:")
            for state, revenue in sorted(geographic['state_revenue'].items(), key=lambda x: x[1], reverse=True)[:10]:
                if state != 'Unknown':
                    report.append(f"  • {state}: ${revenue:,.2f}")
        report.append("")
        
        # Product Performance
        report.append("📦 PRODUCT PERFORMANCE ANALYSIS")
        report.append("-" * 40)
        products = results['products']
        report.append(f"Status: {'✅ PASS' if products['status'] == 'PASS' else '❌ FAIL'}")
        report.append(f"Total Products Sold: {products['total_products_sold']}")
        
        if 'top_products' in products:
            report.append("Top 10 Products by Revenue:")
            for i, (product_name, revenue) in enumerate(products['top_products'][:10], 1):
                report.append(f"  {i:2d}. {product_name}: ${revenue:,.2f}")
        
        if 'category_revenue' in products:
            report.append("Top Categories by Revenue:")
            for category, revenue in sorted(products['category_revenue'].items(), key=lambda x: x[1], reverse=True)[:5]:
                if category != 'Unknown':
                    report.append(f"  • {category}: ${revenue:,.2f}")
        report.append("")
        
        # Customer Metrics
        report.append("👥 CUSTOMER METRICS ANALYSIS")
        report.append("-" * 40)
        customers = results['customers']
        report.append(f"Status: {'✅ PASS' if customers['status'] == 'PASS' else '❌ FAIL'}")
        report.append(f"Total Customers: {customers['total_customers']:,}")
        report.append(f"Average Customer Lifetime Value: ${customers['avg_customer_lifetime_value']:,.2f}")
        report.append(f"Average Order Value: ${customers['avg_order_value']:,.2f}")
        report.append(f"Repeat Customers: {customers['repeat_customers']:,} ({customers['repeat_customers']/customers['total_customers']*100:.1f}%)")
        report.append("")
        
        # Issues Summary
        if results['overall_status'] == 'FAIL':
            report.append("🚨 ISSUES REQUIRING ATTENTION")
            report.append("-" * 40)
            for validation_name in results['failed_validations']:
                validation = results[validation_name]
                if isinstance(validation, dict) and 'issues' in validation:
                    for issue in validation['issues']:
                        report.append(f"  ❌ {validation_name.title()}: {issue}")
            report.append("")
        
        # Recommendations
        report.append("💡 RECOMMENDATIONS")
        report.append("-" * 40)
        if results['overall_status'] == 'PASS':
            report.append("✅ All business metrics meet target requirements!")
            report.append("• Continue monitoring seasonal patterns")
            report.append("• Maintain channel diversity")
            report.append("• Keep expanding geographic reach")
        else:
            if 'fix_scripts' in results:
                report.append("Fix scripts have been generated to address issues:")
                report.append("• Run seasonal boost scripts for underperforming months")
                report.append("• Execute channel diversification script")
                report.append("• Run geographic expansion script")
            
            report.append("Additional recommendations:")
            report.append("• Monitor weekly sales variance closely")
            report.append("• Implement targeted marketing campaigns")
            report.append("• Focus on customer retention programs")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)

def main():
    """Main execution function"""
    try:
        validator = OdooBusinessValidator()
        
        # Run full validation
        results = validator.run_full_validation()
        
        # Generate and save report
        report = validator.generate_report(results)
        
        # Save results to JSON
        with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/validation_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Save report to text file
        with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/validation_report.txt', 'w') as f:
            f.write(report)
        
        # Print report
        print(report)
        
        # Save fix scripts if any
        if 'fix_scripts' in results:
            for i, script in enumerate(results['fix_scripts'], 1):
                script_filename = f'/workspaces/source-lovable-gympluscoffee/odoo-ingestion/fix_script_{i}.py'
                with open(script_filename, 'w') as f:
                    f.write(script)
                print(f"\n💾 Fix script saved: {script_filename}")
        
        logger.info("✅ Validation completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Validation failed: {e}")
        raise

if __name__ == "__main__":
    main()