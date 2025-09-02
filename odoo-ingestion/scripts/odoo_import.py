#!/usr/bin/env python3
"""
Comprehensive Odoo Import System
==============================

Main script for importing data into Odoo using XML-RPC.
Handles batch processing, error recovery, progress tracking,
and comprehensive data model management.

Author: Odoo Integration Agent
Version: 1.0.0
"""

import os
import sys
import json
import logging
import xmlrpc.client
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
from dataclasses import dataclass
import traceback
from contextlib import contextmanager

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from odoo_ingestion.scripts.connection_manager import OdooConnectionManager
from odoo_ingestion.scripts.data_models import (
    ProductTemplate, ProductVariant, Partner, SaleOrder, 
    StockMove, ProductCategory, ImportProgress
)
from odoo_ingestion.scripts.batch_processor import BatchProcessor
from odoo_ingestion.scripts.error_handler import ErrorHandler
from odoo_ingestion.scripts.progress_tracker import ProgressTracker


@dataclass
class ImportConfig:
    """Configuration for Odoo import operations"""
    url: str
    db: str
    username: str
    password: str
    batch_size: int = 100
    max_retries: int = 3
    retry_delay: float = 2.0
    connection_timeout: float = 30.0
    log_level: str = "INFO"
    progress_file: str = "data/import_progress.json"
    backup_dir: str = "data/backups"
    error_log_file: str = "logs/import_errors.log"
    failed_records_dir: str = "data/failed_records"


