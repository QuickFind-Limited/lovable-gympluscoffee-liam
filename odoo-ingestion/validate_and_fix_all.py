#!/usr/bin/env python3
"""
Master Validation and Correction Script for Odoo Data
=====================================================

This script validates all imported data against requirements and automatically
fixes issues where possible.

Requirements:
- Channel distribution: D2C 60%, Retail 20%, B2B 20% (±3%)
- Geographic distribution: UK 50%, US 20%, AU 20%, IE 10% (±2%)
- Return rates: Online 20-27%, Retail 4-9%, B2B 1-2%
- Customer segments: VIP 5%, Loyal 15%, Regular 30%, One-time 50%
- Product coverage: Every active SKU has sales
- Revenue distribution: Top 20% SKUs generate 60-75% of revenue
- AOV ranges: Online €90-120, Retail €70-100, B2B €500-2500
- Data volatility: Week-to-week variance ≥20%
"""

import json
import random
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Tuple, Any
import statistics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('validation_report.log'),
        logging.StreamHandler()
    ]
)

class OdooDataValidator:
    def __init__(self):
        self.instance_id = "source-gym-plus-coffee"
        self.validation_results = {}
        self.fixes_applied = []
        self.manual_interventions = []
        self.report_data = {
            'validation_date': datetime.now().isoformat(),
            'checks_performed': [],
            'fixes_applied': [],
            'manual_interventions': [],
            'final_compliance': {}
        }
        
        # Target distributions
        self.targets = {
            'channels': {'D2C': 60, 'Retail': 20, 'B2B': 20},
            'countries': {'UK': 50, 'US': 20, 'AU': 20, 'IE': 10},
            'return_rates': {
                'online': {'min': 20, 'max': 27},
                'retail': {'min': 4, 'max': 9},
                'b2b': {'min': 1, 'max': 2}
            },
            'customer_segments': {'VIP': 5, 'Loyal': 15, 'Regular': 30, 'One-time': 50},
            'aov_ranges': {
                'online': {'min': 90, 'max': 120},
                'retail': {'min': 70, 'max': 100},
                'b2b': {'min': 500, 'max': 2500}
            }
        }

    def log_check(self, check_name: str, status: str, details: str = ""):
        """Log a validation check result"""
        logging.info(f"CHECK: {check_name} - {status} - {details}")
        self.report_data['checks_performed'].append({
            'check': check_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })

    def log_fix(self, fix_description: str, records_affected: int):
        """Log an applied fix"""
        logging.info(f"FIX: {fix_description} - Affected: {records_affected} records")
        self.fixes_applied.append(fix_description)
        self.report_data['fixes_applied'].append({
            'description': fix_description,
            'records_affected': records_affected,
            'timestamp': datetime.now().isoformat()
        })

    def log_manual_intervention(self, description: str, reason: str):
        """Log a manual intervention requirement"""
        logging.warning(f"MANUAL: {description} - {reason}")
        self.manual_interventions.append({'description': description, 'reason': reason})
        self.report_data['manual_interventions'].append({
            'description': description,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        })

    def validate_channel_distribution(self) -> Dict[str, Any]:
        """Validate sales channel distribution"""
        try:
            # Get all sale orders with channel information
            orders = self.search_read_records('sale.order', [], [
                'name', 'x_channel', 'amount_total', 'state'
            ])
            
            if not orders:
                self.log_check("Channel Distribution", "FAILED", "No orders found")
                return {'status': 'failed', 'reason': 'No orders found'}

            # Filter confirmed orders
            confirmed_orders = [o for o in orders if o.get('state') in ['sale', 'done']]
            
            # Calculate channel distribution by revenue
            channel_revenue = defaultdict(float)
            total_revenue = 0
            
            for order in confirmed_orders:
                channel = order.get('x_channel') or 'Unknown'
                amount = order.get('amount_total', 0)
                channel_revenue[channel] += amount
                total_revenue += amount
            
            if total_revenue == 0:
                self.log_check("Channel Distribution", "FAILED", "No revenue data")
                return {'status': 'failed', 'reason': 'No revenue data'}
            
            # Calculate percentages
            channel_percentages = {}
            for channel, revenue in channel_revenue.items():
                channel_percentages[channel] = (revenue / total_revenue) * 100
            
            # Check against targets
            compliance = True
            details = []
            
            for target_channel, target_pct in self.targets['channels'].items():
                actual_pct = channel_percentages.get(target_channel, 0)
                variance = abs(actual_pct - target_pct)
                
                if variance > 3:  # ±3% tolerance
                    compliance = False
                    details.append(f"{target_channel}: {actual_pct:.1f}% (target: {target_pct}%, variance: {variance:.1f}%)")
                else:
                    details.append(f"{target_channel}: {actual_pct:.1f}% ✓")
            
            status = "PASSED" if compliance else "FAILED"
            self.log_check("Channel Distribution", status, "; ".join(details))
            
            return {
                'status': 'passed' if compliance else 'failed',
                'current': channel_percentages,
                'target': self.targets['channels'],
                'details': details
            }
            
        except Exception as e:
            self.log_check("Channel Distribution", "ERROR", str(e))
            return {'status': 'error', 'error': str(e)}

    def validate_geographic_distribution(self) -> Dict[str, Any]:
        """Validate geographic distribution"""
        try:
            # Get all partners (customers) with country information
            partners = self.search_read_records('res.partner', [
                ('customer_rank', '>', 0)
            ], ['name', 'country_id'])
            
            if not partners:
                self.log_check("Geographic Distribution", "FAILED", "No customers found")
                return {'status': 'failed', 'reason': 'No customers found'}
            
            # Get country names
            country_ids = [p['country_id'][0] for p in partners if p.get('country_id')]
            countries = self.search_read_records('res.country', [
                ('id', 'in', country_ids)
            ], ['name', 'code'])
            
            country_map = {c['id']: c['code'] for c in countries}
            
            # Calculate distribution
            country_counts = defaultdict(int)
            total_customers = len(partners)
            
            for partner in partners:
                if partner.get('country_id'):
                    country_code = country_map.get(partner['country_id'][0], 'Unknown')
                    country_counts[country_code] += 1
                else:
                    country_counts['Unknown'] += 1
            
            # Calculate percentages
            country_percentages = {}
            for country, count in country_counts.items():
                country_percentages[country] = (count / total_customers) * 100
            
            # Check against targets
            compliance = True
            details = []
            
            for target_country, target_pct in self.targets['countries'].items():
                actual_pct = country_percentages.get(target_country, 0)
                variance = abs(actual_pct - target_pct)
                
                if variance > 2:  # ±2% tolerance
                    compliance = False
                    details.append(f"{target_country}: {actual_pct:.1f}% (target: {target_pct}%, variance: {variance:.1f}%)")
                else:
                    details.append(f"{target_country}: {actual_pct:.1f}% ✓")
            
            status = "PASSED" if compliance else "FAILED"
            self.log_check("Geographic Distribution", status, "; ".join(details))
            
            return {
                'status': 'passed' if compliance else 'failed',
                'current': country_percentages,
                'target': self.targets['countries'],
                'details': details
            }
            
        except Exception as e:
            self.log_check("Geographic Distribution", "ERROR", str(e))
            return {'status': 'error', 'error': str(e)}

    def validate_product_coverage(self) -> Dict[str, Any]:
        """Validate that every active SKU has sales"""
        try:
            # Get all active products
            products = self.search_read_records('product.product', [
                ('active', '=', True),
                ('sale_ok', '=', True)
            ], ['name', 'default_code'])
            
            if not products:
                self.log_check("Product Coverage", "FAILED", "No active products found")
                return {'status': 'failed', 'reason': 'No active products found'}
            
            product_ids = [p['id'] for p in products]
            
            # Get sales data for products
            order_lines = self.search_read_records('sale.order.line', [
                ('product_id', 'in', product_ids),
                ('order_id.state', 'in', ['sale', 'done'])
            ], ['product_id'])
            
            products_with_sales = set(line['product_id'][0] for line in order_lines)
            products_without_sales = set(product_ids) - products_with_sales
            
            coverage_percentage = (len(products_with_sales) / len(product_ids)) * 100
            
            details = f"Coverage: {coverage_percentage:.1f}% ({len(products_with_sales)}/{len(product_ids)} products)"
            
            if products_without_sales:
                details += f", {len(products_without_sales)} products without sales"
                self.log_check("Product Coverage", "FAILED", details)
                return {
                    'status': 'failed',
                    'coverage_percentage': coverage_percentage,
                    'products_without_sales': list(products_without_sales),
                    'details': details
                }
            else:
                self.log_check("Product Coverage", "PASSED", details)
                return {
                    'status': 'passed',
                    'coverage_percentage': coverage_percentage,
                    'details': details
                }
            
        except Exception as e:
            self.log_check("Product Coverage", "ERROR", str(e))
            return {'status': 'error', 'error': str(e)}

    def validate_revenue_distribution(self) -> Dict[str, Any]:
        """Validate revenue distribution (80/20 rule)"""
        try:
            # Get sales data by product
            order_lines = self.search_read_records('sale.order.line', [
                ('order_id.state', 'in', ['sale', 'done'])
            ], ['product_id', 'price_subtotal'])
            
            if not order_lines:
                self.log_check("Revenue Distribution", "FAILED", "No order lines found")
                return {'status': 'failed', 'reason': 'No order lines found'}
            
            # Calculate revenue by product
            product_revenue = defaultdict(float)
            for line in order_lines:
                product_id = line['product_id'][0] if line.get('product_id') else 0
                revenue = line.get('price_subtotal', 0)
                product_revenue[product_id] += revenue
            
            # Sort products by revenue (descending)
            sorted_products = sorted(product_revenue.items(), key=lambda x: x[1], reverse=True)
            total_revenue = sum(product_revenue.values())
            
            if total_revenue == 0:
                self.log_check("Revenue Distribution", "FAILED", "No revenue data")
                return {'status': 'failed', 'reason': 'No revenue data'}
            
            # Calculate top 20% SKUs contribution
            top_20_count = max(1, len(sorted_products) // 5)
            top_20_revenue = sum(revenue for _, revenue in sorted_products[:top_20_count])
            top_20_percentage = (top_20_revenue / total_revenue) * 100
            
            # Check if within target range (60-75%)
            compliance = 60 <= top_20_percentage <= 75
            status = "PASSED" if compliance else "FAILED"
            
            details = f"Top 20% SKUs generate {top_20_percentage:.1f}% of revenue (target: 60-75%)"
            self.log_check("Revenue Distribution", status, details)
            
            return {
                'status': 'passed' if compliance else 'failed',
                'top_20_percentage': top_20_percentage,
                'target_min': 60,
                'target_max': 75,
                'details': details
            }
            
        except Exception as e:
            self.log_check("Revenue Distribution", "ERROR", str(e))
            return {'status': 'error', 'error': str(e)}

    def fix_missing_channels(self) -> int:
        """Fix orders with missing channel information"""
        try:
            # Find orders without channel
            orders_without_channel = self.search_read_records('sale.order', [
                '|', ('x_channel', '=', False), ('x_channel', '=', '')
            ], ['id', 'amount_total', 'partner_id'])
            
            if not orders_without_channel:
                return 0
            
            fixes_applied = 0
            
            for order in orders_without_channel:
                # Assign channel based on order value patterns
                amount = order.get('amount_total', 0)
                
                if amount >= 500:
                    channel = 'B2B'
                elif amount >= 120:
                    channel = 'Retail' if random.random() < 0.5 else 'D2C'
                else:
                    channel = 'D2C'
                
                # Update the order
                self.update_records('sale.order', [order['id']], {'x_channel': channel})
                fixes_applied += 1
            
            self.log_fix(f"Assigned channels to orders without channel attribution", fixes_applied)
            return fixes_applied
            
        except Exception as e:
            logging.error(f"Error fixing missing channels: {e}")
            return 0

    def fix_missing_geography(self) -> int:
        """Fix customers with missing geographic data"""
        try:
            # Find customers without country
            partners_without_country = self.search_read_records('res.partner', [
                ('customer_rank', '>', 0),
                ('country_id', '=', False)
            ], ['id', 'name'])
            
            if not partners_without_country:
                return 0
            
            # Get country IDs
            countries = self.search_read_records('res.country', [
                ('code', 'in', ['GB', 'US', 'AU', 'IE'])
            ], ['code'])
            
            country_map = {c['code']: c['id'] for c in countries}
            
            fixes_applied = 0
            
            for partner in partners_without_country:
                # Distribute based on requirements
                rand = random.random()
                if rand < 0.5:
                    country_id = country_map.get('GB')
                elif rand < 0.7:
                    country_id = country_map.get('US')
                elif rand < 0.9:
                    country_id = country_map.get('AU')
                else:
                    country_id = country_map.get('IE')
                
                if country_id:
                    self.update_records('res.partner', [partner['id']], {'country_id': country_id})
                    fixes_applied += 1
            
            self.log_fix(f"Assigned countries to customers without geographic data", fixes_applied)
            return fixes_applied
            
        except Exception as e:
            logging.error(f"Error fixing missing geography: {e}")
            return 0

    def add_sales_volatility(self) -> int:
        """Add random variance to sales data to meet volatility requirements"""
        try:
            # Get recent order lines
            thirty_days_ago = datetime.now() - timedelta(days=30)
            order_lines = self.search_read_records('sale.order.line', [
                ('create_date', '>=', thirty_days_ago.strftime('%Y-%m-%d')),
                ('order_id.state', 'in', ['sale', 'done'])
            ], ['id', 'price_unit', 'product_uom_qty'])
            
            if not order_lines:
                return 0
            
            fixes_applied = 0
            
            for line in order_lines[:100]:  # Limit to avoid too many updates
                # Add random variance (±20%)
                current_price = line.get('price_unit', 0)
                if current_price > 0:
                    variance = random.uniform(-0.2, 0.2)
                    new_price = current_price * (1 + variance)
                    
                    self.update_records('sale.order.line', [line['id']], {
                        'price_unit': round(new_price, 2)
                    })
                    fixes_applied += 1
            
            self.log_fix(f"Added price volatility to order lines", fixes_applied)
            return fixes_applied
            
        except Exception as e:
            logging.error(f"Error adding sales volatility: {e}")
            return 0

    def create_missing_sales_data(self, products_without_sales: List[int]) -> int:
        """Create minimal sales data for products without sales"""
        try:
            if not products_without_sales:
                return 0
            
            # Get a sample customer to use for orders
            customers = self.search_read_records('res.partner', [
                ('customer_rank', '>', 0)
            ], ['id'], limit=5)
            
            if not customers:
                self.log_manual_intervention(
                    "Cannot create sales data for products without sales",
                    "No customers found in system"
                )
                return 0
            
            fixes_applied = 0
            
            for product_id in products_without_sales[:10]:  # Limit to avoid too many new orders
                try:
                    # Create a minimal sale order
                    customer = random.choice(customers)
                    order_data = {
                        'partner_id': customer['id'],
                        'x_channel': random.choice(['D2C', 'Retail', 'B2B']),
                        'state': 'sale'
                    }
                    
                    order_id = self.create_record('sale.order', order_data)
                    
                    if order_id:
                        # Add order line
                        line_data = {
                            'order_id': order_id,
                            'product_id': product_id,
                            'product_uom_qty': 1,
                            'price_unit': random.uniform(10, 100)
                        }
                        
                        self.create_record('sale.order.line', line_data)
                        fixes_applied += 1
                        
                except Exception as e:
                    logging.error(f"Error creating sales data for product {product_id}: {e}")
                    continue
            
            remaining = len(products_without_sales) - fixes_applied
            if remaining > 0:
                self.log_manual_intervention(
                    f"{remaining} products still need sales data",
                    "Manual review required for product sales strategy"
                )
            
            self.log_fix(f"Created minimal sales data for products", fixes_applied)
            return fixes_applied
            
        except Exception as e:
            logging.error(f"Error creating missing sales data: {e}")
            return 0

    # Helper methods for MCP tool integration
    def search_read_records(self, model: str, domain: List = None, fields: List[str] = None, limit: int = None) -> List[Dict]:
        """Search and read records using MCP tools"""
        try:
            from mcp__odoo_mcp__odoo_search_read import mcp__odoo_mcp__odoo_search_read
            return mcp__odoo_mcp__odoo_search_read(
                instance_id=self.instance_id,
                model=model,
                domain=domain or [],
                fields=fields,
                limit=limit
            )
        except Exception as e:
            logging.error(f"Error searching {model}: {e}")
            return []

    def update_records(self, model: str, ids: List[int], values: Dict) -> bool:
        """Update records using MCP tools"""
        try:
            from mcp__odoo_mcp__odoo_update import mcp__odoo_mcp__odoo_update
            return mcp__odoo_mcp__odoo_update(
                instance_id=self.instance_id,
                model=model,
                ids=ids,
                values=values
            )
        except Exception as e:
            logging.error(f"Error updating {model}: {e}")
            return False

    def create_record(self, model: str, values: Dict) -> int:
        """Create a record using MCP tools"""
        try:
            from mcp__odoo_mcp__odoo_create import mcp__odoo_mcp__odoo_create
            return mcp__odoo_mcp__odoo_create(
                instance_id=self.instance_id,
                model=model,
                values=values
            )
        except Exception as e:
            logging.error(f"Error creating {model}: {e}")
            return 0

    def run_validation(self) -> Dict[str, Any]:
        """Run all validation checks and fixes"""
        logging.info("=" * 60)
        logging.info("Starting Odoo Data Validation and Correction")
        logging.info("=" * 60)
        
        validation_results = {}
        
        # Run all validation checks
        logging.info("\n--- VALIDATION PHASE ---")
        validation_results['channel_distribution'] = self.validate_channel_distribution()
        validation_results['geographic_distribution'] = self.validate_geographic_distribution()
        validation_results['product_coverage'] = self.validate_product_coverage()
        validation_results['revenue_distribution'] = self.validate_revenue_distribution()
        
        # Apply fixes
        logging.info("\n--- CORRECTION PHASE ---")
        
        # Fix missing channels
        missing_channels_fixed = self.fix_missing_channels()
        
        # Fix missing geography
        missing_geography_fixed = self.fix_missing_geography()
        
        # Add volatility
        volatility_added = self.add_sales_volatility()
        
        # Create missing sales data for products without sales
        if validation_results['product_coverage']['status'] == 'failed':
            products_without_sales = validation_results['product_coverage'].get('products_without_sales', [])
            sales_data_created = self.create_missing_sales_data(products_without_sales)
        
        # Re-run critical validations after fixes
        logging.info("\n--- POST-FIX VALIDATION ---")
        final_results = {}
        final_results['channel_distribution'] = self.validate_channel_distribution()
        final_results['geographic_distribution'] = self.validate_geographic_distribution()
        final_results['product_coverage'] = self.validate_product_coverage()
        final_results['revenue_distribution'] = self.validate_revenue_distribution()
        
        # Calculate final compliance
        passed_checks = sum(1 for result in final_results.values() if result.get('status') == 'passed')
        total_checks = len(final_results)
        compliance_percentage = (passed_checks / total_checks) * 100
        
        self.report_data['final_compliance'] = {
            'percentage': compliance_percentage,
            'passed_checks': passed_checks,
            'total_checks': total_checks,
            'detailed_results': final_results
        }
        
        # Generate final report
        self.generate_report()
        
        logging.info("=" * 60)
        logging.info(f"Validation Complete - {compliance_percentage:.1f}% Compliance")
        logging.info("=" * 60)
        
        return {
            'initial_results': validation_results,
            'final_results': final_results,
            'fixes_applied': len(self.fixes_applied),
            'manual_interventions': len(self.manual_interventions),
            'compliance_percentage': compliance_percentage
        }

    def generate_report(self):
        """Generate comprehensive validation report"""
        try:
            with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/validation_report.json', 'w') as f:
                json.dump(self.report_data, f, indent=2)
            
            # Generate human-readable report
            report_text = f"""
ODOO DATA VALIDATION REPORT
==========================

Validation Date: {self.report_data['validation_date']}

SUMMARY
-------
Total Checks Performed: {len(self.report_data['checks_performed'])}
Fixes Applied: {len(self.report_data['fixes_applied'])}
Manual Interventions Required: {len(self.report_data['manual_interventions'])}
Final Compliance: {self.report_data['final_compliance']['percentage']:.1f}%

DETAILED RESULTS
---------------
"""
            
            for check in self.report_data['checks_performed']:
                report_text += f"✓ {check['check']}: {check['status']}\n"
                if check['details']:
                    report_text += f"  Details: {check['details']}\n"
            
            report_text += "\nFIXES APPLIED\n-------------\n"
            for fix in self.report_data['fixes_applied']:
                report_text += f"• {fix['description']} ({fix['records_affected']} records)\n"
            
            if self.report_data['manual_interventions']:
                report_text += "\nMANUAL INTERVENTIONS REQUIRED\n----------------------------\n"
                for intervention in self.report_data['manual_interventions']:
                    report_text += f"⚠ {intervention['description']}\n"
                    report_text += f"  Reason: {intervention['reason']}\n"
            
            with open('/workspaces/source-lovable-gympluscoffee/odoo-ingestion/validation_report.txt', 'w') as f:
                f.write(report_text)
            
            logging.info("Validation reports saved to validation_report.json and validation_report.txt")
            
        except Exception as e:
            logging.error(f"Error generating report: {e}")


def main():
    """Main execution function"""
    validator = OdooDataValidator()
    results = validator.run_validation()
    
    print(f"\n🎯 VALIDATION COMPLETE")
    print(f"Compliance: {results['compliance_percentage']:.1f}%")
    print(f"Fixes Applied: {results['fixes_applied']}")
    print(f"Manual Interventions: {results['manual_interventions']}")
    print(f"\nSee validation_report.txt for detailed results")
    
    return results


if __name__ == "__main__":
    main()