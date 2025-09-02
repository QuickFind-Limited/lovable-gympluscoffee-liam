#!/usr/bin/env python3
"""Complete product mapping including all products, even those without categories"""

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
        
        # Extract colors from names
        color_keywords = ['Pink', 'Black', 'White', 'Navy', 'Grey', 'Blue', 'Green', 'Red', 'Yellow', 'Purple', 'Orange']
        for color in color_keywords:
            if color.lower() in name.lower():
                colors.add(color)
        
        # Extract sizes from codes and names
        size_keywords = ['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL']
        for size in size_keywords:
            if f'-{size}' in code or code.endswith(size) or f' {size}' in name or f'({size})' in name:
                sizes.add(size)
    
    # Also extract from attribute values
    for attr_val in analysis['attribute_values'].values():
        if attr_val['attribute_id'] and len(attr_val['attribute_id']) > 1:
            attr_name = attr_val['attribute_id'][1]
            val_name = attr_val['name']
            
            if attr_name == 'Size':
                sizes.add(val_name)
            elif attr_name == 'Color':
                colors.add(val_name)
    
    return sorted(list(sizes)), sorted(list(colors))

def categorize_uncategorized_products(product):
    """Categorize products that don't have a category assigned"""
    name = product['name'].lower()
    code = (product['default_code'] or '').lower()
    
    # Define category keywords
    category_keywords = {
        'T-Shirts': ['t-shirt', 'tee', 'top', 'shirt'],
        'Hoodies': ['hoodie', 'sweatshirt', 'pullover'],
        'Leggings': ['legging', 'tights', 'pant'],
        'Shorts': ['short', 'brief'],
        'Jackets': ['jacket', 'coat', 'blazer'],
        'Accessories': ['bag', 'hat', 'cap', 'beanie', 'accessory', 'sock'],
        'Sports-Bras': ['bra', 'sports bra'],
        'Joggers': ['jogger', 'trackpant', 'sweatpant'],
        'Goods': ['canvas', 'tote', 'bottle', 'mug', 'gift', 'card']
    }
    
    # Check name and code against keywords
    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in name or keyword in code:
                return category
    
    # Default category for uncategorized
    return 'Uncategorized'

