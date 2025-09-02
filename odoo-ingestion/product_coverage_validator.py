#!/usr/bin/env python3
"""
Product Coverage Validator and Fixer
====================================

Ensures every active SKU has sales data and validates revenue distribution patterns.
"""

import random
import logging
from typing import Dict, List, Tuple
from collections import defaultdict
from datetime import datetime, timedelta

class ProductCoverageValidator:
    def __init__(self, instance_id: str = "source-gym-plus-coffee"):
        self.instance_id = instance_id
        self.target_coverage = 100  # 100% of active SKUs should have sales
        self.revenue_80_20_min = 60  # Top 20% should generate at least 60% of revenue
        self.revenue_80_20_max = 75  # Top 20% should generate at most 75% of revenue
    
    def get_products_data(self) -> List[Dict]:
        """Get all active, saleable products"""
        try:
            # This will use MCP search_read
            domain = [
                ('active', '=', True),
                ('sale_ok', '=', True)
            ]
            fields = ['name', 'default_code', 'list_price', 'categ_id', 'type']
            
            products = []  # Will be populated by MCP tools
            return products
            
        except Exception as e:
            logging.error(f"Error fetching products: {e}")
            return []
    
    def get_sales_data(self, product_ids: List[int]) -> List[Dict]:
        """Get sales data for products"""
        try:
            # Get order lines for products
            domain = [
                ('product_id', 'in', product_ids),
                ('order_id.state', 'in', ['sale', 'done'])
            ]
            fields = ['product_id', 'product_uom_qty', 'price_subtotal', 'order_id']
            
            order_lines = []  # Will be populated by MCP tools
            return order_lines
            
        except Exception as e:
            logging.error(f"Error fetching sales data: {e}")
            return []
    
    def analyze_product_coverage(self, products: List[Dict], sales_data: List[Dict]) -> Dict:
        """Analyze which products have sales and revenue distribution"""
        
        # Create product sales mapping
        product_sales = defaultdict(lambda: {'qty': 0, 'revenue': 0, 'orders': set()})
        
        for line in sales_data:
            if line.get('product_id'):
                product_id = line['product_id'][0]
                product_sales[product_id]['qty'] += line.get('product_uom_qty', 0)
                product_sales[product_id]['revenue'] += line.get('price_subtotal', 0)
                if line.get('order_id'):
                    product_sales[product_id]['orders'].add(line['order_id'][0])
        
        # Analyze coverage
        total_products = len(products)
        products_with_sales = len([p for p in products if product_sales[p['id']]['revenue'] > 0])
        products_without_sales = [p for p in products if product_sales[p['id']]['revenue'] == 0]
        
        coverage_percentage = (products_with_sales / total_products * 100) if total_products > 0 else 0
        
        # Analyze revenue distribution (80/20 rule)
        product_revenues = [(p['id'], product_sales[p['id']]['revenue']) for p in products]
        product_revenues.sort(key=lambda x: x[1], reverse=True)
        
        total_revenue = sum(rev for _, rev in product_revenues)
        
        # Top 20% of products
        top_20_count = max(1, len(product_revenues) // 5)
        top_20_revenue = sum(rev for _, rev in product_revenues[:top_20_count])
        top_20_percentage = (top_20_revenue / total_revenue * 100) if total_revenue > 0 else 0
        
        return {
            'total_products': total_products,
            'products_with_sales': products_with_sales,
            'products_without_sales': len(products_without_sales),
            'products_without_sales_list': products_without_sales,
            'coverage_percentage': coverage_percentage,
            'total_revenue': total_revenue,
            'top_20_count': top_20_count,
            'top_20_revenue': top_20_revenue,
            'top_20_percentage': top_20_percentage,
            'product_sales_data': dict(product_sales)
        }
    
    def check_coverage_compliance(self, analysis: Dict) -> Dict:
        """Check if product coverage meets requirements"""
        issues = []
        
        # Check coverage percentage
        coverage_pct = analysis['coverage_percentage']
        if coverage_pct < self.target_coverage:
            issues.append({
                'type': 'coverage',
                'issue': f'Only {coverage_pct:.1f}% of products have sales (target: {self.target_coverage}%)',
                'severity': 'high',
                'products_affected': analysis['products_without_sales']
            })
        
        # Check 80/20 revenue distribution
        top_20_pct = analysis['top_20_percentage']
        if not (self.revenue_80_20_min <= top_20_pct <= self.revenue_80_20_max):
            severity = 'medium' if abs(top_20_pct - 67.5) < 10 else 'high'
            issues.append({
                'type': 'revenue_distribution',
                'issue': f'Top 20% products generate {top_20_pct:.1f}% of revenue (target: {self.revenue_80_20_min}-{self.revenue_80_20_max}%)',
                'severity': severity
            })
        
        is_compliant = len(issues) == 0
        
        return {
            'is_compliant': is_compliant,
            'issues': issues
        }
    
    def create_minimal_sales_for_products(self, products_without_sales: List[Dict]) -> List[Dict]:
        """Create minimal sales data for products without sales"""
        if not products_without_sales:
            return []
        
        # Limit the number of new sales to avoid system overload
        max_new_sales = min(20, len(products_without_sales))
        selected_products = random.sample(products_without_sales, max_new_sales)
        
        new_sales_data = []
        
        for product in selected_products:
            # Create a realistic sales scenario
            list_price = product.get('list_price', 50)
            
            # Create 1-3 sales per product
            num_sales = random.randint(1, 3)
            
            for _ in range(num_sales):
                sale_data = {
                    'product_id': product['id'],
                    'product_name': product.get('name', 'Unknown Product'),
                    'quantity': random.randint(1, 5),
                    'unit_price': list_price * random.uniform(0.8, 1.2),  # ±20% of list price
                    'channel': random.choice(['D2C', 'Retail', 'B2B']),
                    'sale_date': self._generate_random_date()
                }
                
                new_sales_data.append(sale_data)
        
        return new_sales_data
    
    def _generate_random_date(self) -> str:
        """Generate a random date within the last 12 months"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        random_date = start_date + timedelta(
            days=random.randint(0, (end_date - start_date).days)
        )
        
        return random_date.strftime('%Y-%m-%d')
    
    def get_sample_customers(self) -> List[Dict]:
        """Get sample customers for creating orders"""
        try:
            # This will use MCP search_read
            domain = [('customer_rank', '>', 0)]
            fields = ['name', 'country_id']
            
            customers = []  # Will be populated by MCP tools
            return customers
            
        except Exception as e:
            logging.error(f"Error fetching customers: {e}")
            return []
    
    def create_sales_orders_for_products(self, sales_data: List[Dict], customers: List[Dict]) -> List[Dict]:
        """Create actual sales orders and order lines"""
        if not sales_data or not customers:
            return []
        
        created_orders = []
        
        # Group sales by date and channel for efficiency
        grouped_sales = defaultdict(list)
        for sale in sales_data:
            key = (sale['sale_date'], sale['channel'])
            grouped_sales[key].append(sale)
        
        for (sale_date, channel), group_sales in grouped_sales.items():
            try:
                # Select random customer
                customer = random.choice(customers)
                
                # Create order data
                order_data = {
                    'partner_id': customer['id'],
                    'date_order': sale_date,
                    'x_channel': channel,
                    'state': 'sale'
                }
                
                # Calculate order total
                order_total = sum(sale['quantity'] * sale['unit_price'] for sale in group_sales)
                
                # Create order lines data
                order_lines = []
                for sale in group_sales:
                    line_data = {
                        'product_id': sale['product_id'],
                        'product_uom_qty': sale['quantity'],
                        'price_unit': sale['unit_price']
                    }
                    order_lines.append(line_data)
                
                created_orders.append({
                    'order_data': order_data,
                    'order_lines': order_lines,
                    'total_amount': order_total,
                    'products_count': len(order_lines)
                })
                
            except Exception as e:
                logging.error(f"Error creating order for date {sale_date}: {e}")
                continue
        
        return created_orders
    
    def apply_product_coverage_fixes(self, new_orders: List[Dict]) -> int:
        """Apply product coverage fixes by creating orders"""
        if not new_orders:
            return 0
        
        applied_count = 0
        
        try:
            for order_info in new_orders:
                try:
                    # Create the order using MCP tools
                    # order_id = create_record('sale.order', order_info['order_data'])
                    order_id = f"test_order_{applied_count}"  # Placeholder
                    
                    if order_id:
                        # Create order lines
                        for line_data in order_info['order_lines']:
                            line_data['order_id'] = order_id
                            # line_id = create_record('sale.order.line', line_data)
                        
                        applied_count += 1
                        logging.info(f"Created order with {len(order_info['order_lines'])} products")
                
                except Exception as e:
                    logging.error(f"Error creating individual order: {e}")
                    continue
        
        except Exception as e:
            logging.error(f"Error applying product coverage fixes: {e}")
        
        return applied_count
    
    def optimize_revenue_distribution(self, products: List[Dict], sales_analysis: Dict) -> List[Dict]:
        """Optimize revenue distribution to meet 80/20 targets"""
        current_top_20_pct = sales_analysis['top_20_percentage']
        
        if self.revenue_80_20_min <= current_top_20_pct <= self.revenue_80_20_max:
            return []  # Already compliant
        
        adjustments = []
        
        # Get top and bottom performing products
        product_revenues = []
        for product in products:
            revenue = sales_analysis['product_sales_data'].get(product['id'], {}).get('revenue', 0)
            product_revenues.append((product, revenue))
        
        product_revenues.sort(key=lambda x: x[1], reverse=True)
        
        total_products = len(product_revenues)
        top_20_count = max(1, total_products // 5)
        
        # If top 20% generates too little revenue, boost top performers
        if current_top_20_pct < self.revenue_80_20_min:
            boost_products = product_revenues[:top_20_count]
            
            for product, current_revenue in boost_products:
                if current_revenue > 0:  # Only boost products that already have sales
                    # Suggest boosting sales for these products
                    adjustments.append({
                        'type': 'boost_sales',
                        'product_id': product['id'],
                        'product_name': product.get('name'),
                        'current_revenue': current_revenue,
                        'suggested_boost': 'Increase marketing/promotion for this top performer'
                    })
        
        # If top 20% generates too much revenue, diversify
        elif current_top_20_pct > self.revenue_80_20_max:
            bottom_80_products = product_revenues[top_20_count:]
            
            # Select some bottom performers to boost
            boost_count = min(10, len(bottom_80_products))
            products_to_boost = random.sample(bottom_80_products[:50], boost_count)  # From products ranked 20-70%
            
            for product, current_revenue in products_to_boost:
                adjustments.append({
                    'type': 'diversify_sales',
                    'product_id': product['id'],
                    'product_name': product.get('name'),
                    'current_revenue': current_revenue,
                    'suggested_action': 'Create promotional campaigns for this mid-tier product'
                })
        
        return adjustments
    
    def validate_and_fix_product_coverage(self) -> Dict:
        """Main method to validate and fix product coverage"""
        try:
            # Get products data
            products = self.get_products_data()
            
            if not products:
                return {'error': 'No products found'}
            
            product_ids = [p['id'] for p in products]
            
            # Get sales data
            sales_data = self.get_sales_data(product_ids)
            
            # Analyze coverage
            analysis = self.analyze_product_coverage(products, sales_data)
            
            # Check compliance
            compliance = self.check_coverage_compliance(analysis)
            
            # Apply fixes if needed
            fixes_applied = 0
            
            if not compliance['is_compliant']:
                # Get customers for creating orders
                customers = self.get_sample_customers()
                
                # Create sales for products without sales
                if analysis['products_without_sales_list']:
                    new_sales_data = self.create_minimal_sales_for_products(
                        analysis['products_without_sales_list']
                    )
                    
                    if new_sales_data and customers:
                        new_orders = self.create_sales_orders_for_products(new_sales_data, customers)
                        fixes_applied = self.apply_product_coverage_fixes(new_orders)
                
                # Optimize revenue distribution
                revenue_adjustments = self.optimize_revenue_distribution(products, analysis)
            
            return {
                'analysis': analysis,
                'compliance': compliance,
                'fixes_applied': fixes_applied,
                'revenue_adjustments': revenue_adjustments if 'revenue_adjustments' in locals() else [],
                'status': 'compliant' if compliance['is_compliant'] else 'non_compliant'
            }
            
        except Exception as e:
            logging.error(f"Error in product coverage validation: {e}")
            return {'error': str(e)}


def main():
    """Test the product coverage validator"""
    validator = ProductCoverageValidator()
    results = validator.validate_and_fix_product_coverage()
    
    print("Product Coverage Validation Results:")
    print(f"Status: {results.get('status', 'error')}")
    if 'fixes_applied' in results:
        print(f"Fixes Applied: {results['fixes_applied']}")
    if 'revenue_adjustments' in results:
        print(f"Revenue Adjustments Suggested: {len(results['revenue_adjustments'])}")


if __name__ == "__main__":
    main()