#!/usr/bin/env python3
"""
Complete Product & Inventory Analysis for Odoo
===============================================

This script analyzes ALL products (stockable, consumable, service) 
and provides comprehensive insights into the entire product catalog
and inventory management.

Agent: Complete Product Analysis Specialist
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
        logging.FileHandler('complete_product_analysis.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class CompleteProductAnalysis:
    """Complete product and inventory analysis report"""
    analysis_date: str
    
    # Product counts by type
    total_products: int
    stockable_products: int
    consumable_products: int
    service_products: int
    
    # Inventory analysis (for stockable/consumable)
    products_with_inventory: int
    products_without_inventory: int
    total_inventory_value: float
    
    # Category breakdown
    categories: Dict[str, dict]
    
    # Product type details
    product_type_details: Dict[str, dict]
    
    # Stock alerts
    low_stock_items: List[dict]
    out_of_stock_items: List[dict]
    overstocked_items: List[dict]
    
    # Business insights
    recommendations: List[str]
    
    # Raw data samples
    sample_products: List[dict]

class OdooCompleteAnalyzer:
    """
    Complete Product & Inventory Analyzer for Odoo
    ==============================================
    
    Analyzes all product types and provides comprehensive
    business insights for inventory management.
    """
    
    def __init__(self):
        self.url = os.getenv('ODOO_URL', 'https://source-gym-plus-coffee.odoo.com')
        self.db = os.getenv('ODOO_DB', 'source-gym-plus-coffee')
        self.username = os.getenv('ODOO_USERNAME', 'admin@quickfindai.com')
        self.password = os.getenv('ODOO_PASSWORD', 'BJ62wX2J4yzjS$i')
        
        self.common = None
        self.models = None
        self.uid = None
        
        logger.info("Complete Product Analyzer initialized")
    
    def connect(self) -> bool:
        """Establish connection to Odoo"""
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
    
    def get_all_products_by_type(self) -> Dict[str, List[dict]]:
        """Get all products organized by type"""
        try:
            logger.info("Analyzing all products by type...")
            
            products_by_type = {
                'product': [],     # Stockable
                'consu': [],       # Consumable
                'service': []      # Service
            }
            
            for product_type, products_list in products_by_type.items():
                # Search for products of this type
                product_ids = self.models.execute_kw(
                    self.db, self.uid, self.password,
                    'product.product', 'search',
                    [[['type', '=', product_type]]]
                )
                
                if product_ids:
                    logger.info(f"Found {len(product_ids)} {product_type} products")
                    
                    # Get product details in batches
                    batch_size = 100
                    for i in range(0, len(product_ids), batch_size):
                        batch_ids = product_ids[i:i+batch_size]
                        
                        batch_products = self.models.execute_kw(
                            self.db, self.uid, self.password,
                            'product.product', 'read',
                            [batch_ids],
                            {
                                'fields': [
                                    'name', 'default_code', 'categ_id', 'type',
                                    'standard_price', 'list_price', 'uom_id',
                                    'qty_available', 'virtual_available',
                                    'incoming_qty', 'outgoing_qty', 
                                    'reordering_min_qty', 'reordering_max_qty',
                                    'active', 'sale_ok', 'purchase_ok',
                                    'create_date', 'write_date'
                                ]
                            }
                        )
                        
                        products_list.extend(batch_products)
                else:
                    logger.info(f"No {product_type} products found")
            
            return products_by_type
            
        except Exception as e:
            logger.error(f"Error fetching products by type: {e}")
            return {'product': [], 'consu': [], 'service': []}
    
    def get_product_categories(self) -> Dict[int, str]:
        """Get all product categories"""
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
                {'fields': ['name', 'complete_name', 'parent_id']}
            )
            
            return {cat['id']: cat['complete_name'] for cat in categories}
            
        except Exception as e:
            logger.error(f"Error fetching categories: {e}")
            return {}
    
    def analyze_complete_inventory(self) -> CompleteProductAnalysis:
        """Perform complete product and inventory analysis"""
        logger.info("Starting complete product and inventory analysis...")
        
        # Get all data
        products_by_type = self.get_all_products_by_type()
        categories = self.get_product_categories()
        
        # Initialize counters
        total_products = sum(len(products) for products in products_by_type.values())
        stockable_products = len(products_by_type['product'])
        consumable_products = len(products_by_type['consu'])
        service_products = len(products_by_type['service'])
        
        products_with_inventory = 0
        products_without_inventory = 0
        total_inventory_value = 0.0
        
        # Category analysis
        category_stats = defaultdict(lambda: {
            'total_products': 0,
            'stockable': 0,
            'consumable': 0,
            'service': 0,
            'with_inventory': 0,
            'total_value': 0.0,
            'avg_price': 0.0
        })
        
        # Product type details
        product_type_details = {}
        
        # Stock alerts
        low_stock_items = []
        out_of_stock_items = []
        overstocked_items = []
        
        # Sample products for reference
        sample_products = []
        
        # Analyze each product type
        for product_type, products in products_by_type.items():
            type_stats = {
                'count': len(products),
                'with_inventory': 0,
                'total_value': 0.0,
                'avg_cost': 0.0,
                'avg_sale_price': 0.0,
                'categories': set()
            }
            
            total_cost = 0.0
            total_sale_price = 0.0
            
            for product in products[:5]:  # Sample first 5 products
                sample_products.append({
                    'name': product['name'],
                    'code': product.get('default_code') or '',
                    'type': product['type'],
                    'category': categories.get(product['categ_id'][0], 'Unknown') if product['categ_id'] else 'Unknown',
                    'cost_price': product.get('standard_price', 0.0),
                    'sale_price': product.get('list_price', 0.0),
                    'qty_available': product.get('qty_available', 0.0),
                    'active': product.get('active', True)
                })
            
            for product in products:
                category_name = categories.get(product['categ_id'][0], 'Unknown') if product['categ_id'] else 'Unknown'
                
                # Update category stats
                category_stats[category_name]['total_products'] += 1
                if product_type == 'product':
                    category_stats[category_name]['stockable'] += 1
                elif product_type == 'consu':
                    category_stats[category_name]['consumable'] += 1
                elif product_type == 'service':
                    category_stats[category_name]['service'] += 1
                
                type_stats['categories'].add(category_name)
                
                # For stockable and consumable products, analyze inventory
                if product_type in ['product', 'consu']:
                    qty_available = product.get('qty_available', 0.0)
                    cost_price = product.get('standard_price', 0.0)
                    sale_price = product.get('list_price', 0.0)
                    
                    total_cost += cost_price
                    total_sale_price += sale_price
                    
                    if qty_available > 0:
                        products_with_inventory += 1
                        type_stats['with_inventory'] += 1
                        inventory_value = qty_available * cost_price
                        total_inventory_value += inventory_value
                        type_stats['total_value'] += inventory_value
                        category_stats[category_name]['with_inventory'] += 1
                        category_stats[category_name]['total_value'] += inventory_value
                    else:
                        products_without_inventory += 1
                        
                        # Add to out of stock if it's supposed to have inventory
                        if product_type == 'product':  # Only stockable products
                            out_of_stock_items.append({
                                'product_name': product['name'],
                                'product_code': product.get('default_code') or '',
                                'category': category_name,
                                'type': product_type,
                                'cost_price': cost_price,
                                'sale_price': sale_price
                            })
                    
                    # Check for stock level issues
                    reorder_min = product.get('reordering_min_qty', 0.0) or 0.0
                    reorder_max = product.get('reordering_max_qty', 0.0) or 0.0
                    
                    if reorder_min > 0 and 0 < qty_available <= reorder_min:
                        low_stock_items.append({
                            'product_name': product['name'],
                            'product_code': product.get('default_code') or '',
                            'category': category_name,
                            'type': product_type,
                            'current_qty': qty_available,
                            'reorder_point': reorder_min,
                            'shortage': reorder_min - qty_available
                        })
                    
                    if reorder_max > 0 and qty_available > reorder_max:
                        overstocked_items.append({
                            'product_name': product['name'],
                            'product_code': product.get('default_code') or '',
                            'category': category_name,
                            'type': product_type,
                            'current_qty': qty_available,
                            'max_stock': reorder_max,
                            'excess': qty_available - reorder_max
                        })
            
            # Calculate averages
            if products:
                type_stats['avg_cost'] = total_cost / len(products)
                type_stats['avg_sale_price'] = total_sale_price / len(products)
                type_stats['categories'] = list(type_stats['categories'])
            
            product_type_details[product_type] = type_stats
        
        # Calculate category averages
        for category_name, stats in category_stats.items():
            if stats['total_products'] > 0:
                stats['avg_price'] = stats['total_value'] / max(stats['with_inventory'], 1)
        
        # Generate recommendations
        recommendations = self._generate_comprehensive_recommendations(
            total_products, stockable_products, consumable_products, service_products,
            products_with_inventory, products_without_inventory,
            len(low_stock_items), len(out_of_stock_items), len(overstocked_items),
            category_stats, product_type_details
        )
        
        # Create final analysis
        analysis = CompleteProductAnalysis(
            analysis_date=datetime.now().isoformat(),
            total_products=total_products,
            stockable_products=stockable_products,
            consumable_products=consumable_products,
            service_products=service_products,
            products_with_inventory=products_with_inventory,
            products_without_inventory=products_without_inventory,
            total_inventory_value=total_inventory_value,
            categories=dict(category_stats),
            product_type_details=product_type_details,
            low_stock_items=low_stock_items[:20],
            out_of_stock_items=out_of_stock_items[:20],
            overstocked_items=overstocked_items[:20],
            recommendations=recommendations,
            sample_products=sample_products[:20]
        )
        
        logger.info("Complete analysis finished successfully")
        return analysis
    
    def _generate_comprehensive_recommendations(self, total_products: int, stockable: int,
                                              consumable: int, service: int,
                                              with_inventory: int, without_inventory: int,
                                              low_stock_count: int, out_of_stock_count: int,
                                              overstock_count: int, category_stats: dict,
                                              type_details: dict) -> List[str]:
        """Generate comprehensive business recommendations"""
        recommendations = []
        
        # Product mix analysis
        if total_products > 0:
            consumable_ratio = consumable / total_products
            stockable_ratio = stockable / total_products
            service_ratio = service / total_products
            
            if consumable_ratio > 0.8:
                recommendations.append(
                    f"PRODUCT MIX: {consumable_ratio:.1%} of products are consumable. "
                    "Consider converting high-volume consumables to stockable for better inventory control."
                )
            
            if stockable_ratio < 0.1 and stockable > 0:
                recommendations.append(
                    f"INVENTORY CONTROL: Only {stockable_ratio:.1%} are stockable products. "
                    "Consider which consumables should be tracked as stockable inventory."
                )
            
            if service_ratio > 0.3:
                recommendations.append(
                    f"SERVICE FOCUS: {service_ratio:.1%} are services. "
                    "Ensure service pricing and delivery are optimized."
                )
        
        # Stock level recommendations
        if out_of_stock_count > 0:
            recommendations.append(
                f"URGENT: {out_of_stock_count} stockable products are out of stock. "
                "Immediate restocking required to avoid sales loss."
            )
        
        if low_stock_count > 0:
            recommendations.append(
                f"RESTOCK NEEDED: {low_stock_count} products below reorder point. "
                "Schedule procurement to maintain service levels."
            )
        
        if overstock_count > 0:
            recommendations.append(
                f"EXCESS INVENTORY: {overstock_count} products overstocked. "
                "Consider promotions or return policies to optimize cash flow."
            )
        
        # Category insights
        if category_stats:
            high_value_categories = sorted(
                [(cat, stats['total_value']) for cat, stats in category_stats.items()],
                key=lambda x: x[1], reverse=True
            )[:3]
            
            if high_value_categories and high_value_categories[0][1] > 0:
                recommendations.append(
                    f"HIGH VALUE CATEGORIES: Focus inventory control on "
                    f"{', '.join([cat for cat, _ in high_value_categories])} - "
                    "they represent the highest inventory investment."
                )
        
        # Operational recommendations
        total_trackable = stockable + consumable
        if total_trackable > 0:
            inventory_coverage = with_inventory / total_trackable
            if inventory_coverage < 0.5:
                recommendations.append(
                    f"INVENTORY COVERAGE: Only {inventory_coverage:.1%} of trackable products have stock. "
                    "Review purchasing processes and supplier relationships."
                )
        
        # Business optimization
        if 'consu' in type_details and type_details['consu']['count'] > 100:
            recommendations.append(
                "CONSUMABLE OPTIMIZATION: Large number of consumable products detected. "
                "Consider implementing automated reordering for high-turnover items."
            )
        
        if not recommendations:
            recommendations.append(
                "SYSTEM READY: Product catalog is configured. "
                "Consider setting up reorder rules for inventory automation."
            )
        
        return recommendations

def print_complete_analysis_report(analysis: CompleteProductAnalysis):
    """Print comprehensive analysis report"""
    
    print("\n" + "="*90)
    print("🏪 COMPLETE PRODUCT & INVENTORY ANALYSIS REPORT")
    print("="*90)
    print(f"Analysis Date: {analysis.analysis_date}")
    print(f"Generated by: Complete Product Analysis Specialist")
    
    print(f"\n📊 PRODUCT CATALOG OVERVIEW")
    print("-" * 50)
    print(f"Total Products in Catalog:      {analysis.total_products:,}")
    print(f"├─ Stockable Products:          {analysis.stockable_products:,} ({analysis.stockable_products/max(analysis.total_products,1)*100:.1f}%)")
    print(f"├─ Consumable Products:         {analysis.consumable_products:,} ({analysis.consumable_products/max(analysis.total_products,1)*100:.1f}%)")
    print(f"└─ Service Products:            {analysis.service_products:,} ({analysis.service_products/max(analysis.total_products,1)*100:.1f}%)")
    
    trackable_products = analysis.stockable_products + analysis.consumable_products
    if trackable_products > 0:
        print(f"\n📦 INVENTORY ANALYSIS (Stockable + Consumable)")
        print("-" * 50)
        print(f"Trackable Products:             {trackable_products:,}")
        print(f"├─ With Inventory:              {analysis.products_with_inventory:,} ({analysis.products_with_inventory/trackable_products*100:.1f}%)")
        print(f"└─ Without Inventory:           {analysis.products_without_inventory:,} ({analysis.products_without_inventory/trackable_products*100:.1f}%)")
        print(f"Total Inventory Value:          ${analysis.total_inventory_value:,.2f}")
    
    print(f"\n🚨 STOCK ALERTS")
    print("-" * 30)
    print(f"Out of Stock:                   {len(analysis.out_of_stock_items)}")
    print(f"Low Stock:                      {len(analysis.low_stock_items)}")
    print(f"Overstocked:                    {len(analysis.overstocked_items)}")
    
    # Product type details
    print(f"\n🔍 PRODUCT TYPE ANALYSIS")
    print("-" * 70)
    print(f"{'Type':<12} {'Count':<8} {'W/Inventory':<12} {'Avg Cost':<12} {'Avg Sale':<12}")
    print("-" * 70)
    
    type_names = {'product': 'Stockable', 'consu': 'Consumable', 'service': 'Service'}
    for type_key, details in analysis.product_type_details.items():
        type_name = type_names.get(type_key, type_key)
        print(f"{type_name:<12} {details['count']:<8} {details['with_inventory']:<12} ${details['avg_cost']:<11.2f} ${details['avg_sale_price']:<11.2f}")
    
    # Category breakdown
    if analysis.categories:
        print(f"\n📂 TOP CATEGORIES BY VALUE")
        print("-" * 80)
        print(f"{'Category':<35} {'Products':<10} {'W/Inv':<8} {'Value':<15}")
        print("-" * 80)
        
        sorted_categories = sorted(
            analysis.categories.items(), 
            key=lambda x: x[1]['total_value'], 
            reverse=True
        )
        
        for category, stats in sorted_categories[:10]:
            print(f"{category[:34]:<35} {stats['total_products']:<10} {stats['with_inventory']:<8} ${stats['total_value']:>12,.2f}")
    
    # Sample products
    if analysis.sample_products:
        print(f"\n📋 SAMPLE PRODUCTS")
        print("-" * 80)
        print(f"{'Name':<30} {'Type':<12} {'Code':<15} {'Cost':<10} {'Stock':<8}")
        print("-" * 80)
        for product in analysis.sample_products[:10]:
            print(f"{product['name'][:29]:<30} {product['type']:<12} {product['code'][:14]:<15} ${product['cost_price']:<9.2f} {product['qty_available']:<8.1f}")
    
    # Stock alerts details
    if analysis.out_of_stock_items:
        print(f"\n❌ OUT OF STOCK ITEMS (Top 10)")
        print("-" * 80)
        print(f"{'Product':<35} {'Type':<12} {'Code':<15} {'Category':<15}")
        print("-" * 80)
        for item in analysis.out_of_stock_items[:10]:
            print(f"{item['product_name'][:34]:<35} {item['type']:<12} {item['product_code'][:14]:<15} {item['category'][:14]:<15}")
    
    if analysis.low_stock_items:
        print(f"\n⚠️  LOW STOCK ITEMS (Top 10)")
        print("-" * 80)
        print(f"{'Product':<35} {'Current':<10} {'Reorder':<10} {'Shortage':<10}")
        print("-" * 80)
        for item in analysis.low_stock_items[:10]:
            print(f"{item['product_name'][:34]:<35} {item['current_qty']:<10.1f} {item['reorder_point']:<10.1f} {item['shortage']:<10.1f}")
    
    print(f"\n💡 BUSINESS RECOMMENDATIONS")
    print("-" * 80)
    for i, recommendation in enumerate(analysis.recommendations, 1):
        print(f"{i}. {recommendation}")
    
    print("\n" + "="*90)
    print("📋 Complete analysis finished!")
    print("="*90)

def save_complete_analysis(analysis: CompleteProductAnalysis, filename: str = None):
    """Save complete analysis to JSON file"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"complete_product_analysis_{timestamp}.json"
    
    try:
        # Convert analysis to dictionary
        analysis_dict = asdict(analysis)
        
        with open(filename, 'w') as f:
            json.dump(analysis_dict, f, indent=2, default=str)
        
        logger.info(f"Complete analysis saved to {filename}")
        print(f"\n📄 Complete analysis saved to: {filename}")
        
    except Exception as e:
        logger.error(f"Error saving analysis: {e}")

def main():
    """Main execution function"""
    print("🚀 Starting Complete Odoo Product & Inventory Analysis...")
    print("=" * 70)
    
    # Initialize analyzer
    analyzer = OdooCompleteAnalyzer()
    
    # Connect to Odoo
    if not analyzer.connect():
        print("❌ Failed to connect to Odoo. Please check your credentials.")
        return
    
    try:
        # Perform complete analysis
        analysis = analyzer.analyze_complete_inventory()
        
        # Display report
        print_complete_analysis_report(analysis)
        
        # Save detailed analysis
        save_complete_analysis(analysis)
        
        print("\n✅ Complete product analysis finished successfully!")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        print(f"❌ Analysis failed: {e}")

if __name__ == "__main__":
    main()