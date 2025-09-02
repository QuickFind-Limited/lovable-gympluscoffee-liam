#!/usr/bin/env python3
"""
Comprehensive Seasonal Distribution Fix Script
- Redistributes excessive August orders
- Creates proper seasonal distribution
- Adds realistic seasonal orders for June, July, and September
"""

import xmlrpc.client
import random
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SeasonalDistributionFixer:
    def __init__(self):
        # Connection setup
        self.url = 'https://source-gym-plus-coffee.odoo.com/'
        self.db = 'source-gym-plus-coffee'
        self.username = 'admin@quickfindai.com'
        self.password = 'BJ62wX2J4yzjS$i'
        
        # Initialize connections
        self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
        self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
        self.uid = self.common.authenticate(self.db, self.username, self.password, {})
        
        # Cache data
        self.customers = []
        self.products = []
        self.teams = []
        
        # Target distribution (percentages of summer total)
        self.target_distribution = {
            'june': 21.5,    # Target: 20-23%
            'july': 25.5,    # Target: 24-27%
            'august': 29.0,  # Target: 27-31% 
            'september': 24.0 # Target: 22-26%
        }
        
    def load_reference_data(self):
        """Load customers, products, and teams for order creation"""
        logger.info("Loading reference data...")
        
        # Get customers
        self.customers = self.models.execute_kw(
            self.db, self.uid, self.password,
            'res.partner', 'search',
            [[['is_company', '=', False]]],
            {'limit': 200}
        )
        
        # Get products
        self.products = self.models.execute_kw(
            self.db, self.uid, self.password,
            'product.product', 'search',
            [[]],
            {'limit': 100}
        )
        
        # Get sales teams
        self.teams = self.models.execute_kw(
            self.db, self.uid, self.password,
            'crm.team', 'search',
            [[]]
        )
        
        logger.info(f"Loaded {len(self.customers)} customers, {len(self.products)} products, {len(self.teams)} teams")
    
    def get_current_summer_orders(self):
        """Get current summer orders for analysis"""
        logger.info("Analyzing current summer orders...")
        
        # Get all summer orders (2024 and 2025)
        summer_orders = self.models.execute_kw(
            self.db, self.uid, self.password,
            'sale.order', 'search_read',
            [['&', 
              ['state', 'in', ['sale', 'done']], 
              '|',
              '&', ['date_order', '>=', '2024-06-01'], ['date_order', '<', '2024-10-01'],
              '&', ['date_order', '>=', '2025-06-01'], ['date_order', '<', '2025-10-01']
            ]],
            {'fields': ['id', 'date_order', 'amount_total', 'state']}
        )
        
        # Group by month
        monthly_totals = {
            'june': {'total': 0, 'orders': []},
            'july': {'total': 0, 'orders': []},
            'august': {'total': 0, 'orders': []},
            'september': {'total': 0, 'orders': []}
        }
        
        for order in summer_orders:
            date_obj = datetime.strptime(order['date_order'], '%Y-%m-%d %H:%M:%S')
            month_key = None
            
            if date_obj.month == 6:
                month_key = 'june'
            elif date_obj.month == 7:
                month_key = 'july'
            elif date_obj.month == 8:
                month_key = 'august'
            elif date_obj.month == 9:
                month_key = 'september'
            
            if month_key:
                monthly_totals[month_key]['total'] += order['amount_total']
                monthly_totals[month_key]['orders'].append(order)
        
        total_summer = sum([month['total'] for month in monthly_totals.values()])
        
        logger.info("Current distribution:")
        for month, data in monthly_totals.items():
            percentage = (data['total'] / total_summer * 100) if total_summer > 0 else 0
            logger.info(f"  {month.title()}: ${data['total']:,.2f} ({percentage:.1f}%) - {len(data['orders'])} orders")
        
        return monthly_totals, total_summer
    
    def create_seasonal_orders(self, month, target_amount, base_year=2024):
        """Create realistic seasonal orders for the specified month"""
        logger.info(f"Creating seasonal orders for {month.title()} - Target: ${target_amount:,.2f}")
        
        # Calculate number of orders needed based on typical AOV
        typical_aov = 250  # Average Order Value
        orders_needed = max(1, int(target_amount / typical_aov))
        
        # Month configuration
        month_config = {
            'june': {'days': 30, 'month_num': 6, 'themes': ['summer_prep', 'fitness', 'outdoor']},
            'july': {'days': 31, 'month_num': 7, 'themes': ['summer_peak', 'vacation', 'active']},
            'august': {'days': 31, 'month_num': 8, 'themes': ['back_to_school', 'fitness', 'casual']},
            'september': {'days': 30, 'month_num': 9, 'themes': ['fall_prep', 'layering', 'cozy']}
        }
        
        if month not in month_config:
            logger.error(f"Invalid month: {month}")
            return
        
        config = month_config[month]
        created_orders = 0
        
        for i in range(orders_needed):
            try:
                # Random date in month
                day = random.randint(1, config['days'])
                hour = random.randint(8, 22)  # Business hours
                minute = random.randint(0, 59)
                
                order_date = datetime(base_year, config['month_num'], day, hour, minute)
                
                # Select random customer and products
                customer_id = random.choice(self.customers)
                num_items = random.randint(1, 4)  # 1-4 items per order
                
                # Create order lines
                order_lines = []
                order_total = 0
                
                for j in range(num_items):
                    product_id = random.choice(self.products)
                    quantity = random.randint(1, 3)
                    
                    # Seasonal pricing adjustments
                    base_price = random.uniform(20, 80)
                    if month == 'july':  # Summer peak - higher prices
                        price = base_price * random.uniform(1.1, 1.3)
                    elif month == 'september':  # Fall prep - moderate prices
                        price = base_price * random.uniform(0.95, 1.15)
                    else:
                        price = base_price * random.uniform(0.9, 1.2)
                    
                    line_total = quantity * price
                    order_total += line_total
                    
                    order_lines.append((0, 0, {
                        'product_id': product_id,
                        'product_uom_qty': quantity,
                        'price_unit': round(price, 2)
                    }))
                
                # Select random team
                team_id = random.choice(self.teams) if self.teams else False
                
                # Create the order
                order_data = {
                    'partner_id': customer_id,
                    'date_order': order_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'state': 'sale',
                    'team_id': team_id,
                    'order_line': order_lines
                }
                
                order_id = self.models.execute_kw(
                    self.db, self.uid, self.password,
                    'sale.order', 'create',
                    [order_data]
                )
                
                created_orders += 1
                if created_orders % 10 == 0:
                    logger.info(f"  Created {created_orders}/{orders_needed} orders for {month.title()}")
                    
            except Exception as e:
                logger.error(f"Error creating order for {month}: {e}")
                continue
        
        logger.info(f"✅ Created {created_orders} seasonal orders for {month.title()}")
        return created_orders
    
    def fix_seasonal_distribution(self):
        """Fix the seasonal distribution to match targets"""
        logger.info("🌞 Starting seasonal distribution fix...")
        
        # Load reference data
        self.load_reference_data()
        
        # Get current distribution
        monthly_totals, total_summer = self.get_current_summer_orders()
        
        if total_summer == 0:
            logger.error("No summer orders found!")
            return
        
        # Calculate target amounts
        logger.info("\n📊 Target vs Current Analysis:")
        for month in ['june', 'july', 'august', 'september']:
            current_amount = monthly_totals[month]['total']
            current_percentage = (current_amount / total_summer * 100)
            target_percentage = self.target_distribution[month]
            
            logger.info(f"{month.title()}:")
            logger.info(f"  Current: ${current_amount:,.2f} ({current_percentage:.1f}%)")
            logger.info(f"  Target:  {target_percentage:.1f}%")
            
            # For months that need boosting, create additional orders
            if current_percentage < target_percentage - 2:  # 2% tolerance
                target_amount = (total_summer * target_percentage / 100)
                additional_needed = target_amount - current_amount
                
                if additional_needed > 1000:  # Only if significant amount needed
                    logger.info(f"  📈 Need to add: ${additional_needed:,.2f}")
                    self.create_seasonal_orders(month, additional_needed)
        
        logger.info("✅ Seasonal distribution fix completed!")

def main():
    fixer = SeasonalDistributionFixer()
    fixer.fix_seasonal_distribution()

if __name__ == "__main__":
    main()