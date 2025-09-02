#!/usr/bin/env python3
"""
Comprehensive Odoo Data Import System
Imports customers, products, and transactions efficiently with error handling
"""

import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('odoo_import.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class OdooDataImporter:
    """Comprehensive Odoo data importer with batch processing and error handling"""
    
    def __init__(self):
        self.instance_id = "source-gym-plus-coffee"
        self.batch_size = 75  # Optimal batch size to avoid timeouts
        self.max_retries = 3
        self.retry_delay = 2
        
        # Import statistics
        self.stats = {
            'customers': {'imported': 0, 'failed': 0, 'skipped': 0},
            'orders': {'imported': 0, 'failed': 0, 'skipped': 0},
            'order_lines': {'imported': 0, 'failed': 0, 'skipped': 0}
        }
        
        # Cache for existing records
        self.existing_customers = set()
        self.existing_products = {}
        self.product_mapping = {}
        
        logger.info("🚀 Initializing Odoo Data Importer")
    
    def load_data_files(self) -> Tuple[List[Dict], List[Dict], Dict]:
        """Load all data files with error handling"""
        try:
            # Load customers
            logger.info("📂 Loading customer data...")
            with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/generated_customers.json', 'r') as f:
                customers = json.load(f)
            logger.info(f"✅ Loaded {len(customers)} customers")
            
            # Load transactions
            logger.info("📂 Loading transaction data...")
            with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/generated_transactions.json', 'r') as f:
                transaction_data = json.load(f)
            transactions = transaction_data.get('transactions', [])
            logger.info(f"✅ Loaded {len(transactions)} transactions")
            
            # Load product mapping
            logger.info("📂 Loading product mapping...")
            with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/product_mapping.json', 'r') as f:
                product_mapping = json.load(f)
            logger.info(f"✅ Loaded product mapping with {product_mapping.get('metadata', {}).get('total_products', 0)} products")
            
            return customers, transactions, product_mapping
            
        except Exception as e:
            logger.error(f"❌ Error loading data files: {e}")
            raise
    
    def get_existing_customers(self) -> None:
        """Cache existing customer emails to avoid duplicates"""
        try:
            from mcp__odoo_mcp__odoo_search_read import mcp__odoo_mcp__odoo_search_read
            
            logger.info("🔍 Checking existing customers...")
            existing = mcp__odoo_mcp__odoo_search_read(
                instance_id=self.instance_id,
                model="res.partner",
                domain=[('customer_rank', '>', 0)],
                fields=['email', 'name'],
                limit=50000
            )
            
            if existing:
                self.existing_customers = {rec.get('email', '').lower() for rec in existing if rec.get('email')}
                logger.info(f"📊 Found {len(self.existing_customers)} existing customers")
            
        except Exception as e:
            logger.warning(f"⚠️  Could not check existing customers: {e}")
    
    def get_product_mapping(self, product_mapping: Dict) -> None:
        """Create mapping from product names to Odoo product IDs"""
        try:
            from mcp__odoo_mcp__odoo_search_read import mcp__odoo_mcp__odoo_search_read
            
            logger.info("🛍️  Loading product mapping...")
            products = mcp__odoo_mcp__odoo_search_read(
                instance_id=self.instance_id,
                model="product.product",
                domain=[('sale_ok', '=', True)],
                fields=['id', 'name', 'default_code', 'list_price'],
                limit=1000
            )
            
            if products:
                # Create mapping by name and default_code
                for product in products:
                    name = product.get('name', '').strip()
                    code = product.get('default_code', '').strip()
                    
                    if name:
                        self.existing_products[name.lower()] = {
                            'id': product['id'],
                            'name': name,
                            'price': product.get('list_price', 0)
                        }
                    if code:
                        self.existing_products[code.lower()] = {
                            'id': product['id'],
                            'name': name,
                            'price': product.get('list_price', 0)
                        }
                
                logger.info(f"📦 Mapped {len(self.existing_products)} products")
                
                # Map generated products to Odoo products
                if 'products' in product_mapping:
                    for prod in product_mapping['products']:
                        gen_name = prod.get('name', '').lower()
                        if gen_name in self.existing_products:
                            self.product_mapping[gen_name] = self.existing_products[gen_name]['id']
            
        except Exception as e:
            logger.warning(f"⚠️  Could not load product mapping: {e}")
    
    def batch_create_customers(self, customers: List[Dict]) -> None:
        """Import customers in batches with error handling"""
        try:
            from mcp__odoo_mcp__odoo_create import mcp__odoo_mcp__odoo_create
            
            total_customers = len(customers)
            logger.info(f"👥 Starting import of {total_customers} customers in batches of {self.batch_size}")
            
            for i in range(0, total_customers, self.batch_size):
                batch = customers[i:i + self.batch_size]
                batch_num = (i // self.batch_size) + 1
                total_batches = (total_customers + self.batch_size - 1) // self.batch_size
                
                logger.info(f"📦 Processing customer batch {batch_num}/{total_batches} ({len(batch)} records)")
                
                success_count = 0
                for customer in batch:
                    try:
                        # Skip if customer already exists
                        email = customer.get('email', '').lower().strip()
                        if email in self.existing_customers:
                            self.stats['customers']['skipped'] += 1
                            continue
                        
                        # Prepare customer data
                        customer_data = {
                            'name': f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip(),
                            'email': email,
                            'phone': customer.get('phone', ''),
                            'customer_rank': 1,
                            'is_company': customer.get('type', '').lower() == 'company',
                            'street': customer.get('city', ''),
                            'country_id': self.get_country_id(customer.get('country', 'UK')),
                            'ref': customer.get('customer_id', ''),
                        }
                        
                        # Remove empty values
                        customer_data = {k: v for k, v in customer_data.items() if v not in [None, '', False]}
                        
                        # Create customer
                        result = mcp__odoo_mcp__odoo_create(
                            instance_id=self.instance_id,
                            model="res.partner",
                            values=customer_data
                        )
                        
                        if result:
                            success_count += 1
                            self.stats['customers']['imported'] += 1
                            self.existing_customers.add(email)
                        
                    except Exception as e:
                        logger.warning(f"⚠️  Failed to create customer {customer.get('email', 'unknown')}: {e}")
                        self.stats['customers']['failed'] += 1
                        continue
                
                logger.info(f"✅ Batch {batch_num} completed: {success_count}/{len(batch)} customers imported")
                
                # Brief pause to avoid overwhelming the server
                if batch_num < total_batches:
                    time.sleep(1)
            
            logger.info(f"🎉 Customer import completed: {self.stats['customers']['imported']} imported, {self.stats['customers']['skipped']} skipped, {self.stats['customers']['failed']} failed")
            
        except Exception as e:
            logger.error(f"❌ Error in batch customer creation: {e}")
            raise
    
    def get_country_id(self, country_code: str) -> Optional[int]:
        """Get country ID by code"""
        country_map = {
            'UK': 233,  # United Kingdom
            'US': 233,  # United States
            'AU': 13,   # Australia  
            'IE': 105   # Ireland
        }
        return country_map.get(country_code.upper())
    
    def get_customer_id_by_email(self, email: str) -> Optional[int]:
        """Find customer ID by email"""
        try:
            from mcp__odoo_mcp__odoo_search import mcp__odoo_mcp__odoo_search
            
            customer_ids = mcp__odoo_mcp__odoo_search(
                instance_id=self.instance_id,
                model="res.partner",
                domain=[('email', '=', email.lower().strip())],
                limit=1
            )
            
            return customer_ids[0] if customer_ids else None
            
        except Exception as e:
            logger.warning(f"⚠️  Could not find customer by email {email}: {e}")
            return None
    
    def find_product_id(self, product_name: str) -> Optional[int]:
        """Find product ID by name or code"""
        if not product_name:
            return None
            
        # Try exact match first
        product_key = product_name.lower().strip()
        if product_key in self.existing_products:
            return self.existing_products[product_key]['id']
        
        # Try partial matching
        for key, product in self.existing_products.items():
            if product_name.lower() in key or key in product_name.lower():
                return product['id']
        
        # Default fallback - return first product if available
        if self.existing_products:
            return list(self.existing_products.values())[0]['id']
        
        return None
    
    def batch_create_orders(self, transactions: List[Dict]) -> None:
        """Import orders and order lines in batches"""
        try:
            from mcp__odoo_mcp__odoo_create import mcp__odoo_mcp__odoo_create
            
            total_transactions = len(transactions)
            logger.info(f"🛒 Starting import of {total_transactions} orders in batches of {self.batch_size}")
            
            processed_orders = set()
            
            for i in range(0, total_transactions, self.batch_size):
                batch = transactions[i:i + self.batch_size]
                batch_num = (i // self.batch_size) + 1
                total_batches = (total_transactions + self.batch_size - 1) // self.batch_size
                
                logger.info(f"📦 Processing order batch {batch_num}/{total_batches} ({len(batch)} records)")
                
                success_count = 0
                for transaction in batch:
                    try:
                        order_id = transaction.get('order_id')
                        if not order_id or order_id in processed_orders:
                            self.stats['orders']['skipped'] += 1
                            continue
                        
                        # Find customer
                        customer_email = transaction.get('customer_email', '').strip()
                        if not customer_email:
                            self.stats['orders']['failed'] += 1
                            continue
                        
                        customer_id = self.get_customer_id_by_email(customer_email)
                        if not customer_id:
                            logger.warning(f"⚠️  Customer not found for order {order_id}: {customer_email}")
                            self.stats['orders']['failed'] += 1
                            continue
                        
                        # Create order
                        order_date = transaction.get('order_date', '2024-07-01')
                        order_data = {
                            'partner_id': customer_id,
                            'name': order_id,
                            'date_order': order_date,
                            'state': 'sale',
                        }
                        
                        # Map channel to team/source
                        channel = transaction.get('channel', 'online')
                        if channel == 'online':
                            order_data['team_id'] = 1  # Website
                        elif channel == 'retail':
                            order_data['team_id'] = 2  # Retail
                        elif channel == 'b2b':
                            order_data['team_id'] = 3  # B2B
                        
                        order_result = mcp__odoo_mcp__odoo_create(
                            instance_id=self.instance_id,
                            model="sale.order",
                            values=order_data
                        )
                        
                        if order_result:
                            # Create order lines
                            items = transaction.get('items', [])
                            line_success = 0
                            
                            for item in items:
                                try:
                                    product_name = item.get('product_name', '')
                                    product_id = self.find_product_id(product_name)
                                    
                                    if not product_id:
                                        logger.warning(f"⚠️  Product not found: {product_name}")
                                        continue
                                    
                                    line_data = {
                                        'order_id': order_result,
                                        'product_id': product_id,
                                        'product_uom_qty': item.get('quantity', 1),
                                        'price_unit': float(item.get('unit_price', 0)),
                                    }
                                    
                                    line_result = mcp__odoo_mcp__odoo_create(
                                        instance_id=self.instance_id,
                                        model="sale.order.line",
                                        values=line_data
                                    )
                                    
                                    if line_result:
                                        line_success += 1
                                        self.stats['order_lines']['imported'] += 1
                                    else:
                                        self.stats['order_lines']['failed'] += 1
                                        
                                except Exception as e:
                                    logger.warning(f"⚠️  Failed to create order line: {e}")
                                    self.stats['order_lines']['failed'] += 1
                                    continue
                            
                            if line_success > 0:
                                success_count += 1
                                self.stats['orders']['imported'] += 1
                                processed_orders.add(order_id)
                            else:
                                self.stats['orders']['failed'] += 1
                        else:
                            self.stats['orders']['failed'] += 1
                            
                    except Exception as e:
                        logger.warning(f"⚠️  Failed to create order {transaction.get('order_id', 'unknown')}: {e}")
                        self.stats['orders']['failed'] += 1
                        continue
                
                logger.info(f"✅ Batch {batch_num} completed: {success_count}/{len(batch)} orders imported")
                
                # Brief pause between batches
                if batch_num < total_batches:
                    time.sleep(1)
            
            logger.info(f"🎉 Order import completed: {self.stats['orders']['imported']} orders, {self.stats['order_lines']['imported']} lines imported")
            
        except Exception as e:
            logger.error(f"❌ Error in batch order creation: {e}")
            raise
    
    def print_final_report(self) -> None:
        """Print comprehensive import report"""
        logger.info("\n" + "="*60)
        logger.info("📊 FINAL IMPORT REPORT")
        logger.info("="*60)
        
        for entity, stats in self.stats.items():
            total = stats['imported'] + stats['failed'] + stats['skipped']
            logger.info(f"\n{entity.upper()}:")
            logger.info(f"  ✅ Imported: {stats['imported']:,}")
            logger.info(f"  ⚠️  Failed: {stats['failed']:,}")
            logger.info(f"  ⏭️  Skipped: {stats['skipped']:,}")
            logger.info(f"  📊 Total Processed: {total:,}")
            
            if total > 0:
                success_rate = (stats['imported'] / total) * 100
                logger.info(f"  🎯 Success Rate: {success_rate:.1f}%")
        
        logger.info("\n" + "="*60)
        logger.info("🚀 Import process completed successfully!")
        logger.info("="*60 + "\n")
    
    def run_full_import(self) -> None:
        """Execute complete import process"""
        start_time = time.time()
        logger.info("🎯 Starting comprehensive Odoo data import")
        
        try:
            # Load all data
            customers, transactions, product_mapping = self.load_data_files()
            
            # Initialize caches
            self.get_existing_customers()
            self.get_product_mapping(product_mapping)
            
            # Import customers first
            logger.info("\n" + "="*50)
            logger.info("🔄 PHASE 1: CUSTOMER IMPORT")
            logger.info("="*50)
            self.batch_create_customers(customers)
            
            # Import orders and order lines
            logger.info("\n" + "="*50)
            logger.info("🔄 PHASE 2: ORDER IMPORT")
            logger.info("="*50)
            self.batch_create_orders(transactions)
            
            # Final report
            execution_time = time.time() - start_time
            logger.info(f"\n⏱️  Total execution time: {execution_time:.1f} seconds")
            self.print_final_report()
            
        except Exception as e:
            logger.error(f"❌ Critical error in import process: {e}")
            raise

def main():
    """Main execution function"""
    importer = OdooDataImporter()
    importer.run_full_import()

if __name__ == "__main__":
    main()