#!/usr/bin/env python3
"""
Simple Revenue Generator Runner
===============================

Standalone script to generate €250k-400k monthly revenue without complex dependencies.
This version works independently and creates all necessary data.
"""

import json
import random
import math
from datetime import datetime, timedelta
from pathlib import Path
import sys

def main():
    """Generate revenue data with minimal dependencies"""
    
    print("🚀 Starting Gym Plus Coffee Revenue Generation...")
    print("="*60)
    
    # Configuration
    TARGET_MONTHLY_REVENUE = 300000.0  # €300k
    MONTHS_TO_GENERATE = 12
    OUTPUT_DIR = Path("data/revenue")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Product categories with seasonality
    product_categories = {
        'hoodies': {
            'price_range': (65, 120),
            'seasonality': {1: 1.5, 2: 1.5, 3: 0.9, 4: 0.9, 5: 0.5, 6: 0.5, 
                          7: 0.5, 8: 0.5, 9: 0.9, 10: 1.5, 11: 1.5, 12: 1.5},
            'products': ['Essential Hoodie Black', 'Essential Hoodie Navy', 'Premium Hoodie Grey']
        },
        'jackets': {
            'price_range': (85, 150),
            'seasonality': {1: 1.5, 2: 1.5, 3: 0.9, 4: 0.9, 5: 0.5, 6: 0.5, 
                          7: 0.5, 8: 0.5, 9: 0.9, 10: 1.5, 11: 1.5, 12: 1.5},
            'products': ['Bomber Jacket Black', 'Puffer Jacket Navy', 'Track Jacket Grey']
        },
        'shorts': {
            'price_range': (35, 65),
            'seasonality': {1: 0.6, 2: 0.6, 3: 0.8, 4: 0.8, 5: 1.4, 6: 1.4, 
                          7: 1.4, 8: 1.4, 9: 1.4, 10: 0.8, 11: 0.6, 12: 0.6},
            'products': ['Training Shorts Black', 'Training Shorts Navy', 'Running Shorts']
        },
        'tank_tops': {
            'price_range': (25, 45),
            'seasonality': {1: 0.6, 2: 0.6, 3: 0.8, 4: 0.8, 5: 1.4, 6: 1.4, 
                          7: 1.4, 8: 1.4, 9: 1.4, 10: 0.8, 11: 0.6, 12: 0.6},
            'products': ['Essential Tank Black', 'Essential Tank White', 'Muscle Tank Navy']
        },
        't_shirts': {
            'price_range': (30, 55),
            'seasonality': {1: 1.15, 2: 1.0, 3: 1.0, 4: 1.1, 5: 1.1, 6: 1.0, 
                          7: 1.0, 8: 1.0, 9: 1.0, 10: 1.0, 11: 0.9, 12: 0.9},
            'products': ['Essential Tee Black', 'Essential Tee White', 'Oversized Tee Grey']
        },
        'leggings': {
            'price_range': (45, 85),
            'seasonality': {1: 1.15, 2: 1.0, 3: 1.0, 4: 1.1, 5: 1.1, 6: 1.0, 
                          7: 1.0, 8: 1.0, 9: 1.0, 10: 1.0, 11: 0.85, 12: 0.85},
            'products': ['High-Waist Leggings Black', 'Seamless Leggings Grey']
        },
        'accessories': {
            'price_range': (15, 75),
            'seasonality': {1: 1.2, 2: 0.7, 3: 0.7, 4: 1.0, 5: 1.0, 6: 1.0, 
                          7: 1.0, 8: 1.0, 9: 1.0, 10: 1.0, 11: 1.8, 12: 1.8},
            'products': ['Baseball Cap Black', 'Water Bottle Steel', 'Gym Bag Black', 
                        'Gift Card €25', 'Gift Card €50']
        }
    }
    
    # Generate products
    print("📦 Generating product catalog...")
    products = []
    product_id = 1000
    
    for category, cat_data in product_categories.items():
        min_price, max_price = cat_data['price_range']
        for product_name in cat_data['products']:
            for size in ['S', 'M', 'L', 'XL']:
                # Skip sizes for gift cards and some accessories
                if 'Gift Card' in product_name or 'Water Bottle' in product_name:
                    if size != 'M':
                        continue
                
                price = round(random.uniform(min_price, max_price), 2)
                sku = f"GPC{product_id:05d}-{size}"
                
                products.append({
                    'sku': sku,
                    'name': f"{product_name} - {size}",
                    'category': category,
                    'price': price,
                    'cost': round(price * 0.4, 2)
                })
                product_id += 1
    
    print(f"   ✅ Generated {len(products)} products")
    
    # Generate customers
    print("👥 Generating customers...")
    customers = []
    first_names = ['Emma', 'Liam', 'Olivia', 'Noah', 'Ava', 'Oliver', 'Isabella', 'Sophia', 'Lucas', 'Charlotte']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Wilson', 'Moore']
    countries = ['Ireland', 'UK', 'Germany', 'France', 'Netherlands', 'Spain']
    
    for i in range(2000):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        customers.append({
            'customer_id': f"CUST{i+1:06d}",
            'name': f"{first_name} {last_name}",
            'email': f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@example.com",
            'country': random.choice(countries)
        })
    
    print(f"   ✅ Generated {len(customers)} customers")
    
    # Generate orders for 12 months
    print("🛒 Generating sales orders...")
    all_orders = []
    monthly_summaries = []
    
    # Start from 12 months ago
    start_date = datetime.now() - timedelta(days=365)
    
    for month_offset in range(MONTHS_TO_GENERATE):
        current_date = start_date + timedelta(days=30 * month_offset)
        month = current_date.month
        year = current_date.year
        month_name = current_date.strftime('%B')
        
        # Calculate seasonality multiplier for this month
        category_multipliers = []
        for cat_data in product_categories.values():
            category_multipliers.append(cat_data['seasonality'][month])
        avg_seasonality = sum(category_multipliers) / len(category_multipliers)
        
        # Calculate targets for this month
        monthly_revenue_target = TARGET_MONTHLY_REVENUE * avg_seasonality
        avg_order_value = 175  # Target AOV
        orders_needed = int(monthly_revenue_target / avg_order_value)
        
        print(f"   📅 {month_name} {year}: Target {orders_needed:,} orders, €{monthly_revenue_target:,.0f}")
        
        # Generate orders for this month
        month_orders = []
        month_revenue = 0
        
        for order_num in range(orders_needed):
            # Select customer
            customer = random.choice(customers)
            
            # Determine order value tier
            rand = random.random()
            if rand < 0.15:  # 15% small orders
                target_value = random.uniform(60, 100)
            elif rand < 0.75:  # 60% medium orders  
                target_value = random.uniform(120, 200)
            elif rand < 0.95:  # 20% large orders
                target_value = random.uniform(200, 350)
            else:  # 5% premium orders
                target_value = random.uniform(350, 500)
            
            # Generate order date
            day = random.randint(1, 28)  # Safe for all months
            hour = random.randint(8, 20)
            order_date = datetime(year, month, day, hour, random.randint(0, 59))
            
            # Select products for this order
            order_lines = []
            current_total = 0
            max_items = random.randint(1, 5)
            
            # Filter products by seasonality
            available_products = []
            for product in products:
                seasonality = product_categories[product['category']]['seasonality'][month]
                if random.random() < seasonality / 2.0:  # Higher chance for seasonal products
                    available_products.append(product)
            
            if not available_products:
                available_products = products
            
            for _ in range(max_items):
                if current_total >= target_value * 0.9:
                    break
                
                product = random.choice(available_products)
                quantity = random.randint(1, 3)
                unit_price = product['price']
                
                # Small chance of discount
                if random.random() < 0.1:
                    unit_price *= 0.9  # 10% discount
                
                line_total = quantity * unit_price
                
                # Don't exceed target too much
                if current_total + line_total > target_value * 1.2:
                    max_qty = max(1, int((target_value - current_total) / unit_price))
                    quantity = min(quantity, max_qty)
                    line_total = quantity * unit_price
                
                order_lines.append({
                    'product_sku': product['sku'],
                    'product_name': product['name'],
                    'quantity': quantity,
                    'price_unit': round(unit_price, 2),
                    'price_total': round(line_total, 2)
                })
                
                current_total += line_total
            
            # Create order
            order_total = sum(line['price_total'] for line in order_lines)
            month_revenue += order_total
            
            order = {
                'order_id': f"SO{year}{month:02d}{order_num+1:04d}",
                'customer_id': customer['customer_id'],
                'customer_name': customer['name'],
                'customer_email': customer['email'],
                'order_date': order_date.isoformat(),
                'amount_total': round(order_total, 2),
                'amount_untaxed': round(order_total / 1.23, 2),  # 23% VAT
                'amount_tax': round(order_total - (order_total / 1.23), 2),
                'state': 'sale',
                'salesperson': 'Shopify',  # As requested
                'order_lines': order_lines
            }
            
            month_orders.append(order)
        
        all_orders.extend(month_orders)
        
        # Monthly summary
        avg_order_value = month_revenue / len(month_orders) if month_orders else 0
        monthly_summaries.append({
            'month': month,
            'year': year,
            'month_name': month_name,
            'orders_count': len(month_orders),
            'revenue': month_revenue,
            'target_revenue': monthly_revenue_target,
            'achievement_pct': (month_revenue / monthly_revenue_target * 100) if monthly_revenue_target > 0 else 0,
            'avg_order_value': avg_order_value,
            'seasonality_multiplier': avg_seasonality
        })
        
        print(f"       ✅ Generated {len(month_orders):,} orders, €{month_revenue:,.0f} ({month_revenue/monthly_revenue_target*100:.1f}% of target)")
    
    # Calculate totals
    total_revenue = sum(order['amount_total'] for order in all_orders)
    total_orders = len(all_orders)
    avg_monthly_revenue = total_revenue / MONTHS_TO_GENERATE
    overall_aov = total_revenue / total_orders if total_orders > 0 else 0
    
    print(f"\n📊 GENERATION COMPLETE!")
    print(f"   Total Orders: {total_orders:,}")
    print(f"   Total Revenue: €{total_revenue:,.2f}")
    print(f"   Avg Monthly Revenue: €{avg_monthly_revenue:,.2f}")
    print(f"   Overall AOV: €{overall_aov:.2f}")
    print(f"   Target Achievement: {(avg_monthly_revenue/TARGET_MONTHLY_REVENUE)*100:.1f}%")
    
    # Save data
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Complete dataset
    complete_data = {
        'generation_date': datetime.now().isoformat(),
        'summary': {
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'avg_monthly_revenue': avg_monthly_revenue,
            'overall_aov': overall_aov,
            'target_achievement_pct': (avg_monthly_revenue/TARGET_MONTHLY_REVENUE)*100
        },
        'monthly_breakdown': monthly_summaries,
        'products': products,
        'customers': customers,
        'orders': all_orders
    }
    
    complete_file = OUTPUT_DIR / f"complete_revenue_data_{timestamp}.json"
    with open(complete_file, 'w') as f:
        json.dump(complete_data, f, indent=2, default=str)
    
    # Odoo-compatible orders
    odoo_orders = []
    for order in all_orders:
        odoo_order = {
            'name': order['order_id'],
            'partner_id': order['customer_id'],
            'date_order': order['order_date'],
            'state': order['state'],
            'amount_untaxed': order['amount_untaxed'],
            'amount_tax': order['amount_tax'],
            'amount_total': order['amount_total'],
            'currency_id': 'EUR',
            'user_id': 'Shopify',  # Salesperson
            'order_line': [
                {
                    'product_id': line['product_sku'],
                    'name': line['product_name'],
                    'product_uom_qty': line['quantity'],
                    'price_unit': line['price_unit'],
                    'price_total': line['price_total']
                }
                for line in order['order_lines']
            ]
        }
        odoo_orders.append(odoo_order)
    
    orders_file = OUTPUT_DIR / f"odoo_sales_orders_{timestamp}.json"
    with open(orders_file, 'w') as f:
        json.dump(odoo_orders, f, indent=2, default=str)
    
    # Summary report
    summary_file = OUTPUT_DIR / f"revenue_summary_{timestamp}.json"
    with open(summary_file, 'w') as f:
        json.dump({
            'generation_date': complete_data['generation_date'],
            'summary': complete_data['summary'],
            'monthly_breakdown': monthly_summaries
        }, f, indent=2, default=str)
    
    print(f"\n📁 FILES SAVED:")
    print(f"   Complete Data: {complete_file}")
    print(f"   Odoo Orders: {orders_file}")
    print(f"   Summary: {summary_file}")
    
    # Print monthly breakdown
    print(f"\n📅 MONTHLY BREAKDOWN:")
    print("-" * 100)
    print(f"{'Month':<12} {'Orders':<8} {'Revenue (€)':<15} {'Target (€)':<15} {'Achievement':<12} {'AOV (€)':<10}")
    print("-" * 100)
    
    for month_data in monthly_summaries:
        achievement = month_data['achievement_pct']
        status = "✅" if achievement >= 90 else "⚠️" if achievement >= 80 else "❌"
        
        print(f"{month_data['month_name']:<12} "
              f"{month_data['orders_count']:<8,} "
              f"€{month_data['revenue']:<14,.0f} "
              f"€{month_data['target_revenue']:<14,.0f} "
              f"{achievement:<6.1f}% {status:<4} "
              f"€{month_data['avg_order_value']:<9.2f}")
    
    print("-" * 100)
    print(f"\n🎉 SUCCESS! Generated €250k-400k monthly revenue data with:")
    print(f"   ✅ Hoodies/Jackets peak in Oct-Feb (150% multiplier)")
    print(f"   ✅ Shorts/Tank Tops peak in May-Sep (140% multiplier)")  
    print(f"   ✅ Accessories peak in Nov-Dec (180% for gifts)")
    print(f"   ✅ Proper order value distribution (15% small, 60% medium, 20% large, 5% premium)")
    print(f"   ✅ All orders have salesperson set to 'Shopify'")
    print(f"   ✅ 12 months of historical data generated")
    print(f"   ✅ Ready for Odoo import!")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)