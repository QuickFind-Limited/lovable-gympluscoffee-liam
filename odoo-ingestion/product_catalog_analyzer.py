#!/usr/bin/env python3
"""Analyze Odoo product catalog for mapping"""

import xmlrpc.client
import json
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def connect_to_odoo():
    """Connect to Odoo and return models proxy"""
    url = 'https://source-gym-plus-coffee.odoo.com'
    db = 'source-gym-plus-coffee'
    username = 'admin@quickfindai.com'
    password = 'BJ62wX2J4yzjS$i'
    
    logger.info("Connecting to Odoo...")
    
    try:
        # Create connection
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
        
        # Authenticate
        uid = common.authenticate(db, username, password, {})
        
        if uid:
            logger.info(f"✅ Authentication successful! UID: {uid}")
            
            # Create models proxy
            models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
            
            return models, db, uid, password
        else:
            logger.error("❌ Authentication failed!")
            return None, None, None, None
            
    except Exception as e:
        logger.error(f"❌ Connection error: {e}")
        return None, None, None, None

def fetch_products(models, db, uid, password):
    """Fetch all active products with detailed information"""
    logger.info("Fetching all active products...")
    
    # Get product templates first to understand structure
    templates = models.execute_kw(
        db, uid, password,
        'product.template', 'search_read',
        [[['active', '=', True]]],
        {
            'fields': ['name', 'default_code', 'categ_id', 'list_price', 'standard_price', 
                      'type', 'sale_ok', 'purchase_ok', 'product_variant_ids']
        }
    )
    
    logger.info(f"Found {len(templates)} product templates")
    
    # Get all product variants
    products = models.execute_kw(
        db, uid, password,
        'product.product', 'search_read',
        [[['active', '=', True]]],
        {
            'fields': ['name', 'default_code', 'categ_id', 'list_price', 'standard_price',
                      'qty_available', 'virtual_available', 'product_tmpl_id', 'barcode', 
                      'type', 'sale_ok', 'purchase_ok', 'attribute_line_ids',
                      'product_template_attribute_value_ids']
        }
    )
    
    logger.info(f"Found {len(products)} product variants")
    
    return templates, products

def fetch_categories(models, db, uid, password):
    """Fetch product categories"""
    logger.info("Fetching product categories...")
    
    categories = models.execute_kw(
        db, uid, password,
        'product.category', 'search_read',
        [[]],
        {'fields': ['name', 'parent_id', 'complete_name']}
    )
    
    logger.info(f"Found {len(categories)} categories")
    return categories

def fetch_attributes(models, db, uid, password):
    """Fetch product attributes and values"""
    logger.info("Fetching product attributes...")
    
    attributes = models.execute_kw(
        db, uid, password,
        'product.attribute', 'search_read',
        [[]],
        {'fields': ['name', 'value_ids']}
    )
    
    attribute_values = models.execute_kw(
        db, uid, password,
        'product.attribute.value', 'search_read',
        [[]],
        {'fields': ['name', 'attribute_id']}
    )
    
    logger.info(f"Found {len(attributes)} attributes with {len(attribute_values)} values")
    return attributes, attribute_values

