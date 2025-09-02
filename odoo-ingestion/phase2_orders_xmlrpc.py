#!/usr/bin/env python3
"""
Phase 2: Sales Orders Import using XML-RPC
Import sales orders with proper states, channel tags, and customer links
"""

import json
import xmlrpc.client
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import sys
import random

class SalesOrderImporterXMLRPC:
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
        
        # Load customer mappings from Phase 1
        self.id_mappings = {'customers': {}, 'orders': {}}
        self.load_previous_progress()
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'duplicates': 0,
            'errors': [],
            'states_created': {},
            'channels_created': {}
        }
        
        # Order state configuration
        self.order_states = {
            'draft': 0.05,      # 5% draft orders
            'sent': 0.10,       # 10% sent (quotations)
            'sale': 0.70,       # 70% confirmed sales
            'done': 0.15        # 15% completed orders
        }
        
        # Channel distribution targets
        self.channel_targets = {
            'online': 0.60,     # 60% online orders
            'retail': 0.30,     # 30% retail orders  
            'b2b': 0.10         # 10% B2B orders
        }
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def load_previous_progress(self):
        """Load customer mappings from Phase 1"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    data = json.load(f)
                    if 'id_mappings' in data:
                        self.id_mappings.update(data['id_mappings'])
                print(f"📋 Loaded {len(self.id_mappings['customers'])} customer mappings from Phase 1")
            except Exception as e:
                print(f"⚠️ Could not load previous progress: {e}")
    
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
    
    def get_weighted_state(self) -> str:
        """Get order state based on configured weights"""
        rand = random.random()
        cumulative = 0
        
        for state, weight in self.order_states.items():
            cumulative += weight
            if rand <= cumulative:
                return state
        
        return 'sale'  # Default fallback
    
    def generate_order_date(self, preference: str = 'main') -> datetime:
        """Generate realistic order dates"""
        if preference == 'historical':
            # Historical orders from 2023
            start_date = datetime(2023, 1, 1)
            end_date = datetime(2023, 12, 31)
        elif preference == 'recent':
            # Recent orders from 2024
            start_date = datetime(2024, 1, 1)
            end_date = datetime(2024, 5, 31)
        else:
            # Main period: June-September 2024
            start_date = datetime(2024, 6, 1)
            end_date = datetime(2024, 9, 30)
        
        # Generate random date in range
        time_between = end_date - start_date
        days_between = time_between.days
        random_days = random.randrange(days_between)
        
        # Add some time-of-day variation
        random_hours = random.randrange(24)
        random_minutes = random.randrange(60)
        
        return start_date + timedelta(
            days=random_days,
            hours=random_hours,
            minutes=random_minutes
        )
    
    def create_sales_order(self, order_data: Dict) -> Optional[int]:
        """Create a single sales order in Odoo"""
        try:
            order_id = self.models.execute_kw(
                self.db, self.uid, self.password,
                'sale.order', 'create', [order_data]
            )
            return order_id
        except Exception as e:
            self.logger.error(f"Failed to create order: {e}")
            return None
    
    def generate_mock_orders(self, num_orders: int = 300):
        """Generate mock order data for testing"""
        mock_orders = []
        
        # Get customer emails for linking
        customer_emails = list(self.id_mappings.get('customers', {}).keys())
        if not customer_emails:
            print("❌ No customer mappings found. Run Phase 1 first.")
            return
        
        channels = ['online', 'retail', 'b2b']
        
        for i in range(num_orders):
            # Select channel based on distribution
            rand = random.random()
            if rand < 0.6:
                channel = 'online'
            elif rand < 0.9:
                channel = 'retail'
            else:
                channel = 'b2b'
            
            # Select random customer
            customer_email = random.choice(customer_emails)
            
            order = {
                'external_order_ref': f'ORD-2024-{i+1:06d}',
                'customer_email': customer_email,
                'channel': channel,
                'date_preference': random.choice(['main', 'main', 'main', 'recent', 'historical']),
                'notes': f'Order from {channel} channel'
            }
            
            # Add delivery date for some orders
            if random.random() < 0.3:  # 30% have specific delivery dates
                order_date = self.generate_order_date(order['date_preference'])
                delivery_date = order_date + timedelta(days=random.randint(1, 14))
                order['delivery_date'] = delivery_date.isoformat()
            
            mock_orders.append(order)
        
        # Save mock data in batches
        batch_size = 50  # Smaller batches for orders
        for i in range(0, len(mock_orders), batch_size):
            batch = mock_orders[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            batch_file = os.path.join(self.batch_data_dir, f'orders_batch_{batch_num:03d}.json')
            with open(batch_file, 'w') as f:
                json.dump(batch, f, indent=2, default=str)
        
        print(f"📦 Generated {len(mock_orders)} mock orders in {(len(mock_orders) + batch_size - 1) // batch_size} batches")
    
    def prepare_order_data(self, raw_order: Dict) -> Dict:
        """Prepare sales order data for Odoo import"""
        
        # Get customer ID from mapping
        customer_email = raw_order.get('customer_email')
        partner_id = self.id_mappings['customers'].get(customer_email)
        
        if not partner_id:
            raise ValueError(f"Customer not found for email: {customer_email}")
        
        # Determine order state based on distribution
        state = self.get_weighted_state()
        
        # Generate order date
        order_date = self.generate_order_date(raw_order.get('date_preference', 'main'))
        
        order_data = {
            'partner_id': partner_id,
            'date_order': order_date.strftime('%Y-%m-%d %H:%M:%S'),
            'state': state,
            'company_id': 1,  # Default company
            'client_order_ref': raw_order.get('external_order_ref'),
            'note': raw_order.get('notes', ''),
        }
        
        # Add channel-specific fields
        channel = raw_order.get('channel', 'online')
        if channel == 'online':
            order_data['origin'] = 'Website'
        elif channel == 'retail':
            order_data['origin'] = 'Store POS'
        elif channel == 'b2b':
            order_data['origin'] = 'B2B Portal'
        
        # Add delivery information if available
        if raw_order.get('delivery_date'):
            delivery_date = datetime.fromisoformat(raw_order['delivery_date'].replace('Z', '+00:00'))
            order_data['commitment_date'] = delivery_date.strftime('%Y-%m-%d %H:%M:%S')
        
        return order_data
    
    def import_order_batch(self, orders: List[Dict]) -> Dict:
        """Import a batch of sales orders"""
        batch_stats = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'duplicates': 0,
            'errors': [],
            'states_created': {},
            'channels_created': {}
        }
        
        for order in orders:
            batch_stats['processed'] += 1
            
            try:
                # Prepare order data
                order_data = self.prepare_order_data(order)
                
                # Create order
                order_id = self.create_sales_order(order_data)
                
                if order_id:
                    batch_stats['successful'] += 1
                    
                    # Store ID mapping
                    external_ref = order.get('external_order_ref', f'order_{order_id}')
                    self.id_mappings['orders'][external_ref] = order_id
                    
                    # Track statistics
                    state = order_data.get('state', 'sale')
                    batch_stats['states_created'][state] = batch_stats['states_created'].get(state, 0) + 1
                    
                    channel = order.get('channel', 'online')
                    batch_stats['channels_created'][channel] = batch_stats['channels_created'].get(channel, 0) + 1
                    
                    print(f"  ✅ Created: {external_ref} (ID: {order_id}, State: {state}, Channel: {channel})")
                else:
                    batch_stats['failed'] += 1
                    batch_stats['errors'].append(f"Failed to create order {order.get('external_order_ref', 'unknown')}")
                
            except Exception as e:
                batch_stats['failed'] += 1
                error_msg = f"Error processing order {order.get('external_order_ref', 'unknown')}: {e}"
                batch_stats['errors'].append(error_msg)
                print(f"  ❌ Error: {order.get('external_order_ref', 'unknown')} - {e}")
        
        return batch_stats
    
    def save_progress(self):
        """Save progress to JSON file"""
        progress_data = {
            'last_updated': datetime.now().isoformat(),
            'phase': 'PHASE2_ORDERS',
            'statistics': self.stats,
            'id_mappings': self.id_mappings
        }
        
        with open(self.log_file, 'w') as f:
            json.dump(progress_data, f, indent=2, default=str)
    
    def run_phase2_import(self):
        """Execute Phase 2: Sales Orders import"""
        print("🚀 Starting Phase 2: Sales Orders Import")
        
        # Check if we have customer mappings
        if not self.id_mappings.get('customers'):
            print("❌ No customer mappings found. Run Phase 1 first.")
            return False
        
        print(f"📋 Using {len(self.id_mappings['customers'])} customers from Phase 1")
        
        # Connect to Odoo
        if not self.connect_to_odoo():
            print("❌ Failed to connect to Odoo. Aborting.")
            return False
        
        # Generate mock orders for testing
        self.generate_mock_orders(300)
        
        # Find batch files
        batch_files = []
        for file in os.listdir(self.batch_data_dir):
            if file.startswith('orders_batch_') and file.endswith('.json'):
                batch_files.append(os.path.join(self.batch_data_dir, file))
        
        batch_files.sort()
        
        if not batch_files:
            print(f"❌ No order batch files found in {self.batch_data_dir}")
            return False
        
        print(f"📁 Found {len(batch_files)} batch files")
        
        start_time = datetime.now()
        
        # Process each batch file
        for batch_num, batch_file in enumerate(batch_files, 1):
            print(f"\n📦 Processing batch {batch_num}/{len(batch_files)}: {os.path.basename(batch_file)}")
            
            try:
                # Load batch data
                with open(batch_file, 'r') as f:
                    orders = json.load(f)
                
                print(f"  📊 Loaded {len(orders)} orders")
                
                # Import batch
                batch_results = self.import_order_batch(orders)
                
                # Update overall statistics
                self.stats['total_processed'] += batch_results['processed']
                self.stats['successful'] += batch_results['successful']
                self.stats['failed'] += batch_results['failed']
                self.stats['duplicates'] += batch_results['duplicates']
                self.stats['errors'].extend(batch_results['errors'])
                
                # Aggregate state and channel summaries
                for state, count in batch_results['states_created'].items():
                    self.stats['states_created'][state] = self.stats['states_created'].get(state, 0) + count
                
                for channel, count in batch_results['channels_created'].items():
                    self.stats['channels_created'][channel] = self.stats['channels_created'].get(channel, 0) + count
                
                # Save progress after each batch
                self.save_progress()
                
                print(f"  📊 Batch {batch_num} completed:")
                print(f"    ✅ Successful: {batch_results['successful']}")
                print(f"    ❌ Failed: {batch_results['failed']}")
                print(f"    📈 States: {batch_results['states_created']}")
                print(f"    🏪 Channels: {batch_results['channels_created']}")
                
            except Exception as e:
                error_msg = f"Critical error processing batch {batch_num}: {e}"
                print(f"  ❌ {error_msg}")
                self.stats['errors'].append(error_msg)
        
        # Final summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n✅ Phase 2: Sales Orders Import Completed!")
        print(f"📊 Final Statistics:")
        print(f"  📁 Batches processed: {len(batch_files)}")
        print(f"  📊 Total orders processed: {self.stats['total_processed']}")
        print(f"  ✅ Successfully imported: {self.stats['successful']}")
        print(f"  ❌ Failed to import: {self.stats['failed']}")
        print(f"  🔄 Duplicates found: {self.stats['duplicates']}")
        print(f"  ⏱️ Duration: {duration}")
        
        if self.stats['successful'] > 0:
            rate = self.stats['successful'] / duration.total_seconds()
            print(f"  🚀 Import rate: {rate:.2f} orders/second")
        
        print(f"\n📈 Order States Distribution:")
        for state, count in self.stats['states_created'].items():
            percentage = (count / self.stats['successful']) * 100 if self.stats['successful'] > 0 else 0
            print(f"  {state}: {count} ({percentage:.1f}%)")
        
        print(f"\n🏪 Channels Distribution:")
        for channel, count in self.stats['channels_created'].items():
            percentage = (count / self.stats['successful']) * 100 if self.stats['successful'] > 0 else 0
            print(f"  {channel}: {count} ({percentage:.1f}%)")
        
        # Save final progress
        self.save_progress()
        
        print(f"\n📋 Order ID mappings saved for Phase 3")
        print(f"🎯 Ready to proceed to Phase 3: Order Lines Import")
        
        return True

def main():
    """Main entry point"""
    importer = SalesOrderImporterXMLRPC()
    
    print("🎯 Mass Import System - Phase 2: Sales Orders")
    print(f"🏢 Target Instance: {importer.url}")
    print(f"📊 Database: {importer.db}")
    
    success = importer.run_phase2_import()
    
    if success:
        print("\n🎉 Phase 2 completed successfully!")
        return 0
    else:
        print("\n❌ Phase 2 failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())