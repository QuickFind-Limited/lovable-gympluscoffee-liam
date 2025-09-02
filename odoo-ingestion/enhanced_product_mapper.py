#!/usr/bin/env python3
"""Enhanced product mapping with size/color distribution and seasonal patterns"""

import json
import random
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_analysis():
    """Load the product analysis"""
    with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/product_catalog_analysis.json', 'r') as f:
        return json.load(f)

def extract_size_color_from_products(analysis):
    """Extract size and color information from product codes"""
    sizes = set()
    colors = set()
    
    # Extract from product names and codes
    for product in analysis['products']:
        name = product['name']
        code = product['default_code'] or ''
        
        # Extract from attribute values
        if 'Pink' in name:
            colors.add('Pink')
        if 'Black' in name:
            colors.add('Black')
        if 'White' in name:
            colors.add('White')
        if 'Navy' in name:
            colors.add('Navy')
        if 'Grey' in name:
            colors.add('Grey')
        if 'Blue' in name:
            colors.add('Blue')
        if 'Green' in name:
            colors.add('Green')
        if 'Red' in name:
            colors.add('Red')
        
        # Extract sizes from codes
        if '-XS' in code or code.endswith('XS'):
            sizes.add('XS')
        elif '-S' in code or code.endswith('S'):
            sizes.add('S')
        elif '-M' in code or code.endswith('M'):
            sizes.add('M')
        elif '-L' in code or code.endswith('L'):
            sizes.add('L')
        elif '-XL' in code or code.endswith('XL'):
            sizes.add('XL')
        elif '-XXL' in code or code.endswith('XXL'):
            sizes.add('XXL')
    
    # Also extract from attribute values
    for attr_val in analysis['attribute_values'].values():
        if attr_val['attribute_id'] and len(attr_val['attribute_id']) > 1:
            attr_name = attr_val['attribute_id'][1]
            val_name = attr_val['name']
            
            if attr_name == 'Size':
                sizes.add(val_name)
            elif attr_name == 'Color':
                colors.add(val_name)
    
    return list(sizes), list(colors)

