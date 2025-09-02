#!/usr/bin/env python3
"""
Phase 1: Customer Import using XML-RPC
Import customers using direct XML-RPC calls to Odoo
"""

import json
import xmlrpc.client
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
import os
import sys

class CustomerImporterXMLRPC:
    def __init__(self):
        # Odoo connection parameters
        self.url = "https://source-gym-plus-coffee.odoo.com/"
        self.db = "source-gym-plus-coffee"
        self.username = "admin@quickfindai.com"
        self.password = "BJ62wX2J4yzjS$i"
        
        # Connection objects
        self.common = None
        self.models = None
        self.uid = None
        
        # Progress tracking
        self.log_file = "/workspaces/source-lovable-gympluscoffee/odoo-ingestion/mass_import_log.json"
        self.batch_data_dir = "/workspaces/source-lovable-gympluscoffee/odoo-ingestion/batch_data"
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'duplicates': 0,
            'errors': []
        }
        
        # ID mappings for next phases
        self.id_mappings = {'customers': {}}
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def connect_to_odoo(self) -> bool:
        """Establish connection to Odoo"""
        try:
            print(f"🔗 Connecting to Odoo: {self.url}")
            
            self.common = xmlrpc.client.ServerProxy(f'{self.url}xmlrpc/2/common')
            self.models = xmlrpc.client.ServerProxy(f'{self.url}xmlrpc/2/object')
            
            # Authenticate
            self.uid = self.common.authenticate(self.db, self.username, self.password, {})
            
            if not self.uid:
                print("❌ Authentication failed!")
                return False
            
            print(f"✅ Connected successfully! User ID: {self.uid}")
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def check_duplicate_customer(self, email: str) -> Optional[int]:
        """Check if customer already exists by email"""
        try:
            existing = self.models.execute_kw(
                self.db, self.uid, self.password,
                'res.partner', 'search', [
                    [['email', '=', email]]
                ]
            )
            return existing[0] if existing else None
        except Exception as e:
            self.logger.warning(f"Error checking duplicate customer: {e}")
            return None
    
    def create_customer(self, customer_data: Dict) -> Optional[int]:
        """Create a single customer in Odoo"""
        try:
            customer_id = self.models.execute_kw(
                self.db, self.uid, self.password,
                'res.partner', 'create', [customer_data]
            )
            return customer_id
        except Exception as e:
            self.logger.error(f"Failed to create customer {customer_data.get('name')}: {e}")
            return None
    
    def import_customer_batch(self, customers: List[Dict]) -> Dict:
        """Import a batch of customers"""
        batch_stats = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'duplicates': 0,
            'errors': []
        }
        
        for customer in customers:
            batch_stats['processed'] += 1
            
            try:
                # Check for duplicates
                email = customer.get('email')
                if email:
                    existing_id = self.check_duplicate_customer(email)
                    if existing_id:
                        batch_stats['duplicates'] += 1
                        # Store mapping for existing customer
                        self.id_mappings['customers'][email] = existing_id
                        print(f"  📋 Duplicate found: {customer['name']} (ID: {existing_id})")
                        continue
                
                # Create customer
                customer_id = self.create_customer(customer)
                
                if customer_id:
                    batch_stats['successful'] += 1
                    # Store ID mapping
                    self.id_mappings['customers'][email or customer['name']] = customer_id
                    print(f"  ✅ Created: {customer['name']} (ID: {customer_id})")
                else:
                    batch_stats['failed'] += 1
                    batch_stats['errors'].append(f"Failed to create {customer.get('name', 'unknown')}")
                
            except Exception as e:
                batch_stats['failed'] += 1
                error_msg = f"Error processing customer {customer.get('name', 'unknown')}: {e}"
                batch_stats['errors'].append(error_msg)
                print(f"  ❌ Error: {customer.get('name', 'unknown')} - {e}")
        
        return batch_stats
    
    def save_progress(self):
        """Save progress to JSON file"""
        progress_data = {
            'last_updated': datetime.now().isoformat(),
            'phase': 'PHASE1_CUSTOMERS',
            'statistics': self.stats,
            'id_mappings': self.id_mappings
        }
        
        with open(self.log_file, 'w') as f:
            json.dump(progress_data, f, indent=2, default=str)
    
    def run_phase1_import(self):
        """Execute Phase 1: Customer import"""
        print("🚀 Starting Phase 1: Customer Import")
        
        # Connect to Odoo
        if not self.connect_to_odoo():
            print("❌ Failed to connect to Odoo. Aborting.")
            return False
        
        # Find batch files
        batch_files = []
        for file in os.listdir(self.batch_data_dir):
            if file.startswith('customers_batch_') and file.endswith('.json'):
                batch_files.append(os.path.join(self.batch_data_dir, file))
        
        batch_files.sort()
        
        if not batch_files:
            print(f"❌ No customer batch files found in {self.batch_data_dir}")
            return False
        
        print(f"📁 Found {len(batch_files)} batch files")
        
        start_time = datetime.now()
        
        # Process each batch file
        for batch_num, batch_file in enumerate(batch_files, 1):
            print(f"\n📦 Processing batch {batch_num}/{len(batch_files)}: {os.path.basename(batch_file)}")
            
            try:
                # Load batch data
                with open(batch_file, 'r') as f:
                    customers = json.load(f)
                
                print(f"  📊 Loaded {len(customers)} customers")
                
                # Import batch
                batch_results = self.import_customer_batch(customers)
                
                # Update overall statistics
                self.stats['total_processed'] += batch_results['processed']
                self.stats['successful'] += batch_results['successful']
                self.stats['failed'] += batch_results['failed']
                self.stats['duplicates'] += batch_results['duplicates']
                self.stats['errors'].extend(batch_results['errors'])
                
                # Save progress after each batch
                self.save_progress()
                
                print(f"  📊 Batch {batch_num} completed:")
                print(f"    ✅ Successful: {batch_results['successful']}")
                print(f"    ❌ Failed: {batch_results['failed']}")
                print(f"    🔄 Duplicates: {batch_results['duplicates']}")
                
            except Exception as e:
                error_msg = f"Critical error processing batch {batch_num}: {e}"
                print(f"  ❌ {error_msg}")
                self.stats['errors'].append(error_msg)
        
        # Final summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n✅ Phase 1: Customer Import Completed!")
        print(f"📊 Final Statistics:")
        print(f"  📁 Batches processed: {len(batch_files)}")
        print(f"  📊 Total customers processed: {self.stats['total_processed']}")
        print(f"  ✅ Successfully imported: {self.stats['successful']}")
        print(f"  ❌ Failed to import: {self.stats['failed']}")
        print(f"  🔄 Duplicates found: {self.stats['duplicates']}")
        print(f"  ⏱️ Duration: {duration}")
        
        if self.stats['successful'] > 0:
            rate = self.stats['successful'] / duration.total_seconds()
            print(f"  🚀 Import rate: {rate:.2f} customers/second")
        
        # Save final progress
        self.save_progress()
        
        print(f"\n📋 Customer ID mappings saved for Phase 2")
        print(f"🎯 Ready to proceed to Phase 2: Sales Orders Import")
        
        return True

def main():
    """Main entry point"""
    importer = CustomerImporterXMLRPC()
    
    print("🎯 Mass Import System - Phase 1: Customers")
    print(f"🏢 Target Instance: {importer.url}")
    print(f"📊 Database: {importer.db}")
    
    success = importer.run_phase1_import()
    
    if success:
        print("\n🎉 Phase 1 completed successfully!")
        return 0
    else:
        print("\n❌ Phase 1 failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())