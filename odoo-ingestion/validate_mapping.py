#!/usr/bin/env python3
"""Validate the product mapping for completeness and accuracy"""

import json
import logging
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_data():
    """Load both analysis and mapping data"""
    with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/product_catalog_analysis.json', 'r') as f:
        analysis = json.load(f)
    
    with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/product_mapping.json', 'r') as f:
        mapping = json.load(f)
    
    return analysis, mapping

def validate_product_coverage(analysis, mapping):
    """Validate all products are covered in the mapping"""
    logger.info("Validating product coverage...")
    
    # Get all product IDs from analysis
    analysis_product_ids = set(p['id'] for p in analysis['products'])
    
    # Get all product IDs from mapping
    mapping_product_ids = set(mapping['product_lookup'].keys())
    
    # Convert mapping keys to integers for comparison
    mapping_product_ids_int = set(int(pid) for pid in mapping_product_ids)
    
    missing_in_mapping = analysis_product_ids - mapping_product_ids_int
    extra_in_mapping = mapping_product_ids_int - analysis_product_ids
    
    validation_results = {
        'total_products_analysis': len(analysis_product_ids),
        'total_products_mapping': len(mapping_product_ids),
        'missing_in_mapping': list(missing_in_mapping),
        'extra_in_mapping': list(extra_in_mapping),
        'coverage_percentage': ((len(analysis_product_ids) - len(missing_in_mapping)) / len(analysis_product_ids)) * 100 if analysis_product_ids else 0
    }
    
    logger.info(f"Coverage: {validation_results['coverage_percentage']:.1f}%")
    if missing_in_mapping:
        logger.warning(f"Missing {len(missing_in_mapping)} products in mapping")
    
    return validation_results

def validate_tier_distribution(mapping):
    """Validate tier distribution follows 20/30/50 rule approximately"""
    logger.info("Validating tier distribution...")
    
    tier_counts = {
        'tier_1': len(mapping['revenue_tiers']['tier_1_high_volume']),
        'tier_2': len(mapping['revenue_tiers']['tier_2_medium']), 
        'tier_3': len(mapping['revenue_tiers']['tier_3_low'])
    }
    
    total = sum(tier_counts.values())
    
    tier_percentages = {
        'tier_1': (tier_counts['tier_1'] / total) * 100 if total > 0 else 0,
        'tier_2': (tier_counts['tier_2'] / total) * 100 if total > 0 else 0,
        'tier_3': (tier_counts['tier_3'] / total) * 100 if total > 0 else 0
    }
    
    # Check if distribution is reasonable (not strict 20/30/50 due to rounding)
    tier_1_ok = 15 <= tier_percentages['tier_1'] <= 25
    tier_2_ok = 25 <= tier_percentages['tier_2'] <= 35
    tier_3_ok = 40 <= tier_percentages['tier_3'] <= 60
    
    validation = {
        'tier_counts': tier_counts,
        'tier_percentages': tier_percentages,
        'tier_1_within_range': tier_1_ok,
        'tier_2_within_range': tier_2_ok,
        'tier_3_within_range': tier_3_ok,
        'overall_distribution_valid': tier_1_ok and tier_2_ok and tier_3_ok
    }
    
    return validation

def validate_seasonal_patterns(mapping):
    """Validate seasonal patterns are properly assigned"""
    logger.info("Validating seasonal patterns...")
    
    seasonal_stats = defaultdict(int)
    category_seasonal = defaultdict(list)
    
    for category, cat_data in mapping['product_categories'].items():
        seasonal_pattern = cat_data['seasonal_pattern']['pattern']
        seasonal_stats[seasonal_pattern] += cat_data['total_products']
        category_seasonal[seasonal_pattern].append(category)
    
    # Check specific categories have correct patterns
    expected_patterns = {
        'T-Shirts': 'summer_items',
        'Shorts': 'summer_items', 
        'Hoodies': 'winter_items',
        'Leggings': ['spring_items', 'autumn_items', 'year_round']  # Can be multiple
    }
    
    pattern_validation = {}
    for category, cat_data in mapping['product_categories'].items():
        actual_pattern = cat_data['seasonal_pattern']['pattern']
        if category in expected_patterns:
            expected = expected_patterns[category]
            if isinstance(expected, list):
                pattern_validation[category] = actual_pattern in expected
            else:
                pattern_validation[category] = actual_pattern == expected
        else:
            pattern_validation[category] = True  # Unknown categories are OK
    
    validation = {
        'seasonal_distribution': dict(seasonal_stats),
        'category_patterns': dict(category_seasonal),
        'pattern_validation': pattern_validation,
        'all_patterns_valid': all(pattern_validation.values())
    }
    
    return validation

