#!/usr/bin/env python3
"""
Product Transformation Script for Gym+Coffee to Odoo Integration

This script transforms Gym+Coffee product data to Odoo-compatible format.
It reads the JSON product catalog and converts it to Odoo product.product format.
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, List, Any, Optional
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProductTransformer:
    """Transforms Gym+Coffee products to Odoo format"""
    
    def __init__(self, source_file: str, output_dir: str = "data/transformed"):
        self.source_file = Path(source_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Odoo product categories mapping
        self.odoo_categories = {
            "hoodies": {"name": "Hoodies & Sweatshirts", "parent": "Apparel"},
            "t-shirts": {"name": "T-Shirts", "parent": "Apparel"},
            "joggers": {"name": "Joggers & Pants", "parent": "Apparel"},
            "leggings": {"name": "Leggings", "parent": "Apparel"},
            "shorts": {"name": "Shorts", "parent": "Apparel"},
            "tops": {"name": "Tops", "parent": "Apparel"},
            "sports-bras": {"name": "Sports Bras", "parent": "Apparel"},
            "jackets": {"name": "Jackets", "parent": "Apparel"},
            "accessories": {"name": "Accessories", "parent": "Fashion"},
            "beanies": {"name": "Beanies & Hats", "parent": "Accessories"}
        }
        
        # Size standardization
        self.size_mapping = {
            "XS": "Extra Small",
            "S": "Small", 
            "M": "Medium",
            "L": "Large",
            "XL": "Extra Large",
            "XXL": "2X Large",
            "XXXL": "3X Large",
            "OS": "One Size"
        }
    
    def load_source_data(self) -> Dict[str, Any]:
        """Load the source JSON data"""
        logger.info(f"Loading source data from {self.source_file}")
        
        with open(self.source_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Loaded {len(data.get('products', []))} products from catalog")
        return data
    
    def create_product_categories(self, products: List[Dict]) -> pd.DataFrame:
        """Create Odoo product categories"""
        categories = []
        unique_categories = set()
        
        # Extract unique categories from products
        for product in products:
            category = product.get('category')
            if category and category not in unique_categories:
                unique_categories.add(category)
                
                odoo_cat = self.odoo_categories.get(category, {
                    "name": category.title().replace('-', ' '),
                    "parent": "Apparel"
                })
                
                categories.append({
                    'external_id': f'gym_coffee_cat_{category}',
                    'name': odoo_cat['name'],
                    'parent_category': odoo_cat['parent'],
                    'sequence': len(categories) + 10
                })
        
        # Add parent categories
        parent_cats = ["Apparel", "Fashion", "Accessories"]
        for idx, parent in enumerate(parent_cats):
            categories.insert(0, {
                'external_id': f'gym_coffee_parent_{parent.lower()}',
                'name': parent,
                'parent_category': '',
                'sequence': idx + 1
            })
        
        df_categories = pd.DataFrame(categories)
        logger.info(f"Created {len(df_categories)} product categories")
        return df_categories
    
    def create_product_attributes(self, products: List[Dict]) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Create product attributes and values for variants"""
        attributes = []
        attribute_values = []
        
        # Color attribute
        colors = set()
        sizes = set()
        
        for product in products:
            if product.get('color'):
                colors.add(product['color'])
            if product.get('size'):
                sizes.add(product['size'])
        
        # Color attribute
        attributes.append({
            'external_id': 'gym_coffee_attr_color',
            'name': 'Color',
            'type': 'radio',
            'display_type': 'color',
            'sequence': 1
        })
        
        for idx, color in enumerate(sorted(colors)):
            attribute_values.append({
                'external_id': f'gym_coffee_color_{color.lower().replace(" ", "_")}',
                'name': color,
                'attribute_id': 'gym_coffee_attr_color',
                'sequence': idx + 1,
                'html_color': self._get_color_hex(color)
            })
        
        # Size attribute
        attributes.append({
            'external_id': 'gym_coffee_attr_size',
            'name': 'Size',
            'type': 'radio',
            'display_type': 'select',
            'sequence': 2
        })
        
        size_order = ['XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL', 'OS']
        sorted_sizes = sorted(sizes, key=lambda x: size_order.index(x) if x in size_order else 999)
        
        for idx, size in enumerate(sorted_sizes):
            attribute_values.append({
                'external_id': f'gym_coffee_size_{size.lower()}',
                'name': self.size_mapping.get(size, size),
                'attribute_id': 'gym_coffee_attr_size',
                'sequence': idx + 1
            })
        
        df_attributes = pd.DataFrame(attributes)
        df_attribute_values = pd.DataFrame(attribute_values)
        
        logger.info(f"Created {len(df_attributes)} attributes with {len(df_attribute_values)} values")
        return df_attributes, df_attribute_values
    
    def transform_products(self, products: List[Dict]) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Transform products to Odoo format with templates and variants"""
        templates = []
        variants = []
        
        # Group products by base name (without color/size)
        product_groups = {}
        for product in products:
            # Extract base name by removing color and size info
            base_name = product['name'].split(' - ')[0] if ' - ' in product['name'] else product['name']
            
            if base_name not in product_groups:
                product_groups[base_name] = []
            product_groups[base_name].append(product)
        
        template_id = 1
        variant_id = 1
        
        for base_name, group_products in product_groups.items():
            # Create product template
            first_product = group_products[0]
            
            # Calculate average price and cost
            avg_price = np.mean([p['list_price'] for p in group_products])
            avg_cost = np.mean([p['standard_cost'] for p in group_products])
            total_inventory = sum([p['inventory_on_hand'] for p in group_products])
            
            template = {
                'external_id': f'gym_coffee_template_{template_id}',
                'name': base_name,
                'type': 'product',
                'sale_ok': True,
                'purchase_ok': True,
                'can_be_sold': True,
                'can_be_purchased': True,
                'tracking': 'lot',
                'category_id': f'gym_coffee_cat_{first_product["category"]}',
                'list_price': round(avg_price, 2),
                'standard_price': round(avg_cost, 2),
                'default_code': f'GYM-{template_id:04d}',
                'description': first_product.get('description', ''),
                'weight': self._estimate_weight(first_product['category']),
                'volume': self._estimate_volume(first_product['category']),
                'has_variants': len(group_products) > 1,
                'attribute_line_ids': 'color,size' if len(group_products) > 1 else '',
                'company_id': 1,
                'active': True,
                'detailed_type': 'product',
                'invoice_policy': 'order',
                'expense_policy': 'no',
                'service_type': 'manual'
            }
            
            # Add features if available
            if first_product.get('features'):
                template['description'] += '\n\nFeatures:\n' + '\n'.join([f'• {f}' for f in first_product['features']])
            
            templates.append(template)
            
            # Create variants
            for product in group_products:
                variant = {
                    'external_id': f'gym_coffee_variant_{variant_id}',
                    'product_tmpl_id': f'gym_coffee_template_{template_id}',
                    'default_code': product['sku'],
                    'barcode': self._generate_barcode(product['sku']),
                    'list_price': product['list_price'],
                    'standard_price': product['standard_cost'],
                    'weight': self._estimate_weight(product['category']),
                    'volume': self._estimate_volume(product['category']),
                    'active': product.get('status', 'active') == 'active',
                    
                    # Attribute values
                    'color_value': product.get('color', ''),
                    'size_value': product.get('size', ''),
                    
                    # Inventory data
                    'qty_available': product.get('inventory_on_hand', 0),
                    'virtual_available': product.get('inventory_on_hand', 0),
                    'incoming_qty': 0,
                    'outgoing_qty': 0,
                    'reorder_level': product.get('reorder_point', 10),
                    'max_stock': product.get('reorder_point', 10) * 3,
                    
                    # Procurement data
                    'lead_time': product.get('lead_time_days', 7),
                    'procurement_method': 'make_to_stock',
                    'supply_method': 'buy',
                    
                    # Dates
                    'create_date': product.get('created_date', datetime.now().isoformat()),
                    'write_date': product.get('last_modified', datetime.now().isoformat())
                }
                
                variants.append(variant)
                variant_id += 1
            
            template_id += 1
        
        df_templates = pd.DataFrame(templates)
        df_variants = pd.DataFrame(variants)
        
        logger.info(f"Created {len(df_templates)} product templates and {len(df_variants)} variants")
        return df_templates, df_variants
    
    def create_inventory_data(self, variants_df: pd.DataFrame) -> pd.DataFrame:
        """Create initial inventory/stock data"""
        inventory_records = []
        
        for _, variant in variants_df.iterrows():
            if variant['qty_available'] > 0:
                inventory_records.append({
                    'external_id': f'stock_init_{variant["external_id"]}',
                    'product_id': variant['external_id'],
                    'location_id': 'stock_location_stock',  # Main stock location
                    'product_qty': variant['qty_available'],
                    'theoretical_qty': variant['qty_available'],
                    'product_uom_id': 'uom_unit',  # Units
                    'company_id': 1,
                    'inventory_date': datetime.now().date().isoformat(),
                    'accounting_date': datetime.now().date().isoformat(),
                    'state': 'done'
                })
        
        df_inventory = pd.DataFrame(inventory_records)
        logger.info(f"Created {len(df_inventory)} inventory records")
        return df_inventory
    
    def _get_color_hex(self, color_name: str) -> str:
        """Map color names to hex values for Odoo display"""
        color_map = {
            'black': '#000000',
            'white': '#FFFFFF',
            'gray': '#808080',
            'grey': '#808080',
            'red': '#FF0000',
            'blue': '#0000FF',
            'green': '#008000',
            'yellow': '#FFFF00',
            'pink': '#FFC0CB',
            'purple': '#800080',
            'orange': '#FFA500',
            'brown': '#A52A2A',
            'navy': '#000080',
            'beige': '#F5F5DC'
        }
        return color_map.get(color_name.lower(), '#CCCCCC')
    
    def _estimate_weight(self, category: str) -> float:
        """Estimate product weight based on category"""
        weight_map = {
            'hoodies': 0.6,
            't-shirts': 0.2,
            'joggers': 0.4,
            'leggings': 0.3,
            'shorts': 0.2,
            'tops': 0.15,
            'sports-bras': 0.1,
            'jackets': 0.8,
            'accessories': 0.05,
            'beanies': 0.1
        }
        return weight_map.get(category, 0.3)
    
    def _estimate_volume(self, category: str) -> float:
        """Estimate product volume based on category"""
        volume_map = {
            'hoodies': 0.008,
            't-shirts': 0.004,
            'joggers': 0.006,
            'leggings': 0.004,
            'shorts': 0.003,
            'tops': 0.003,
            'sports-bras': 0.002,
            'jackets': 0.012,
            'accessories': 0.001,
            'beanies': 0.001
        }
        return volume_map.get(category, 0.005)
    
    def _generate_barcode(self, sku: str) -> str:
        """Generate EAN13 barcode from SKU"""
        # Simple barcode generation - in real implementation use proper EAN13
        numeric_part = ''.join(filter(str.isdigit, sku))
        if len(numeric_part) < 12:
            numeric_part = numeric_part.ljust(12, '0')
        else:
            numeric_part = numeric_part[:12]
        
        # Calculate check digit (simplified)
        check_digit = (10 - (sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(numeric_part)) % 10)) % 10
        return numeric_part + str(check_digit)
    
    def export_to_csv(self, dataframes: Dict[str, pd.DataFrame]) -> None:
        """Export all dataframes to CSV files"""
        for name, df in dataframes.items():
            output_file = self.output_dir / f"odoo_{name}.csv"
            df.to_csv(output_file, index=False)
            logger.info(f"Exported {len(df)} records to {output_file}")
    
    def run_transformation(self) -> None:
        """Run the complete transformation process"""
        logger.info("Starting Gym+Coffee product transformation")
        
        # Load source data
        source_data = self.load_source_data()
        products = source_data.get('products', [])
        
        if not products:
            logger.error("No products found in source data")
            return
        
        # Create transformations
        categories_df = self.create_product_categories(products)
        attributes_df, attribute_values_df = self.create_product_attributes(products)
        templates_df, variants_df = self.transform_products(products)
        inventory_df = self.create_inventory_data(variants_df)
        
        # Export to CSV files
        dataframes = {
            'product_categories': categories_df,
            'product_attributes': attributes_df,
            'product_attribute_values': attribute_values_df,
            'product_templates': templates_df,
            'product_variants': variants_df,
            'inventory_initial': inventory_df
        }
        
        self.export_to_csv(dataframes)
        
        # Create summary
        summary = {
            'transformation_date': datetime.now().isoformat(),
            'source_products': len(products),
            'categories_created': len(categories_df),
            'attributes_created': len(attributes_df),
            'attribute_values_created': len(attribute_values_df),
            'product_templates_created': len(templates_df),
            'product_variants_created': len(variants_df),
            'inventory_records_created': len(inventory_df)
        }
        
        summary_file = self.output_dir / 'transformation_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info("Product transformation completed successfully")
        logger.info(f"Summary: {summary}")


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Transform Gym+Coffee products to Odoo format')
    parser.add_argument('--source', default='../data/gym_plus_coffee_products.json',
                       help='Source JSON file path')
    parser.add_argument('--output', default='../data/transformed',
                       help='Output directory for transformed files')
    
    args = parser.parse_args()
    
    # Create transformer and run
    transformer = ProductTransformer(args.source, args.output)
    transformer.run_transformation()


if __name__ == "__main__":
    main()