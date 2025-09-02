# How to Use the Product Mapping

## 🎯 Quick Start Guide

The `product_mapping.json` file contains a comprehensive mapping of all 522 Odoo products with sales intelligence data.

## 📖 File Structure Overview

```json
{
  "metadata": {
    "total_products": 522,
    "categories": ["Hoodies", "T-Shirts", ...],
    "available_sizes": ["XS", "S", "M", "L", "XL", "XXL"],
    "available_colors": ["Black", "White", "Navy", ...],
    "mapping_rules": { ... }
  },
  "product_categories": { ... },
  "revenue_tiers": {
    "tier_1_high_volume": [101 product IDs],
    "tier_2_medium": [154 product IDs], 
    "tier_3_low": [267 product IDs]
  },
  "product_lookup": {
    "123": { full product data }
  }
}
```

## 🔍 Common Usage Patterns

### 1. Get Product by ID
```python
import json

with open('product_mapping.json', 'r') as f:
    mapping = json.load(f)

# Quick product lookup
product_id = "123"
product = mapping['product_lookup'][product_id]
print(f"Product: {product['name']}")
print(f"Category: {product['category']}")
print(f"Tier: {product['tier']}")
print(f"Revenue Weight: {product['revenue_weight']}")
```

### 2. Generate Sales by Revenue Tier
```python
import random

# Get high-volume products (should generate 60-75% of sales)
tier_1_products = mapping['revenue_tiers']['tier_1_high_volume']
tier_2_products = mapping['revenue_tiers']['tier_2_medium']
tier_3_products = mapping['revenue_tiers']['tier_3_low']

# Weighted random selection for transaction generation
def select_products_for_transaction(num_products=3):
    # 70% chance tier 1, 25% tier 2, 5% tier 3
    selected = []
    for _ in range(num_products):
        rand = random.random()
        if rand < 0.70:
            product_id = random.choice(tier_1_products)
        elif rand < 0.95:
            product_id = random.choice(tier_2_products)  
        else:
            product_id = random.choice(tier_3_products)
        selected.append(product_id)
    return selected
```

### 3. Apply Seasonal Boost
```python
from datetime import datetime

def get_seasonal_multiplier(product_id, month):
    product = mapping['product_lookup'][str(product_id)]
    seasonal_boost = product['seasonal_boost']
    
    # Check if month is in boost period
    if month in seasonal_boost['months']:
        return seasonal_boost['boost_factor']
    else:
        return 1.0

# Example: T-shirt sales in July (summer boost)
july_multiplier = get_seasonal_multiplier(product_id, 7)
base_sales = 10
boosted_sales = base_sales * july_multiplier
```

### 4. Generate Size Distribution
```python
def select_size_for_product(product_id):
    """Select size based on realistic distribution"""
    product = mapping['product_lookup'][str(product_id)]
    
    # If product has size, return it
    if product['product_attributes']['size']:
        return product['product_attributes']['size']
    
    # Otherwise, use statistical distribution
    size_weights = {
        'XS': 0.10, 'S': 0.20, 'M': 0.32, 
        'L': 0.25, 'XL': 0.15, 'XXL': 0.08
    }
    
    rand = random.random()
    cumulative = 0
    for size, weight in size_weights.items():
        cumulative += weight
        if rand < cumulative:
            return size
    return 'M'  # Default
```

### 5. Monthly Sales Recommendations
```python
def get_monthly_sales_target(product_id, month):
    """Get recommended sales volume for a product in specific month"""
    product = mapping['product_lookup'][str(product_id)]
    return product['recommended_monthly_sales'][str(month)]

# Example: Get sales targets for all products in December
december_targets = {}
for product_id in mapping['product_lookup']:
    target = get_monthly_sales_target(product_id, 12)
    december_targets[product_id] = target
```

### 6. Category-Based Selection
```python
def get_products_by_category(category_name):
    """Get all products in a specific category"""
    if category_name in mapping['product_categories']:
        return mapping['product_categories'][category_name]['products']
    return []

# Get all hoodies
hoodie_products = get_products_by_category('Hoodies')
print(f"Found {len(hoodie_products)} hoodie products")
```