def validate_size_color_weights(mapping):
    """Validate size and color weights are properly assigned"""
    logger.info("Validating size and color weights...")
    
    size_counts = defaultdict(int)
    color_counts = defaultdict(int)
    products_with_size = 0
    products_with_color = 0
    
    for product_id, product_data in mapping['product_lookup'].items():
        attrs = product_data.get('product_attributes', {})
        
        if attrs.get('size'):
            size_counts[attrs['size']] += 1
            products_with_size += 1
        
        if attrs.get('color'):
            color_counts[attrs['color']] += 1
            products_with_color += 1
    
    total_products = len(mapping['product_lookup'])
    
    validation = {
        'size_distribution': dict(size_counts),
        'color_distribution': dict(color_counts),
        'products_with_size': products_with_size,
        'products_with_color': products_with_color,
        'size_coverage': (products_with_size / total_products) * 100 if total_products > 0 else 0,
        'color_coverage': (products_with_color / total_products) * 100 if total_products > 0 else 0,
        'available_sizes': mapping['metadata']['available_sizes'],
        'available_colors': mapping['metadata']['available_colors']
    }
    
    return validation

def validate_pricing_tiers(mapping):
    """Validate products are correctly assigned to tiers based on pricing"""
    logger.info("Validating pricing-based tier assignment...")
    
    tier_prices = {
        'tier_1': [],
        'tier_2': [],
        'tier_3': []
    }
    
    for product_id, product_data in mapping['product_lookup'].items():
        tier = product_data['tier']
        price = product_data['list_price']
        
        if tier in tier_prices:
            tier_prices[tier].append(price)
    
    # Calculate statistics for each tier
    tier_stats = {}
    for tier, prices in tier_prices.items():
        if prices:
            tier_stats[tier] = {
                'count': len(prices),
                'avg_price': sum(prices) / len(prices),
                'min_price': min(prices),
                'max_price': max(prices)
            }
        else:
            tier_stats[tier] = {
                'count': 0,
                'avg_price': 0,
                'min_price': 0,
                'max_price': 0
            }
    
    # Validate tier 1 has higher average price than tier 2, tier 2 higher than tier 3
    tier_1_avg = tier_stats['tier_1']['avg_price']
    tier_2_avg = tier_stats['tier_2']['avg_price'] 
    tier_3_avg = tier_stats['tier_3']['avg_price']
    
    price_hierarchy_valid = tier_1_avg >= tier_2_avg >= tier_3_avg
    
    validation = {
        'tier_price_stats': tier_stats,
        'price_hierarchy_valid': price_hierarchy_valid,
        'tier_1_premium': tier_1_avg / tier_3_avg if tier_3_avg > 0 else 0
    }
    
    return validation

