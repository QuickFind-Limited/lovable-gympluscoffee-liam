#!/usr/bin/env python3
"""
Data Analysis Utility for Transformed Gym+Coffee Data

This script provides analysis and reporting capabilities for the transformed data,
helping to understand patterns, validate business logic, and generate insights.
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
from pathlib import Path
import logging
from typing import Dict, List, Any, Optional
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataAnalyzer:
    """Analyzes transformed Gym+Coffee data for insights and validation"""
    
    def __init__(self, data_dir: str = "../data/transformed"):
        self.data_dir = Path(data_dir)
        
        # Load data files
        self.data = {}
        self._load_data_files()
        
        # Analysis results
        self.analysis_results = {
            'analysis_date': datetime.now().isoformat(),
            'data_summary': {},
            'business_insights': {},
            'data_quality': {},
            'recommendations': []
        }
    
    def _load_data_files(self) -> None:
        """Load all transformed data files"""
        file_mappings = {
            'products': 'odoo_product_variants.csv',
            'product_templates': 'odoo_product_templates.csv',
            'customers': 'odoo_customers.csv',
            'orders': 'odoo_sales_orders.csv',
            'order_lines': 'odoo_order_lines.csv',
            'categories': 'odoo_product_categories.csv'
        }
        
        for key, filename in file_mappings.items():
            file_path = self.data_dir / filename
            if file_path.exists():
                try:
                    self.data[key] = pd.read_csv(file_path)
                    logger.info(f"Loaded {len(self.data[key])} records from {filename}")
                except Exception as e:
                    logger.error(f"Error loading {filename}: {e}")
            else:
                logger.warning(f"File not found: {filename}")
    
    def analyze_product_data(self) -> Dict[str, Any]:
        """Analyze product data patterns"""
        if 'products' not in self.data or self.data['products'].empty:
            return {'error': 'No product data available'}
        
        df = self.data['products']
        templates_df = self.data.get('product_templates', pd.DataFrame())
        
        analysis = {
            'total_products': len(df),
            'total_templates': len(templates_df),
            'variants_per_template': len(df) / len(templates_df) if not templates_df.empty else 0,
            
            # Price analysis
            'price_statistics': {
                'min_price': float(df['list_price'].min()) if 'list_price' in df.columns else 0,
                'max_price': float(df['list_price'].max()) if 'list_price' in df.columns else 0,
                'avg_price': float(df['list_price'].mean()) if 'list_price' in df.columns else 0,
                'median_price': float(df['list_price'].median()) if 'list_price' in df.columns else 0
            },
            
            # Category distribution
            'category_distribution': {},
            'color_distribution': {},
            'size_distribution': {},
            
            # Inventory analysis
            'inventory_statistics': {
                'total_inventory_value': 0,
                'out_of_stock_products': 0,
                'low_stock_products': 0,
                'avg_inventory_level': 0
            }
        }
        
        # Category analysis
        if 'product_category' in df.columns:
            analysis['category_distribution'] = df['product_category'].value_counts().to_dict()
        elif 'category' in df.columns:
            analysis['category_distribution'] = df['category'].value_counts().to_dict()
        
        # Color and size analysis
        if 'color_value' in df.columns:
            analysis['color_distribution'] = df['color_value'].value_counts().to_dict()
        
        if 'size_value' in df.columns:
            analysis['size_distribution'] = df['size_value'].value_counts().to_dict()
        
        # Inventory analysis
        if 'qty_available' in df.columns and 'list_price' in df.columns:
            analysis['inventory_statistics']['total_inventory_value'] = float(
                (df['qty_available'] * df['list_price']).sum()
            )
            analysis['inventory_statistics']['out_of_stock_products'] = (df['qty_available'] <= 0).sum()
            analysis['inventory_statistics']['low_stock_products'] = (
                (df['qty_available'] > 0) & (df['qty_available'] <= 10)
            ).sum()
            analysis['inventory_statistics']['avg_inventory_level'] = float(df['qty_available'].mean())
        
        return analysis
    
    def analyze_customer_data(self) -> Dict[str, Any]:
        """Analyze customer data patterns"""
        if 'customers' not in self.data or self.data['customers'].empty:
            return {'error': 'No customer data available'}
        
        df = self.data['customers']
        
        analysis = {
            'total_customers': len(df),
            
            # Segmentation analysis
            'segment_distribution': {},
            'geographic_distribution': {},
            'company_vs_individual': {},
            
            # Spending analysis
            'spending_statistics': {
                'avg_expected_spend': 0,
                'total_expected_spend': 0,
                'spending_by_segment': {}
            },
            
            # Data quality
            'data_quality_metrics': {
                'missing_emails': 0,
                'missing_addresses': 0,
                'invalid_countries': 0
            }
        }
        
        # Segmentation analysis
        if 'category_id' in df.columns:
            segment_map = {
                'gym_coffee_cat_consumer': 'Consumer',
                'gym_coffee_cat_corporate': 'Corporate',
                'gym_coffee_cat_home_office': 'Home Office'
            }
            df['segment'] = df['category_id'].map(segment_map).fillna('Unknown')
            analysis['segment_distribution'] = df['segment'].value_counts().to_dict()
        
        # Geographic analysis
        if 'country_id' in df.columns:
            analysis['geographic_distribution'] = df['country_id'].value_counts().head(10).to_dict()
        
        # Company vs individual
        if 'is_company' in df.columns:
            analysis['company_vs_individual'] = {
                'companies': (df['is_company'] == True).sum(),
                'individuals': (df['is_company'] == False).sum()
            }
        
        # Spending analysis
        if 'expected_annual_spend' in df.columns:
            analysis['spending_statistics']['avg_expected_spend'] = float(df['expected_annual_spend'].mean())
            analysis['spending_statistics']['total_expected_spend'] = float(df['expected_annual_spend'].sum())
            
            if 'segment' in df.columns:
                spending_by_segment = df.groupby('segment')['expected_annual_spend'].agg(['mean', 'count']).to_dict()
                analysis['spending_statistics']['spending_by_segment'] = {
                    segment: {'avg_spend': float(mean), 'customer_count': int(count)}
                    for segment, mean, count in zip(
                        spending_by_segment['mean'].keys(),
                        spending_by_segment['mean'].values(),
                        spending_by_segment['count'].values()
                    )
                }
        
        # Data quality metrics
        if 'email' in df.columns:
            analysis['data_quality_metrics']['missing_emails'] = df['email'].isna().sum()
        
        if 'street' in df.columns:
            analysis['data_quality_metrics']['missing_addresses'] = df['street'].isna().sum()
        
        return analysis
    
    def analyze_order_data(self) -> Dict[str, Any]:
        """Analyze order data patterns"""
        if 'orders' not in self.data or self.data['orders'].empty:
            return {'error': 'No order data available'}
        
        orders_df = self.data['orders']
        lines_df = self.data.get('order_lines', pd.DataFrame())
        
        analysis = {
            'total_orders': len(orders_df),
            'total_order_lines': len(lines_df),
            'avg_items_per_order': len(lines_df) / len(orders_df) if len(orders_df) > 0 else 0,
            
            # Revenue analysis
            'revenue_statistics': {
                'total_revenue': 0,
                'avg_order_value': 0,
                'median_order_value': 0,
                'revenue_by_month': {},
                'revenue_by_segment': {}
            },
            
            # Order status analysis
            'status_distribution': {},
            'shipping_analysis': {},
            
            # Product popularity
            'product_popularity': {},
            'category_performance': {},
            
            # Customer behavior
            'customer_behavior': {
                'repeat_customers': 0,
                'orders_per_customer': 0,
                'segment_preferences': {}
            }
        }
        
        # Revenue analysis
        if 'amount_total' in orders_df.columns:
            analysis['revenue_statistics']['total_revenue'] = float(orders_df['amount_total'].sum())
            analysis['revenue_statistics']['avg_order_value'] = float(orders_df['amount_total'].mean())
            analysis['revenue_statistics']['median_order_value'] = float(orders_df['amount_total'].median())
            
            # Monthly revenue
            if 'order_month' in orders_df.columns:
                monthly_revenue = orders_df.groupby('order_month')['amount_total'].sum().to_dict()
                analysis['revenue_statistics']['revenue_by_month'] = {
                    str(k): float(v) for k, v in monthly_revenue.items()
                }
            
            # Revenue by segment
            if 'customer_segment' in orders_df.columns:
                segment_revenue = orders_df.groupby('customer_segment')['amount_total'].sum().to_dict()
                analysis['revenue_statistics']['revenue_by_segment'] = {
                    str(k): float(v) for k, v in segment_revenue.items()
                }
        
        # Order status analysis
        if 'state' in orders_df.columns:
            analysis['status_distribution'] = orders_df['state'].value_counts().to_dict()
        
        if 'delivery_method' in orders_df.columns:
            analysis['shipping_analysis'] = orders_df['delivery_method'].value_counts().to_dict()
        
        # Product popularity analysis
        if not lines_df.empty:
            if 'product_id' in lines_df.columns and 'product_uom_qty' in lines_df.columns:
                product_sales = lines_df.groupby('product_id')['product_uom_qty'].sum().sort_values(ascending=False)
                analysis['product_popularity'] = product_sales.head(10).to_dict()
            
            if 'product_category' in lines_df.columns and 'price_total' in lines_df.columns:
                category_revenue = lines_df.groupby('product_category')['price_total'].sum().sort_values(ascending=False)
                analysis['category_performance'] = category_revenue.to_dict()
        
        # Customer behavior analysis
        if 'partner_id' in orders_df.columns:
            customer_order_counts = orders_df['partner_id'].value_counts()
            analysis['customer_behavior']['repeat_customers'] = (customer_order_counts > 1).sum()
            analysis['customer_behavior']['orders_per_customer'] = float(customer_order_counts.mean())
        
        return analysis
    
    def analyze_seasonal_patterns(self) -> Dict[str, Any]:
        """Analyze seasonal buying patterns"""
        if 'orders' not in self.data or 'order_lines' not in self.data:
            return {'error': 'Order data not available for seasonal analysis'}
        
        orders_df = self.data['orders']
        lines_df = self.data['order_lines']
        
        analysis = {
            'monthly_patterns': {},
            'category_seasonality': {},
            'recommendations': []
        }
        
        # Monthly order patterns
        if 'order_month' in orders_df.columns:
            monthly_orders = orders_df['order_month'].value_counts().sort_index()
            monthly_revenue = orders_df.groupby('order_month')['amount_total'].sum() if 'amount_total' in orders_df.columns else pd.Series()
            
            for month in range(1, 13):
                month_name = datetime(2024, month, 1).strftime('%B')
                analysis['monthly_patterns'][month_name] = {
                    'order_count': int(monthly_orders.get(month, 0)),
                    'revenue': float(monthly_revenue.get(month, 0)) if not monthly_revenue.empty else 0
                }
        
        # Category seasonality
        if 'product_category' in lines_df.columns:
            # Merge with orders to get month information
            lines_with_month = lines_df.merge(
                orders_df[['external_id', 'order_month']], 
                left_on='order_id', 
                right_on='external_id',
                how='left'
            )
            
            if 'order_month' in lines_with_month.columns:
                category_monthly = lines_with_month.groupby(['product_category', 'order_month']).size().unstack(fill_value=0)
                
                # Calculate seasonal indices (compared to average month)
                for category in category_monthly.index:
                    monthly_sales = category_monthly.loc[category]
                    avg_monthly = monthly_sales.mean()
                    
                    if avg_monthly > 0:
                        seasonal_index = (monthly_sales / avg_monthly).to_dict()
                        analysis['category_seasonality'][category] = {
                            month: float(index) for month, index in seasonal_index.items()
                        }
        
        # Generate recommendations
        analysis['recommendations'] = self._generate_seasonal_recommendations(analysis)
        
        return analysis
    
    def _generate_seasonal_recommendations(self, seasonal_data: Dict[str, Any]) -> List[str]:
        """Generate business recommendations based on seasonal analysis"""
        recommendations = []
        
        # Analyze category seasonality for recommendations
        if 'category_seasonality' in seasonal_data:
            for category, monthly_indices in seasonal_data['category_seasonality'].items():
                if not monthly_indices:
                    continue
                
                # Find peak months (index > 1.2)
                peak_months = [month for month, index in monthly_indices.items() if index > 1.2]
                low_months = [month for month, index in monthly_indices.items() if index < 0.8]
                
                if peak_months:
                    month_names = [datetime(2024, int(m), 1).strftime('%B') for m in peak_months]
                    recommendations.append(
                        f"Increase {category} inventory before {', '.join(month_names)} (peak season)"
                    )
                
                if low_months:
                    month_names = [datetime(2024, int(m), 1).strftime('%B') for m in low_months]
                    recommendations.append(
                        f"Consider promotions for {category} during {', '.join(month_names)} (low season)"
                    )
        
        return recommendations
    
    def generate_data_quality_report(self) -> Dict[str, Any]:
        """Generate comprehensive data quality report"""
        report = {
            'overall_score': 0,
            'issues_found': [],
            'recommendations': [],
            'detailed_checks': {}
        }
        
        total_checks = 0
        passed_checks = 0
        
        # Check each dataset
        for dataset_name, df in self.data.items():
            if df.empty:
                continue
            
            dataset_checks = {
                'record_count': len(df),
                'column_count': len(df.columns),
                'missing_data_percentage': 0,
                'duplicate_records': 0,
                'data_type_issues': 0
            }
            
            # Missing data check
            missing_percentage = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
            dataset_checks['missing_data_percentage'] = round(missing_percentage, 2)
            
            if missing_percentage < 5:
                passed_checks += 1
            else:
                report['issues_found'].append(f"{dataset_name}: High missing data percentage ({missing_percentage:.1f}%)")
            total_checks += 1
            
            # Duplicate records check
            if 'external_id' in df.columns:
                duplicates = df['external_id'].duplicated().sum()
                dataset_checks['duplicate_records'] = duplicates
                
                if duplicates == 0:
                    passed_checks += 1
                else:
                    report['issues_found'].append(f"{dataset_name}: {duplicates} duplicate external_id values")
                total_checks += 1
            
            # Data type consistency checks
            numeric_issues = 0
            for col in df.columns:
                if 'price' in col.lower() or 'amount' in col.lower() or 'qty' in col.lower():
                    try:
                        pd.to_numeric(df[col], errors='coerce')
                    except:
                        numeric_issues += 1
            
            dataset_checks['data_type_issues'] = numeric_issues
            if numeric_issues == 0:
                passed_checks += 1
            else:
                report['issues_found'].append(f"{dataset_name}: {numeric_issues} columns with data type issues")
            total_checks += 1
            
            report['detailed_checks'][dataset_name] = dataset_checks
        
        # Calculate overall score
        if total_checks > 0:
            report['overall_score'] = round((passed_checks / total_checks) * 100, 1)
        
        # Generate recommendations
        if report['overall_score'] < 90:
            report['recommendations'].append("Review data transformation logic to reduce missing data")
        if any('duplicate' in issue for issue in report['issues_found']):
            report['recommendations'].append("Implement stricter unique constraint validation")
        if any('data type' in issue for issue in report['issues_found']):
            report['recommendations'].append("Add data type validation in transformation scripts")
        
        return report
    
    def run_full_analysis(self) -> Dict[str, Any]:
        """Run complete data analysis"""
        logger.info("Starting comprehensive data analysis...")
        
        # Run all analysis components
        self.analysis_results['data_summary']['products'] = self.analyze_product_data()
        self.analysis_results['data_summary']['customers'] = self.analyze_customer_data()
        self.analysis_results['data_summary']['orders'] = self.analyze_order_data()
        
        self.analysis_results['business_insights']['seasonal_patterns'] = self.analyze_seasonal_patterns()
        self.analysis_results['data_quality'] = self.generate_data_quality_report()
        
        # Generate overall recommendations
        self.analysis_results['recommendations'] = self._generate_overall_recommendations()
        
        logger.info("Data analysis completed")
        return self.analysis_results
    
    def _generate_overall_recommendations(self) -> List[str]:
        """Generate overall business recommendations"""
        recommendations = []
        
        # Product recommendations
        products = self.analysis_results['data_summary'].get('products', {})
        if 'inventory_statistics' in products:
            inv_stats = products['inventory_statistics']
            if inv_stats.get('out_of_stock_products', 0) > 0:
                recommendations.append(f"Restock {inv_stats['out_of_stock_products']} out-of-stock products")
            
            if inv_stats.get('low_stock_products', 0) > 0:
                recommendations.append(f"Monitor {inv_stats['low_stock_products']} low-stock products")
        
        # Customer recommendations
        customers = self.analysis_results['data_summary'].get('customers', {})
        if 'segment_distribution' in customers:
            segments = customers['segment_distribution']
            if segments.get('Corporate', 0) > segments.get('Consumer', 0):
                recommendations.append("Consider B2B-focused marketing strategies")
        
        # Order recommendations
        orders = self.analysis_results['data_summary'].get('orders', {})
        if 'revenue_statistics' in orders:
            rev_stats = orders['revenue_statistics']
            if rev_stats.get('avg_order_value', 0) < 100:
                recommendations.append("Implement strategies to increase average order value")
        
        return recommendations
    
    def export_analysis_report(self, output_file: str = None) -> str:
        """Export analysis results to JSON file"""
        if output_file is None:
            output_file = self.data_dir / f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_file, 'w') as f:
            json.dump(self.analysis_results, f, indent=2)
        
        logger.info(f"Analysis report exported to: {output_file}")
        return str(output_file)
    
    def print_summary(self) -> None:
        """Print analysis summary to console"""
        print("\n" + "="*80)
        print("GYM+COFFEE DATA ANALYSIS SUMMARY")
        print("="*80)
        
        # Data summary
        data_summary = self.analysis_results.get('data_summary', {})
        
        if 'products' in data_summary and 'total_products' in data_summary['products']:
            products = data_summary['products']
            print(f"\n📦 PRODUCTS:")
            print(f"  Total Products: {products['total_products']}")
            print(f"  Avg Price: ${products['price_statistics'].get('avg_price', 0):.2f}")
            print(f"  Inventory Value: ${products['inventory_statistics'].get('total_inventory_value', 0):,.2f}")
        
        if 'customers' in data_summary and 'total_customers' in data_summary['customers']:
            customers = data_summary['customers']
            print(f"\n👥 CUSTOMERS:")
            print(f"  Total Customers: {customers['total_customers']}")
            if 'segment_distribution' in customers:
                for segment, count in customers['segment_distribution'].items():
                    print(f"  {segment}: {count}")
        
        if 'orders' in data_summary and 'total_orders' in data_summary['orders']:
            orders = data_summary['orders']
            print(f"\n🛒 ORDERS:")
            print(f"  Total Orders: {orders['total_orders']}")
            print(f"  Total Revenue: ${orders['revenue_statistics'].get('total_revenue', 0):,.2f}")
            print(f"  Avg Order Value: ${orders['revenue_statistics'].get('avg_order_value', 0):.2f}")
        
        # Data quality
        quality = self.analysis_results.get('data_quality', {})
        if 'overall_score' in quality:
            print(f"\n🔍 DATA QUALITY:")
            print(f"  Overall Score: {quality['overall_score']}%")
            print(f"  Issues Found: {len(quality.get('issues_found', []))}")
        
        # Recommendations
        recommendations = self.analysis_results.get('recommendations', [])
        if recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations[:5], 1):
                print(f"  {i}. {rec}")
        
        print("="*80)


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Analyze transformed Gym+Coffee data')
    parser.add_argument('--data-dir', default='../data/transformed',
                       help='Directory containing transformed data files')
    parser.add_argument('--output', help='Output file for analysis report')
    parser.add_argument('--summary-only', action='store_true',
                       help='Print summary to console only (no file export)')
    
    args = parser.parse_args()
    
    # Create analyzer and run analysis
    analyzer = DataAnalyzer(args.data_dir)
    analyzer.run_full_analysis()
    
    # Print summary
    analyzer.print_summary()
    
    # Export report unless summary-only
    if not args.summary_only:
        report_file = analyzer.export_analysis_report(args.output)
        print(f"\n📄 Detailed analysis report saved to: {report_file}")


if __name__ == "__main__":
    main()