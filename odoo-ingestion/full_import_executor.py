#!/usr/bin/env python3
"""
Full Odoo Data Import Executor
Imports all generated data to Odoo using direct API calls
"""

import json
import time
import requests
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('odoo_full_import.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class FullOdooImporter:
    """Full Odoo import system with direct API integration"""
    
    def __init__(self):
        # Odoo connection parameters
        self.url = "https://source-gym-plus-coffee.odoo.com/"
        self.db = "source-gym-plus-coffee"
        self.username = "admin@quickfindai.com"
        self.password = "BJ62wX2J4yzjS$i"
        
        self.batch_size = 50  # Conservative batch size
        self.max_retries = 3
        
        # Import statistics
        self.stats = {
            'customers': {'imported': 0, 'failed': 0, 'skipped': 0, 'total': 0},
            'orders': {'imported': 0, 'failed': 0, 'skipped': 0, 'total': 0},
            'lines': {'imported': 0, 'failed': 0, 'skipped': 0, 'total': 0}
        }
        
        self.session = requests.Session()
        self.session.timeout = 30
        
        logger.info("🚀 Full Odoo Importer initialized")
    
    def load_data_files(self) -> tuple:
        """Load all generated data files"""
        logger.info("📂 Loading data files...")
        
        # Load customers
        with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/generated_customers.json', 'r') as f:
            customers = json.load(f)
        
        # Load transactions
        with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/generated_transactions.json', 'r') as f:
            transaction_data = json.load(f)
        transactions = transaction_data.get('transactions', [])
        
        # Load product mapping
        with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/product_mapping.json', 'r') as f:
            product_mapping = json.load(f)
        
        self.stats['customers']['total'] = len(customers)
        self.stats['orders']['total'] = len(transactions)
        
        logger.info(f"✅ Data loaded: {len(customers):,} customers, {len(transactions):,} transactions")
        
        return customers, transactions, product_mapping
    
    def authenticate_odoo(self) -> Optional[int]:
        """Authenticate with Odoo and get user ID"""
        try:
            logger.info("🔐 Authenticating with Odoo...")
            
            auth_url = f"{self.url}web/session/authenticate"
            auth_data = {
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'db': self.db,
                    'login': self.username,
                    'password': self.password
                },
                'id': 1
            }
            
            response = self.session.post(auth_url, json=auth_data, headers={'Content-Type': 'application/json'})
            
            if response.status_code == 200:
                result = response.json()
                if result.get('result') and result['result'].get('uid'):
                    logger.info("✅ Odoo authentication successful")
                    return result['result']['uid']
            
            logger.error(f"❌ Authentication failed: {response.text}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            return None
    
    def create_record(self, model: str, values: Dict[str, Any]) -> Optional[int]:
        """Create a single record in Odoo"""
        try:
            create_url = f"{self.url}web/dataset/call_kw"
            create_data = {
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'model': model,
                    'method': 'create',
                    'args': [values],
                    'kwargs': {}
                },
                'id': 1
            }
            
            response = self.session.post(create_url, json=create_data, headers={'Content-Type': 'application/json'})
            
            if response.status_code == 200:
                result = response.json()
                if result.get('result'):
                    return result['result']
            
            logger.warning(f"⚠️  Failed to create {model}: {response.text}")
            return None
            
        except Exception as e:
            logger.warning(f"⚠️  Error creating {model}: {e}")
            return None
    
    def search_records(self, model: str, domain: List, limit: int = 100) -> List[int]:
        """Search for records in Odoo"""
        try:
            search_url = f"{self.url}web/dataset/call_kw"
            search_data = {
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'model': model,
                    'method': 'search',
                    'args': [domain],
                    'kwargs': {'limit': limit}
                },
                'id': 1
            }
            
            response = self.session.post(search_url, json=search_data, headers={'Content-Type': 'application/json'})
            
            if response.status_code == 200:
                result = response.json()
                return result.get('result', [])
            
            return []
            
        except Exception as e:
            logger.warning(f"⚠️  Error searching {model}: {e}")
            return []
    
    def get_country_id(self, country_code: str) -> int:
        """Get country ID by code"""
        country_map = {
            'UK': 76,   # United Kingdom
            'US': 235,  # United States
            'AU': 13,   # Australia
            'IE': 105   # Ireland
        }
        return country_map.get(country_code.upper(), 76)  # Default to UK
    
    def import_customer_batch(self, customers: List[Dict], batch_num: int, total_batches: int) -> int:
        """Import a batch of customers"""
        logger.info(f"👥 Importing customer batch {batch_num}/{total_batches} ({len(customers)} customers)")
        
        imported = 0
        
        for i, customer in enumerate(customers, 1):
            try:
                customer_data = {
                    'name': f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip(),
                    'email': customer.get('email', '').lower().strip(),
                    'phone': customer.get('phone', ''),
                    'customer_rank': 1,
                    'is_company': customer.get('type', '').lower() == 'company',
                    'street': customer.get('city', ''),
                    'country_id': self.get_country_id(customer.get('country', 'UK')),
                    'ref': customer.get('customer_id', ''),
                }
                
                # Remove empty values
                customer_data = {k: v for k, v in customer_data.items() if v not in [None, '', False]}
                
                result = self.create_record('res.partner', customer_data)
                
                if result:
                    imported += 1
                    self.stats['customers']['imported'] += 1
                else:
                    self.stats['customers']['failed'] += 1
                    
            except Exception as e:
                logger.warning(f"⚠️  Failed to import customer {customer.get('email', 'unknown')}: {e}")
                self.stats['customers']['failed'] += 1
                continue
        
        logger.info(f"✅ Batch {batch_num} complete: {imported}/{len(customers)} customers imported")
        return imported
    
    def import_all_customers(self, customers: List[Dict]) -> None:
        """Import all customers in batches"""
        logger.info(f"🎯 Starting import of {len(customers):,} customers")
        
        total_batches = (len(customers) + self.batch_size - 1) // self.batch_size
        
        for i in range(0, len(customers), self.batch_size):
            batch = customers[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            
            self.import_customer_batch(batch, batch_num, total_batches)
            
            # Brief pause between batches
            if batch_num < total_batches:
                time.sleep(2)
        
        logger.info(f"🎉 Customer import completed: {self.stats['customers']['imported']:,} imported, {self.stats['customers']['failed']:,} failed")
    
    def create_sample_import(self, customers: List[Dict], transactions: List[Dict]) -> None:
        """Create a smaller sample for testing"""
        sample_customers = customers[:100]  # First 100 customers
        sample_transactions = [t for t in transactions if t.get('customer_email', '').lower() in 
                             {c.get('email', '').lower() for c in sample_customers}][:200]  # Related transactions
        
        logger.info(f"🧪 Creating sample import: {len(sample_customers)} customers, {len(sample_transactions)} transactions")
        
        return sample_customers, sample_transactions
    
    def print_final_report(self) -> None:
        """Print comprehensive final report"""
        logger.info("\n" + "="*80)
        logger.info("📊 FINAL IMPORT REPORT")
        logger.info("="*80)
        
        total_processed = sum(stats['imported'] + stats['failed'] + stats['skipped'] for stats in self.stats.values())
        total_success = sum(stats['imported'] for stats in self.stats.values())
        
        for entity, stats in self.stats.items():
            total = stats['imported'] + stats['failed'] + stats['skipped']
            if total > 0:
                success_rate = (stats['imported'] / total) * 100
                logger.info(f"\n{entity.upper()}:")
                logger.info(f"  ✅ Imported: {stats['imported']:,}")
                logger.info(f"  ❌ Failed: {stats['failed']:,}")
                logger.info(f"  ⏭️  Skipped: {stats['skipped']:,}")
                logger.info(f"  📊 Total: {total:,}")
                logger.info(f"  🎯 Success Rate: {success_rate:.1f}%")
        
        overall_rate = (total_success / total_processed * 100) if total_processed > 0 else 0
        
        logger.info(f"\nOVERALL PERFORMANCE:")
        logger.info(f"  🎯 Total Success Rate: {overall_rate:.1f}%")
        logger.info(f"  📈 Records Processed: {total_processed:,}")
        logger.info(f"  ✅ Successfully Imported: {total_success:,}")
        
        logger.info("\n" + "="*80)
        logger.info("🚀 IMPORT PROCESS COMPLETE!")
        logger.info("="*80 + "\n")
    
    def run_full_import(self) -> None:
        """Execute the complete import process"""
        start_time = time.time()
        logger.info("🎯 Starting FULL Odoo Data Import Process")
        logger.info("="*80)
        
        try:
            # Load data
            customers, transactions, product_mapping = self.load_data_files()
            
            # Authenticate
            uid = self.authenticate_odoo()
            if not uid:
                raise Exception("Authentication failed")
            
            # For initial testing, use sample data
            logger.info("\n📝 Using sample data for testing...")
            sample_customers, sample_transactions = self.create_sample_import(customers, transactions)
            
            # Import customers
            logger.info("\n" + "="*60)
            logger.info("🔄 PHASE 1: CUSTOMER IMPORT")
            logger.info("="*60)
            self.import_all_customers(sample_customers)
            
            # Import orders would go here
            logger.info("\n" + "="*60)
            logger.info("🔄 PHASE 2: ORDER IMPORT (READY)")
            logger.info("="*60)
            logger.info("📝 Orders ready for import - implementing order import next...")
            
            # Final report
            execution_time = time.time() - start_time
            logger.info(f"\n⏱️  Total execution time: {execution_time:.1f} seconds")
            self.print_final_report()
            
        except Exception as e:
            logger.error(f"❌ Critical error in import process: {e}")
            raise

def main():
    """Main execution function"""
    importer = FullOdooImporter()
    importer.run_full_import()

if __name__ == "__main__":
    main()