def create_complete_mapping():
    """Create complete product mapping including ALL products"""
    logger.info("Creating complete product mapping...")
    
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
            'categories': ['Leggings', 'Accessories', 'Goods', 'Services', 'Uncategorized'],
            'months': list(range(1, 13)),
            'boost_factor': 1.0
        }
    }
    
    # Size distribution according to requirements
    size_distribution = {
        'XXS': 0.05,  # 5%
        'XS': 0.10,   # 10%
        'S': 0.20,    # 20% (18-22% range)
        'M': 0.32,    # 32% (28-35% range)
        'L': 0.25,    # 25% (23-28% range)
        'XL': 0.15,   # 15% (12-18% range)
        'XXL': 0.08,  # 8%
        'XXXL': 0.05  # 5%
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
        'Red': 1.2,        # Lower popularity
        'Yellow': 1.1,
        'Purple': 1.1,
        'Orange': 1.0
    }
    
    # Categorize ALL products
    all_categorized_products = {}
    for product in analysis['products']:
        if product['categ_id']:
            # Use existing category
            cat_name = product['categ_id'][1]
        else:
            # Assign category based on product name/code
            cat_name = categorize_uncategorized_products(product)
        
        if cat_name not in all_categorized_products:
            all_categorized_products[cat_name] = []
        all_categorized_products[cat_name].append(product)
    
    logger.info(f"Categorized {len(analysis['products'])} products into {len(all_categorized_products)} categories")
    for cat, products in all_categorized_products.items():
        logger.info(f"  {cat}: {len(products)} products")
    
    # Create mapping structure
    mapping = {
        'metadata': {
            'created_date': datetime.now().isoformat(),
            'total_products': analysis['total_products'],
            'categories': list(all_categorized_products.keys()),
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
    
    for category, products in all_categorized_products.items():
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
            
            # Extract size (check larger sizes first to avoid conflicts)
            for size in sorted(sizes, key=len, reverse=True):
                if f'-{size}' in code or code.endswith(size) or f' {size}' in name or f'({size})' in name:
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
            
            # Apply size weight modifier
            if product_size and product_size in size_distribution:
                revenue_weight *= (size_distribution[product_size] * 5)  # Scale up size weight
            
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
                'recommended_monthly_sales': {}
            }
            
            # Calculate monthly sales recommendations
            base_monthly_sales = revenue_weight * (product['list_price'] / 100)  # Scale by price
            for month in range(1, 13):
                monthly_factor = 1.0
                
                # Apply seasonal boost
                if month in seasonal_info['months']:
                    monthly_factor *= seasonal_info['boost_factor']
                
                # Apply general monthly patterns (retail seasonality)
                monthly_patterns = {
                    1: 0.8,   # January - post-holiday lull
                    2: 0.9,   # February - low season
                    3: 1.1,   # March - spring start
                    4: 1.2,   # April - spring peak
                    5: 1.3,   # May - pre-summer
                    6: 1.4,   # June - summer start
                    7: 1.5,   # July - summer peak
                    8: 1.4,   # August - late summer
                    9: 1.2,   # September - back to school
                    10: 1.1,  # October - autumn
                    11: 1.6,  # November - Black Friday
                    12: 1.7   # December - Christmas
                }
                
                monthly_factor *= monthly_patterns.get(month, 1.0)
                product_mapping['recommended_monthly_sales'][month] = base_monthly_sales * monthly_factor
            
            category_mapping['products'].append(product_mapping)
            mapping['product_lookup'][str(product['id'])] = product_mapping
        
        mapping['product_categories'][category] = category_mapping
    
    # Add summary statistics
    mapping['summary_statistics'] = {
        'total_categories': len(all_categorized_products),
        'tier_distribution': {
            'tier_1_count': len(mapping['revenue_tiers']['tier_1_high_volume']),
            'tier_2_count': len(mapping['revenue_tiers']['tier_2_medium']),
            'tier_3_count': len(mapping['revenue_tiers']['tier_3_low']),
            'tier_1_percentage': (len(mapping['revenue_tiers']['tier_1_high_volume']) / analysis['total_products']) * 100,
            'tier_2_percentage': (len(mapping['revenue_tiers']['tier_2_medium']) / analysis['total_products']) * 100,
            'tier_3_percentage': (len(mapping['revenue_tiers']['tier_3_low']) / analysis['total_products']) * 100
        },
        'seasonal_distribution': {
            pattern: sum(1 for cat_data in mapping['product_categories'].values() 
                        if cat_data['seasonal_pattern']['pattern'] == pattern)
            for pattern in seasonal_patterns.keys()
        },
        'size_availability': {size: sum(1 for prod in mapping['product_lookup'].values()
                                      if prod['product_attributes']['size'] == size)
                            for size in sizes},
        'color_availability': {color: sum(1 for prod in mapping['product_lookup'].values()
                                        if prod['product_attributes']['color'] == color)
                             for color in colors}
    }
    
    logger.info(f"Complete mapping created:")
    logger.info(f"  Total products: {len(mapping['product_lookup'])}")
    logger.info(f"  Categories: {len(all_categorized_products)}")
    logger.info(f"  Tier 1 products: {len(mapping['revenue_tiers']['tier_1_high_volume'])}")
    logger.info(f"  Tier 2 products: {len(mapping['revenue_tiers']['tier_2_medium'])}")
    logger.info(f"  Tier 3 products: {len(mapping['revenue_tiers']['tier_3_low'])}")
    
    return mapping

def main():
    """Main execution function"""
    try:
        # Create complete mapping
        mapping = create_complete_mapping()
        
        # Save mapping
        mapping_file = '/workspaces/source-lovable-gympluscoffee/odoo-ingestion/product_mapping.json'
        with open(mapping_file, 'w') as f:
            json.dump(mapping, f, indent=2, default=str)
        logger.info(f"Complete mapping saved to {mapping_file}")
        
        # Print summary
        print("\n" + "="*70)
        print("COMPLETE PRODUCT MAPPING SUMMARY")
        print("="*70)
        print(f"Total Products: {mapping['metadata']['total_products']}")
        print(f"Categories: {len(mapping['metadata']['categories'])}")
        print(f"Available Sizes: {', '.join(mapping['metadata']['available_sizes'])}")
        print(f"Available Colors: {', '.join(mapping['metadata']['available_colors'])}")
        
        print(f"\nCategory Breakdown:")
        for category, cat_data in mapping['product_categories'].items():
            print(f"  {category}: {cat_data['total_products']} products")
        
        print(f"\nRevenue Tiers:")
        stats = mapping['summary_statistics']['tier_distribution']
        print(f"  Tier 1 (High Volume): {stats['tier_1_count']} products ({stats['tier_1_percentage']:.1f}%)")
        print(f"  Tier 2 (Medium): {stats['tier_2_count']} products ({stats['tier_2_percentage']:.1f}%)")
        print(f"  Tier 3 (Low): {stats['tier_3_count']} products ({stats['tier_3_percentage']:.1f}%)")
        
        print(f"\nSeasonal Distribution:")
        for pattern, count in mapping['summary_statistics']['seasonal_distribution'].items():
            print(f"  {pattern.replace('_', ' ').title()}: {count} categories")
        
        print(f"\nSize Distribution (Products with size info):")
        total_with_sizes = sum(mapping['summary_statistics']['size_availability'].values())
        for size, count in mapping['summary_statistics']['size_availability'].items():
            if count > 0:
                percentage = (count / total_with_sizes) * 100 if total_with_sizes > 0 else 0
                print(f"  {size}: {count} products ({percentage:.1f}%)")
        
        print(f"\nTop Color Distribution:")
        sorted_colors = sorted(mapping['summary_statistics']['color_availability'].items(), 
                             key=lambda x: x[1], reverse=True)
        for color, count in sorted_colors[:5]:
            if count > 0:
                print(f"  {color}: {count} products")
        
        print("\n✅ Complete mapping created successfully!")
        print(f"📁 File saved to: {mapping_file}")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    main()