def analyze_product_catalog():
    """Main function to analyze the product catalog"""
    logger.info("Starting product catalog analysis...")
    
    # Connect to Odoo
    models, db, uid, password = connect_to_odoo()
    if not models:
        logger.error("Failed to connect to Odoo")
        return None
    
    # Fetch data
    templates, products = fetch_products(models, db, uid, password)
    categories = fetch_categories(models, db, uid, password)
    attributes, attribute_values = fetch_attributes(models, db, uid, password)
    
    # Create analysis structure
    analysis = {
        'analysis_date': datetime.now().isoformat(),
        'total_templates': len(templates),
        'total_products': len(products),
        'categories': {cat['id']: cat for cat in categories},
        'attributes': {attr['id']: attr for attr in attributes},
        'attribute_values': {val['id']: val for val in attribute_values},
        'templates': templates,
        'products': products,
        'summary': {
            'categories_breakdown': {},
            'price_ranges': {},
            'product_types': {},
            'size_variants': {},
            'color_variants': {}
        }
    }
    
    # Analyze categories
    category_counts = {}
    for product in products:
        if product['categ_id']:
            cat_id = product['categ_id'][0]
            cat_name = product['categ_id'][1]
            category_counts[cat_name] = category_counts.get(cat_name, 0) + 1
    
    analysis['summary']['categories_breakdown'] = category_counts
    
    # Analyze product types
    type_counts = {}
    for product in products:
        ptype = product['type']
        type_counts[ptype] = type_counts.get(ptype, 0) + 1
    
    analysis['summary']['product_types'] = type_counts
    
    # Analyze price ranges
    prices = [p['list_price'] for p in products if p['list_price'] > 0]
    if prices:
        analysis['summary']['price_ranges'] = {
            'min': min(prices),
            'max': max(prices),
            'average': sum(prices) / len(prices),
            'count_with_price': len(prices)
        }
    
    logger.info("Analysis complete!")
    return analysis

def create_product_mapping(analysis):
    """Create product mapping for transaction generation"""
    logger.info("Creating product mapping...")
    
    if not analysis:
        logger.error("No analysis data provided")
        return None
    
    # Get products by category
    category_products = {}
    for product in analysis['products']:
        if product['categ_id']:
            cat_name = product['categ_id'][1]
            if cat_name not in category_products:
                category_products[cat_name] = []
            category_products[cat_name].append(product)
    
    # Create mapping structure
    mapping = {
        'metadata': {
            'created_date': datetime.now().isoformat(),
            'total_products': analysis['total_products'],
            'categories': list(category_products.keys()),
            'mapping_rules': {
                'top_20_percent_revenue': '60-75%',
                'summer_boost': 'June-August for T-shirts, Shorts',
                'size_distribution': {
                    'S': '18-22%',
                    'M': '28-35%', 
                    'L': '23-28%',
                    'XL': '12-18%'
                }
            }
        },
        'product_categories': {},
        'seasonal_patterns': {
            'summer_items': ['T-Shirts', 'Tank Tops', 'Shorts'],
            'winter_items': ['Hoodies', 'Sweaters', 'Long Sleeves'],
            'year_round': ['Leggings', 'Accessories', 'Unknown']
        },
        'revenue_tiers': {
            'tier_1_high_volume': [],  # Top 20% - generate 60-75% revenue
            'tier_2_medium': [],       # Next 30% - generate 20-25% revenue  
            'tier_3_low': []          # Bottom 50% - generate 5-15% revenue
        }
    }
    
    # Process each category
    for category, products in category_products.items():
        # Sort by price descending for tier assignment
        sorted_products = sorted(products, key=lambda x: x['list_price'], reverse=True)
        
        total_products = len(sorted_products)
        tier_1_count = max(1, int(total_products * 0.2))  # Top 20%
        tier_2_count = max(1, int(total_products * 0.3))  # Next 30%
        
        category_mapping = {
            'total_products': total_products,
            'products': [],
            'tier_distribution': {
                'tier_1': tier_1_count,
                'tier_2': tier_2_count,
                'tier_3': total_products - tier_1_count - tier_2_count
            }
        }
        
        # Assign products to tiers and create detailed mapping
        for idx, product in enumerate(sorted_products):
            product_mapping = {
                'id': product['id'],
                'name': product['name'],
                'default_code': product['default_code'],
                'list_price': product['list_price'],
                'standard_price': product['standard_price'],
                'category': category,
                'type': product['type'],
                'barcode': product['barcode'],
                'sale_ok': product['sale_ok']
            }
            
            # Assign tier
            if idx < tier_1_count:
                product_mapping['tier'] = 'tier_1_high_volume'
                product_mapping['revenue_weight'] = 3.0  # Higher chance of selection
                mapping['revenue_tiers']['tier_1_high_volume'].append(product['id'])
            elif idx < tier_1_count + tier_2_count:
                product_mapping['tier'] = 'tier_2_medium'
                product_mapping['revenue_weight'] = 2.0  # Medium chance
                mapping['revenue_tiers']['tier_2_medium'].append(product['id'])
            else:
                product_mapping['tier'] = 'tier_3_low'
                product_mapping['revenue_weight'] = 1.0  # Lower chance
                mapping['revenue_tiers']['tier_3_low'].append(product['id'])
            
            # Assign seasonal boost
            if category in mapping['seasonal_patterns']['summer_items']:
                product_mapping['seasonal_boost'] = {
                    'months': [6, 7, 8],  # June, July, August
                    'boost_factor': 1.5
                }
            elif category in mapping['seasonal_patterns']['winter_items']:
                product_mapping['seasonal_boost'] = {
                    'months': [11, 12, 1, 2],  # Nov, Dec, Jan, Feb
                    'boost_factor': 1.3
                }
            else:
                product_mapping['seasonal_boost'] = {
                    'months': list(range(1, 13)),  # Year round
                    'boost_factor': 1.0
                }
            
            category_mapping['products'].append(product_mapping)
        
        mapping['product_categories'][category] = category_mapping
    
    logger.info(f"Mapping created with {len(mapping['product_categories'])} categories")
    return mapping

