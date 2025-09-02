#!/usr/bin/env python3
"""
Comprehensive Inventory Analysis Script for Odoo
================================================

This script performs detailed inventory analysis including:
- Current stock levels for all products
- Inventory valuation and reporting
- Products with/without inventory
- Recommended stock levels by category
- Inventory movement analysis

Agent: Inventory Analysis Specialist
"""

import xmlrpc.client
import os
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('inventory_analysis.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class InventoryItem:
    """Represents an inventory item with all relevant data"""
    product_id: int
    product_name: str
    default_code: str
    category: str
    quantity: float
    unit_of_measure: str
    inventory_value: float
    cost_price: float
    sale_price: float
    location: str
    last_movement_date: Optional[str]
    reorder_point: float
    max_stock: float
    reserved_qty: float
    available_qty: float

@dataclass
class InventoryReport:
    """Complete inventory analysis report"""
    total_products: int
    products_with_inventory: int
    products_without_inventory: int
    total_inventory_value: float
    categories: Dict[str, dict]
    low_stock_items: List[dict]
    out_of_stock_items: List[dict]
    overstocked_items: List[dict]
    recommendations: List[str]
    analysis_date: str

class OdooInventoryAnalyzer:
    """
    Comprehensive Inventory Analyzer for Odoo
    =========================================
    
    Connects to Odoo and performs detailed inventory analysis
    including stock levels, valuation, and recommendations.
    """
    
    def __init__(self):
        self.url = os.getenv('ODOO_URL', 'https://source-gym-plus-coffee.odoo.com')
        self.db = os.getenv('ODOO_DB', 'source-gym-plus-coffee')
        self.username = os.getenv('ODOO_USERNAME', 'admin@quickfindai.com')
        self.password = os.getenv('ODOO_PASSWORD', 'BJ62wX2J4yzjS$i')
        
        self.common = None
        self.models = None
        self.uid = None
        
        logger.info("Inventory Analyzer initialized")
    
    def connect(self) -> bool:
        """
        Establish connection to Odoo
        
        Returns:
            bool: True if connection successful
        """
        try:
            logger.info(f"Connecting to Odoo at {self.url}")
            
            # Create connection
            self.common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
            
            # Test version
            version = self.common.version()
            logger.info(f"Connected to Odoo version: {version.get('server_version', 'Unknown')}")
            
            # Authenticate
            self.uid = self.common.authenticate(self.db, self.username, self.password, {})
            
            if self.uid:
                logger.info(f"Authentication successful! UID: {self.uid}")
                
                # Create models proxy
                self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")
                return True
            else:
                logger.error("Authentication failed!")
                return False
                
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    def get_all_products(self) -> List[dict]:
        """
        Get all products with detailed information
        
        Returns:
            List of product dictionaries
        """
        try:
            logger.info("Fetching all products...")
            
            # First, check what types of products exist
            all_product_ids = self.models.execute_kw(
                self.db, self.uid, self.password,
                'product.product', 'search',
                [[]]  # All products
            )
            
            if all_product_ids:
                # Get product types
                all_products_info = self.models.execute_kw(
                    self.db, self.uid, self.password,
                    'product.product', 'read',
                    [all_product_ids[:10]],  # Check first 10 to see types
                    {'fields': ['name', 'type', 'active']}
                )
                
                product_types = {}
                for prod in all_products_info:
                    product_type = prod.get('type', 'unknown')
                    product_types[product_type] = product_types.get(product_type, 0) + 1
                
                logger.info(f"Found {len(all_product_ids)} total products with types: {product_types}")
            
            # Search for stockable products
            product_ids = self.models.execute_kw(
                self.db, self.uid, self.password,
                'product.product', 'search',
                [[['type', '=', 'product']]]  # Only stockable products
            )
            
            logger.info(f"Found {len(product_ids)} stockable products")
            
            if not product_ids:
                logger.warning("No stockable products found. Checking for service products...")
                # If no stockable products, try to get service products for info
                service_ids = self.models.execute_kw(
                    self.db, self.uid, self.password,
                    'product.product', 'search',
                    [[['type', '=', 'service']]]
                )
                logger.info(f"Found {len(service_ids)} service products")
                return []
            
            # Get product details
            products = self.models.execute_kw(
                self.db, self.uid, self.password,
                'product.product', 'read',
                [product_ids],
                {
                    'fields': [
                        'name', 'default_code', 'categ_id', 'standard_price',
                        'list_price', 'uom_id', 'qty_available', 'virtual_available',
                        'incoming_qty', 'outgoing_qty', 'reordering_min_qty',
                        'reordering_max_qty', 'cost_method', 'valuation', 'type'
                    ]
                }
            )
            
            return products
            
        except Exception as e:
            logger.error(f"Error fetching products: {e}")
            return []
    
    def get_stock_quants(self) -> List[dict]:
        """
        Get all stock quants (inventory records)
        
        Returns:
            List of stock quant dictionaries
        """
        try:
            logger.info("Fetching stock quants...")
            
            # Search for all stock quants with quantity > 0
            quant_ids = self.models.execute_kw(
                self.db, self.uid, self.password,
                'stock.quant', 'search',
                [[]]
            )
            
            logger.info(f"Found {len(quant_ids)} stock quant records")
            
            # Get quant details
            quants = self.models.execute_kw(
                self.db, self.uid, self.password,
                'stock.quant', 'read',
                [quant_ids],
                {
                    'fields': [
                        'product_id', 'location_id', 'quantity', 'reserved_quantity',
                        'available_quantity', 'inventory_quantity', 'inventory_date',
                        'create_date', 'write_date'
                    ]
                }
            )
            
            return quants
            
        except Exception as e:
            logger.error(f"Error fetching stock quants: {e}")
            return []
    
    def get_product_categories(self) -> Dict[int, str]:
        """
        Get all product categories
        
        Returns:
            Dictionary mapping category ID to category name
        """
        try:
            logger.info("Fetching product categories...")
            
            category_ids = self.models.execute_kw(
                self.db, self.uid, self.password,
                'product.category', 'search',
                [[]]
            )
            
            categories = self.models.execute_kw(
                self.db, self.uid, self.password,
                'product.category', 'read',
                [category_ids],
                {'fields': ['name', 'complete_name']}
            )
            
            return {cat['id']: cat['complete_name'] for cat in categories}
            
        except Exception as e:
            logger.error(f"Error fetching categories: {e}")
            return {}
    
    def get_stock_locations(self) -> Dict[int, str]:
        """
        Get all stock locations
        
        Returns:
            Dictionary mapping location ID to location name
        """
        try:
            logger.info("Fetching stock locations...")
            
            location_ids = self.models.execute_kw(
                self.db, self.uid, self.password,
                'stock.location', 'search',
                [[['usage', '=', 'internal']]]  # Only internal locations
            )
            
            locations = self.models.execute_kw(
                self.db, self.uid, self.password,
                'stock.location', 'read',
                [location_ids],
                {'fields': ['name', 'complete_name']}
            )
            
            return {loc['id']: loc['complete_name'] for loc in locations}
            
        except Exception as e:
            logger.error(f"Error fetching locations: {e}")
            return {}
    
    def get_recent_stock_moves(self, days: int = 30) -> List[dict]:
        """
        Get recent stock movements for analysis
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of stock move dictionaries
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            logger.info(f"Fetching stock moves since {cutoff_date}...")
            
            move_ids = self.models.execute_kw(
                self.db, self.uid, self.password,
                'stock.move', 'search',
                [[
                    ['date', '>=', cutoff_date],
                    ['state', '=', 'done']
                ]]
            )
            
            if move_ids:
                moves = self.models.execute_kw(
                    self.db, self.uid, self.password,
                    'stock.move', 'read',
                    [move_ids],
                    {
                        'fields': [
                            'product_id', 'quantity_done', 'date',
                            'location_id', 'location_dest_id', 'origin',
                            'picking_type_id'
                        ]
                    }
                )
                return moves
            
            return []
            
        except Exception as e:
            logger.error(f"Error fetching stock moves: {e}")
            return []
    
    def analyze_inventory(self) -> InventoryReport:
        """
        Perform comprehensive inventory analysis
        
        Returns:
            Complete inventory analysis report
        """
        logger.info("Starting comprehensive inventory analysis...")
        
        # Get basic data
        products = self.get_all_products()
        quants = self.get_stock_quants()
        categories = self.get_product_categories()
        locations = self.get_stock_locations()
        recent_moves = self.get_recent_stock_moves()
        
        # Build inventory items
        inventory_items = []
        quant_by_product = defaultdict(list)
        
        # Group quants by product
        for quant in quants:
            if quant['product_id']:
                quant_by_product[quant['product_id'][0]].append(quant)
        
        # Process each product
        products_with_inventory = 0
        products_without_inventory = 0
        total_inventory_value = 0.0
        category_stats = defaultdict(lambda: {
            'products': 0,
            'with_inventory': 0,
            'total_value': 0.0,
            'total_quantity': 0.0
        })
        
        low_stock_items = []
        out_of_stock_items = []
        overstocked_items = []
        
        for product in products:
            product_id = product['id']
            category_name = categories.get(product['categ_id'][0], 'Unknown') if product['categ_id'] else 'Unknown'
            
            # Calculate totals for this product across all locations
            total_qty = product.get('qty_available', 0.0)
            reserved_qty = total_qty - product.get('virtual_available', 0.0)
            available_qty = product.get('virtual_available', 0.0)
            
            cost_price = product.get('standard_price', 0.0)
            sale_price = product.get('list_price', 0.0)
            inventory_value = total_qty * cost_price
            
            # Get reordering rules
            reorder_point = product.get('reordering_min_qty', 0.0) or 0.0
            max_stock = product.get('reordering_max_qty', 0.0) or 0.0
            
            # Find primary location for this product
            primary_location = "Multiple Locations"
            if product_id in quant_by_product:
                main_quant = max(quant_by_product[product_id], key=lambda q: q['quantity'])
                if main_quant['location_id']:
                    primary_location = locations.get(main_quant['location_id'][0], 'Unknown Location')
            
            # Create inventory item
            inventory_item = InventoryItem(
                product_id=product_id,
                product_name=product['name'],
                default_code=product.get('default_code') or '',
                category=category_name,
                quantity=total_qty,
                unit_of_measure=product['uom_id'][1] if product['uom_id'] else 'Unit',
                inventory_value=inventory_value,
                cost_price=cost_price,
                sale_price=sale_price,
                location=primary_location,
                last_movement_date=None,  # Could be enhanced with move data
                reorder_point=reorder_point,
                max_stock=max_stock,
                reserved_qty=reserved_qty,
                available_qty=available_qty
            )
            
            inventory_items.append(inventory_item)
            
            # Update counters
            if total_qty > 0:
                products_with_inventory += 1
                total_inventory_value += inventory_value
            else:
                products_without_inventory += 1
            
            # Update category statistics
            category_stats[category_name]['products'] += 1
            if total_qty > 0:
                category_stats[category_name]['with_inventory'] += 1
                category_stats[category_name]['total_value'] += inventory_value
                category_stats[category_name]['total_quantity'] += total_qty
            
            # Identify stock issues
            if total_qty <= 0:
                out_of_stock_items.append({
                    'product_name': product['name'],
                    'product_code': product.get('default_code') or '',
                    'category': category_name,
                    'quantity': total_qty
                })
            elif reorder_point > 0 and total_qty <= reorder_point:
                low_stock_items.append({
                    'product_name': product['name'],
                    'product_code': product.get('default_code') or '',
                    'category': category_name,
                    'current_qty': total_qty,
                    'reorder_point': reorder_point,
                    'shortage': reorder_point - total_qty
                })
            elif max_stock > 0 and total_qty > max_stock:
                overstocked_items.append({
                    'product_name': product['name'],
                    'product_code': product.get('default_code') or '',
                    'category': category_name,
                    'current_qty': total_qty,
                    'max_stock': max_stock,
                    'excess': total_qty - max_stock
                })
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            len(products), products_with_inventory, products_without_inventory,
            len(low_stock_items), len(out_of_stock_items), len(overstocked_items),
            category_stats
        )
        
        # Create final report
        report = InventoryReport(
            total_products=len(products),
            products_with_inventory=products_with_inventory,
            products_without_inventory=products_without_inventory,
            total_inventory_value=total_inventory_value,
            categories=dict(category_stats),
            low_stock_items=low_stock_items[:20],  # Top 20 items
            out_of_stock_items=out_of_stock_items[:20],
            overstocked_items=overstocked_items[:20],
            recommendations=recommendations,
            analysis_date=datetime.now().isoformat()
        )
        
        logger.info("Inventory analysis completed successfully")
        return report
    
    def _generate_recommendations(self, total_products: int, with_inventory: int, 
                                without_inventory: int, low_stock_count: int,
                                out_of_stock_count: int, overstock_count: int,
                                category_stats: dict) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        # Stock level recommendations
        if out_of_stock_count > 0:
            recommendations.append(
                f"URGENT: {out_of_stock_count} products are out of stock. "
                "Prioritize restocking to avoid sales disruption."
            )
        
        if low_stock_count > 0:
            recommendations.append(
                f"WARNING: {low_stock_count} products are below reorder point. "
                "Review and restock these items soon."
            )
        
        if overstock_count > 0:
            recommendations.append(
                f"OPTIMIZE: {overstock_count} products are overstocked. "
                "Consider promotions or redistribution to optimize cash flow."
            )
        
        # Inventory coverage recommendations
        coverage_ratio = with_inventory / total_products if total_products > 0 else 0
        if total_products > 0 and coverage_ratio < 0.7:
            recommendations.append(
                f"COVERAGE: Only {coverage_ratio:.1%} of products have inventory. "
                "Review product catalog and stocking strategy."
            )
        elif total_products == 0:
            recommendations.append(
                "NO PRODUCTS: No stockable products found in the database. "
                "Check product configuration or import products first."
            )
        
        # Category-specific recommendations
        zero_inventory_categories = [
            cat for cat, stats in category_stats.items() 
            if stats['with_inventory'] == 0 and stats['products'] > 0
        ]
        
        if zero_inventory_categories:
            recommendations.append(
                f"CATEGORIES: {len(zero_inventory_categories)} categories have no inventory: "
                f"{', '.join(zero_inventory_categories[:3])}{'...' if len(zero_inventory_categories) > 3 else ''}"
            )
        
        # Value concentration
        top_categories = sorted(
            category_stats.items(), 
            key=lambda x: x[1]['total_value'], 
            reverse=True
        )[:3]
        
        if top_categories:
            recommendations.append(
                f"VALUE FOCUS: Top inventory value categories are "
                f"{', '.join([cat for cat, _ in top_categories])}. "
                "Ensure adequate monitoring and control for these high-value items."
            )
        
        # General recommendations
        if not recommendations:
            recommendations.append("EXCELLENT: Inventory levels appear well-managed across all categories.")
        
        return recommendations

def print_inventory_report(report: InventoryReport):
    """Print formatted inventory report to console"""
    
    print("\n" + "="*80)
    print("📊 COMPREHENSIVE INVENTORY ANALYSIS REPORT")
    print("="*80)
    print(f"Analysis Date: {report.analysis_date}")
    print(f"Generated by: Inventory Analysis Specialist")
    
    print(f"\n📈 INVENTORY OVERVIEW")
    print("-" * 40)
    print(f"Total Products (Stockable):     {report.total_products:,}")
    
    if report.total_products > 0:
        print(f"Products with Inventory:        {report.products_with_inventory:,} ({report.products_with_inventory/report.total_products*100:.1f}%)")
        print(f"Products without Inventory:     {report.products_without_inventory:,} ({report.products_without_inventory/report.total_products*100:.1f}%)")
    else:
        print(f"Products with Inventory:        {report.products_with_inventory:,} (N/A - No products)")
        print(f"Products without Inventory:     {report.products_without_inventory:,} (N/A - No products)")
    
    print(f"Total Inventory Value:          ${report.total_inventory_value:,.2f}")
    
    print(f"\n🎯 STOCK ALERTS")
    print("-" * 40)
    print(f"Out of Stock Items:             {len(report.out_of_stock_items)}")
    print(f"Low Stock Items:                {len(report.low_stock_items)}")
    print(f"Overstocked Items:              {len(report.overstocked_items)}")
    
    print(f"\n📂 CATEGORY BREAKDOWN")
    print("-" * 60)
    print(f"{'Category':<30} {'Products':<10} {'With Inv':<10} {'Value':<15}")
    print("-" * 60)
    
    sorted_categories = sorted(
        report.categories.items(), 
        key=lambda x: x[1]['total_value'], 
        reverse=True
    )
    
    for category, stats in sorted_categories[:10]:  # Top 10 categories
        print(f"{category[:29]:<30} {stats['products']:<10} {stats['with_inventory']:<10} ${stats['total_value']:>12,.2f}")
    
    if len(report.out_of_stock_items) > 0:
        print(f"\n❌ OUT OF STOCK ITEMS (Top {min(10, len(report.out_of_stock_items))})")
        print("-" * 80)
        print(f"{'Product Name':<40} {'Code':<15} {'Category':<20}")
        print("-" * 80)
        for item in report.out_of_stock_items[:10]:
            print(f"{item['product_name'][:39]:<40} {item['product_code'][:14]:<15} {item['category'][:19]:<20}")
    
    if len(report.low_stock_items) > 0:
        print(f"\n⚠️  LOW STOCK ITEMS (Top {min(10, len(report.low_stock_items))})")
        print("-" * 90)
        print(f"{'Product Name':<35} {'Code':<12} {'Current':<8} {'Reorder':<8} {'Shortage':<8}")
        print("-" * 90)
        for item in report.low_stock_items[:10]:
            print(f"{item['product_name'][:34]:<35} {item['product_code'][:11]:<12} {item['current_qty']:<8.1f} {item['reorder_point']:<8.1f} {item['shortage']:<8.1f}")
    
    if len(report.overstocked_items) > 0:
        print(f"\n📈 OVERSTOCKED ITEMS (Top {min(10, len(report.overstocked_items))})")
        print("-" * 90)
        print(f"{'Product Name':<35} {'Code':<12} {'Current':<8} {'Max':<8} {'Excess':<8}")
        print("-" * 90)
        for item in report.overstocked_items[:10]:
            print(f"{item['product_name'][:34]:<35} {item['product_code'][:11]:<12} {item['current_qty']:<8.1f} {item['max_stock']:<8.1f} {item['excess']:<8.1f}")
    
    print(f"\n💡 RECOMMENDATIONS")
    print("-" * 80)
    for i, recommendation in enumerate(report.recommendations, 1):
        print(f"{i}. {recommendation}")
    
    print("\n" + "="*80)
    print("📋 Report completed successfully!")
    print("="*80)

def save_detailed_report(report: InventoryReport, filename: str = None):
    """Save detailed report to JSON file"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"inventory_analysis_{timestamp}.json"
    
    try:
        # Convert report to dictionary
        report_dict = asdict(report)
        
        with open(filename, 'w') as f:
            json.dump(report_dict, f, indent=2, default=str)
        
        logger.info(f"Detailed report saved to {filename}")
        print(f"\n📄 Detailed analysis saved to: {filename}")
        
    except Exception as e:
        logger.error(f"Error saving report: {e}")

def main():
    """Main execution function"""
    print("🚀 Starting Comprehensive Odoo Inventory Analysis...")
    print("=" * 60)
    
    # Initialize analyzer
    analyzer = OdooInventoryAnalyzer()
    
    # Connect to Odoo
    if not analyzer.connect():
        print("❌ Failed to connect to Odoo. Please check your credentials.")
        return
    
    try:
        # Perform analysis
        report = analyzer.analyze_inventory()
        
        # Display report
        print_inventory_report(report)
        
        # Save detailed report
        save_detailed_report(report)
        
        print("\n✅ Inventory analysis completed successfully!")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        print(f"❌ Analysis failed: {e}")

if __name__ == "__main__":
    main()