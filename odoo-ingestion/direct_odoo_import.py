#!/usr/bin/env python3
"""
Direct Odoo Data Import System using MCP tools
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

class DirectOdooImporter:
    """Direct Odoo data importer using MCP function calls"""
    
    def __init__(self):
        self.instance_id = "source-gym-plus-coffee"
        self.batch_size = 50  # Conservative batch size
        
        # Import statistics
        self.stats = {
            'customers': {'imported': 0, 'failed': 0, 'skipped': 0, 'total': 0},
            'orders': {'imported': 0, 'failed': 0, 'skipped': 0, 'total': 0},
            'order_lines': {'imported': 0, 'failed': 0, 'skipped': 0, 'total': 0}
        }
        
        # Data caches
        self.customers_data = []
        self.transactions_data = []
        self.product_mapping = {}
        self.existing_customers = set()
        self.existing_products = {}
        
        logger.info("🚀 Initializing Direct Odoo Data Importer")
    
    def load_all_data(self):
        """Load all data files"""
        try:
            # Load customers
            logger.info("📂 Loading customer data...")
            with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/generated_customers.json', 'r') as f:
                self.customers_data = json.load(f)
            logger.info(f"✅ Loaded {len(self.customers_data)} customers")
            self.stats['customers']['total'] = len(self.customers_data)
            
            # Load transactions
            logger.info("📂 Loading transaction data...")
            with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/generated_transactions.json', 'r') as f:
                transaction_data = json.load(f)
            self.transactions_data = transaction_data.get('transactions', [])
            logger.info(f"✅ Loaded {len(self.transactions_data)} transactions")
            self.stats['orders']['total'] = len(self.transactions_data)
            
            # Load product mapping
            logger.info("📂 Loading product mapping...")
            with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/product_mapping.json', 'r') as f:
                self.product_mapping = json.load(f)
            logger.info(f"✅ Loaded product mapping")
            
        except Exception as e:
            logger.error(f"❌ Error loading data files: {e}")
            raise
    
    def get_country_id(self, country_code: str) -> int:
        """Get country ID by code - using reasonable defaults"""
        country_map = {
            'UK': 76,   # United Kingdom
            'US': 235,  # United States  
            'AU': 13,   # Australia
            'IE': 105   # Ireland
        }
        return country_map.get(country_code.upper(), 76)  # Default to UK
    
    def create_sample_data(self):
        """Create a sample of data for testing"""
        # Take first 100 customers and 200 transactions for testing
        sample_customers = self.customers_data[:100]
        sample_transactions = self.transactions_data[:200]
        
        logger.info(f"🧪 Creating sample: {len(sample_customers)} customers, {len(sample_transactions)} transactions")
        
        return sample_customers, sample_transactions
    
    def print_data_preview(self):
        """Print preview of the data structure"""
        logger.info("\n📋 DATA PREVIEW:")
        logger.info(f"Total customers: {len(self.customers_data)}")
        logger.info(f"Total transactions: {len(self.transactions_data)}")
        
        if self.customers_data:
            logger.info(f"Customer sample: {json.dumps(self.customers_data[0], indent=2)}")
        
        if self.transactions_data:
            logger.info(f"Transaction sample: {json.dumps(self.transactions_data[0], indent=2)}")
    
    def run_import(self):
        """Run the import process"""
        start_time = time.time()
        logger.info("🎯 Starting direct Odoo import process")
        
        try:
            # Load data
            self.load_all_data()
            self.print_data_preview()
            
            # For now, let's work with a sample to test the process
            sample_customers, sample_transactions = self.create_sample_data()
            
            logger.info("\n" + "="*60)
            logger.info("📊 IMPORT SUMMARY")
            logger.info("="*60)
            logger.info(f"Ready to import:")
            logger.info(f"  👥 Customers: {len(sample_customers):,}")
            logger.info(f"  🛒 Transactions: {len(sample_transactions):,}")
            
            execution_time = time.time() - start_time
            logger.info(f"⏱️  Preparation time: {execution_time:.1f} seconds")
            
            # The actual import will be done by the calling function using MCP tools
            return sample_customers, sample_transactions
            
        except Exception as e:
            logger.error(f"❌ Critical error in import process: {e}")
            raise

def main():
    """Main execution function"""
    importer = DirectOdooImporter()
    return importer.run_import()

if __name__ == "__main__":
    main()