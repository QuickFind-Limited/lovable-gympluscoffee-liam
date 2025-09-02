#!/usr/bin/env python3
"""
Comprehensive Data Pipeline for Gym+Coffee to Odoo Integration

This script orchestrates the complete data transformation pipeline:
1. Transform products from Gym+Coffee format to Odoo
2. Generate customers based on DataCo patterns
3. Create realistic sales orders with proper relationships
4. Generate inventory and stock movements
5. Validate data integrity and relationships
6. Create summary reports and analytics

Usage:
    python data_pipeline.py --full-pipeline
    python data_pipeline.py --products-only
    python data_pipeline.py --customers-only
    python data_pipeline.py --orders-only
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

# Import our transformation modules
from transform_products import ProductTransformer
from generate_customers import CustomerGenerator
from create_orders import SalesOrderGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataPipeline:
    """Orchestrates the complete data transformation pipeline"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_dir = Path(config.get('base_dir', '.'))
        self.data_dir = self.base_dir / 'data'
        self.output_dir = Path(config.get('output_dir', 'data/transformed'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize pipeline state
        self.pipeline_state = {
            'started_at': datetime.now().isoformat(),
            'products_transformed': False,
            'customers_generated': False,
            'orders_generated': False,
            'validation_passed': False,
            'completed_at': None,
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
        
        # File paths
        self.file_paths = {
            'source_products': self.data_dir / 'gym_plus_coffee_products.json',
            'dataco_dataset': self.data_dir / 'dataco' / 'DataCoSupplyChainDataset.csv',
            'output_products': self.output_dir / 'odoo_product_variants.csv',
            'output_customers': self.output_dir / 'odoo_customers.csv',
            'output_orders': self.output_dir / 'odoo_sales_orders.csv'
        }
    
    def validate_prerequisites(self) -> bool:
        """Validate that required source files exist"""
        logger.info("Validating prerequisites...")
        
        required_files = [
            ('Gym+Coffee Products', self.file_paths['source_products']),
            ('DataCo Dataset', self.file_paths['dataco_dataset'])
        ]
        
        missing_files = []
        for name, path in required_files:
            if not path.exists():
                missing_files.append(f"{name}: {path}")
                self.pipeline_state['errors'].append(f"Missing required file: {path}")
        
        if missing_files:
            logger.error(f"Missing required files: {missing_files}")
            return False
        
        logger.info("All prerequisites validated successfully")
        return True
    
    def transform_products(self) -> bool:
        """Run product transformation"""
        logger.info("Starting product transformation...")
        
        try:
            transformer = ProductTransformer(
                source_file=str(self.file_paths['source_products']),
                output_dir=str(self.output_dir)
            )
            transformer.run_transformation()
            
            self.pipeline_state['products_transformed'] = True
            self.pipeline_state['statistics']['products'] = self._get_product_stats()
            
            logger.info("Product transformation completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Product transformation failed: {e}")
            self.pipeline_state['errors'].append(f"Product transformation error: {str(e)}")
            return False
    
    def generate_customers(self) -> bool:
        """Run customer generation"""
        logger.info("Starting customer generation...")
        
        try:
            generator = CustomerGenerator(
                dataco_file=str(self.file_paths['dataco_dataset']),
                output_dir=str(self.output_dir),
                num_customers=self.config.get('num_customers', 1000)
            )
            generator.run_generation()
            
            self.pipeline_state['customers_generated'] = True
            self.pipeline_state['statistics']['customers'] = self._get_customer_stats()
            
            logger.info("Customer generation completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Customer generation failed: {e}")
            self.pipeline_state['errors'].append(f"Customer generation error: {str(e)}")
            return False
    
    def generate_orders(self) -> bool:
        """Run order generation"""
        logger.info("Starting order generation...")
        
        # Check if prerequisites exist
        customers_file = self.output_dir / 'odoo_customers.csv'
        products_file = self.output_dir / 'odoo_product_variants.csv'
        
        if not customers_file.exists():
            logger.error("Customer file not found. Run customer generation first.")
            self.pipeline_state['errors'].append("Customer file missing for order generation")
            return False
        
        if not products_file.exists():
            logger.error("Product file not found. Run product transformation first.")
            self.pipeline_state['errors'].append("Product file missing for order generation")
            return False
        
        try:
            generator = SalesOrderGenerator(
                dataco_file=str(self.file_paths['dataco_dataset']),
                customers_file=str(customers_file),
                products_file=str(products_file),
                output_dir=str(self.output_dir),
                num_orders=self.config.get('num_orders', 2000)
            )
            generator.run_generation()
            
            self.pipeline_state['orders_generated'] = True
            self.pipeline_state['statistics']['orders'] = self._get_order_stats()
            
            logger.info("Order generation completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Order generation failed: {e}")
            self.pipeline_state['errors'].append(f"Order generation error: {str(e)}")
            return False
    
    def validate_data_integrity(self) -> bool:
        """Validate data integrity and relationships"""
        logger.info("Validating data integrity...")
        
        validation_results = {
            'products': self._validate_products(),
            'customers': self._validate_customers(),
            'orders': self._validate_orders(),
            'relationships': self._validate_relationships()
        }
        
        # Check if any validation failed
        all_passed = all(validation_results.values())
        
        if all_passed:
            logger.info("All data integrity validations passed")
            self.pipeline_state['validation_passed'] = True
        else:
            failed_validations = [k for k, v in validation_results.items() if not v]
            logger.error(f"Data integrity validation failed for: {failed_validations}")
            self.pipeline_state['errors'].append(f"Validation failed: {failed_validations}")
        
        self.pipeline_state['statistics']['validation'] = validation_results
        return all_passed
    
    def _validate_products(self) -> bool:
        """Validate product data integrity"""
        try:
            products_file = self.output_dir / 'odoo_product_variants.csv'
            if not products_file.exists():
                return False
            
            df = pd.read_csv(products_file)
            
            # Check required fields
            required_fields = ['external_id', 'default_code', 'list_price', 'standard_price']
            missing_fields = [f for f in required_fields if f not in df.columns]
            
            if missing_fields:
                self.pipeline_state['warnings'].append(f"Missing product fields: {missing_fields}")
            
            # Check for duplicates
            duplicates = df['external_id'].duplicated().sum()
            if duplicates > 0:
                self.pipeline_state['warnings'].append(f"Found {duplicates} duplicate product external_ids")
            
            # Check for invalid prices
            invalid_prices = (df['list_price'] <= 0).sum()
            if invalid_prices > 0:
                self.pipeline_state['warnings'].append(f"Found {invalid_prices} products with invalid prices")
            
            logger.info(f"Product validation: {len(df)} products validated")
            return True
            
        except Exception as e:
            logger.error(f"Product validation error: {e}")
            return False
    
    def _validate_customers(self) -> bool:
        """Validate customer data integrity"""
        try:
            customers_file = self.output_dir / 'odoo_customers.csv'
            if not customers_file.exists():
                return False
            
            df = pd.read_csv(customers_file)
            
            # Check required fields
            required_fields = ['external_id', 'name', 'email']
            missing_fields = [f for f in required_fields if f not in df.columns]
            
            if missing_fields:
                self.pipeline_state['warnings'].append(f"Missing customer fields: {missing_fields}")
            
            # Check for duplicates
            duplicates = df['external_id'].duplicated().sum()
            if duplicates > 0:
                self.pipeline_state['warnings'].append(f"Found {duplicates} duplicate customer external_ids")
            
            # Check email format (basic validation)
            if 'email' in df.columns:
                invalid_emails = df[~df['email'].str.contains('@', na=False)].shape[0]
                if invalid_emails > 0:
                    self.pipeline_state['warnings'].append(f"Found {invalid_emails} customers with invalid emails")
            
            logger.info(f"Customer validation: {len(df)} customers validated")
            return True
            
        except Exception as e:
            logger.error(f"Customer validation error: {e}")
            return False
    
    def _validate_orders(self) -> bool:
        """Validate order data integrity"""
        try:
            orders_file = self.output_dir / 'odoo_sales_orders.csv'
            order_lines_file = self.output_dir / 'odoo_order_lines.csv'
            
            if not orders_file.exists() or not order_lines_file.exists():
                return False
            
            orders_df = pd.read_csv(orders_file)
            lines_df = pd.read_csv(order_lines_file)
            
            # Check required fields
            required_order_fields = ['external_id', 'partner_id', 'amount_total']
            required_line_fields = ['external_id', 'order_id', 'product_id', 'price_total']
            
            missing_order_fields = [f for f in required_order_fields if f not in orders_df.columns]
            missing_line_fields = [f for f in required_line_fields if f not in lines_df.columns]
            
            if missing_order_fields:
                self.pipeline_state['warnings'].append(f"Missing order fields: {missing_order_fields}")
            
            if missing_line_fields:
                self.pipeline_state['warnings'].append(f"Missing order line fields: {missing_line_fields}")
            
            # Check order totals consistency
            if 'amount_total' in orders_df.columns and 'price_total' in lines_df.columns:
                line_totals = lines_df.groupby('order_id')['price_total'].sum()
                order_totals = orders_df.set_index('external_id')['amount_total']
                
                # Allow for small rounding differences
                tolerance = 0.01
                mismatched = 0
                for order_id in order_totals.index:
                    if order_id in line_totals.index:
                        diff = abs(order_totals[order_id] - line_totals[order_id])
                        if diff > tolerance:
                            mismatched += 1
                
                if mismatched > 0:
                    self.pipeline_state['warnings'].append(f"Found {mismatched} orders with mismatched totals")
            
            logger.info(f"Order validation: {len(orders_df)} orders and {len(lines_df)} lines validated")
            return True
            
        except Exception as e:
            logger.error(f"Order validation error: {e}")
            return False
    
    def _validate_relationships(self) -> bool:
        """Validate relationships between entities"""
        try:
            # Load data files
            customers_file = self.output_dir / 'odoo_customers.csv'
            products_file = self.output_dir / 'odoo_product_variants.csv'
            orders_file = self.output_dir / 'odoo_sales_orders.csv'
            lines_file = self.output_dir / 'odoo_order_lines.csv'
            
            files_exist = all(f.exists() for f in [customers_file, products_file, orders_file, lines_file])
            if not files_exist:
                return False
            
            customers_df = pd.read_csv(customers_file)
            products_df = pd.read_csv(products_file)
            orders_df = pd.read_csv(orders_file)
            lines_df = pd.read_csv(lines_file)
            
            # Check customer references in orders
            customer_ids = set(customers_df['external_id'])
            order_customer_refs = set(orders_df['partner_id'])
            missing_customers = order_customer_refs - customer_ids
            
            if missing_customers:
                self.pipeline_state['warnings'].append(
                    f"Found {len(missing_customers)} orders with missing customer references"
                )
            
            # Check product references in order lines
            product_ids = set(products_df['external_id'])
            line_product_refs = set(lines_df['product_id'])
            missing_products = line_product_refs - product_ids
            
            if missing_products:
                self.pipeline_state['warnings'].append(
                    f"Found {len(missing_products)} order lines with missing product references"
                )
            
            # Check order references in order lines
            order_ids = set(orders_df['external_id'])
            line_order_refs = set(lines_df['order_id'])
            orphaned_lines = line_order_refs - order_ids
            
            if orphaned_lines:
                self.pipeline_state['warnings'].append(
                    f"Found {len(orphaned_lines)} orphaned order lines"
                )
            
            logger.info("Relationship validation completed")
            return len(missing_customers) == 0 and len(missing_products) == 0 and len(orphaned_lines) == 0
            
        except Exception as e:
            logger.error(f"Relationship validation error: {e}")
            return False
    
    def _get_product_stats(self) -> Dict[str, Any]:
        """Get product transformation statistics"""
        try:
            templates_file = self.output_dir / 'odoo_product_templates.csv'
            variants_file = self.output_dir / 'odoo_product_variants.csv'
            
            stats = {}
            
            if templates_file.exists():
                templates_df = pd.read_csv(templates_file)
                stats['templates_created'] = len(templates_df)
                stats['categories'] = templates_df.groupby('category_id').size().to_dict() if 'category_id' in templates_df.columns else {}
            
            if variants_file.exists():
                variants_df = pd.read_csv(variants_file)
                stats['variants_created'] = len(variants_df)
                stats['total_inventory_value'] = float(variants_df['list_price'].sum()) if 'list_price' in variants_df.columns else 0
                stats['avg_price'] = float(variants_df['list_price'].mean()) if 'list_price' in variants_df.columns else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting product stats: {e}")
            return {}
    
    def _get_customer_stats(self) -> Dict[str, Any]:
        """Get customer generation statistics"""
        try:
            customers_file = self.output_dir / 'odoo_customers.csv'
            
            if not customers_file.exists():
                return {}
            
            df = pd.read_csv(customers_file)
            
            stats = {
                'total_customers': len(df),
                'segments': df.groupby('category_id').size().to_dict() if 'category_id' in df.columns else {},
                'countries': df.groupby('country_id').size().to_dict() if 'country_id' in df.columns else {},
                'companies': (df['is_company'] == True).sum() if 'is_company' in df.columns else 0,
                'avg_expected_spend': float(df['expected_annual_spend'].mean()) if 'expected_annual_spend' in df.columns else 0
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting customer stats: {e}")
            return {}
    
    def _get_order_stats(self) -> Dict[str, Any]:
        """Get order generation statistics"""
        try:
            orders_file = self.output_dir / 'odoo_sales_orders.csv'
            lines_file = self.output_dir / 'odoo_order_lines.csv'
            
            stats = {}
            
            if orders_file.exists():
                orders_df = pd.read_csv(orders_file)
                stats['total_orders'] = len(orders_df)
                stats['total_revenue'] = float(orders_df['amount_total'].sum()) if 'amount_total' in orders_df.columns else 0
                stats['avg_order_value'] = float(orders_df['amount_total'].mean()) if 'amount_total' in orders_df.columns else 0
                stats['orders_by_status'] = orders_df.groupby('state').size().to_dict() if 'state' in orders_df.columns else {}
                stats['orders_by_segment'] = orders_df.groupby('customer_segment').size().to_dict() if 'customer_segment' in orders_df.columns else {}
            
            if lines_file.exists():
                lines_df = pd.read_csv(lines_file)
                stats['total_order_lines'] = len(lines_df)
                stats['avg_items_per_order'] = len(lines_df) / len(orders_df) if 'total_orders' in stats and stats['total_orders'] > 0 else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting order stats: {e}")
            return {}
    
    def generate_summary_report(self) -> None:
        """Generate comprehensive summary report"""
        logger.info("Generating summary report...")
        
        self.pipeline_state['completed_at'] = datetime.now().isoformat()
        
        # Calculate runtime
        start_time = datetime.fromisoformat(self.pipeline_state['started_at'])
        end_time = datetime.fromisoformat(self.pipeline_state['completed_at'])
        runtime_seconds = (end_time - start_time).total_seconds()
        
        # Create comprehensive report
        report = {
            'pipeline_execution': {
                'started_at': self.pipeline_state['started_at'],
                'completed_at': self.pipeline_state['completed_at'],
                'runtime_seconds': runtime_seconds,
                'runtime_formatted': f"{runtime_seconds//60:.0f}m {runtime_seconds%60:.0f}s"
            },
            'execution_status': {
                'products_transformed': self.pipeline_state['products_transformed'],
                'customers_generated': self.pipeline_state['customers_generated'], 
                'orders_generated': self.pipeline_state['orders_generated'],
                'validation_passed': self.pipeline_state['validation_passed'],
                'overall_success': (
                    self.pipeline_state['products_transformed'] and
                    self.pipeline_state['customers_generated'] and
                    self.pipeline_state['orders_generated'] and
                    self.pipeline_state['validation_passed']
                )
            },
            'statistics': self.pipeline_state['statistics'],
            'data_quality': {
                'errors': self.pipeline_state['errors'],
                'warnings': self.pipeline_state['warnings'],
                'error_count': len(self.pipeline_state['errors']),
                'warning_count': len(self.pipeline_state['warnings'])
            },
            'output_files': self._list_output_files(),
            'configuration': self.config
        }
        
        # Save report
        report_file = self.output_dir / 'pipeline_execution_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary to console
        self._print_summary_console(report)
        
        logger.info(f"Summary report saved to: {report_file}")
    
    def _list_output_files(self) -> Dict[str, Any]:
        """List all output files with metadata"""
        output_files = {}
        
        for file_path in self.output_dir.glob('*.csv'):
            try:
                df = pd.read_csv(file_path)
                output_files[file_path.name] = {
                    'path': str(file_path),
                    'size_bytes': file_path.stat().st_size,
                    'record_count': len(df),
                    'column_count': len(df.columns),
                    'created': datetime.fromtimestamp(file_path.stat().st_ctime).isoformat()
                }
            except Exception as e:
                output_files[file_path.name] = {
                    'path': str(file_path),
                    'error': f"Could not read file: {str(e)}"
                }
        
        return output_files
    
    def _print_summary_console(self, report: Dict[str, Any]) -> None:
        """Print formatted summary to console"""
        print("\n" + "="*80)
        print("GYM+COFFEE TO ODOO DATA PIPELINE EXECUTION SUMMARY")
        print("="*80)
        
        # Execution status
        exec_status = report['execution_status']
        print(f"\n📊 EXECUTION STATUS:")
        print(f"  ✅ Products Transformed: {'Yes' if exec_status['products_transformed'] else '❌ No'}")
        print(f"  ✅ Customers Generated: {'Yes' if exec_status['customers_generated'] else '❌ No'}")
        print(f"  ✅ Orders Generated: {'Yes' if exec_status['orders_generated'] else '❌ No'}")
        print(f"  ✅ Validation Passed: {'Yes' if exec_status['validation_passed'] else '❌ No'}")
        print(f"  🎯 Overall Success: {'✅ YES' if exec_status['overall_success'] else '❌ NO'}")
        
        # Statistics
        stats = report['statistics']
        if 'products' in stats:
            p = stats['products']
            print(f"\n🛍️ PRODUCTS:")
            print(f"  Templates: {p.get('templates_created', 'N/A')}")
            print(f"  Variants: {p.get('variants_created', 'N/A')}")
            print(f"  Avg Price: ${p.get('avg_price', 0):.2f}")
        
        if 'customers' in stats:
            c = stats['customers']
            print(f"\n👥 CUSTOMERS:")
            print(f"  Total: {c.get('total_customers', 'N/A')}")
            print(f"  Companies: {c.get('companies', 'N/A')}")
            print(f"  Avg Expected Spend: ${c.get('avg_expected_spend', 0):.2f}")
        
        if 'orders' in stats:
            o = stats['orders']
            print(f"\n🛒 ORDERS:")
            print(f"  Total Orders: {o.get('total_orders', 'N/A')}")
            print(f"  Total Revenue: ${o.get('total_revenue', 0):,.2f}")
            print(f"  Avg Order Value: ${o.get('avg_order_value', 0):.2f}")
            print(f"  Avg Items/Order: {o.get('avg_items_per_order', 0):.1f}")
        
        # Data quality
        quality = report['data_quality']
        print(f"\n🔍 DATA QUALITY:")
        print(f"  Errors: {quality['error_count']}")
        print(f"  Warnings: {quality['warning_count']}")
        
        if quality['errors']:
            print(f"  Error Details:")
            for error in quality['errors'][:5]:  # Show first 5
                print(f"    - {error}")
        
        # Runtime
        runtime = report['pipeline_execution']
        print(f"\n⏱️ RUNTIME: {runtime['runtime_formatted']}")
        
        print("="*80 + "\n")
    
    def run_full_pipeline(self) -> bool:
        """Run the complete data pipeline"""
        logger.info("Starting full data pipeline execution")
        
        # Validate prerequisites
        if not self.validate_prerequisites():
            return False
        
        # Run transformations in order
        steps = [
            ("Product Transformation", self.transform_products),
            ("Customer Generation", self.generate_customers),
            ("Order Generation", self.generate_orders),
            ("Data Validation", self.validate_data_integrity)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"Executing: {step_name}")
            if not step_func():
                logger.error(f"Pipeline failed at step: {step_name}")
                self.generate_summary_report()
                return False
        
        # Generate final report
        self.generate_summary_report()
        
        logger.info("Full pipeline execution completed successfully")
        return True


def create_default_config() -> Dict[str, Any]:
    """Create default configuration"""
    return {
        'base_dir': '../..',
        'output_dir': '../data/transformed',
        'num_customers': 1000,
        'num_orders': 2000,
        'validation_enabled': True,
        'generate_reports': True
    }


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Gym+Coffee to Odoo Data Pipeline')
    
    # Pipeline modes
    parser.add_argument('--full-pipeline', action='store_true', 
                       help='Run complete pipeline (default)')
    parser.add_argument('--products-only', action='store_true',
                       help='Transform products only')
    parser.add_argument('--customers-only', action='store_true',
                       help='Generate customers only')
    parser.add_argument('--orders-only', action='store_true',
                       help='Generate orders only')
    parser.add_argument('--validate-only', action='store_true',
                       help='Run data validation only')
    
    # Configuration
    parser.add_argument('--config', type=str,
                       help='JSON configuration file path')
    parser.add_argument('--output-dir', type=str, default='../data/transformed',
                       help='Output directory for transformed files')
    parser.add_argument('--num-customers', type=int, default=1000,
                       help='Number of customers to generate')
    parser.add_argument('--num-orders', type=int, default=2000,
                       help='Number of orders to generate')
    
    args = parser.parse_args()
    
    # Load configuration
    if args.config and Path(args.config).exists():
        with open(args.config) as f:
            config = json.load(f)
    else:
        config = create_default_config()
    
    # Override with command line arguments
    if args.output_dir:
        config['output_dir'] = args.output_dir
    if args.num_customers:
        config['num_customers'] = args.num_customers
    if args.num_orders:
        config['num_orders'] = args.num_orders
    
    # Create pipeline
    pipeline = DataPipeline(config)
    
    # Determine execution mode
    if args.products_only:
        success = pipeline.transform_products()
    elif args.customers_only:
        success = pipeline.generate_customers()
    elif args.orders_only:
        success = pipeline.generate_orders()
    elif args.validate_only:
        success = pipeline.validate_data_integrity()
    else:
        # Default: run full pipeline
        success = pipeline.run_full_pipeline()
    
    # Generate report for single-step executions
    if not args.full_pipeline:
        pipeline.generate_summary_report()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()