def create_enhanced_mapping():
    """Create enhanced product mapping with detailed size/color distributions"""
    logger.info("Creating enhanced product mapping...")
    
    # Load analysis
    analysis = load_analysis()
    
    # Extract sizes and colors
    sizes, colors = extract_size_color_from_products(analysis)
    
    logger.info(f"Found sizes: {sizes}")
    logger.info(f"Found colors: {colors}")
    
    # Define seasonal patterns - more comprehensive
    seasonal_patterns = {
        'spring_items': {
            'categories': ['T-Shirts', 'Leggings', 'Joggers', 'Shorts'],
            'months': [3, 4, 5],  # March, April, May
            'boost_factor': 1.2
        },
        'summer_items': {
            'categories': ['T-Shirts', 'Shorts', 'Sports-Bras', 'Tops'],
            'months': [6, 7, 8],  # June, July, August
            'boost_factor': 1.5
        },
        'autumn_items': {
            'categories': ['Hoodies', 'Leggings', 'Joggers', 'Jackets'],
            'months': [9, 10, 11],  # September, October, November
            'boost_factor': 1.3
        },
        'winter_items': {
            'categories': ['Hoodies', 'Jackets', 'Beanies'],
            'months': [12, 1, 2],  # December, January, February
            'boost_factor': 1.4
        },
        'year_round': {
            'categories': ['Leggings', 'Accessories', 'Goods', 'Services'],
            'months': list(range(1, 13)),
            'boost_factor': 1.0
        }
    }
    
    # Size distribution according to requirements
    size_distribution = {
        'XS': 0.10,  # 10%
        'S': 0.20,   # 20% (18-22% range)
        'M': 0.32,   # 32% (28-35% range)
        'L': 0.25,   # 25% (23-28% range)
        'XL': 0.15,  # 15% (12-18% range)
        'XXL': 0.08  # 8%
    }
    
    # Color popularity (based on typical fashion trends)
    color_weights = {
        'Black': 3.0,      # Most popular
        'White': 2.5,      # Very popular
        'Navy': 2.2,       # Popular
        'Grey': 2.0,       # Popular
        'Blue': 1.8,       # Moderate
        'Green': 1.5,      # Moderate
        'Pink': 1.3,       # Moderate
        'Red': 1.2         # Lower popularity
    }
    
    # Get products by category
    category_products = {}
    for product in analysis['products']:
        if product['categ_id']:
            cat_name = product['categ_id'][1]
            if cat_name not in category_products:
                category_products[cat_name] = []
            category_products[cat_name].append(product)
    
    # Create enhanced mapping structure
    mapping = {
        'metadata': {
            'created_date': datetime.now().isoformat(),
            'total_products': analysis['total_products'],
            'categories': list(category_products.keys()),
            'available_sizes': sizes,
            'available_colors': colors,
            'mapping_rules': {
                'top_20_percent_revenue': '60-75%',
                'size_distribution': size_distribution,
                'seasonal_patterns': seasonal_patterns,
                'color_weights': color_weights
            }
        },
        'product_categories': {},
        'seasonal_patterns': seasonal_patterns,
        'size_distribution': size_distribution,
        'color_weights': color_weights,
        'revenue_tiers': {
            'tier_1_high_volume': [],  # Top 20% - generate 60-75% revenue
            'tier_2_medium': [],       # Next 30% - generate 20-25% revenue  
            'tier_3_low': []          # Bottom 50% - generate 5-15% revenue
        },
        'product_lookup': {}  # Quick lookup by product ID
    }
    
    # Process each category
    total_tier_1 = 0
    total_tier_2 = 0
    total_tier_3 = 0
    
    for category, products in category_products.items():
        if not products:
            continue
            
        logger.info(f"Processing category '{category}' with {len(products)} products")
        
        # Sort by price descending for tier assignment
        sorted_products = sorted(products, key=lambda x: x['list_price'], reverse=True)
        
        total_products = len(sorted_products)
        tier_1_count = max(1, int(total_products * 0.2))  # Top 20%
        tier_2_count = max(1, int(total_products * 0.3))  # Next 30%
        tier_3_count = total_products - tier_1_count - tier_2_count
        
        # Determine seasonal pattern
        seasonal_info = None
        for pattern_name, pattern_data in seasonal_patterns.items():
            if category in pattern_data['categories']:
                seasonal_info = {
                    'pattern': pattern_name,
                    'months': pattern_data['months'],
                    'boost_factor': pattern_data['boost_factor']
                }
                break
        
        # Default to year-round if not found
        if not seasonal_info:
            seasonal_info = {
                'pattern': 'year_round',
                'months': list(range(1, 13)),
                'boost_factor': 1.0
            }
        
        category_mapping = {
            'total_products': total_products,
            'products': [],
            'tier_distribution': {
                'tier_1': tier_1_count,
                'tier_2': tier_2_count,
                'tier_3': tier_3_count
            },
            'seasonal_pattern': seasonal_info,
            'category_stats': {
                'avg_price': sum(p['list_price'] for p in products) / len(products),
                'price_range': [min(p['list_price'] for p in products), 
                              max(p['list_price'] for p in products)],
                'has_variants': any('-' in (p['default_code'] or '') for p in products)
            }
        }
        
        # Assign products to tiers and create detailed mapping
        for idx, product in enumerate(sorted_products):
            # Extract size and color from product name/code
            product_size = None
            product_color = None
            
            name = product['name']
            code = product['default_code'] or ''
            
            # Extract size
            for size in sizes:
                if f'-{size}' in code or code.endswith(size) or size in name:
                    product_size = size
                    break
            
            # Extract color
            for color in colors:
                if color.lower() in name.lower() or color.upper() in code:
                    product_color = color
                    break
            
            # Assign tier
            if idx < tier_1_count:
                tier = 'tier_1_high_volume'
                revenue_weight = 3.5
                total_tier_1 += 1
                mapping['revenue_tiers']['tier_1_high_volume'].append(product['id'])
            elif idx < tier_1_count + tier_2_count:
                tier = 'tier_2_medium'
                revenue_weight = 2.0
                total_tier_2 += 1
                mapping['revenue_tiers']['tier_2_medium'].append(product['id'])
            else:
                tier = 'tier_3_low'
                revenue_weight = 1.0
                total_tier_3 += 1
                mapping['revenue_tiers']['tier_3_low'].append(product['id'])
            
            # Apply color weight modifier
            if product_color and product_color in color_weights:
                revenue_weight *= color_weights[product_color]
            
            product_mapping = {
                'id': product['id'],
                'name': product['name'],
                'default_code': product['default_code'],
                'list_price': product['list_price'],
                'standard_price': product['standard_price'],
                'category': category,
                'type': product['type'],
                'barcode': product['barcode'],
                'sale_ok': product['sale_ok'],
                'tier': tier,
                'revenue_weight': revenue_weight,
                'seasonal_boost': seasonal_info,
                'product_attributes': {
                    'size': product_size,
                    'color': product_color,
                    'size_weight': size_distribution.get(product_size, 1.0) if product_size else 1.0,
                    'color_weight': color_weights.get(product_color, 1.0) if product_color else 1.0
                },
                'sales_probability': revenue_weight * seasonal_info['boost_factor'],
                'recommended_monthly_sales': {
                    1: revenue_weight * 0.8,  # January
                    2: revenue_weight * 0.9,  # February
                    3: revenue_weight * 1.1,  # March
                    4: revenue_weight * 1.2,  # April
                    5: revenue_weight * 1.3,  # May
                    6: revenue_weight * 1.4,  # June
                    7: revenue_weight * 1.5,  # July
                    8: revenue_weight * 1.4,  # August
                    9: revenue_weight * 1.2,  # September
                    10: revenue_weight * 1.1, # October
                    11: revenue_weight * 1.3, # November
                    12: revenue_weight * 1.4  # December
                }
            }
            
            # Apply seasonal boost to monthly sales
            for month in seasonal_info['months']:
                if month in product_mapping['recommended_monthly_sales']:
                    product_mapping['recommended_monthly_sales'][month] *= seasonal_info['boost_factor']
            
            category_mapping['products'].append(product_mapping)
            mapping['product_lookup'][product['id']] = product_mapping
        
        mapping['product_categories'][category] = category_mapping
        total_tier_1 += tier_1_count
        total_tier_2 += tier_2_count
        total_tier_3 += tier_3_count
    
    # Add summary statistics
    mapping['summary_statistics'] = {
        'total_categories': len(category_products),
        'tier_distribution': {
            'tier_1_count': total_tier_1,
            'tier_2_count': total_tier_2,
            'tier_3_count': total_tier_3,
            'tier_1_percentage': (total_tier_1 / analysis['total_products']) * 100,
            'tier_2_percentage': (total_tier_2 / analysis['total_products']) * 100,
            'tier_3_percentage': (total_tier_3 / analysis['total_products']) * 100
        },
        'seasonal_distribution': {
            pattern: len([cat for cat in category_products.keys() 
                         if cat in pattern_data['categories']])
            for pattern, pattern_data in seasonal_patterns.items()
        },
        'size_availability': {size: len([p for p in analysis['products'] 
                                       if size in (p['name'] + (p['default_code'] or ''))]) 
                            for size in sizes},
        'color_availability': {color: len([p for p in analysis['products']
                                         if color.lower() in p['name'].lower()])
                             for color in colors}
    }
    
    logger.info(f"Enhanced mapping created:")
    logger.info(f"  Categories: {len(category_products)}")
    logger.info(f"  Tier 1 products: {len(mapping['revenue_tiers']['tier_1_high_volume'])}")
    logger.info(f"  Tier 2 products: {len(mapping['revenue_tiers']['tier_2_medium'])}")
    logger.info(f"  Tier 3 products: {len(mapping['revenue_tiers']['tier_3_low'])}")
    
    return mapping