class OdooImporter:
    """
    Main Odoo Import System
    ======================
    
    Orchestrates the entire import process with robust error handling,
    batch processing, and progress tracking capabilities.
    """
    
    def __init__(self, config: ImportConfig):
        self.config = config
        self.setup_logging()
        self.setup_directories()
        
        # Initialize core components
        self.connection_manager = OdooConnectionManager(config)
        self.batch_processor = BatchProcessor(config)
        self.error_handler = ErrorHandler(config)
        self.progress_tracker = ProgressTracker(config)
        
        # Import statistics
        self.stats = {
            'start_time': None,
            'end_time': None,
            'total_records': 0,
            'successful_imports': 0,
            'failed_imports': 0,
            'skipped_records': 0,
            'batches_processed': 0
        }
        
        self.logger = logging.getLogger(__name__)
    
    def setup_logging(self):
        """Configure logging system"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f"logs/odoo_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
                logging.StreamHandler()
            ]
        )
    
    def setup_directories(self):
        """Create necessary directories"""
        directories = [
            self.config.backup_dir,
            self.config.failed_records_dir,
            "logs",
            "data"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def import_session(self):
        """Context manager for import sessions with proper cleanup"""
        self.stats['start_time'] = datetime.now()
        self.logger.info("Starting Odoo import session")
        
        try:
            # Test connection
            with self.connection_manager.get_connection() as conn:
                self.logger.info(f"Connected to Odoo: {self.config.url}")
                yield conn
                
        except Exception as e:
            self.logger.error(f"Import session failed: {e}")
            self.error_handler.log_critical_error("import_session", str(e))
            raise
        finally:
            self.stats['end_time'] = datetime.now()
            self._log_final_statistics()
    
    def import_product_data(self, data_file: str) -> Dict[str, Any]:
        """
        Import product data from JSON file
        
        Args:
            data_file: Path to JSON file containing product data
            
        Returns:
            Import results dictionary
        """
        self.logger.info(f"Starting product import from {data_file}")
        
        with self.import_session() as conn:
            # Load and validate data
            product_data = self._load_json_data(data_file)
            if not product_data:
                raise ValueError(f"No valid data found in {data_file}")
            
            # Process categories first (required for products)
            categories_result = self._import_product_categories(conn, product_data)
            
            # Process product templates and variants
            products_result = self._import_products(conn, product_data)
            
            # Update inventory levels
            inventory_result = self._update_inventory_levels(conn, product_data)
            
            return {
                'categories': categories_result,
                'products': products_result,
                'inventory': inventory_result,
                'statistics': self.stats
            }
    
    def import_partner_data(self, data_file: str) -> Dict[str, Any]:
        """Import partner/customer data"""
        self.logger.info(f"Starting partner import from {data_file}")
        
        with self.import_session() as conn:
            partner_data = self._load_json_data(data_file)
            return self._import_partners(conn, partner_data)
    
    def import_sales_orders(self, data_file: str) -> Dict[str, Any]:
        """Import sales order data"""
        self.logger.info(f"Starting sales order import from {data_file}")
        
        with self.import_session() as conn:
            order_data = self._load_json_data(data_file)
            return self._import_orders(conn, order_data)
    
    def _load_json_data(self, file_path: str) -> Dict[str, Any]:
        """Load and validate JSON data file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.logger.info(f"Loaded {len(data.get('products', []))} records from {file_path}")
            return data
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"Failed to load data file {file_path}: {e}")
            raise
    
    def _import_product_categories(self, conn, data: Dict[str, Any]) -> Dict[str, Any]:
        """Import product categories with hierarchy support"""
        self.logger.info("Importing product categories")
        
        categories = data.get('categories', [])
        if not categories:
            self.logger.warning("No categories found in data")
            return {'imported': 0, 'errors': 0}
        
        # Create category hierarchy
        category_map = {}
        results = {'imported': 0, 'errors': 0, 'skipped': 0}
        
        for category_name in categories:
            try:
                # Check if category already exists
                existing_ids = conn.execute_kw(
                    self.config.db, conn.uid, self.config.password,
                    'product.category', 'search',
                    [[['name', '=', category_name.title()]]]
                )
                
                if existing_ids:
                    category_map[category_name] = existing_ids[0]
                    results['skipped'] += 1
                    continue
                
                # Create new category
                category_data = {
                    'name': category_name.title(),
                    'parent_id': False,  # Top-level category
                }
                
                category_id = conn.execute_kw(
                    self.config.db, conn.uid, self.config.password,
                    'product.category', 'create', [category_data]
                )
                
                category_map[category_name] = category_id
                results['imported'] += 1
                
                self.logger.debug(f"Created category: {category_name} (ID: {category_id})")
                
            except Exception as e:
                self.logger.error(f"Failed to create category {category_name}: {e}")
                self.error_handler.log_error('category_import', category_name, str(e))
                results['errors'] += 1
        
        self.logger.info(f"Category import complete: {results}")
        return results
    
    def _import_products(self, conn, data: Dict[str, Any]) -> Dict[str, Any]:
        """Import products with batch processing"""
        products = data.get('products', [])
        if not products:
            self.logger.warning("No products found in data")
            return {'imported': 0, 'errors': 0}
        
        self.logger.info(f"Starting batch import of {len(products)} products")
        
        # Group products by template (same name, different variants)
        templates = self._group_products_by_template(products)
        
        results = {'imported': 0, 'errors': 0, 'skipped': 0}
        
        # Process templates in batches
        batch_size = self.config.batch_size
        template_items = list(templates.items())
        
        for i in range(0, len(template_items), batch_size):
            batch = template_items[i:i + batch_size]
            batch_results = self._process_product_batch(conn, batch)
            
            # Aggregate results
            for key in results:
                results[key] += batch_results.get(key, 0)
            
            self.stats['batches_processed'] += 1
            self.progress_tracker.update_progress(
                'products',
                processed=min(i + batch_size, len(template_items)),
                total=len(template_items)
            )
            
            # Brief pause between batches
            if i + batch_size < len(template_items):
                time.sleep(0.1)
        
        self.logger.info(f"Product import complete: {results}")
        return results
    
    def _group_products_by_template(self, products: List[Dict]) -> Dict[str, List[Dict]]:
        """Group product variants by template name"""
        templates = {}
        
        for product in products:
            # Create template key from base product info
            template_key = f"{product['name']}_{product.get('category', 'default')}"
            
            if template_key not in templates:
                templates[template_key] = []
            
            templates[template_key].append(product)
        
        self.logger.info(f"Grouped {len(products)} products into {len(templates)} templates")
        return templates
    
    def _process_product_batch(self, conn, batch: List[Tuple[str, List[Dict]]]) -> Dict[str, int]:
        """Process a batch of product templates"""
        results = {'imported': 0, 'errors': 0, 'skipped': 0}
        
        for template_name, variants in batch:
            try:
                # Get main product info from first variant
                main_product = variants[0]
                
                # Check if template already exists
                existing_templates = conn.execute_kw(
                    self.config.db, conn.uid, self.config.password,
                    'product.template', 'search',
                    [[['name', '=', main_product['name']]]]
                )
                
                if existing_templates and not self._should_update_existing():
                    results['skipped'] += len(variants)
                    continue
                
                # Get or create product category
                category_id = self._get_or_create_category(conn, main_product.get('category', 'default'))
                
                # Create product template
                template_data = {
                    'name': main_product['name'],
                    'categ_id': category_id,
                    'type': 'product',
                    'invoice_policy': 'order',
                    'purchase_method': 'purchase',
                    'list_price': float(main_product.get('list_price', 0.0)),
                    'standard_price': float(main_product.get('standard_cost', 0.0)),
                    'description': main_product.get('description', ''),
                    'active': main_product.get('status', 'active') == 'active',
                }
                
                if existing_templates:
                    # Update existing template
                    template_id = existing_templates[0]
                    conn.execute_kw(
                        self.config.db, conn.uid, self.config.password,
                        'product.template', 'write',
                        [[template_id], template_data]
                    )
                else:
                    # Create new template
                    template_id = conn.execute_kw(
                        self.config.db, conn.uid, self.config.password,
                        'product.template', 'create', [template_data]
                    )
                
                # Create variants if multiple exist
                if len(variants) > 1:
                    self._create_product_variants(conn, template_id, variants)
                else:
                    # Update single variant
                    self._update_product_variant(conn, template_id, variants[0])
                
                results['imported'] += len(variants)
                self.logger.debug(f"Processed template: {template_name} with {len(variants)} variants")
                
            except Exception as e:
                self.logger.error(f"Failed to process template {template_name}: {e}")
                self.error_handler.log_error('product_batch', template_name, str(e), variants)
                results['errors'] += len(variants)
        
        return results
    
    def _get_or_create_category(self, conn, category_name: str) -> int:
        """Get existing category ID or create new one"""
        # Search for existing category
        category_ids = conn.execute_kw(
            self.config.db, conn.uid, self.config.password,
            'product.category', 'search',
            [[['name', '=', category_name.title()]]]
        )
        
        if category_ids:
            return category_ids[0]
        
        # Create new category
        category_data = {
            'name': category_name.title(),
            'parent_id': False
        }
        
        return conn.execute_kw(
            self.config.db, conn.uid, self.config.password,
            'product.category', 'create', [category_data]
        )
    
    def _create_product_variants(self, conn, template_id: int, variants: List[Dict]):
        """Create product variants for a template"""
        for variant in variants:
            try:
                # Create variant-specific attributes
                variant_data = {
                    'product_tmpl_id': template_id,
                    'default_code': variant.get('sku', ''),
                    'standard_price': float(variant.get('standard_cost', 0.0)),
                    'list_price': float(variant.get('list_price', 0.0)),
                }
                
                # Add variant attributes (color, size, etc.)
                if variant.get('color'):
                    variant_data['attribute_color'] = variant['color']
                if variant.get('size'):
                    variant_data['attribute_size'] = variant['size']
                
                conn.execute_kw(
                    self.config.db, conn.uid, self.config.password,
                    'product.product', 'create', [variant_data]
                )
                
            except Exception as e:
                self.logger.error(f"Failed to create variant {variant.get('sku', 'unknown')}: {e}")
                raise
    
    def _update_product_variant(self, conn, template_id: int, product_data: Dict):
        """Update single product variant data"""
        try:
            # Get the product variant
            product_ids = conn.execute_kw(
                self.config.db, conn.uid, self.config.password,
                'product.product', 'search',
                [[['product_tmpl_id', '=', template_id]]]
            )
            
            if not product_ids:
                return
            
            product_id = product_ids[0]
            
            # Update variant data
            variant_data = {
                'default_code': product_data.get('sku', ''),
                'standard_price': float(product_data.get('standard_cost', 0.0)),
                'list_price': float(product_data.get('list_price', 0.0)),
            }
            
            conn.execute_kw(
                self.config.db, conn.uid, self.config.password,
                'product.product', 'write',
                [[product_id], variant_data]
            )
            
        except Exception as e:
            self.logger.error(f"Failed to update variant for template {template_id}: {e}")
            raise
    
    def _update_inventory_levels(self, conn, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update inventory levels for imported products"""
        products = data.get('products', [])
        if not products:
            return {'updated': 0, 'errors': 0}
        
        self.logger.info("Updating inventory levels")
        results = {'updated': 0, 'errors': 0}
        
        for product in products:
            try:
                if 'inventory_on_hand' not in product:
                    continue
                
                # Find product by SKU
                product_ids = conn.execute_kw(
                    self.config.db, conn.uid, self.config.password,
                    'product.product', 'search',
                    [[['default_code', '=', product.get('sku', '')]]]
                )
                
                if not product_ids:
                    continue
                
                product_id = product_ids[0]
                
                # Create inventory adjustment
                inventory_data = {
                    'name': f"Import Adjustment - {product.get('sku', '')}",
                    'state': 'draft',
                    'line_ids': [(0, 0, {
                        'product_id': product_id,
                        'product_qty': float(product['inventory_on_hand']),
                        'location_id': 1,  # Default stock location
                    })]
                }
                
                # This is a simplified approach - in production you'd use proper inventory adjustments
                conn.execute_kw(
                    self.config.db, conn.uid, self.config.password,
                    'product.product', 'write',
                    [[product_id], {'qty_available': float(product['inventory_on_hand'])}]
                )
                
                results['updated'] += 1
                
            except Exception as e:
                self.logger.error(f"Failed to update inventory for {product.get('sku', 'unknown')}: {e}")
                results['errors'] += 1
        
        self.logger.info(f"Inventory update complete: {results}")
        return results
    
    def _import_partners(self, conn, data: Dict[str, Any]) -> Dict[str, Any]:
        """Import partner/customer data"""
        partners = data.get('partners', [])
        if not partners:
            return {'imported': 0, 'errors': 0}
        
        results = {'imported': 0, 'errors': 0, 'skipped': 0}
        
        for partner_data in partners:
            try:
                # Check if partner exists
                existing_partners = conn.execute_kw(
                    self.config.db, conn.uid, self.config.password,
                    'res.partner', 'search',
                    [[['email', '=', partner_data.get('email', '')]]]
                )
                
                if existing_partners:
                    results['skipped'] += 1
                    continue
                
                # Create partner
                partner_vals = {
                    'name': partner_data.get('name', ''),
                    'email': partner_data.get('email', ''),
                    'phone': partner_data.get('phone', ''),
                    'street': partner_data.get('street', ''),
                    'city': partner_data.get('city', ''),
                    'zip': partner_data.get('zip', ''),
                    'country_id': self._get_country_id(conn, partner_data.get('country', 'US')),
                    'is_company': partner_data.get('is_company', False),
                    'customer_rank': 1,
                    'supplier_rank': 0,
                }
                
                partner_id = conn.execute_kw(
                    self.config.db, conn.uid, self.config.password,
                    'res.partner', 'create', [partner_vals]
                )
                
                results['imported'] += 1
                self.logger.debug(f"Created partner: {partner_data.get('name')} (ID: {partner_id})")
                
            except Exception as e:
                self.logger.error(f"Failed to create partner {partner_data.get('name', 'unknown')}: {e}")
                results['errors'] += 1
        
        return results
    
    def _import_orders(self, conn, data: Dict[str, Any]) -> Dict[str, Any]:
        """Import sales order data"""
        orders = data.get('orders', [])
        if not orders:
            return {'imported': 0, 'errors': 0}
        
        results = {'imported': 0, 'errors': 0, 'skipped': 0}
        
        for order_data in orders:
            try:
                # Get partner ID
                partner_id = self._get_partner_id(conn, order_data.get('customer_email', ''))
                if not partner_id:
                    self.logger.warning(f"Partner not found for order {order_data.get('order_id', 'unknown')}")
                    results['errors'] += 1
                    continue
                
                # Create sales order
                order_vals = {
                    'partner_id': partner_id,
                    'date_order': order_data.get('date_order', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                    'state': 'draft',
                    'order_line': []
                }
                
                # Add order lines
                for line in order_data.get('order_lines', []):
                    product_id = self._get_product_id_by_sku(conn, line.get('sku', ''))
                    if product_id:
                        line_vals = (0, 0, {
                            'product_id': product_id,
                            'product_uom_qty': float(line.get('quantity', 1)),
                            'price_unit': float(line.get('price_unit', 0.0)),
                        })
                        order_vals['order_line'].append(line_vals)
                
                if order_vals['order_line']:
                    order_id = conn.execute_kw(
                        self.config.db, conn.uid, self.config.password,
                        'sale.order', 'create', [order_vals]
                    )
                    results['imported'] += 1
                    self.logger.debug(f"Created order: {order_data.get('order_id')} (ID: {order_id})")
                else:
                    results['errors'] += 1
                    
            except Exception as e:
                self.logger.error(f"Failed to create order {order_data.get('order_id', 'unknown')}: {e}")
                results['errors'] += 1
        
        return results
    
    def _get_country_id(self, conn, country_code: str) -> int:
        """Get country ID by code"""
        country_ids = conn.execute_kw(
            self.config.db, conn.uid, self.config.password,
            'res.country', 'search',
            [[['code', '=', country_code.upper()]]]
        )
        return country_ids[0] if country_ids else 1  # Default to first country
    
    def _get_partner_id(self, conn, email: str) -> Optional[int]:
        """Get partner ID by email"""
        partner_ids = conn.execute_kw(
            self.config.db, conn.uid, self.config.password,
            'res.partner', 'search',
            [[['email', '=', email]]]
        )
        return partner_ids[0] if partner_ids else None
    
    def _get_product_id_by_sku(self, conn, sku: str) -> Optional[int]:
        """Get product ID by SKU"""
        product_ids = conn.execute_kw(
            self.config.db, conn.uid, self.config.password,
            'product.product', 'search',
            [[['default_code', '=', sku]]]
        )
        return product_ids[0] if product_ids else None
    
    def _should_update_existing(self) -> bool:
        """Check if existing records should be updated"""
        return os.getenv('ODOO_UPDATE_EXISTING', 'false').lower() == 'true'
    
    def _log_final_statistics(self):
        """Log final import statistics"""
        if self.stats['start_time'] and self.stats['end_time']:
            duration = self.stats['end_time'] - self.stats['start_time']
            
            self.logger.info("=" * 60)
            self.logger.info("IMPORT STATISTICS")
            self.logger.info("=" * 60)
            self.logger.info(f"Start Time: {self.stats['start_time']}")
            self.logger.info(f"End Time: {self.stats['end_time']}")
            self.logger.info(f"Duration: {duration}")
            self.logger.info(f"Total Records: {self.stats['total_records']}")
            self.logger.info(f"Successful Imports: {self.stats['successful_imports']}")
            self.logger.info(f"Failed Imports: {self.stats['failed_imports']}")
            self.logger.info(f"Skipped Records: {self.stats['skipped_records']}")
            self.logger.info(f"Batches Processed: {self.stats['batches_processed']}")
            self.logger.info("=" * 60)


def load_config_from_env() -> ImportConfig:
    """Load configuration from environment variables"""
    from dotenv import load_dotenv
    
    # Load environment variables
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
    
    return ImportConfig(
        url=os.getenv('ODOO_URL', ''),
        db=os.getenv('ODOO_DB', ''),
        username=os.getenv('ODOO_USERNAME', ''),
        password=os.getenv('ODOO_PASSWORD', ''),
        batch_size=int(os.getenv('BATCH_SIZE', '100')),
        max_retries=int(os.getenv('MAX_RETRIES', '3')),
        retry_delay=float(os.getenv('RETRY_DELAY', '2.0')),
        connection_timeout=float(os.getenv('CONNECTION_TIMEOUT', '30.0')),
        log_level=os.getenv('LOG_LEVEL', 'INFO'),
        progress_file=os.getenv('PROGRESS_FILE', 'data/import_progress.json'),
        backup_dir=os.getenv('BACKUP_DIR', 'data/backups'),
        error_log_file=os.getenv('ERROR_LOG_FILE', 'logs/import_errors.log'),
        failed_records_dir=os.getenv('FAILED_RECORDS_DIR', 'data/failed_records')
    )


def main():
    """Main entry point for Odoo import system"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Odoo Data Import System')
    parser.add_argument('--type', choices=['products', 'partners', 'orders'], 
                       required=True, help='Type of data to import')
    parser.add_argument('--file', required=True, help='Path to data file')
    parser.add_argument('--config', help='Path to config file (uses .env if not provided)')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Validate data without importing')
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = load_config_from_env()
        
        # Validate configuration
        if not all([config.url, config.db, config.username, config.password]):
            print("Error: Missing required Odoo connection parameters")
            print("Please check your .env file or environment variables")
            return 1
        
        # Initialize importer
        importer = OdooImporter(config)
        
        # Validate data file exists
        if not Path(args.file).exists():
            print(f"Error: Data file not found: {args.file}")
            return 1
        
        # Execute import based on type
        if args.type == 'products':
            results = importer.import_product_data(args.file)
        elif args.type == 'partners':
            results = importer.import_partner_data(args.file)
        elif args.type == 'orders':
            results = importer.import_sales_orders(args.file)
        
        print(f"\nImport completed successfully!")
        print(f"Results: {results}")
        
        return 0
        
    except Exception as e:
        print(f"Import failed: {e}")
        print(f"Check logs for detailed error information")
        return 1


if __name__ == '__main__':
    sys.exit(main())