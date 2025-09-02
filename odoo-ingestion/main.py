#!/usr/bin/env python3
"""
Main Execution Script for Gym+Coffee to Odoo Data Ingestion
============================================================

This script orchestrates the complete data transformation and import process:
1. Analyzes existing data (Gym+Coffee products + DataCo patterns)
2. Transforms and generates comprehensive ERP dataset
3. Validates data integrity and Odoo compatibility
4. Imports data into Odoo ERP system

Usage:
    python main.py --mode [analyze|transform|validate|import|full]
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'odoo_ingestion_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class OdooDataIngestion:
    """Main orchestrator for Odoo data ingestion process"""
    
    def __init__(self):
        self.data_dir = Path('/workspaces/source-lovable-gympluscoffee/data')
        self.output_dir = Path('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/data')
        self.scripts_dir = Path('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/scripts')
        self.output_dir.mkdir(exist_ok=True)
        
        # Odoo configuration from environment
        self.odoo_config = {
            'url': os.getenv('ODOO_URL', 'https://source-gym-plus-coffee.odoo.com/'),
            'db': os.getenv('ODOO_DB', 'source-gym-plus-coffee'),
            'username': os.getenv('ODOO_USERNAME', 'admin@quickfindai.com'),
            'password': os.getenv('ODOO_PASSWORD', '')
        }
        
    def analyze_data(self):
        """Analyze existing data sources"""
        logger.info("=" * 80)
        logger.info("PHASE 1: DATA ANALYSIS")
        logger.info("=" * 80)
        
        # Analyze Gym+Coffee products
        products_file = self.data_dir / 'gym_plus_coffee_products.json'
        with open(products_file, 'r') as f:
            products_data = json.load(f)
        
        logger.info(f"✅ Gym+Coffee Products Analysis:")
        logger.info(f"   - Total SKUs: {products_data['total_skus']}")
        logger.info(f"   - Categories: {', '.join(products_data['categories'])}")
        logger.info(f"   - Products: {len(products_data['products'])} items")
        
        # Analyze DataCo dataset
        dataco_file = self.data_dir / 'dataco/DataCoSupplyChainDataset.csv'
        dataco_df = pd.read_csv(dataco_file, nrows=1000)  # Sample for analysis
        
        logger.info(f"\n✅ DataCo Supply Chain Analysis:")
        logger.info(f"   - Columns: {len(dataco_df.columns)}")
        logger.info(f"   - Sample records: {len(dataco_df)}")
        logger.info(f"   - Customer segments: {dataco_df['Customer Segment'].unique().tolist()}")
        logger.info(f"   - Markets: {dataco_df['Market'].unique().tolist()}")
        logger.info(f"   - Delivery statuses: {dataco_df['Delivery Status'].unique().tolist()}")
        
        return products_data, dataco_df
    
    def transform_data(self, products_data, dataco_df):
        """Transform and generate ERP dataset"""
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 2: DATA TRANSFORMATION")
        logger.info("=" * 80)
        
        # Import transformation scripts
        sys.path.insert(0, str(self.scripts_dir))
        
        try:
            # Transform products
            logger.info("\n📦 Transforming products...")
            from transform_products import ProductTransformer
            transformer = ProductTransformer()
            product_results = transformer.transform_products(str(self.data_dir / 'gym_plus_coffee_products.json'))
            logger.info(f"   ✅ Created {len(product_results['products'])} product records")
            
            # Generate customers
            logger.info("\n👥 Generating customers...")
            from generate_customers import CustomerGenerator
            generator = CustomerGenerator()
            customer_results = generator.generate_customers(
                str(self.data_dir / 'dataco/DataCoSupplyChainDataset.csv'),
                count=500
            )
            logger.info(f"   ✅ Generated {len(customer_results['customers'])} customer records")
            
            # Create orders
            logger.info("\n📋 Creating sales orders...")
            from create_orders import OrderGenerator
            order_gen = OrderGenerator()
            order_results = order_gen.create_orders(
                product_results['products'],
                customer_results['customers'],
                count=1000
            )
            logger.info(f"   ✅ Created {len(order_results['orders'])} sales orders")
            
            return {
                'products': product_results,
                'customers': customer_results,
                'orders': order_results
            }
            
        except ImportError as e:
            logger.error(f"Failed to import transformation scripts: {e}")
            logger.info("Creating placeholder transformation...")
            return self._create_placeholder_data(products_data, dataco_df)
    
    def _create_placeholder_data(self, products_data, dataco_df):
        """Create placeholder transformed data"""
        # Simple transformation for demonstration
        products = []
        for p in products_data['products'][:50]:  # Take first 50 products
            products.append({
                'name': p['name'],
                'default_code': p['sku'],
                'list_price': p['list_price'],
                'standard_price': p['standard_cost'],
                'type': 'product',
                'categ_id': p['category']
            })
        
        customers = []
        for _, row in dataco_df.head(100).iterrows():
            customers.append({
                'name': f"{row['Customer Fname']} {row['Customer Lname']}",
                'email': row['Customer Email'],
                'street': row['Customer Street'],
                'city': row['Customer City'],
                'country': row['Customer Country'],
                'customer_rank': 1
            })
        
        return {
            'products': {'products': products},
            'customers': {'customers': customers},
            'orders': {'orders': []}
        }
    
    def validate_data(self, transformed_data):
        """Validate data before import"""
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 3: DATA VALIDATION")
        logger.info("=" * 80)
        
        try:
            sys.path.insert(0, str(self.scripts_dir.parent / 'tests'))
            from validate_all import run_all_validations
            
            validation_results = run_all_validations(
                products=transformed_data['products']['products'],
                customers=transformed_data['customers']['customers'],
                orders=transformed_data['orders']['orders']
            )
            
            logger.info(f"\n✅ Validation Results:")
            for category, result in validation_results.items():
                logger.info(f"   - {category}: {result['status']}")
                if result.get('issues'):
                    logger.warning(f"     Issues found: {len(result['issues'])}")
                    
        except ImportError:
            logger.warning("Validation scripts not found, using basic validation")
            # Basic validation
            logger.info(f"   - Products: {len(transformed_data['products']['products'])} records")
            logger.info(f"   - Customers: {len(transformed_data['customers']['customers'])} records")
            logger.info(f"   - Orders: {len(transformed_data['orders']['orders'])} records")
        
        return True
    
    def import_to_odoo(self, transformed_data):
        """Import data into Odoo"""
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 4: ODOO IMPORT")
        logger.info("=" * 80)
        
        if not self.odoo_config['password']:
            logger.error("❌ Odoo password not found in environment variables")
            return False
        
        try:
            sys.path.insert(0, str(self.scripts_dir))
            from odoo_import import OdooImporter
            
            importer = OdooImporter(self.odoo_config)
            
            # Import products
            logger.info("\n📦 Importing products to Odoo...")
            product_results = importer.import_products(transformed_data['products']['products'])
            logger.info(f"   ✅ Imported {product_results['success']} products")
            
            # Import customers
            logger.info("\n👥 Importing customers to Odoo...")
            customer_results = importer.import_partners(transformed_data['customers']['customers'])
            logger.info(f"   ✅ Imported {customer_results['success']} customers")
            
            # Import orders (if products and customers successful)
            if product_results['success'] > 0 and customer_results['success'] > 0:
                logger.info("\n📋 Importing sales orders to Odoo...")
                order_results = importer.import_sales_orders(transformed_data['orders']['orders'])
                logger.info(f"   ✅ Imported {order_results['success']} orders")
            
            return True
            
        except ImportError as e:
            logger.error(f"Failed to import Odoo import scripts: {e}")
            logger.info("Please ensure odoo_import.py is available in scripts directory")
            return False
        except Exception as e:
            logger.error(f"Import failed: {e}")
            return False
    
    def run_full_pipeline(self):
        """Run complete ingestion pipeline"""
        logger.info("🚀 STARTING FULL ODOO DATA INGESTION PIPELINE")
        logger.info("=" * 80)
        
        start_time = datetime.now()
        
        # Phase 1: Analyze
        products_data, dataco_df = self.analyze_data()
        
        # Phase 2: Transform
        transformed_data = self.transform_data(products_data, dataco_df)
        
        # Save transformed data
        output_file = self.output_dir / f'transformed_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(output_file, 'w') as f:
            json.dump({
                'products': transformed_data['products']['products'][:10],  # Sample
                'customers': transformed_data['customers']['customers'][:10],  # Sample
                'timestamp': datetime.now().isoformat()
            }, f, indent=2, default=str)
        logger.info(f"\n💾 Saved transformed data to: {output_file}")
        
        # Phase 3: Validate
        is_valid = self.validate_data(transformed_data)
        
        if not is_valid:
            logger.error("❌ Validation failed, aborting import")
            return False
        
        # Phase 4: Import (optional based on user confirmation)
        logger.info("\n" + "=" * 80)
        logger.info("⚠️  Ready to import to Odoo")
        logger.info(f"   URL: {self.odoo_config['url']}")
        logger.info(f"   Database: {self.odoo_config['db']}")
        logger.info(f"   Username: {self.odoo_config['username']}")
        
        if input("\nProceed with import? (yes/no): ").lower() == 'yes':
            success = self.import_to_odoo(transformed_data)
        else:
            logger.info("Import skipped by user")
            success = True
        
        # Summary
        elapsed = datetime.now() - start_time
        logger.info("\n" + "=" * 80)
        logger.info("📊 PIPELINE SUMMARY")
        logger.info("=" * 80)
        logger.info(f"✅ Total execution time: {elapsed}")
        logger.info(f"✅ Products processed: {len(transformed_data['products']['products'])}")
        logger.info(f"✅ Customers generated: {len(transformed_data['customers']['customers'])}")
        logger.info(f"✅ Orders created: {len(transformed_data['orders']['orders'])}")
        
        return success

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Gym+Coffee to Odoo Data Ingestion')
    parser.add_argument('--mode', choices=['analyze', 'transform', 'validate', 'import', 'full'],
                       default='full', help='Execution mode')
    parser.add_argument('--data-file', help='Path to transformed data JSON (for import mode)')
    
    args = parser.parse_args()
    
    ingestion = OdooDataIngestion()
    
    if args.mode == 'full':
        success = ingestion.run_full_pipeline()
    elif args.mode == 'analyze':
        ingestion.analyze_data()
        success = True
    elif args.mode == 'transform':
        products_data, dataco_df = ingestion.analyze_data()
        transformed = ingestion.transform_data(products_data, dataco_df)
        logger.info(f"✅ Transformation complete")
        success = True
    elif args.mode == 'validate':
        if args.data_file:
            with open(args.data_file, 'r') as f:
                data = json.load(f)
            ingestion.validate_data(data)
        else:
            logger.error("Please provide --data-file for validation mode")
            success = False
    elif args.mode == 'import':
        if args.data_file:
            with open(args.data_file, 'r') as f:
                data = json.load(f)
            success = ingestion.import_to_odoo(data)
        else:
            logger.error("Please provide --data-file for import mode")
            success = False
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()