def main():
    """Main execution function"""
    try:
        # Create enhanced mapping
        mapping = create_enhanced_mapping()
        
        # Save mapping
        mapping_file = '/workspaces/source-lovable-gympluscoffee/odoo-ingestion/product_mapping.json'
        with open(mapping_file, 'w') as f:
            json.dump(mapping, f, indent=2, default=str)
        logger.info(f"Enhanced mapping saved to {mapping_file}")
        
        # Print summary
        print("\n" + "="*70)
        print("ENHANCED PRODUCT MAPPING SUMMARY")
        print("="*70)
        print(f"Total Products: {mapping['metadata']['total_products']}")
        print(f"Categories: {len(mapping['metadata']['categories'])}")
        print(f"Available Sizes: {mapping['metadata']['available_sizes']}")
        print(f"Available Colors: {mapping['metadata']['available_colors']}")
        
        print(f"\nRevenue Tiers:")
        stats = mapping['summary_statistics']['tier_distribution']
        print(f"  Tier 1 (High Volume): {stats['tier_1_count']} products ({stats['tier_1_percentage']:.1f}%)")
        print(f"  Tier 2 (Medium): {stats['tier_2_count']} products ({stats['tier_2_percentage']:.1f}%)")
        print(f"  Tier 3 (Low): {stats['tier_3_count']} products ({stats['tier_3_percentage']:.1f}%)")
        
        print(f"\nSeasonal Distribution:")
        for pattern, count in mapping['summary_statistics']['seasonal_distribution'].items():
            print(f"  {pattern.replace('_', ' ').title()}: {count} categories")
        
        print(f"\nSize Distribution Rules:")
        for size, percentage in mapping['size_distribution'].items():
            print(f"  {size}: {percentage*100:.0f}%")
        
        print(f"\nTop Color Weights:")
        sorted_colors = sorted(mapping['color_weights'].items(), key=lambda x: x[1], reverse=True)
        for color, weight in sorted_colors[:5]:
            print(f"  {color}: {weight}x weight")
        
        print("\n✅ Enhanced mapping completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    main()