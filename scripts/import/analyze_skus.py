#!/usr/bin/env python3
"""
Analyze SKUs in the scraped Kukoon Rugs data
"""

import json

# Load the data
with open('kukoon_products.json', 'r') as f:
    data = json.load(f)

products = data['products']
total_skus = 0
skus_per_product = []
unique_skus = set()

# Count SKUs
for product in products:
    product_sku_count = 0
    for variant in product.get('variants', []):
        if variant.get('sku'):
            unique_skus.add(variant['sku'])
            product_sku_count += 1
            total_skus += 1
    
    skus_per_product.append({
        'product': product['title'],
        'sku_count': product_sku_count,
        'variants': len(product.get('variants', []))
    })

# Analysis
print(f"Total products: {len(products)}")
print(f"Total variants: {sum(len(p.get('variants', [])) for p in products)}")
print(f"Total SKUs (non-empty): {total_skus}")
print(f"Unique SKUs: {len(unique_skus)}")

# Distribution
variant_counts = {}
for product in products:
    count = len(product.get('variants', []))
    variant_counts[count] = variant_counts.get(count, 0) + 1

print("\nVariants per product distribution:")
for count, num_products in sorted(variant_counts.items()):
    print(f"  {count} variants: {num_products} products")

# Check for missing data
print("\nChecking for potential missing data...")
print(f"Average variants per product: {sum(len(p.get('variants', [])) for p in products) / len(products):.1f}")

# Sample some products with many variants
print("\nProducts with most variants:")
sorted_products = sorted(skus_per_product, key=lambda x: x['sku_count'], reverse=True)
for i, p in enumerate(sorted_products[:10]):
    print(f"  {i+1}. {p['product'][:50]}... - {p['sku_count']} SKUs")