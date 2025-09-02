#!/usr/bin/env python3
"""
Batch Importer for Odoo
Handles importing customer and order batches with retry logic
"""

import json
import logging
import os
import time
from typing import List, Dict, Any
import xmlrpc.client
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OdooBatchImporter:
    def __init__(self, url: str = "http://localhost:8069", 
                 db: str = "gym_coffee_db", 
                 username: str = "admin", 
                 password: str = "admin"):
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.uid = None
        self.common = None
        self.models = None
        
        self.connect()
        
    def connect(self):
        """Connect to Odoo"""
        try:
            self.common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
            self.uid = self.common.authenticate(self.db, self.username, self.password, {})
            self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")
            logger.info(f"Connected to Odoo as user {self.uid}")
        except Exception as e:
            logger.error(f"Failed to connect to Odoo: {e}")
            raise
            
    def execute_with_retry(self, model: str, method: str, args: List, 
                          max_retries: int = 3, delay: int = 5) -> Any:
        """Execute Odoo method with retry logic"""
        for attempt in range(max_retries):
            try:
                return self.models.execute_kw(self.db, self.uid, self.password, 
                                            model, method, args)
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    logger.error(f"All {max_retries} attempts failed: {e}")
                    raise
                    
    def import_customer_batch(self, batch_file: str) -> Dict:
        """Import a customer batch file"""
        try:
            with open(batch_file, 'r') as f:
                batch_data = json.load(f)
                
            customers = batch_data.get('customers', [])
            batch_num = batch_data.get('batch_number', 0)
            
            logger.info(f"Importing customer batch {batch_num} with {len(customers)} records")
            
            success_count = 0
            error_count = 0
            errors = []
            
            for customer in customers:
                try:
                    # Check if customer already exists
                    existing = self.execute_with_retry('res.partner', 'search', 
                                                     [[('ref', '=', customer.get('ref'))]])
                    
                    if existing:
                        # Update existing
                        self.execute_with_retry('res.partner', 'write', 
                                              [existing, customer])
                        logger.debug(f"Updated customer {customer.get('ref')}")
                    else:
                        # Create new
                        self.execute_with_retry('res.partner', 'create', [customer])
                        logger.debug(f"Created customer {customer.get('ref')}")
                        
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    error_msg = f"Customer {customer.get('ref', 'Unknown')}: {str(e)}"
                    errors.append(error_msg)
                    logger.warning(error_msg)
                    
            result = {
                'batch_file': batch_file,
                'batch_number': batch_num,
                'total_records': len(customers),
                'success_count': success_count,
                'error_count': error_count,
                'errors': errors,
                'import_timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Customer batch {batch_num} completed: {success_count} success, {error_count} errors")
            return result
            
        except Exception as e:
            logger.error(f"Failed to import customer batch {batch_file}: {e}")
            return {'error': str(e), 'batch_file': batch_file}
            
    def import_order_batch(self, batch_file: str) -> Dict:
        """Import an order batch file"""
        try:
            with open(batch_file, 'r') as f:
                batch_data = json.load(f)
                
            orders = batch_data.get('orders', [])
            batch_num = batch_data.get('batch_number', 0)
            
            logger.info(f"Importing order batch {batch_num} with {len(orders)} records")
            
            success_count = 0
            error_count = 0
            errors = []
            
            for order in orders:
                try:
                    # Check if order already exists
                    existing = self.execute_with_retry('sale.order', 'search', 
                                                     [[('name', '=', order.get('name'))]])
                    
                    if existing:
                        logger.debug(f"Order {order.get('name')} already exists, skipping")
                        continue
                        
                    # Create order
                    order_id = self.execute_with_retry('sale.order', 'create', [order])
                    
                    # Confirm order if specified
                    if order.get('state') == 'sale':
                        self.execute_with_retry('sale.order', 'action_confirm', [order_id])
                        
                    success_count += 1
                    logger.debug(f"Created order {order.get('name')}")
                    
                except Exception as e:
                    error_count += 1
                    error_msg = f"Order {order.get('name', 'Unknown')}: {str(e)}"
                    errors.append(error_msg)
                    logger.warning(error_msg)
                    
            result = {
                'batch_file': batch_file,
                'batch_number': batch_num,
                'total_records': len(orders),
                'success_count': success_count,
                'error_count': error_count,
                'errors': errors,
                'import_timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Order batch {batch_num} completed: {success_count} success, {error_count} errors")
            return result
            
        except Exception as e:
            logger.error(f"Failed to import order batch {batch_file}: {e}")
            return {'error': str(e), 'batch_file': batch_file}
            
    def import_all_batches(self, batches_dir: str):
        """Import all batch files in directory"""
        if not os.path.exists(batches_dir):
            logger.error(f"Batches directory not found: {batches_dir}")
            return
            
        results = {'customers': [], 'orders': []}
        
        # Import customer batches first
        customer_files = sorted([f for f in os.listdir(batches_dir) 
                               if f.startswith('customers_batch_')])
        
        logger.info(f"Found {len(customer_files)} customer batch files")
        
        for file in customer_files:
            file_path = os.path.join(batches_dir, file)
            result = self.import_customer_batch(file_path)
            results['customers'].append(result)
            
        # Import order batches
        order_files = sorted([f for f in os.listdir(batches_dir) 
                            if f.startswith('orders_batch_')])
        
        logger.info(f"Found {len(order_files)} order batch files")
        
        for file in order_files:
            file_path = os.path.join(batches_dir, file)
            result = self.import_order_batch(file_path)
            results['orders'].append(result)
            
        # Save results summary
        summary_file = os.path.join(batches_dir, 'import_results.json')
        with open(summary_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        logger.info(f"Import completed. Results saved to {summary_file}")
        
        # Print summary
        customer_success = sum(r.get('success_count', 0) for r in results['customers'])
        customer_errors = sum(r.get('error_count', 0) for r in results['customers'])
        order_success = sum(r.get('success_count', 0) for r in results['orders'])
        order_errors = sum(r.get('error_count', 0) for r in results['orders'])
        
        logger.info(f"FINAL SUMMARY:")
        logger.info(f"Customers: {customer_success} success, {customer_errors} errors")
        logger.info(f"Orders: {order_success} success, {order_errors} errors")

def main():
    """Main execution"""
    batches_dir = "/workspaces/source-lovable-gympluscoffee/odoo-ingestion/batches"
    
    importer = OdooBatchImporter()
    importer.import_all_batches(batches_dir)

if __name__ == "__main__":
    main()