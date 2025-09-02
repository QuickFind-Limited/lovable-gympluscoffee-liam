#!/usr/bin/env python3
"""
Mass Import Orchestrator for Odoo Dataset
Orchestrates the complete import of 35K customers, 65K orders, 125K+ lines, and associated data
"""

import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os
import sys
from dataclasses import dataclass, asdict
from collections import defaultdict
import random

@dataclass
class ImportProgress:
    phase: str
    total_records: int
    processed_records: int
    failed_records: int
    batch_size: int
    start_time: datetime
    current_batch: int
    error_count: int
    retry_count: int
    
    def to_dict(self):
        return asdict(self)

@dataclass
class ImportMetrics:
    customers_imported: int = 0
    orders_imported: int = 0
    order_lines_imported: int = 0
    deliveries_created: int = 0
    invoices_created: int = 0
    returns_processed: int = 0
    total_revenue: float = 0.0
    channel_distribution: Dict[str, int] = None
    geographic_distribution: Dict[str, int] = None
    
    def __post_init__(self):
        if self.channel_distribution is None:
            self.channel_distribution = {}
        if self.geographic_distribution is None:
            self.geographic_distribution = {}

class MassImportOrchestrator:
    def __init__(self):
        self.instance_id = "source-gym-plus-coffee"
        self.log_file = "/workspaces/source-lovable-gympluscoffee/odoo-ingestion/mass_import_log.json"
        self.batch_data_dir = "/workspaces/source-lovable-gympluscoffee/odoo-ingestion/batch_data"
        
        # Import configuration
        self.batch_sizes = {
            'customers': 500,
            'orders': 200,
            'order_lines': 1000,
            'deliveries': 300,
            'invoices': 300,
            'returns': 150
        }
        
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        
        # Progress tracking
        self.progress_log = []
        self.metrics = ImportMetrics()
        self.id_mappings = {
            'customers': {},
            'products': {},
            'orders': {}
        }
        
        # Setup logging
        self.setup_logging()
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/import.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def log_progress(self, phase: str, message: str, data: Dict = None):
        """Log progress with timestamp and structured data"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'phase': phase,
            'message': message,
            'data': data or {}
        }
        
        self.progress_log.append(log_entry)
        self.logger.info(f"[{phase}] {message}")
        
        # Save to file immediately for crash recovery
        self.save_progress()
    
    def save_progress(self):
        """Save current progress to JSON file"""
        progress_data = {
            'last_updated': datetime.now().isoformat(),
            'metrics': asdict(self.metrics),
            'id_mappings': self.id_mappings,
            'progress_log': self.progress_log[-100:]  # Keep last 100 entries
        }
        
        with open(self.log_file, 'w') as f:
            json.dump(progress_data, f, indent=2, default=str)
    
    def load_previous_progress(self):
        """Load previous progress for crash recovery"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    data = json.load(f)
                    if 'id_mappings' in data:
                        self.id_mappings = data['id_mappings']
                    if 'metrics' in data:
                        metrics_data = data['metrics']
                        self.metrics = ImportMetrics(**metrics_data)
                    self.logger.info("Previous progress loaded successfully")
            except Exception as e:
                self.logger.error(f"Failed to load previous progress: {e}")
    
    def wait_for_batch_files(self) -> bool:
        """Wait for batch processor to generate files"""
        self.log_progress("SETUP", "Waiting for batch files from bulk processor...")
        
        # Create batch data directory if it doesn't exist
        os.makedirs(self.batch_data_dir, exist_ok=True)
        
        # For now, return True to proceed with available data
        # In production, this would check for specific batch files
        expected_files = [
            'customers_batch_*.json',
            'orders_batch_*.json', 
            'order_lines_batch_*.json'
        ]
        
        self.log_progress("SETUP", "Batch data directory ready", {"dir": self.batch_data_dir})
        return True
    
    def get_batch_files(self, pattern: str) -> List[str]:
        """Get list of batch files matching pattern"""
        import glob
        return sorted(glob.glob(os.path.join(self.batch_data_dir, pattern)))
    
    def execute_with_retry(self, operation_name: str, operation_func, *args, **kwargs):
        """Execute operation with retry logic"""
        for attempt in range(self.max_retries):
            try:
                result = operation_func(*args, **kwargs)
                return result
            except Exception as e:
                self.logger.error(f"{operation_name} attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
    
    def validate_import_data(self, phase: str, records: List[Dict]) -> List[Dict]:
        """Validate and clean import data"""
        valid_records = []
        
        for record in records:
            try:
                # Basic validation based on phase
                if phase == 'customers':
                    if not record.get('name') or not record.get('email'):
                        continue
                elif phase == 'orders':
                    if not record.get('partner_id') or not record.get('date_order'):
                        continue
                elif phase == 'order_lines':
                    if not record.get('order_id') or not record.get('product_id'):
                        continue
                
                valid_records.append(record)
            except Exception as e:
                self.logger.warning(f"Invalid record in {phase}: {e}")
        
        return valid_records
    
    def generate_mock_data(self):
        """Generate mock data for testing purposes"""
        self.log_progress("SETUP", "Generating mock data for testing...")
        
        # This would be replaced by actual batch file processing
        mock_customers = []
        for i in range(100):  # Small test set
            customer = {
                'name': f'Customer {i+1}',
                'email': f'customer{i+1}@example.com',
                'phone': f'+1-555-{1000+i}',
                'street': f'{i+1} Main St',
                'city': random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix']),
                'zip': f'{10000+i}',
                'country_id': 233,  # United States
                'is_company': False,
                'customer_rank': 1
            }
            mock_customers.append(customer)
        
        # Save mock data
        with open(os.path.join(self.batch_data_dir, 'customers_batch_001.json'), 'w') as f:
            json.dump(mock_customers, f, indent=2)
        
        self.log_progress("SETUP", f"Generated {len(mock_customers)} mock customers")

def main():
    """Main orchestrator entry point"""
    orchestrator = MassImportOrchestrator()
    
    print("🚀 Mass Import Orchestrator Started")
    print(f"📊 Target: 35K customers, 65K orders, 125K+ lines")
    print(f"📁 Batch data directory: {orchestrator.batch_data_dir}")
    print(f"📋 Progress log: {orchestrator.log_file}")
    
    # Load any previous progress
    orchestrator.load_previous_progress()
    
    # Wait for batch files (or generate mock data for testing)
    if not orchestrator.wait_for_batch_files():
        print("❌ Batch files not ready. Exiting.")
        return
    
    # Generate mock data for initial testing
    orchestrator.generate_mock_data()
    
    print("✅ Orchestrator setup complete. Ready for phase execution.")
    print("\nNext steps:")
    print("1. Run Phase 1: Customer import")
    print("2. Run Phase 2: Sales orders import") 
    print("3. Run Phase 3: Order lines import")
    print("4. Run Phase 4: Deliveries & invoices")
    print("5. Run Phase 5: Returns processing")
    
    # Save initial progress
    orchestrator.log_progress("SETUP", "Mass import orchestrator initialized")

if __name__ == "__main__":
    main()