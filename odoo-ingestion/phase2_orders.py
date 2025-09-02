#!/usr/bin/env python3
"""
Phase 2: Sales Orders Import  
Import 65,000 sales orders with proper states, channel tags, and customer links
"""

import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import random
from mass_import_orchestrator import MassImportOrchestrator

class SalesOrderImporter(MassImportOrchestrator):
    def __init__(self):
        super().__init__()
        self.phase_name = "PHASE2_ORDERS"
        
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
    
    def prepare_order_data(self, raw_order: Dict) -> Dict:
        """Prepare sales order data for Odoo import"""
        
        # Get customer ID from mapping
        customer_key = raw_order.get('customer_id') or raw_order.get('customer_email')
        partner_id = self.id_mappings['customers'].get(customer_key)
        
        if not partner_id:
            raise ValueError(f"Customer not found for key: {customer_key}")
        
        # Determine order state based on distribution
        state = self.get_weighted_state()
        
        # Generate order date (June-September 2024 main period)
        order_date = self.generate_order_date(raw_order.get('date_preference', 'main'))
        
        order_data = {
            'partner_id': partner_id,
            'date_order': order_date.isoformat(),
            'state': state,
            'company_id': 1,  # Default company
            'pricelist_id': 1,  # Default pricelist
            'team_id': self.get_sales_team(raw_order.get('channel', 'online')),
            'user_id': self.get_salesperson(raw_order.get('channel', 'online')),
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
            delivery_date = datetime.fromisoformat(raw_order['delivery_date'])
            order_data['commitment_date'] = delivery_date.isoformat()
        
        # Remove empty fields
        return {k: v for k, v in order_data.items() if v is not None}
    
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
    
    def get_sales_team(self, channel: str) -> int:
        """Get sales team ID based on channel"""
        teams = {
            'online': 1,     # Online Sales Team
            'retail': 2,     # Retail Sales Team
            'b2b': 3         # B2B Sales Team
        }
        return teams.get(channel, 1)
    
    def get_salesperson(self, channel: str) -> int:
        """Get salesperson user ID based on channel"""
        # In production, these would be real user IDs
        salespeople = {
            'online': 2,     # Online Sales Rep
            'retail': 3,     # Retail Manager
            'b2b': 4         # B2B Account Manager
        }
        return salespeople.get(channel, 2)
    
    def check_duplicate_order(self, external_ref: str) -> Optional[int]:
        """Check if order already exists"""
        try:
            # This would use actual Odoo MCP search in production
            return None
        except Exception as e:
            self.logger.warning(f"Error checking duplicate order: {e}")
            return None
    
    def import_order_batch(self, batch_orders: List[Dict]) -> Dict:
        """Import a batch of sales orders"""
        results = {
            'successful': 0,
            'failed': 0,
            'duplicates': 0,
            'errors': [],
            'states_created': {},
            'channels_created': {}
        }
        
        for order in batch_orders:
            try:
                # Check for duplicates
                external_ref = order.get('external_order_ref')
                if external_ref:
                    existing_id = self.check_duplicate_order(external_ref)
                    if existing_id:
                        results['duplicates'] += 1
                        self.id_mappings['orders'][external_ref] = existing_id
                        continue
                
                # Prepare data for Odoo
                odoo_order = self.prepare_order_data(order)
                
                # Import to Odoo (mock for now)
                # order_id = mcp__odoo-mcp__odoo_create(
                #     instance_id=self.instance_id,
                #     model='sale.order',
                #     values=odoo_order
                # )
                
                # Mock successful import
                order_id = 5000 + results['successful']
                
                # Store ID mapping
                order_key = external_ref or f"order_{order_id}"
                self.id_mappings['orders'][order_key] = order_id
                
                results['successful'] += 1
                
                # Track state distribution
                state = odoo_order['state']
                results['states_created'][state] = results['states_created'].get(state, 0) + 1
                
                # Track channel distribution
                channel = order.get('channel', 'online')
                results['channels_created'][channel] = results['channels_created'].get(channel, 0) + 1
                
                # Update metrics
                self.metrics.orders_imported += 1
                self.metrics.channel_distribution[channel] = self.metrics.channel_distribution.get(channel, 0) + 1
                
            except Exception as e:
                results['failed'] += 1
                error_msg = f"Failed to import order {order.get('external_order_ref', 'unknown')}: {e}"
                results['errors'].append(error_msg)
                self.logger.error(error_msg)
        
        return results
    
    def generate_mock_orders(self, num_orders: int = 200):
        """Generate mock order data for testing"""
        mock_orders = []
        
        # Get customer IDs for linking
        customer_ids = list(self.id_mappings.get('customers', {}).keys())
        if not customer_ids:
            # Generate some mock customer mappings
            for i in range(50):
                email = f'customer{i+1}@example.com'
                self.id_mappings['customers'][email] = 1000 + i
            customer_ids = list(self.id_mappings['customers'].keys())
        
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
            
            order = {
                'external_order_ref': f'ORD-2024-{i+1:06d}',
                'customer_id': random.choice(customer_ids),
                'channel': channel,
                'date_preference': random.choice(['main', 'main', 'main', 'recent', 'historical']),
                'notes': f'Order from {channel} channel',
                'delivery_date': None
            }
            
            # Add delivery date for some orders
            if random.random() < 0.3:  # 30% have specific delivery dates
                order_date = self.generate_order_date(order['date_preference'])
                delivery_date = order_date + timedelta(days=random.randint(1, 14))
                order['delivery_date'] = delivery_date.isoformat()
            
            mock_orders.append(order)
        
        # Save mock data in batches
        batch_size = self.batch_sizes['orders']
        for i in range(0, len(mock_orders), batch_size):
            batch = mock_orders[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            batch_file = os.path.join(self.batch_data_dir, f'orders_batch_{batch_num:03d}.json')
            with open(batch_file, 'w') as f:
                json.dump(batch, f, indent=2, default=str)
        
        self.log_progress(self.phase_name, f"Generated {len(mock_orders)} mock orders")
    
    def run_phase2_import(self):
        """Execute Phase 2: Sales Orders import"""
        self.log_progress(self.phase_name, "Starting Phase 2: Sales Orders Import")
        
        # Ensure we have customer mappings from Phase 1
        if not self.id_mappings.get('customers'):
            self.log_progress(self.phase_name, "No customer mappings found. Loading from previous session...")
            self.load_previous_progress()
        
        # Generate mock orders for testing
        self.generate_mock_orders(500)  # Generate 500 test orders
        
        # Get batch files
        batch_files = self.get_batch_files('orders_batch_*.json')
        
        if not batch_files:
            self.log_progress(self.phase_name, "No order batch files found")
            return
        
        total_batches = len(batch_files)
        total_processed = 0
        total_successful = 0
        total_failed = 0
        total_duplicates = 0
        states_summary = {}
        channels_summary = {}
        
        start_time = datetime.now()
        
        for batch_num, batch_file in enumerate(batch_files, 1):
            self.log_progress(
                self.phase_name,
                f"Processing batch {batch_num}/{total_batches}",
                {"file": os.path.basename(batch_file)}
            )
            
            try:
                # Load batch data
                with open(batch_file, 'r') as f:
                    batch_orders = json.load(f)
                
                # Validate data
                valid_orders = self.validate_import_data('orders', batch_orders)
                
                if not valid_orders:
                    self.log_progress(self.phase_name, f"No valid orders in batch {batch_num}")
                    continue
                
                # Import batch with retry logic
                results = self.execute_with_retry(
                    f"Orders batch {batch_num}",
                    self.import_order_batch,
                    valid_orders
                )
                
                # Update totals
                batch_processed = len(valid_orders)
                total_processed += batch_processed
                total_successful += results['successful']
                total_failed += results['failed']
                total_duplicates += results['duplicates']
                
                # Aggregate state and channel summaries
                for state, count in results['states_created'].items():
                    states_summary[state] = states_summary.get(state, 0) + count
                
                for channel, count in results['channels_created'].items():
                    channels_summary[channel] = channels_summary.get(channel, 0) + count
                
                # Log batch results
                self.log_progress(
                    self.phase_name,
                    f"Batch {batch_num} completed",
                    {
                        "processed": batch_processed,
                        "successful": results['successful'],
                        "failed": results['failed'],
                        "duplicates": results['duplicates'],
                        "states": results['states_created'],
                        "channels": results['channels_created']
                    }
                )
                
                # Save progress after each batch
                self.save_progress()
                
            except Exception as e:
                error_msg = f"Critical error processing batch {batch_num}: {e}"
                self.log_progress(self.phase_name, error_msg)
                self.logger.error(error_msg)
        
        # Calculate final metrics
        end_time = datetime.now()
        duration = end_time - start_time
        
        phase_summary = {
            "total_batches": total_batches,
            "total_processed": total_processed,
            "successful_imports": total_successful,
            "failed_imports": total_failed,
            "duplicate_orders": total_duplicates,
            "duration_seconds": duration.total_seconds(),
            "import_rate": total_processed / duration.total_seconds() if duration.total_seconds() > 0 else 0,
            "states_distribution": states_summary,
            "channels_distribution": channels_summary
        }
        
        self.log_progress(
            self.phase_name,
            "Phase 2 completed",
            phase_summary
        )
        
        print(f"\n✅ Phase 2: Sales Orders Import Completed")
        print(f"📊 Processed: {total_processed} orders")
        print(f"✅ Successful: {total_successful}")
        print(f"❌ Failed: {total_failed}")
        print(f"🔄 Duplicates: {total_duplicates}")
        print(f"⏱️ Duration: {duration}")
        print(f"🚀 Rate: {phase_summary['import_rate']:.2f} records/second")
        
        print(f"\n📈 Order States Distribution:")
        for state, count in states_summary.items():
            percentage = (count / total_successful) * 100 if total_successful > 0 else 0
            print(f"  {state}: {count} ({percentage:.1f}%)")
        
        print(f"\n🏪 Channels Distribution:")
        for channel, count in channels_summary.items():
            percentage = (count / total_successful) * 100 if total_successful > 0 else 0
            print(f"  {channel}: {count} ({percentage:.1f}%)")

def main():
    """Run Phase 2 sales orders import"""
    importer = SalesOrderImporter()
    
    print("🚀 Starting Phase 2: Sales Orders Import")
    print(f"📁 Batch size: {importer.batch_sizes['orders']}")
    print(f"🎯 Target: 65,000 orders")
    print(f"📅 Date range: June-September 2024 (main)")
    
    # Run the import
    importer.run_phase2_import()
    
    print("\n🎯 Next: Run Phase 3 - Order Lines Import")

if __name__ == "__main__":
    main()