def main():
    """Main validation function"""
    try:
        # Load data
        analysis, mapping = load_data()
        
        # Run all validations
        print("\n" + "="*70)
        print("PRODUCT MAPPING VALIDATION REPORT")
        print("="*70)
        
        # 1. Product Coverage
        coverage = validate_product_coverage(analysis, mapping)
        print(f"\n1. PRODUCT COVERAGE")
        print(f"   ✅ Coverage: {coverage['coverage_percentage']:.1f}%")
        print(f"   📊 Analysis Products: {coverage['total_products_analysis']}")
        print(f"   📊 Mapped Products: {coverage['total_products_mapping']}")
        if coverage['missing_in_mapping']:
            print(f"   ⚠️  Missing: {len(coverage['missing_in_mapping'])} products")
        else:
            print(f"   ✅ All products mapped successfully")
        
        # 2. Tier Distribution
        tiers = validate_tier_distribution(mapping)
        print(f"\n2. TIER DISTRIBUTION")
        print(f"   📊 Tier 1: {tiers['tier_counts']['tier_1']} products ({tiers['tier_percentages']['tier_1']:.1f}%)")
        print(f"   📊 Tier 2: {tiers['tier_counts']['tier_2']} products ({tiers['tier_percentages']['tier_2']:.1f}%)")
        print(f"   📊 Tier 3: {tiers['tier_counts']['tier_3']} products ({tiers['tier_percentages']['tier_3']:.1f}%)")
        if tiers['overall_distribution_valid']:
            print(f"   ✅ Distribution within expected ranges")
        else:
            print(f"   ⚠️  Distribution outside expected ranges")
        
        # 3. Seasonal Patterns
        seasonal = validate_seasonal_patterns(mapping)
        print(f"\n3. SEASONAL PATTERNS")
        for pattern, categories in seasonal['category_patterns'].items():
            count = seasonal['seasonal_distribution'][pattern]
            print(f"   📊 {pattern.replace('_', ' ').title()}: {count} products ({', '.join(categories)})")
        if seasonal['all_patterns_valid']:
            print(f"   ✅ All seasonal patterns correctly assigned")
        else:
            invalid = [cat for cat, valid in seasonal['pattern_validation'].items() if not valid]
            print(f"   ⚠️  Invalid patterns for: {', '.join(invalid)}")
        
        # 4. Size and Color Distribution
        size_color = validate_size_color_weights(mapping)
        print(f"\n4. SIZE & COLOR DISTRIBUTION")
        print(f"   📊 Products with size info: {size_color['products_with_size']} ({size_color['size_coverage']:.1f}%)")
        print(f"   📊 Products with color info: {size_color['products_with_color']} ({size_color['color_coverage']:.1f}%)")
        print(f"   📊 Available sizes: {', '.join(size_color['available_sizes'])}")
        print(f"   📊 Available colors: {', '.join(size_color['available_colors'])}")
        
        # 5. Pricing Validation
        pricing = validate_pricing_tiers(mapping)
        print(f"\n5. PRICING TIER VALIDATION")
        for tier, stats in pricing['tier_price_stats'].items():
            print(f"   📊 {tier.replace('_', ' ').title()}: €{stats['avg_price']:.2f} avg (€{stats['min_price']:.2f}-€{stats['max_price']:.2f})")
        if pricing['price_hierarchy_valid']:
            print(f"   ✅ Price hierarchy correctly maintained")
            print(f"   📊 Tier 1 premium: {pricing['tier_1_premium']:.2f}x higher than Tier 3")
        else:
            print(f"   ⚠️  Price hierarchy not maintained")
        
        # Overall validation summary
        all_validations = [
            coverage['coverage_percentage'] >= 95,
            tiers['overall_distribution_valid'],
            seasonal['all_patterns_valid'],
            pricing['price_hierarchy_valid']
        ]
        
        print(f"\n" + "="*70)
        print("VALIDATION SUMMARY")
        print("="*70)
        if all(all_validations):
            print("🎉 ALL VALIDATIONS PASSED - Mapping is ready for transaction generation!")
        else:
            print("⚠️  Some validations failed - Review and adjust mapping if needed")
        
        print(f"\n📁 Mapping file: /workspaces/source-lovable-gympluscoffee/odoo-ingestion/product_mapping.json")
        print(f"📊 Total products mapped: {len(mapping['product_lookup'])}")
        print(f"🏷️  Revenue tiers: {len(mapping['revenue_tiers']['tier_1_high_volume'])} + {len(mapping['revenue_tiers']['tier_2_medium'])} + {len(mapping['revenue_tiers']['tier_3_low'])}")
        print(f"🗂️  Categories: {len(mapping['product_categories'])}")
        
        # Save validation report
        validation_report = {
            'validation_date': analysis['analysis_date'],
            'coverage': coverage,
            'tier_distribution': tiers,
            'seasonal_patterns': seasonal,
            'size_color_distribution': size_color,
            'pricing_validation': pricing,
            'overall_passed': all(all_validations)
        }
        
        report_file = '/workspaces/source-lovable-gympluscoffee/odoo-ingestion/mapping_validation_report.json'
        with open(report_file, 'w') as f:
            json.dump(validation_report, f, indent=2, default=str)
        print(f"📄 Validation report saved to: {report_file}")
        
    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise

if __name__ == "__main__":
    main()