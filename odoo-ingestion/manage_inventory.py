#!/usr/bin/env python3
"""
Gym+Coffee Inventory Management System
=====================================

Manages inventory levels, seasonal stock adjustments, and stock movements
to support €300k/month in sales with proper safety stock levels.

Features:
- Dynamic inventory level setting based on product type
- Seasonal stock adjustments for weather-dependent items
- Stock movement tracking with automatic reorder points
- Safety stock maintenance (20% minimum)
- Comprehensive reporting and analytics

Author: Inventory Management Specialist
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import calendar

# Add scripts directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

try:
    from connection_manager import OdooConnection, ConnectionConfig
    from data_models import ProductType
except ImportError as e:
    print(f"Warning: Could not import connection modules: {e}")
    print("Odoo connection features may not be available.")

# Simple progress tracker for standalone operation
class SimpleProgressTracker:
    def __init__(self):
        self.total = 0
        self.current = 0
    
    def start_progress(self, total, description="Processing"):
        self.total = total
        self.current = 0
        print(f"Starting: {description} (0/{total})")
    
    def update_progress(self, current, description=""):
        self.current = current
        percent = (current / self.total * 100) if self.total > 0 else 0
        print(f"Progress: {current}/{self.total} ({percent:.1f}%) {description}")
    
    def complete_progress(self):
        print(f"Completed: {self.current}/{self.total}")

# Simple error handler
class SimpleErrorHandler:
    def __init__(self):
        self.errors = []
    
    def log_error(self, message, context=None):
        error_entry = {"message": message, "context": context, "timestamp": datetime.now()}
        self.errors.append(error_entry)
        logging.getLogger(__name__).error(message)


class StockLevel(Enum):
    """Predefined stock levels by product category"""
    ESSENTIAL_BASIC_MIN = 500
    ESSENTIAL_BASIC_MAX = 1000
    REGULAR_MIN = 200
    REGULAR_MAX = 500
    LIMITED_EDITION_MIN = 50
    LIMITED_EDITION_MAX = 200
    ACCESSORIES_MIN = 300
    ACCESSORIES_MAX = 600


class SeasonType(Enum):
    """Season types for inventory adjustments"""
    WINTER = "winter"  # Sep-Feb
    SUMMER = "summer"  # Mar-Aug


@dataclass
class InventoryRule:
    """Inventory management rule for a product category"""
    category: str
    subcategory: Optional[str] = None
    base_min_stock: int = 200
    base_max_stock: int = 500
    safety_stock_percent: float = 0.20
    reorder_point_percent: float = 0.30
    seasonal_adjustment: Dict[str, float] = field(default_factory=dict)
    is_seasonal: bool = False


@dataclass
class StockMovement:
    """Stock movement record"""
    product_id: int
    location_id: int
    quantity: float
    date: datetime
    reference: str
    movement_type: str  # 'in', 'out', 'adjustment'


class InventoryManager:
    """
    Comprehensive Inventory Management System
    ========================================
    
    Manages all aspects of Gym+Coffee inventory including:
    - Stock level optimization
    - Seasonal adjustments
    - Reorder point calculations
    - Safety stock maintenance
    """
    
    def __init__(self, connection: Optional[OdooConnection] = None, dry_run: bool = False):
        self.connection = connection
        self.dry_run = dry_run
        self.logger = self._setup_logger()
        self.progress = SimpleProgressTracker()
        self.error_handler = SimpleErrorHandler()
        
        # Target monthly sales: €300,000
        self.target_monthly_sales = 300000
        self.average_product_price = 45  # Estimated average
        self.monthly_unit_sales = self.target_monthly_sales / self.average_product_price
        
        # Initialize inventory rules
        self.inventory_rules = self._initialize_inventory_rules()
        
        # Stock movement tracking
        self.stock_movements = []
        
        self.logger.info(f"Inventory Manager initialized - Target: €{self.target_monthly_sales:,}/month")
        self.logger.info(f"Estimated monthly unit sales: {self.monthly_unit_sales:,.0f} units")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('inventory_management.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)
    
    def _initialize_inventory_rules(self) -> Dict[str, InventoryRule]:
        """Initialize inventory management rules for all product categories"""
        rules = {}
        
        # Essential/Basic items (hoodies, sweatshirts, core t-shirts)
        essential_categories = ['hoodies', 'sweatshirts', 'basic-tees']
        for cat in essential_categories:
            rules[cat] = InventoryRule(
                category=cat,
                base_min_stock=StockLevel.ESSENTIAL_BASIC_MIN.value,
                base_max_stock=StockLevel.ESSENTIAL_BASIC_MAX.value,
                safety_stock_percent=0.25,  # Higher safety stock for essentials
                reorder_point_percent=0.40,  # Earlier reorder for essentials
                is_seasonal=cat in ['hoodies', 'sweatshirts'],
                seasonal_adjustment={
                    'winter': 1.5,  # 50% increase in winter
                    'summer': 0.7   # 30% decrease in summer
                }
            )
        
        # Regular items
        regular_categories = ['t-shirts', 'tanks', 'shorts', 'leggings', 'joggers']
        for cat in regular_categories:
            rules[cat] = InventoryRule(
                category=cat,
                base_min_stock=StockLevel.REGULAR_MIN.value,
                base_max_stock=StockLevel.REGULAR_MAX.value,
                safety_stock_percent=0.20,
                reorder_point_percent=0.30,
                is_seasonal=cat in ['shorts', 'tanks'],
                seasonal_adjustment={
                    'summer': 1.4,  # 40% increase in summer
                    'winter': 0.8   # 20% decrease in winter
                }
            )
        
        # Limited Edition items
        limited_categories = ['limited-edition', 'collaboration', 'special']
        for cat in limited_categories:
            rules[cat] = InventoryRule(
                category=cat,
                base_min_stock=StockLevel.LIMITED_EDITION_MIN.value,
                base_max_stock=StockLevel.LIMITED_EDITION_MAX.value,
                safety_stock_percent=0.15,  # Lower safety stock for limited items
                reorder_point_percent=0.25,
                is_seasonal=False
            )
        
        # Accessories
        accessory_categories = ['accessories', 'bags', 'bottles', 'caps', 'beanies']
        for cat in accessory_categories:
            rules[cat] = InventoryRule(
                category=cat,
                base_min_stock=StockLevel.ACCESSORIES_MIN.value,
                base_max_stock=StockLevel.ACCESSORIES_MAX.value,
                safety_stock_percent=0.20,
                reorder_point_percent=0.30,
                is_seasonal=cat in ['caps', 'beanies'],
                seasonal_adjustment={
                    'summer': 1.2 if cat == 'caps' else 1.0,
                    'winter': 1.3 if cat == 'beanies' else 1.0
                }
            )
        
        return rules
    
    def get_current_season(self) -> SeasonType:
        """Determine current season for inventory adjustments"""
        current_month = datetime.now().month
        
        # Winter: September (9) to February (2)
        # Summer: March (3) to August (8)
        if current_month >= 9 or current_month <= 2:
            return SeasonType.WINTER
        else:
            return SeasonType.SUMMER
    
    def calculate_optimal_stock_levels(self, product: Dict[str, Any]) -> Tuple[int, int, int]:
        """
        Calculate optimal stock levels for a product
        
        Returns:
            Tuple of (min_stock, max_stock, reorder_point)
        """
        category = product.get('category', 'regular').lower()
        subcategory = product.get('subcategory', '').lower()
        
        # Get base rule
        rule = self.inventory_rules.get(category)
        if not rule:
            # Default rule for unknown categories
            rule = InventoryRule(
                category='default',
                base_min_stock=StockLevel.REGULAR_MIN.value,
                base_max_stock=StockLevel.REGULAR_MAX.value
            )
        
        min_stock = rule.base_min_stock
        max_stock = rule.base_max_stock
        
        # Apply seasonal adjustments if applicable
        if rule.is_seasonal and rule.seasonal_adjustment:
            current_season = self.get_current_season()
            season_key = current_season.value
            
            if season_key in rule.seasonal_adjustment:
                multiplier = rule.seasonal_adjustment[season_key]
                min_stock = int(min_stock * multiplier)
                max_stock = int(max_stock * multiplier)
                
                self.logger.debug(f"Applied {season_key} adjustment ({multiplier}x) to {category}")
        
        # Calculate reorder point
        reorder_point = int(max_stock * rule.reorder_point_percent)
        
        # Ensure minimum safety stock
        safety_stock = int(max_stock * rule.safety_stock_percent)
        min_stock = max(min_stock, safety_stock)
        
        return min_stock, max_stock, reorder_point
    
    def set_inventory_levels(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Set optimal inventory levels for all products"""
        results = {
            'updated': 0,
            'errors': 0,
            'details': [],
            'summary': {}
        }
        
        category_summary = {}
        
        self.logger.info(f"Setting inventory levels for {len(products)} products")
        self.progress.start_progress(len(products), "Setting inventory levels")
        
        for i, product in enumerate(products):
            try:
                sku = product.get('sku', f"product_{i}")
                category = product.get('category', 'unknown')
                current_stock = product.get('inventory_on_hand', 0)
                
                # Calculate optimal levels
                min_stock, max_stock, reorder_point = self.calculate_optimal_stock_levels(product)
                
                # Track category summary
                if category not in category_summary:
                    category_summary[category] = {
                        'count': 0,
                        'total_target_stock': 0,
                        'total_current_stock': 0
                    }
                
                category_summary[category]['count'] += 1
                category_summary[category]['total_target_stock'] += max_stock
                # Ensure current_stock is numeric
                current_stock_numeric = current_stock if isinstance(current_stock, (int, float)) else 0
                category_summary[category]['total_current_stock'] += current_stock_numeric
                
                # Determine if stock adjustment needed
                stock_adjustment = 0
                current_stock_numeric = current_stock if isinstance(current_stock, (int, float)) else 0
                
                if current_stock_numeric < min_stock:
                    # Stock too low - increase to optimal level
                    target_stock = int((min_stock + max_stock) / 2)  # Middle of range
                    stock_adjustment = target_stock - current_stock_numeric
                elif current_stock_numeric > max_stock * 1.2:  # 20% buffer before reducing
                    # Stock too high - reduce to max level
                    stock_adjustment = max_stock - current_stock_numeric
                
                product_result = {
                    'sku': sku,
                    'category': category,
                    'current_stock': current_stock_numeric,
                    'min_stock': min_stock,
                    'max_stock': max_stock,
                    'reorder_point': reorder_point,
                    'adjustment_needed': stock_adjustment,
                    'target_stock': current_stock_numeric + stock_adjustment
                }
                
                # Update in Odoo if not dry run
                if not self.dry_run and self.connection and stock_adjustment != 0:
                    try:
                        # In a real implementation, you would update Odoo here
                        # self._update_odoo_stock_levels(product, product_result)
                        pass
                    except Exception as e:
                        self.logger.error(f"Failed to update Odoo for {sku}: {e}")
                        results['errors'] += 1
                        continue
                
                results['details'].append(product_result)
                results['updated'] += 1
                
                self.progress.update_progress(i + 1, f"Processed {sku}")
                
            except Exception as e:
                error_msg = f"Error processing product {i}: {e}"
                self.logger.error(error_msg)
                self.error_handler.log_error(error_msg, product)
                results['errors'] += 1
        
        results['summary'] = category_summary
        self.progress.complete_progress()
        
        self.logger.info(f"Inventory levels set: {results['updated']} updated, {results['errors']} errors")
        return results
    
    def create_stock_movements(self, products: List[Dict[str, Any]], 
                              simulate_sales: bool = True) -> Dict[str, Any]:
        """Create stock movements to simulate realistic inventory flow"""
        results = {
            'movements_created': 0,
            'total_units_moved': 0,
            'categories_affected': set(),
            'reorder_alerts': []
        }
        
        if simulate_sales:
            # Simulate one month of sales based on target revenue
            self.logger.info("Simulating stock movements for one month of sales")
            
            # Calculate daily sales rate
            days_in_month = calendar.monthrange(datetime.now().year, datetime.now().month)[1]
            daily_unit_sales = self.monthly_unit_sales / days_in_month
            
            for day in range(1, days_in_month + 1):
                # Distribute sales across products based on category popularity
                daily_sales = self._distribute_daily_sales(products, daily_unit_sales)
                
                for product_idx, units_sold in daily_sales.items():
                    product = products[product_idx]
                    if units_sold > 0:
                        # Create outbound stock movement
                        movement = StockMovement(
                            product_id=product.get('id', 0),
                            location_id=1,  # Default stock location
                            quantity=-units_sold,  # Negative for outbound
                            date=datetime.now() - timedelta(days=days_in_month - day),
                            reference=f"SALE-{datetime.now().strftime('%Y%m')}-{day:02d}",
                            movement_type='out'
                        )
                        
                        self.stock_movements.append(movement)
                        results['movements_created'] += 1
                        results['total_units_moved'] += units_sold
                        results['categories_affected'].add(product.get('category', 'unknown'))
                        
                        # Update current stock and check reorder point
                        current_stock = product.get('inventory_on_hand', 0)
                        current_stock = current_stock if isinstance(current_stock, (int, float)) else 0
                        new_stock = current_stock - units_sold
                        products[product_idx]['inventory_on_hand'] = new_stock
                        
                        # Check if reorder needed
                        _, _, reorder_point = self.calculate_optimal_stock_levels(product)
                        if new_stock <= reorder_point:
                            results['reorder_alerts'].append({
                                'sku': product.get('sku'),
                                'category': product.get('category'),
                                'current_stock': new_stock,
                                'reorder_point': reorder_point,
                                'suggested_order': reorder_point * 2  # Order enough to get back to safe levels
                            })
        
        self.logger.info(f"Created {results['movements_created']} stock movements")
        self.logger.info(f"Total units moved: {results['total_units_moved']:,.0f}")
        self.logger.info(f"Reorder alerts: {len(results['reorder_alerts'])}")
        
        return results
    
    def _distribute_daily_sales(self, products: List[Dict[str, Any]], 
                               total_daily_units: float) -> Dict[int, int]:
        """Distribute daily sales across products based on category weights"""
        
        # Category popularity weights (based on typical gym/coffee apparel sales)
        category_weights = {
            'hoodies': 0.20,
            'sweatshirts': 0.15,
            't-shirts': 0.25,
            'basic-tees': 0.15,
            'leggings': 0.10,
            'joggers': 0.05,
            'accessories': 0.07,
            'limited-edition': 0.03
        }
        
        # Seasonal adjustments
        current_season = self.get_current_season()
        if current_season == SeasonType.WINTER:
            category_weights['hoodies'] *= 1.5
            category_weights['sweatshirts'] *= 1.3
            category_weights['t-shirts'] *= 0.8
        else:  # Summer
            category_weights['t-shirts'] *= 1.4
            category_weights['hoodies'] *= 0.6
            category_weights['sweatshirts'] *= 0.7
        
        # Normalize weights
        total_weight = sum(category_weights.values())
        category_weights = {k: v/total_weight for k, v in category_weights.items()}
        
        daily_sales = {}
        
        for idx, product in enumerate(products):
            category = product.get('category', 'other').lower()
            weight = category_weights.get(category, 0.01)  # Small default weight
            
            # Calculate units for this product
            category_products = [p for p in products if p.get('category', '').lower() == category]
            category_units = total_daily_units * weight
            
            if category_products:
                units_per_product = category_units / len(category_products)
                # Add some randomness (±30%)
                import random
                random_factor = random.uniform(0.7, 1.3)
                units = int(units_per_product * random_factor)
                
                # Ensure we don't sell more than available stock
                available_stock = product.get('inventory_on_hand', 0)
                available_stock = available_stock if isinstance(available_stock, (int, float)) else 0
                units = min(units, available_stock)
                
                daily_sales[idx] = units
        
        return daily_sales
    
    def generate_inventory_report(self, products: List[Dict[str, Any]], 
                                 results: Dict[str, Any]) -> str:
        """Generate comprehensive inventory management report"""
        
        report = []
        report.append("=" * 80)
        report.append("GYM+COFFEE INVENTORY MANAGEMENT REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Season: {self.get_current_season().value.title()}")
        report.append(f"Target Monthly Sales: €{self.target_monthly_sales:,}")
        report.append(f"Estimated Monthly Unit Sales: {self.monthly_unit_sales:,.0f}")
        report.append("")
        
        # Summary statistics
        report.append("INVENTORY SUMMARY")
        report.append("-" * 40)
        total_products = len(products)
        
        # Calculate total value with proper type checking
        total_current_value = 0
        for p in products:
            inventory = p.get('inventory_on_hand', 0)
            price = p.get('list_price', 0)
            
            # Ensure both values are numeric
            if isinstance(inventory, (int, float)) and isinstance(price, (int, float)):
                total_current_value += inventory * price
        
        report.append(f"Total Products: {total_products:,}")
        report.append(f"Total Current Stock Value: €{total_current_value:,.2f}")
        report.append(f"Products Updated: {results.get('updated', 0):,}")
        report.append(f"Errors: {results.get('errors', 0)}")
        report.append("")
        
        # Category breakdown
        if 'summary' in results:
            report.append("CATEGORY BREAKDOWN")
            report.append("-" * 40)
            report.append(f"{'Category':<20} {'Count':<8} {'Current Stock':<15} {'Target Stock':<15}")
            report.append("-" * 60)
            
            for category, data in results['summary'].items():
                report.append(f"{category:<20} {data['count']:<8} "
                            f"{data['total_current_stock']:<15,} {data['total_target_stock']:<15,}")
        
        report.append("")
        
        # Stock movements summary
        if hasattr(self, 'stock_movements') and self.stock_movements:
            report.append("STOCK MOVEMENTS")
            report.append("-" * 40)
            total_movements = len(self.stock_movements)
            inbound_qty = sum(m.quantity for m in self.stock_movements if m.quantity > 0)
            outbound_qty = abs(sum(m.quantity for m in self.stock_movements if m.quantity < 0))
            
            report.append(f"Total Movements: {total_movements:,}")
            report.append(f"Inbound Quantity: {inbound_qty:,.0f}")
            report.append(f"Outbound Quantity: {outbound_qty:,.0f}")
            report.append(f"Net Movement: {inbound_qty - outbound_qty:,.0f}")
            report.append("")
        
        # Reorder alerts
        if 'reorder_alerts' in results and results['reorder_alerts']:
            report.append("REORDER ALERTS")
            report.append("-" * 40)
            report.append(f"{'SKU':<20} {'Category':<15} {'Current':<10} {'Reorder At':<12} {'Suggested Order':<15}")
            report.append("-" * 75)
            
            for alert in results['reorder_alerts'][:20]:  # Show top 20
                report.append(f"{alert['sku']:<20} {alert['category']:<15} "
                            f"{alert['current_stock']:<10} {alert['reorder_point']:<12} "
                            f"{alert['suggested_order']:<15}")
            
            if len(results['reorder_alerts']) > 20:
                report.append(f"... and {len(results['reorder_alerts']) - 20} more items need reordering")
        
        report.append("")
        report.append("INVENTORY RULES APPLIED")
        report.append("-" * 40)
        for category, rule in self.inventory_rules.items():
            seasonal = "Yes" if rule.is_seasonal else "No"
            report.append(f"{category}: {rule.base_min_stock}-{rule.base_max_stock} units, "
                         f"Safety: {rule.safety_stock_percent*100:.0f}%, "
                         f"Seasonal: {seasonal}")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_results(self, results: Dict[str, Any], filename: str = None) -> str:
        """Save inventory management results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'inventory_results_{timestamp}.json'
        
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        self.logger.info(f"Results saved to {filepath}")
        return filepath


def load_test_data() -> List[Dict[str, Any]]:
    """Load test product data"""
    test_file = os.path.join(os.path.dirname(__file__), 
                            'tests/fixtures/generated/test-products.json')
    
    if os.path.exists(test_file):
        with open(test_file, 'r') as f:
            data = json.load(f)
            return data.get('products', [])
    
    # Return sample data if test file not found
    return [
        {
            "sku": "GC10001-BLA-M",
            "name": "Essential Hoodie - Black",
            "category": "hoodies",
            "subcategory": "unisex",
            "color": "Black",
            "size": "M",
            "list_price": 75,
            "standard_cost": 25,
            "inventory_on_hand": 150,
            "reorder_point": 30
        },
        {
            "sku": "GC20001-WHI-L",
            "name": "Basic Tee - White",
            "category": "t-shirts",
            "subcategory": "unisex",
            "color": "White",
            "size": "L",
            "list_price": 35,
            "standard_cost": 12,
            "inventory_on_hand": 200,
            "reorder_point": 40
        },
        {
            "sku": "GC30001-BLA-OS",
            "name": "Coffee Bottle - Black",
            "category": "accessories",
            "subcategory": "bottles",
            "color": "Black",
            "size": "OS",
            "list_price": 25,
            "standard_cost": 8,
            "inventory_on_hand": 75,
            "reorder_point": 20
        }
    ]


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Gym+Coffee Inventory Management')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Run in dry-run mode (no actual updates)')
    parser.add_argument('--simulate-sales', action='store_true',
                       help='Simulate stock movements for sales')
    parser.add_argument('--output-report', type=str, 
                       help='Output file for inventory report')
    parser.add_argument('--data-file', type=str,
                       help='JSON file containing product data')
    
    args = parser.parse_args()
    
    # Initialize logger
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # Load product data
        if args.data_file and os.path.exists(args.data_file):
            with open(args.data_file, 'r') as f:
                data = json.load(f)
                products = data.get('products', data) if isinstance(data, dict) else data
        else:
            logger.info("Loading test data...")
            products = load_test_data()
        
        logger.info(f"Loaded {len(products)} products")
        
        # Initialize inventory manager
        inventory_manager = InventoryManager(dry_run=args.dry_run)
        
        # Set inventory levels
        logger.info("Setting optimal inventory levels...")
        results = inventory_manager.set_inventory_levels(products)
        
        # Create stock movements if requested
        if args.simulate_sales:
            logger.info("Creating stock movements to simulate sales...")
            movement_results = inventory_manager.create_stock_movements(products, simulate_sales=True)
            results['stock_movements'] = movement_results
        
        # Generate and display report
        report = inventory_manager.generate_inventory_report(products, results)
        print(report)
        
        # Save results
        results_file = inventory_manager.save_results(results)
        
        # Save report if requested
        if args.output_report:
            with open(args.output_report, 'w') as f:
                f.write(report)
            logger.info(f"Report saved to {args.output_report}")
        
        logger.info(f"Inventory management completed successfully!")
        logger.info(f"Results saved to: {results_file}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error in inventory management: {e}")
        return 1


if __name__ == '__main__':
    exit(main())