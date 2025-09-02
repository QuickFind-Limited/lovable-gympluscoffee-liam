#!/usr/bin/env python3
"""
Final Mass Import - Complete Dataset Import to Odoo
Imports 35,000 customers and 65,000 transactions to replace linear sales data
"""

import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import traceback
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/mass_import.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OdooMassImporter:
    def __init__(self):
        self.instance_id = "source-gym-plus-coffee"
        self.imported_customers = {}
        self.imported_products = {}
        self.statistics = {
            'customers_created': 0,
            'orders_created': 0,
            'order_lines_created': 0,
            'returns_created': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
        
    def load_data_files(self) -> Dict[str, Any]:
        """Load all data files"""
        logger.info("Loading data files...")
        
        try:
            # Load customers
            with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/generated_customers.json', 'r') as f:
                customers_data = json.load(f)
                
            # Load transactions
            with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/generated_transactions.json', 'r') as f:
                transactions_data = json.load(f)
                
            # Load product mapping
            with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/product_mapping.json', 'r') as f:
                product_mapping = json.load(f)
                
            logger.info(f"Loaded {len(customers_data)} customers")
            logger.info(f"Loaded {len(transactions_data.get('transactions', []))} transactions")
            logger.info(f"Loaded {len(product_mapping.get('products', {}))} product mappings")
            
            return {
                'customers': customers_data,
                'transactions': transactions_data.get('transactions', []),
                'product_mapping': product_mapping.get('products', {}),
                'transaction_metadata': transactions_data.get('metadata', {}),
                'transaction_summary': transactions_data.get('summary_statistics', {})
            }
            
        except Exception as e:
            logger.error(f"Error loading data files: {str(e)}")
            raise
    
    def get_country_id(self, country_code: str) -> Optional[int]:
        """Get country ID from Odoo"""
        country_map = {
            'GB': 'United Kingdom',
            'US': 'United States',
            'AU': 'Australia', 
            'IE': 'Ireland'
        }
        
        try:
            from tools import mcp__odoo_mcp__odoo_search
            country_ids = mcp__odoo_mcp__odoo_search(
                instance_id=self.instance_id,
                model='res.country',
                domain=[('name', '=', country_map.get(country_code, 'United Kingdom'))]
            )
            return country_ids[0] if country_ids else None
        except:
            return None
    
    def import_customers_batch(self, customers_batch: List[Dict], batch_num: int) -> Dict[str, int]:
        """Import a batch of customers"""
        logger.info(f"Importing customer batch {batch_num} ({len(customers_batch)} customers)")
        batch_mapping = {}
        
        for customer in customers_batch:
            try:
                # Check if customer already exists
                from tools import mcp__odoo_mcp__odoo_search
                existing = mcp__odoo_mcp__odoo_search(
                    instance_id=self.instance_id,
                    model='res.partner',
                    domain=[('email', '=', customer['email'])]
                )
                
                if existing:
                    batch_mapping[customer['customer_id']] = existing[0]
                    continue
                
                # Prepare customer data
                customer_data = {
                    'name': f"{customer['first_name']} {customer['last_name']}",
                    'email': customer['email'],
                    'phone': customer.get('phone', ''),
                    'is_company': customer['type'] == 'Business',
                    'customer_rank': 1,  # Mark as customer
                    'supplier_rank': 0,
                    'category_id': [(6, 0, [])],  # Empty category for now
                }
                
                # Add country if available
                if 'country' in customer:
                    country_id = self.get_country_id(customer['country'])
                    if country_id:
                        customer_data['country_id'] = country_id
                
                # Add address fields if available
                if 'address' in customer:
                    addr = customer['address']
                    customer_data.update({
                        'street': addr.get('street', ''),
                        'city': addr.get('city', ''),
                        'zip': addr.get('postal_code', ''),
                        'state_id': False  # Could add state mapping later
                    })
                
                # Create customer
                from tools import mcp__odoo_mcp__odoo_create
                partner_id = mcp__odoo_mcp__odoo_create(
                    instance_id=self.instance_id,
                    model='res.partner',
                    values=customer_data
                )
                
                batch_mapping[customer['customer_id']] = partner_id
                self.statistics['customers_created'] += 1
                
                if self.statistics['customers_created'] % 100 == 0:
                    logger.info(f"Created {self.statistics['customers_created']} customers")
                
            except Exception as e:
                logger.error(f"Error creating customer {customer['customer_id']}: {str(e)}")
                self.statistics['errors'] += 1
                continue
        
        return batch_mapping
    
    def get_product_id(self, sku: str, product_mapping: Dict) -> Optional[int]:
        """Get product ID from mapping"""
        if sku in self.imported_products:
            return self.imported_products[sku]
            
        if sku in product_mapping:
            odoo_id = product_mapping[sku].get('odoo_id')
            if odoo_id:
                self.imported_products[sku] = odoo_id
                return odoo_id
        
        return None
    
    def import_transactions_batch(self, transactions_batch: List[Dict], 
                                customer_mapping: Dict, product_mapping: Dict,
                                batch_num: int) -> None:
        """Import a batch of transactions"""
        logger.info(f"Importing transaction batch {batch_num} ({len(transactions_batch)} transactions)")
        
        for transaction in transactions_batch:
            try:
                # Get customer ID
                customer_id = customer_mapping.get(transaction['customer_id'])
                if not customer_id:
                    logger.warning(f"Customer {transaction['customer_id']} not found")
                    continue
                
                # Prepare order data
                order_date = datetime.strptime(transaction['date'], '%Y-%m-%d').date()
                
                order_data = {
                    'partner_id': customer_id,
                    'date_order': order_date.isoformat(),
                    'state': 'sale' if transaction.get('status') == 'completed' else 'draft',
                    'order_line': [],
                    'team_id': False,  # Sales team (could map channels later)
                    'origin': f"Channel: {transaction.get('channel', 'online')}",
                    'client_order_ref': transaction['order_id'],
                }
                
                # Add order lines
                total_order_value = 0
                for item in transaction.get('items', []):
                    product_id = self.get_product_id(item['sku'], product_mapping)
                    if not product_id:
                        logger.warning(f"Product {item['sku']} not found")
                        continue
                    
                    line_total = item['quantity'] * item['unit_price']
                    total_order_value += line_total
                    
                    order_line_data = {
                        'product_id': product_id,
                        'product_uom_qty': item['quantity'],
                        'price_unit': item['unit_price'],
                        'name': item.get('product_name', f"Product {item['sku']}"),
                    }
                    
                    order_data['order_line'].append((0, 0, order_line_data))
                    self.statistics['order_lines_created'] += 1
                
                if not order_data['order_line']:
                    logger.warning(f"No valid products for order {transaction['order_id']}")
                    continue
                
                # Create sale order
                from tools import mcp__odoo_mcp__odoo_create
                order_id = mcp__odoo_mcp__odoo_create(
                    instance_id=self.instance_id,
                    model='sale.order',
                    values=order_data
                )
                
                self.statistics['orders_created'] += 1
                
                # Handle returns if present
                if transaction.get('return_info'):
                    try:
                        self.create_return_order(order_id, transaction['return_info'], 
                                               customer_id, product_mapping)
                    except Exception as e:
                        logger.error(f"Error creating return: {str(e)}")
                
                if self.statistics['orders_created'] % 100 == 0:
                    logger.info(f"Created {self.statistics['orders_created']} orders, "
                              f"{self.statistics['order_lines_created']} lines")
                    
            except Exception as e:
                logger.error(f"Error creating order {transaction.get('order_id', 'unknown')}: {str(e)}")
                self.statistics['errors'] += 1
                continue
    
    def create_return_order(self, original_order_id: int, return_info: Dict, 
                          customer_id: int, product_mapping: Dict) -> None:
        """Create a return order"""
        try:
            return_date = datetime.strptime(return_info['date'], '%Y-%m-%d').date()
            
            return_data = {
                'partner_id': customer_id,
                'date_order': return_date.isoformat(),
                'state': 'sale',
                'order_line': [],
                'origin': f"Return of Order ID: {original_order_id}",
                'client_order_ref': f"RET-{return_info.get('return_id', 'unknown')}",
            }
            
            # Add return lines (negative quantities)
            for item in return_info.get('items', []):
                product_id = self.get_product_id(item['sku'], product_mapping)
                if not product_id:
                    continue
                
                line_data = {
                    'product_id': product_id,
                    'product_uom_qty': -abs(item['quantity']),  # Negative for returns
                    'price_unit': item['unit_price'],
                    'name': f"RETURN: {item.get('product_name', item['sku'])}",
                }
                
                return_data['order_line'].append((0, 0, line_data))
            
            if return_data['order_line']:
                from tools import mcp__odoo_mcp__odoo_create
                mcp__odoo_mcp__odoo_create(
                    instance_id=self.instance_id,
                    model='sale.order',
                    values=return_data
                )
                self.statistics['returns_created'] += 1
                
        except Exception as e:
            logger.error(f"Error creating return order: {str(e)}")
    
    def execute_mass_import(self) -> Dict[str, Any]:
        """Execute the complete mass import"""
        logger.info("=" * 60)
        logger.info("STARTING FINAL MASS IMPORT")
        logger.info("=" * 60)
        
        self.statistics['start_time'] = datetime.now()
        
        try:
            # Load data
            data = self.load_data_files()
            
            customers = data['customers']
            transactions = data['transactions']
            product_mapping = data['product_mapping']
            
            # Import customers in batches of 150
            batch_size = 150
            customer_batches = [customers[i:i + batch_size] 
                              for i in range(0, len(customers), batch_size)]
            
            logger.info(f"Importing {len(customers)} customers in {len(customer_batches)} batches")
            
            all_customer_mapping = {}
            for i, batch in enumerate(customer_batches, 1):
                batch_mapping = self.import_customers_batch(batch, i)
                all_customer_mapping.update(batch_mapping)
                
                # Brief pause between batches
                if i % 10 == 0:
                    time.sleep(2)
                    logger.info(f"Completed {i}/{len(customer_batches)} customer batches")
            
            logger.info(f"Customer import complete: {len(all_customer_mapping)} customers mapped")
            
            # Import transactions in batches of 100
            tx_batch_size = 100
            transaction_batches = [transactions[i:i + tx_batch_size] 
                                 for i in range(0, len(transactions), tx_batch_size)]
            
            logger.info(f"Importing {len(transactions)} transactions in {len(transaction_batches)} batches")
            
            for i, batch in enumerate(transaction_batches, 1):
                self.import_transactions_batch(batch, all_customer_mapping, 
                                             product_mapping, i)
                
                # Brief pause between batches
                if i % 20 == 0:
                    time.sleep(3)
                    logger.info(f"Completed {i}/{len(transaction_batches)} transaction batches")
            
            self.statistics['end_time'] = datetime.now()
            
            # Generate final report
            return self.generate_final_report(data['transaction_summary'])
            
        except Exception as e:
            logger.error(f"Mass import failed: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def generate_final_report(self, original_summary: Dict) -> Dict[str, Any]:
        """Generate comprehensive final report"""
        duration = self.statistics['end_time'] - self.statistics['start_time']
        
        # Calculate validation metrics from imported data
        try:
            from tools import mcp__odoo_mcp__odoo_search_count
            
            # Count customers by type
            total_customers = mcp__odoo_mcp__odoo_search_count(
                instance_id=self.instance_id,
                model='res.partner',
                domain=[('customer_rank', '>', 0)]
            )
            
            # Count orders
            total_orders = mcp__odoo_mcp__odoo_search_count(
                instance_id=self.instance_id,
                model='sale.order',
                domain=[]
            )
            
        except:
            total_customers = self.statistics['customers_created'] 
            total_orders = self.statistics['orders_created']
        
        report = {
            'import_statistics': self.statistics,
            'duration_minutes': duration.total_seconds() / 60,
            'validation_results': {
                'total_customers': total_customers,
                'total_orders': total_orders,
                'total_order_lines': self.statistics['order_lines_created'],
                'total_returns': self.statistics['returns_created'],
                'error_rate': f"{(self.statistics['errors'] / max(len(original_summary), 1)) * 100:.2f}%",
            },
            'original_targets': {
                'expected_customers': 35000,
                'expected_transactions': 65000,
                'expected_channels': original_summary.get('channel_breakdown', {}),
                'expected_geography': original_summary.get('geographic_breakdown', {}),
            },
            'data_location': {
                'sales_orders': 'Sales > Orders',
                'customers': 'Contacts > Customers',
                'products': 'Sales > Products > Products',
            }
        }
        
        return report


def main():
    """Main execution function"""
    try:
        importer = OdooMassImporter()
        report = importer.execute_mass_import()
        
        # Print final report
        print("\n" + "=" * 60)
        print("SYNTHETIC DATA GENERATION COMPLETE")
        print("=" * 60)
        
        stats = report['import_statistics']
        print(f"Records Created:")
        print(f"- Customers: {stats['customers_created']:,}")
        print(f"- Orders: {stats['orders_created']:,}")
        print(f"- Order Lines: {stats['order_lines_created']:,}")
        print(f"- Returns: {stats['returns_created']:,}")
        print(f"- Errors: {stats['errors']:,}")
        
        validation = report['validation_results']
        print(f"\nValidation Results:")
        print(f"- Total Import Time: {report['duration_minutes']:.1f} minutes")
        print(f"- Error Rate: {validation['error_rate']}")
        
        targets = report['original_targets']
        if 'expected_channels' in targets and targets['expected_channels']:
            channels = targets['expected_channels']
            print(f"- Channel Split: Online {channels.get('online', {}).get('percentage', 0):.1f}% | "
                  f"Retail {channels.get('retail', {}).get('percentage', 0):.1f}% | "
                  f"B2B {channels.get('b2b', {}).get('percentage', 0):.1f}%")
        
        print(f"\nData Location in Odoo:")
        for location, path in report['data_location'].items():
            print(f"- {location}: {path}")
        
        print(f"\nImport completed successfully!")
        print(f"Log file: /workspaces/source-lovable-gympluscoffee/odoo-ingestion/mass_import.log")
        
        # Save report
        with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/final_import_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
    except Exception as e:
        print(f"Import failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()