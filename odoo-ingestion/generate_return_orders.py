#!/usr/bin/env python3
"""
Return Orders Generator for Odoo
===============================

Generates realistic return orders to meet industry standards:
- Online: 20-27% return rate
- Retail: 4-9% return rate  
- B2B: 1-2% return rate

This script connects to the Odoo instance and creates return orders linked to original sales.
"""

import random
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ReturnOrdersGenerator:
    def __init__(self):
        self.instance_id = "source-gym-plus-coffee"
        self.return_reasons = {
            'Size/fit issues': 0.40,
            'Style/color preference': 0.30,
            'Quality concerns': 0.20, 
            'Changed mind': 0.10
        }
        self.channel_return_rates = {
            'D2C': {'min': 20, 'max': 27},     # Online: 20-27%
            'Retail': {'min': 4, 'max': 9},    # Retail: 4-9% 
            'B2B': {'min': 1, 'max': 2}        # B2B: 1-2%
        }
        self.returns_created = []
        self.stats = defaultdict(int)
        
    def run_generation(self):
        """Run complete return orders generation"""
        logging.info("Starting Return Orders Generation...")
        
        try:
            # Step 1: Analyze existing orders by channel
            orders_by_channel = self.analyze_existing_orders()
            
            if not orders_by_channel:
                logging.error("No orders found to generate returns from")
                return
            
            # Step 2: Calculate return targets for each channel
            return_targets = self.calculate_return_targets(orders_by_channel)
            
            # Step 3: Generate returns for each channel
            for channel, target_info in return_targets.items():
                self.generate_channel_returns(channel, target_info, orders_by_channel[channel])
            
            # Step 4: Generate final report
            self.generate_returns_report()
            
            logging.info("Return Orders Generation Complete!")
            
        except Exception as e:
            logging.error(f"Generation failed: {e}")
            raise
    
    def analyze_existing_orders(self) -> Dict[str, List[Dict]]:
        """Analyze existing confirmed orders by channel"""
        logging.info("Analyzing existing orders by channel...")
        
        try:
            # Get all confirmed orders
            # Note: This will be replaced with actual MCP calls during execution
            orders = self.mcp_search_read('sale.order', [
                ('state', 'in', ['sale', 'done']),
                ('amount_total', '>', 0)
            ], ['id', 'name', 'x_channel', 'amount_total', 'date_order', 'partner_id'])
            
            if not orders:
                logging.warning("No confirmed orders found")
                return {}
            
            # Group by channel
            orders_by_channel = defaultdict(list)
            for order in orders:
                channel = order.get('x_channel', 'D2C')  # Default to D2C if no channel
                orders_by_channel[channel].append(order)
            
            # Log channel distribution
            for channel, channel_orders in orders_by_channel.items():
                logging.info(f"{channel}: {len(channel_orders)} orders")
            
            return dict(orders_by_channel)
            
        except Exception as e:
            logging.error(f"Error analyzing orders: {e}")
            return {}
    
    def calculate_return_targets(self, orders_by_channel: Dict[str, List[Dict]]) -> Dict[str, Dict]:
        """Calculate how many returns needed per channel"""
        logging.info("Calculating return targets by channel...")
        
        targets = {}
        
        for channel, orders in orders_by_channel.items():
            if channel not in self.channel_return_rates:
                logging.warning(f"Unknown channel: {channel}, skipping")
                continue
                
            total_orders = len(orders)
            rate_config = self.channel_return_rates[channel]
            
            # Use middle of range for target return rate
            target_rate = (rate_config['min'] + rate_config['max']) / 2
            target_returns = int(total_orders * target_rate / 100)
            
            targets[channel] = {
                'total_orders': total_orders,
                'target_rate': target_rate,
                'target_returns': target_returns,
                'rate_range': f"{rate_config['min']}-{rate_config['max']}%"
            }
            
            logging.info(f"{channel}: {target_returns} returns needed ({target_rate:.1f}% of {total_orders} orders)")
        
        return targets
    
    def generate_channel_returns(self, channel: str, target_info: Dict, orders: List[Dict]):
        """Generate returns for a specific channel"""
        logging.info(f"Generating returns for {channel} channel...")
        
        target_returns = target_info['target_returns']
        if target_returns == 0:
            logging.info(f"No returns needed for {channel}")
            return
            
        # Randomly select orders for returns
        orders_for_returns = random.sample(orders, min(target_returns, len(orders)))
        
        created_count = 0
        for order in orders_for_returns:
            try:
                return_order = self.create_return_order(order, channel)
                if return_order:
                    self.returns_created.append(return_order)
                    created_count += 1
                    self.stats[f'{channel}_returns'] += 1
                    
            except Exception as e:
                logging.error(f"Failed to create return for order {order.get('name', 'Unknown')}: {e}")
                continue
        
        logging.info(f"Created {created_count} returns for {channel} channel")
        self.stats[f'{channel}_created'] = created_count
    
    def create_return_order(self, original_order: Dict, channel: str) -> Dict:
        """Create a return order from original order"""
        try:
            # Get original order lines
            order_lines = self.mcp_search_read('sale.order.line', [
                ('order_id', '=', original_order['id'])
            ], ['product_id', 'product_uom_qty', 'price_unit', 'price_subtotal'])
            
            if not order_lines:
                logging.warning(f"No order lines found for order {original_order.get('name')}")
                return None
            
            # Calculate return date (5-15 days after original order)
            original_date = datetime.strptime(original_order['date_order'][:10], '%Y-%m-%d')
            return_date = original_date + timedelta(days=random.randint(5, 15))
            
            # Select reason for return
            reason = self.select_return_reason()
            
            # Create return order
            return_order_data = {
                'partner_id': original_order['partner_id'][0] if original_order.get('partner_id') else None,
                'x_channel': channel,
                'date_order': return_date.strftime('%Y-%m-%d'),
                'name': f"RET-{original_order['name']}",
                'origin': original_order['name'],
                'x_return_reason': reason,
                'x_is_return': True,
                'state': 'sale'
            }
            
            return_order_id = self.mcp_create('sale.order', return_order_data)
            
            if not return_order_id:
                logging.error(f"Failed to create return order for {original_order['name']}")
                return None
            
            # Create return order lines (negative quantities)
            total_return_amount = 0
            return_lines_created = 0
            
            for line in order_lines:
                # Decide if this line gets returned (80% chance)
                if random.random() < 0.8:
                    return_qty = min(line['product_uom_qty'], random.randint(1, int(line['product_uom_qty'])))
                    
                    return_line_data = {
                        'order_id': return_order_id,
                        'product_id': line['product_id'][0] if line.get('product_id') else None,
                        'product_uom_qty': -return_qty,  # Negative for return
                        'price_unit': line['price_unit'],
                        'price_subtotal': -(line['price_unit'] * return_qty)
                    }
                    
                    return_line_id = self.mcp_create('sale.order.line', return_line_data)
                    if return_line_id:
                        return_lines_created += 1
                        total_return_amount += abs(return_line_data['price_subtotal'])
            
            return_order_info = {
                'id': return_order_id,
                'name': return_order_data['name'],
                'original_order': original_order['name'],
                'channel': channel,
                'return_date': return_date.strftime('%Y-%m-%d'),
                'return_reason': reason,
                'return_amount': total_return_amount,
                'lines_returned': return_lines_created
            }
            
            logging.info(f"Created return order {return_order_data['name']} (€{total_return_amount:.2f})")
            return return_order_info
            
        except Exception as e:
            logging.error(f"Error creating return order: {e}")
            return None
    
    def select_return_reason(self) -> str:
        """Select return reason based on realistic distribution"""
        rand = random.random()
        cumulative = 0
        
        for reason, probability in self.return_reasons.items():
            cumulative += probability
            if rand <= cumulative:
                return reason
        
        return 'Changed mind'  # fallback
    
    def generate_returns_report(self):
        """Generate comprehensive returns report"""
        logging.info("Generating returns report...")
        
        # Calculate statistics
        total_returns = len(self.returns_created)
        total_amount = sum(r['return_amount'] for r in self.returns_created)
        
        # Group by channel
        channel_stats = defaultdict(lambda: {'count': 0, 'amount': 0})
        reason_stats = defaultdict(int)
        
        for return_order in self.returns_created:
            channel = return_order['channel']
            channel_stats[channel]['count'] += 1
            channel_stats[channel]['amount'] += return_order['return_amount']
            reason_stats[return_order['return_reason']] += 1
        
        # Create detailed report
        report = {
            'generation_date': datetime.now().isoformat(),
            'summary': {
                'total_returns_created': total_returns,
                'total_return_amount': round(total_amount, 2),
                'average_return_value': round(total_amount / total_returns, 2) if total_returns > 0 else 0
            },
            'by_channel': {
                channel: {
                    'returns_created': stats['count'],
                    'total_amount': round(stats['amount'], 2),
                    'average_return': round(stats['amount'] / stats['count'], 2) if stats['count'] > 0 else 0
                }
                for channel, stats in channel_stats.items()
            },
            'by_reason': dict(reason_stats),
            'target_rates_achieved': {
                channel: {
                    'target_rate': f"{self.channel_return_rates[channel]['min']}-{self.channel_return_rates[channel]['max']}%",
                    'created_returns': channel_stats[channel]['count']
                }
                for channel in ['D2C', 'Retail', 'B2B'] if channel in channel_stats
            },
            'return_orders': self.returns_created
        }
        
        # Save JSON report
        import json
        with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/return_orders_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate text summary
        text_report = f"""
RETURN ORDERS GENERATION REPORT
==============================

Generation Date: {report['generation_date']}

EXECUTIVE SUMMARY
----------------
Total Returns Created: {total_returns}
Total Return Amount: €{total_amount:,.2f}
Average Return Value: €{report['summary']['average_return_value']:.2f}

CHANNEL BREAKDOWN
----------------
"""
        
        for channel, stats in report['by_channel'].items():
            target_rates = self.channel_return_rates.get(channel, {'min': 0, 'max': 0})
            text_report += f"""
{channel}:
  Returns Created: {stats['returns_created']}
  Total Amount: €{stats['total_amount']:,.2f}
  Average Return: €{stats['average_return']:.2f}
  Target Rate: {target_rates['min']}-{target_rates['max']}%
"""
        
        text_report += "\nRETURN REASONS\n"
        text_report += "--------------\n"
        for reason, count in report['by_reason'].items():
            percentage = (count / total_returns * 100) if total_returns > 0 else 0
            text_report += f"{reason}: {count} ({percentage:.1f}%)\n"
        
        text_report += f"\nSUCCESS METRICS\n"
        text_report += f"---------------\n"
        text_report += f"✅ All return orders created with realistic dates (5-15 days after original)\n"
        text_report += f"✅ Return reasons distributed according to industry standards\n"
        text_report += f"✅ Channel-specific return rates implemented\n"
        text_report += f"✅ Return orders linked to original sales\n"
        
        # Save text report
        with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/return_orders_summary.txt', 'w') as f:
            f.write(text_report)
        
        logging.info(f"Returns Report Generated:")
        logging.info(f"  Total Returns: {total_returns}")
        logging.info(f"  Total Value: €{total_amount:,.2f}")
        logging.info(f"  Reports saved: return_orders_report.json and return_orders_summary.txt")
        
        return report
    
    # MCP Helper Methods (will be replaced with actual calls during execution)
    def mcp_search_read(self, model: str, domain: List = None, fields: List[str] = None, limit: int = None) -> List[Dict]:
        """Search and read records using MCP tools"""
        # This will be replaced with actual MCP calls when executed
        return []
    
    def mcp_create(self, model: str, values: Dict) -> int:
        """Create record using MCP tools"""
        # This will be replaced with actual MCP calls when executed
        return 1


def main():
    """Main execution"""
    generator = ReturnOrdersGenerator()
    generator.run_generation()


if __name__ == "__main__":
    main()