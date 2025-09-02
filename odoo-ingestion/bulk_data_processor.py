#!/usr/bin/env python3
"""
Bulk Data Processor for Odoo Import
Handles 65,000 transactions and 35,000 customers
"""

import json
import logging
import os
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import random
from decimal import Decimal, ROUND_HALF_UP

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BulkDataProcessor:
    def __init__(self, base_path: str = "/workspaces/source-lovable-gympluscoffee/odoo-ingestion"):
        self.base_path = base_path
        self.batches_path = os.path.join(base_path, "batches")
        self.irish_vat_rate = Decimal('0.23')  # 23% Irish VAT
        self.product_mapping = {}
        self.customer_data = []
        self.transaction_data = []
        
        # Irish seasonal promotions
        self.seasonal_discounts = {
            "Black Friday": {"start": "2024-11-29", "end": "2024-12-02", "discount": 0.30},
            "Christmas": {"start": "2024-12-20", "end": "2024-12-26", "discount": 0.20},
            "New Year": {"start": "2025-01-01", "end": "2025-01-07", "discount": 0.15},
            "Valentine's": {"start": "2024-02-10", "end": "2024-02-16", "discount": 0.15},
            "St. Patrick's": {"start": "2024-03-15", "end": "2024-03-19", "discount": 0.25},
            "Summer Sale": {"start": "2024-07-01", "end": "2024-07-31", "discount": 0.20},
            "Back to School": {"start": "2024-08-15", "end": "2024-09-15", "discount": 0.18}
        }
        
        # Create directories
        os.makedirs(self.batches_path, exist_ok=True)
        
    def load_data_files(self):
        """Load the large JSON files in chunks"""
        logger.info("Loading customer data...")
        customers_file = os.path.join(self.base_path, "generated_customers.json")
        
        try:
            with open(customers_file, 'r') as f:
                self.customer_data = json.load(f)
            logger.info(f"Loaded {len(self.customer_data)} customers")
        except Exception as e:
            logger.error(f"Failed to load customer data: {e}")
            return False
            
        logger.info("Loading transaction metadata...")
        transactions_file = os.path.join(self.base_path, "generated_transactions.json")
        
        try:
            # Load just metadata first to understand structure
            with open(transactions_file, 'r') as f:
                # Read first part to get metadata and structure
                content = f.read(10000)  # First 10KB
                if '"transactions": [' in content:
                    # Parse structure info
                    logger.info("Transaction file structure confirmed")
                    self.transaction_data = transactions_file  # Store file path for streaming
                    return True
        except Exception as e:
            logger.error(f"Failed to load transaction data: {e}")
            return False
            
        return True
        
    def load_product_mapping(self, products_list: List[Dict]):
        """Create product mapping from Odoo product list"""
        logger.info("Creating product mapping...")
        
        for product in products_list:
            # Map by ID
            self.product_mapping[product['id']] = {
                'odoo_id': product['id'],
                'name': product['name'],
                'sku': product.get('default_code', f"SKU-{product['id']}"),
                'price': product.get('list_price', 0.0),
                'cost': product.get('standard_price', 0.0),
                'type': product.get('detailed_type', 'consu'),
                'category': product.get('categ_id', [1, 'Unknown'])[1] if product.get('categ_id') else 'Unknown'
            }
            
            # Also map by SKU/name for fuzzy matching
            if product.get('default_code'):
                self.product_mapping[product['default_code']] = self.product_mapping[product['id']]
                
        logger.info(f"Created mapping for {len(products_list)} products")
        
    def calculate_irish_pricing(self, base_price: float, order_date: str, channel: str) -> Dict:
        """Calculate Irish pricing with VAT and seasonal discounts"""
        base_decimal = Decimal(str(base_price))
        discount_rate = Decimal('0.0')
        
        # Check for seasonal promotions
        order_dt = datetime.strptime(order_date, "%Y-%m-%d")
        for promo_name, promo_data in self.seasonal_discounts.items():
            start_dt = datetime.strptime(promo_data["start"], "%Y-%m-%d")
            end_dt = datetime.strptime(promo_data["end"], "%Y-%m-%d")
            
            if start_dt <= order_dt <= end_dt:
                discount_rate = Decimal(str(promo_data["discount"]))
                break
        
        # Channel-specific adjustments
        if channel == 'b2b':
            # B2B gets better pricing but no seasonal discounts
            discount_rate = Decimal('0.10')  # 10% B2B discount
        elif channel == 'retail' and discount_rate == Decimal('0.0'):
            # Retail store gets small discount when no promotions
            discount_rate = Decimal('0.05')
            
        # Calculate pricing
        discounted_price = base_decimal * (Decimal('1') - discount_rate)
        vat_amount = discounted_price * self.irish_vat_rate
        total_price = discounted_price + vat_amount
        
        return {
            'base_price': float(base_decimal),
            'discount_rate': float(discount_rate),
            'discounted_price': float(discounted_price),
            'vat_amount': float(vat_amount),
            'total_price': float(total_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        }
        
    def process_transaction_batch(self, transactions: List[Dict], batch_num: int) -> List[Dict]:
        """Process a batch of transactions with proper Odoo formatting"""
        processed_orders = []
        
        for trans in transactions:
            try:
                # Find customer
                customer_id = trans.get('customer_id')
                customer_data = None
                
                if isinstance(customer_id, str) and customer_id.startswith('CUS'):
                    # Find by customer ID
                    customer_data = next((c for c in self.customer_data if c['customer_id'] == customer_id), None)
                elif isinstance(customer_id, int):
                    # Find by index or match somehow
                    if customer_id < len(self.customer_data):
                        customer_data = self.customer_data[customer_id]
                
                if not customer_data:
                    logger.warning(f"Customer not found for transaction {trans.get('order_id', 'Unknown')}")
                    continue
                
                # Process order
                order = self.format_sale_order(trans, customer_data, batch_num)
                if order:
                    processed_orders.append(order)
                    
            except Exception as e:
                logger.error(f"Error processing transaction {trans.get('order_id', 'Unknown')}: {e}")
                continue
                
        return processed_orders
        
    def format_sale_order(self, trans: Dict, customer: Dict, batch_num: int) -> Optional[Dict]:
        """Format transaction as Odoo sale order"""
        try:
            order_date = trans.get('order_date', '2024-01-01')
            channel = trans.get('channel', 'online')
            
            # Process line items
            order_lines = []
            total_amount = 0.0
            
            for item in trans.get('line_items', []):
                # Find product in mapping
                product_id = item.get('product_id', item.get('sku', 'unknown'))
                product_info = self.product_mapping.get(product_id)
                
                if not product_info:
                    # Try fuzzy matching
                    product_name = item.get('product_name', '').lower()
                    for mapped_id, mapped_info in self.product_mapping.items():
                        if isinstance(mapped_id, int) and product_name in mapped_info['name'].lower():
                            product_info = mapped_info
                            break
                
                if not product_info:
                    logger.warning(f"Product not found: {product_id}")
                    continue
                    
                # Calculate pricing
                base_price = item.get('unit_price', product_info['price'])
                pricing = self.calculate_irish_pricing(base_price, order_date, channel)
                quantity = item.get('quantity', 1)
                
                line_total = pricing['total_price'] * quantity
                total_amount += line_total
                
                order_line = {
                    'product_id': product_info['odoo_id'],
                    'name': product_info['name'],
                    'product_uom_qty': quantity,
                    'price_unit': pricing['discounted_price'],
                    'price_subtotal': line_total,
                    'tax_id': [(6, 0, [1])],  # Assuming tax ID 1 is Irish VAT
                    'discount': pricing['discount_rate'] * 100,  # Convert to percentage
                }
                order_lines.append((0, 0, order_line))
            
            if not order_lines:
                logger.warning(f"No valid order lines for {trans.get('order_id')}")
                return None
                
            # Create sale order
            sale_order = {
                'name': trans.get('order_id', f'ORD-{batch_num}-{len(order_lines)}'),
                'partner_id': self.get_or_create_partner_ref(customer),
                'date_order': f"{order_date} {trans.get('order_time', '12:00:00')}",
                'state': 'sale' if trans.get('status') == 'confirmed' else 'draft',
                'order_line': order_lines,
                'amount_total': total_amount,
                'amount_untaxed': total_amount / (1 + float(self.irish_vat_rate)),
                'team_id': self.get_sales_team_by_channel(channel),
                'client_order_ref': trans.get('reference_number'),
                'note': f"Channel: {channel.title()}, Batch: {batch_num}",
            }
            
            # Handle returns
            if trans.get('is_return', False):
                sale_order['note'] += " - RETURN"
                sale_order['amount_total'] = -abs(sale_order['amount_total'])
                sale_order['amount_untaxed'] = -abs(sale_order['amount_untaxed'])
                
            return sale_order
            
        except Exception as e:
            logger.error(f"Error formatting order {trans.get('order_id', 'Unknown')}: {e}")
            return None
    
    def get_or_create_partner_ref(self, customer: Dict) -> int:
        """Get partner reference - assumes partner creation handled separately"""
        # For now, return a placeholder - this should map to actual Odoo partner IDs
        return hash(customer['customer_id']) % 10000 + 1000
        
    def get_sales_team_by_channel(self, channel: str) -> int:
        """Get sales team ID by channel"""
        team_mapping = {
            'online': 1,  # Website Team
            'b2b': 2,     # B2B Team  
            'retail': 3,  # Retail Team
            'mobile': 1   # Website Team (mobile)
        }
        return team_mapping.get(channel.lower(), 1)
        
    def create_customer_batches(self, batch_size: int = 500):
        """Create customer batches for import"""
        logger.info(f"Creating customer batches (size: {batch_size})...")
        
        total_customers = len(self.customer_data)
        num_batches = math.ceil(total_customers / batch_size)
        
        for i in range(num_batches):
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, total_customers)
            batch_customers = self.customer_data[start_idx:end_idx]
            
            # Format customers for Odoo
            formatted_customers = []
            for customer in batch_customers:
                partner = {
                    'name': f"{customer['first_name']} {customer['last_name']}",
                    'email': customer['email'],
                    'phone': customer.get('phone'),
                    'is_company': customer['type'] == 'company',
                    'customer_rank': 1,
                    'supplier_rank': 0,
                    'street': f"Address for {customer['customer_id']}",
                    'city': customer.get('city', 'Dublin'),
                    'country_id': self.get_country_id(customer.get('country', 'IE')),
                    'vat': f"IE{customer['customer_id'][-8:]}" if customer.get('country') == 'IE' else None,
                    'ref': customer['customer_id'],
                    'category_id': [(6, 0, [self.get_customer_category(customer['segment'])])],
                }
                formatted_customers.append(partner)
            
            # Save batch
            batch_filename = f"customers_batch_{i+1:03d}.json"
            batch_path = os.path.join(self.batches_path, batch_filename)
            
            with open(batch_path, 'w') as f:
                json.dump({
                    'batch_number': i + 1,
                    'total_batches': num_batches,
                    'records_count': len(formatted_customers),
                    'customers': formatted_customers
                }, f, indent=2)
                
            logger.info(f"Created {batch_filename} with {len(formatted_customers)} customers")
            
        logger.info(f"Created {num_batches} customer batches")
        
    def get_country_id(self, country_code: str) -> int:
        """Map country codes to Odoo country IDs"""
        mapping = {
            'IE': 105,  # Ireland
            'UK': 233,  # United Kingdom  
            'US': 235,  # United States
            'AU': 13    # Australia
        }
        return mapping.get(country_code, 105)  # Default to Ireland
        
    def get_customer_category(self, segment: str) -> int:
        """Map customer segments to category IDs"""
        mapping = {
            'VIP': 1,
            'Regular': 2,
            'One-Time': 3
        }
        return mapping.get(segment, 2)
        
    def process_transactions_streaming(self, batch_size: int = 100):
        """Process transactions in streaming fashion to handle large file"""
        logger.info(f"Processing transactions in batches of {batch_size}...")
        
        import ijson  # For streaming JSON parsing
        
        try:
            batch_num = 0
            current_batch = []
            
            with open(self.transaction_data, 'rb') as f:
                # Stream parse the transactions array
                parser = ijson.items(f, 'transactions.item')
                
                for transaction in parser:
                    current_batch.append(transaction)
                    
                    if len(current_batch) >= batch_size:
                        batch_num += 1
                        processed_orders = self.process_transaction_batch(current_batch, batch_num)
                        
                        if processed_orders:
                            self.save_order_batch(processed_orders, batch_num)
                            
                        current_batch = []
                        logger.info(f"Processed batch {batch_num}")
                
                # Process final batch
                if current_batch:
                    batch_num += 1
                    processed_orders = self.process_transaction_batch(current_batch, batch_num)
                    if processed_orders:
                        self.save_order_batch(processed_orders, batch_num)
                        
            logger.info(f"Completed processing {batch_num} order batches")
            
        except ImportError:
            logger.error("ijson library required for streaming. Install with: pip install ijson")
            return False
        except Exception as e:
            logger.error(f"Error in streaming processing: {e}")
            return False
            
        return True
        
    def save_order_batch(self, orders: List[Dict], batch_num: int):
        """Save order batch to file"""
        batch_filename = f"orders_batch_{batch_num:03d}.json"
        batch_path = os.path.join(self.batches_path, batch_filename)
        
        with open(batch_path, 'w') as f:
            json.dump({
                'batch_number': batch_num,
                'records_count': len(orders),
                'orders': orders,
                'processing_timestamp': datetime.now().isoformat()
            }, f, indent=2)
            
        logger.info(f"Saved {batch_filename} with {len(orders)} orders")
        
    def create_processing_summary(self):
        """Create summary of processing results"""
        summary = {
            'processing_date': datetime.now().isoformat(),
            'total_customers_processed': len(self.customer_data),
            'total_products_mapped': len(self.product_mapping),
            'batches_created': {
                'customer_batches': len([f for f in os.listdir(self.batches_path) if f.startswith('customers_batch_')]),
                'order_batches': len([f for f in os.listdir(self.batches_path) if f.startswith('orders_batch_')])
            },
            'irish_vat_rate': float(self.irish_vat_rate),
            'seasonal_promotions_count': len(self.seasonal_discounts),
            'processing_status': 'completed'
        }
        
        summary_path = os.path.join(self.base_path, 'bulk_processing_summary.json')
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
            
        logger.info("Processing summary created")
        return summary

def main():
    """Main execution function"""
    processor = BulkDataProcessor()
    
    # Load data
    if not processor.load_data_files():
        logger.error("Failed to load data files")
        return
        
    # Note: Product mapping will be provided by inventory analyzer
    # For now, create a placeholder
    logger.info("Waiting for product mapping from inventory analyzer...")
    
    # Create customer batches
    processor.create_customer_batches(batch_size=500)
    
    # Process transactions (when product mapping available)
    # processor.process_transactions_streaming(batch_size=100)
    
    # Create summary
    summary = processor.create_processing_summary()
    
    logger.info("Bulk data processing setup completed")
    logger.info(f"Summary: {summary}")

if __name__ == "__main__":
    main()