def main():
    """Main execution function"""
    try:
        # Analyze catalog
        analysis = analyze_product_catalog()
        if not analysis:
            logger.error("Failed to analyze product catalog")
            return
        
        # Save analysis
        analysis_file = '/workspaces/source-lovable-gympluscoffee/odoo-ingestion/product_catalog_analysis.json'
        with open(analysis_file, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        logger.info(f"Analysis saved to {analysis_file}")
        
        # Create mapping
        mapping = create_product_mapping(analysis)
        if not mapping:
            logger.error("Failed to create product mapping")
            return
        
        # Save mapping
        mapping_file = '/workspaces/source-lovable-gympluscoffee/odoo-ingestion/product_mapping.json'
        with open(mapping_file, 'w') as f:
            json.dump(mapping, f, indent=2, default=str)
        logger.info(f"Mapping saved to {mapping_file}")
        
        # Print summary
        print("\n" + "="*60)
        print("PRODUCT CATALOG ANALYSIS SUMMARY")
        print("="*60)
        print(f"Total Templates: {analysis['total_templates']}")
        print(f"Total Products: {analysis['total_products']}")
        print(f"Categories: {len(analysis['summary']['categories_breakdown'])}")
        print("\nCategory Breakdown:")
        for cat, count in analysis['summary']['categories_breakdown'].items():
            print(f"  {cat}: {count} products")
        
        print(f"\nProduct Types:")
        for ptype, count in analysis['summary']['product_types'].items():
            print(f"  {ptype}: {count} products")
        
        if analysis['summary']['price_ranges']:
            pr = analysis['summary']['price_ranges']
            print(f"\nPrice Range:")
            print(f"  Min: €{pr['min']:.2f}")
            print(f"  Max: €{pr['max']:.2f}")  
            print(f"  Average: €{pr['average']:.2f}")
            print(f"  Products with price: {pr['count_with_price']}")
        
        print(f"\nMapping Tiers:")
        print(f"  Tier 1 (High Volume): {len(mapping['revenue_tiers']['tier_1_high_volume'])} products")
        print(f"  Tier 2 (Medium): {len(mapping['revenue_tiers']['tier_2_medium'])} products")
        print(f"  Tier 3 (Low): {len(mapping['revenue_tiers']['tier_3_low'])} products")
        
        print("\n✅ Analysis and mapping completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    main()