### 7. Color-Based Weighting
```python
def select_color_variant(base_product_name):
    """Select color variant based on popularity weights"""
    color_weights = mapping['color_weights']
    
    # Find products with same base name but different colors
    variants = []
    for product in mapping['product_lookup'].values():
        if base_product_name.lower() in product['name'].lower():
            color = product['product_attributes']['color']
            if color:
                weight = color_weights.get(color, 1.0)
                variants.append((product['id'], weight))
    
    # Weighted random selection
    if variants:
        total_weight = sum(weight for _, weight in variants)
        rand = random.uniform(0, total_weight)
        cumulative = 0
        for product_id, weight in variants:
            cumulative += weight
            if rand < cumulative:
                return product_id
    
    return None
```

## 🔄 Integration Examples

### For Transaction Generation
```python
import random
from datetime import datetime

def generate_realistic_transaction(month=None):
    if not month:
        month = datetime.now().month
    
    # Select products based on tiers (70% T1, 25% T2, 5% T3)
    num_items = random.randint(1, 5)
    selected_products = []
    
    for _ in range(num_items):
        # Weighted tier selection
        rand = random.random()
        if rand < 0.70:
            tier_products = mapping['revenue_tiers']['tier_1_high_volume']
        elif rand < 0.95:
            tier_products = mapping['revenue_tiers']['tier_2_medium']
        else:
            tier_products = mapping['revenue_tiers']['tier_3_low']
        
        product_id = random.choice(tier_products)
        product = mapping['product_lookup'][str(product_id)]
        
        # Apply seasonal boost
        seasonal_multiplier = 1.0
        if month in product['seasonal_boost']['months']:
            seasonal_multiplier = product['seasonal_boost']['boost_factor']
        
        # Calculate quantity based on monthly recommendation
        base_qty = product['recommended_monthly_sales'][str(month)]
        final_qty = max(1, int(base_qty * seasonal_multiplier * random.uniform(0.5, 2.0)))
        
        selected_products.append({
            'product_id': product_id,
            'name': product['name'],
            'quantity': final_qty,
            'unit_price': product['list_price'],
            'seasonal_boost': seasonal_multiplier
        })
    
    return {
        'transaction_date': f"2024-{month:02d}-{random.randint(1, 28):02d}",
        'products': selected_products,
        'total_value': sum(p['quantity'] * p['unit_price'] for p in selected_products)
    }

# Generate sample transaction
transaction = generate_realistic_transaction(month=7)  # July
print(f"July transaction: €{transaction['total_value']:.2f}")
```

### For Inventory Management
```python
def get_inventory_priorities():
    """Get products that should have higher inventory based on tier"""
    high_priority = []
    medium_priority = []
    
    for product_id in mapping['revenue_tiers']['tier_1_high_volume']:
        product = mapping['product_lookup'][str(product_id)]
        high_priority.append({
            'id': product_id,
            'name': product['name'],
            'revenue_weight': product['revenue_weight']
        })
    
    return sorted(high_priority, key=lambda x: x['revenue_weight'], reverse=True)
```

## 📊 Key Metrics Available

- **Revenue Weight:** Indicates sales probability (1.0 to 10.5+)
- **Seasonal Boost:** Monthly multiplier (1.0 to 1.7) 
- **Tier Classification:** tier_1_high_volume, tier_2_medium, tier_3_low
- **Monthly Sales Targets:** Recommended volume per month
- **Size/Color Weights:** Popularity multipliers

## 🎯 Best Practices

1. **Always use revenue weights** when selecting products for transactions
2. **Apply seasonal boosts** based on the month of transaction
3. **Respect tier distributions** - 70% T1, 25% T2, 5% T3 for realistic sales
4. **Use size distribution** - M and L are most popular
5. **Favor popular colors** - Black, White, Navy have higher weights

## 📁 File Location
`/workspaces/source-lovable-gympluscoffee/odoo-ingestion/product_mapping.json`

This mapping contains everything needed to generate realistic transaction data that reflects actual product popularity, seasonal trends, and variant distributions.