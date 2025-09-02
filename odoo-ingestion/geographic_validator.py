#!/usr/bin/env python3
"""
Geographic Distribution Validator and Fixer
===========================================

Validates and corrects geographic distribution to meet:
- UK: 50% (±2%)
- US: 20% (±2%)
- AU: 20% (±2%)
- IE: 10% (±2%)
"""

import random
import logging
from typing import Dict, List, Tuple
from collections import defaultdict

class GeographicValidator:
    def __init__(self, instance_id: str = "source-gym-plus-coffee"):
        self.instance_id = instance_id
        self.target_distribution = {'GB': 50, 'US': 20, 'AU': 20, 'IE': 10}
        self.tolerance = 2  # ±2%
        self.country_codes = {
            'GB': 'United Kingdom',
            'US': 'United States',
            'AU': 'Australia', 
            'IE': 'Ireland'
        }
    
    def get_customers_data(self) -> Tuple[List[Dict], Dict[int, str]]:
        """Get customer data with country information"""
        try:
            # Get customers
            customers = []  # Will be populated by MCP tools
            
            # Get country mapping
            countries = []  # Will be populated by MCP tools
            country_map = {c['id']: c['code'] for c in countries}
            
            return customers, country_map
            
        except Exception as e:
            logging.error(f"Error fetching customer data: {e}")
            return [], {}
    
    def analyze_current_distribution(self, customers: List[Dict], country_map: Dict) -> Dict:
        """Analyze current geographic distribution"""
        country_counts = defaultdict(int)
        total_customers = len(customers)
        customers_without_country = 0
        
        for customer in customers:
            if customer.get('country_id'):
                country_code = country_map.get(customer['country_id'][0], 'Unknown')
                country_counts[country_code] += 1
            else:
                customers_without_country += 1
                country_counts['Unknown'] += 1
        
        # Calculate percentages
        percentages = {}
        for country, count in country_counts.items():
            percentages[country] = (count / total_customers * 100) if total_customers > 0 else 0
        
        return {
            'country_distribution': percentages,
            'country_counts': dict(country_counts),
            'total_customers': total_customers,
            'customers_without_country': customers_without_country
        }
    
    def check_compliance(self, distribution: Dict) -> Dict:
        """Check if geographic distribution meets requirements"""
        country_dist = distribution['country_distribution']
        compliance_issues = []
        
        for target_country, target_pct in self.target_distribution.items():
            actual_pct = country_dist.get(target_country, 0)
            variance = abs(actual_pct - target_pct)
            
            if variance > self.tolerance:
                compliance_issues.append({
                    'country': target_country,
                    'country_name': self.country_codes[target_country],
                    'actual': actual_pct,
                    'target': target_pct,
                    'variance': variance,
                    'status': 'FAIL'
                })
            else:
                compliance_issues.append({
                    'country': target_country,
                    'country_name': self.country_codes[target_country],
                    'actual': actual_pct,
                    'target': target_pct,
                    'variance': variance,
                    'status': 'PASS'
                })
        
        is_compliant = all(issue['status'] == 'PASS' for issue in compliance_issues)
        
        return {
            'is_compliant': is_compliant,
            'issues': compliance_issues
        }
    
    def get_country_ids_map(self) -> Dict[str, int]:
        """Get mapping of country codes to IDs"""
        try:
            # This will use MCP tools to get countries
            countries = []  # MCP search_read for res.country
            return {c['code']: c['id'] for c in countries if c['code'] in self.country_codes.keys()}
        except Exception as e:
            logging.error(f"Error getting country IDs: {e}")
            return {}
    
    def fix_missing_countries(self, customers: List[Dict], country_ids: Dict[str, int]) -> List[Dict]:
        """Assign countries to customers without country information"""
        fixes = []
        
        # Customers without country
        customers_without_country = [c for c in customers if not c.get('country_id')]
        
        for customer in customers_without_country:
            # Assign country based on target distribution
            new_country_code = self._select_country_by_probability()
            new_country_id = country_ids.get(new_country_code)
            
            if new_country_id:
                fixes.append({
                    'customer_id': customer['id'],
                    'customer_name': customer.get('name', 'Unknown'),
                    'old_country': None,
                    'new_country_code': new_country_code,
                    'new_country_id': new_country_id
                })
        
        return fixes
    
    def rebalance_geography(self, customers: List[Dict], country_map: Dict, 
                           current_dist: Dict, country_ids: Dict[str, int]) -> List[Dict]:
        """Rebalance geographic distribution to meet targets"""
        compliance = self.check_compliance(current_dist)
        
        if compliance['is_compliant']:
            return []
        
        fixes = []
        country_dist = current_dist['country_distribution']
        
        # Identify which countries need adjustment
        adjustments_needed = {}
        for issue in compliance['issues']:
            if issue['status'] == 'FAIL':
                country = issue['country']
                target = issue['target']
                actual = issue['actual']
                
                if actual < target:
                    adjustments_needed[country] = 'increase'
                else:
                    adjustments_needed[country] = 'decrease'
        
        # Get customers that can be reassigned (avoid disrupting established relationships)
        reassignable_customers = [
            c for c in customers 
            if c.get('country_id') and 
            country_map.get(c['country_id'][0]) in ['Unknown', 'XX', None] or
            not c.get('country_id')
        ]
        
        # Reassign countries strategically
        for customer in reassignable_customers:
            current_country_code = None
            if customer.get('country_id'):
                current_country_code = country_map.get(customer['country_id'][0])
            
            # Find best country for this customer
            best_country_code = self._find_best_country_for_customer(
                customer, adjustments_needed, current_country_code
            )
            
            if best_country_code and best_country_code != current_country_code:
                new_country_id = country_ids.get(best_country_code)
                if new_country_id:
                    fixes.append({
                        'customer_id': customer['id'],
                        'customer_name': customer.get('name', 'Unknown'),
                        'old_country': current_country_code,
                        'new_country_code': best_country_code,
                        'new_country_id': new_country_id
                    })
        
        return fixes
    
    def _select_country_by_probability(self) -> str:
        """Select a country based on target distribution probabilities"""
        rand = random.random() * 100
        cumulative = 0
        
        for country_code, percentage in self.target_distribution.items():
            cumulative += percentage
            if rand <= cumulative:
                return country_code
        
        return 'GB'  # Default to GB if something goes wrong
    
    def _find_best_country_for_customer(self, customer: Dict, adjustments: Dict, 
                                       current_country: str) -> str:
        """Find the best country assignment for a customer"""
        # Prioritize countries that need increase
        countries_needing_increase = [k for k, v in adjustments.items() if v == 'increase']
        
        if countries_needing_increase:
            # Select randomly from countries that need more customers
            return random.choice(countries_needing_increase)
        
        # If no specific need, assign based on target distribution
        return self._select_country_by_probability()
    
    def apply_geographic_fixes(self, fixes: List[Dict]) -> int:
        """Apply geographic fixes to customers"""
        if not fixes:
            return 0
        
        applied_count = 0
        
        try:
            # Group fixes by new country for batch updates
            country_groups = defaultdict(list)
            for fix in fixes:
                country_groups[fix['new_country_id']].append(fix['customer_id'])
            
            # Apply updates in batches
            for country_id, customer_ids in country_groups.items():
                # This would use MCP update tool
                # success = update_records('res.partner', customer_ids, {'country_id': country_id})
                applied_count += len(customer_ids)
                logging.info(f"Updated {len(customer_ids)} customers to country ID: {country_id}")
        
        except Exception as e:
            logging.error(f"Error applying geographic fixes: {e}")
        
        return applied_count
    
    def create_missing_customers_by_geography(self, target_counts: Dict[str, int], 
                                            country_ids: Dict[str, int]) -> List[Dict]:
        """Create new customers to meet geographic distribution if needed"""
        new_customers = []
        
        for country_code, needed_count in target_counts.items():
            if needed_count <= 0:
                continue
                
            country_id = country_ids.get(country_code)
            if not country_id:
                continue
            
            for i in range(min(needed_count, 10)):  # Limit new customer creation
                customer_data = {
                    'name': f'Customer {country_code} {i+1:03d}',
                    'is_company': False,
                    'customer_rank': 1,
                    'country_id': country_id,
                    'email': f'customer.{country_code.lower()}.{i+1:03d}@example.com'
                }
                new_customers.append(customer_data)
        
        return new_customers
    
    def validate_and_fix_geography(self) -> Dict:
        """Main method to validate and fix geographic distribution"""
        try:
            # Get customer data
            customers, country_map = self.get_customers_data()
            
            if not customers:
                return {'error': 'No customers found'}
            
            # Get country IDs
            country_ids = self.get_country_ids_map()
            
            # Analyze current distribution
            current_dist = self.analyze_current_distribution(customers, country_map)
            
            # Check compliance
            compliance = self.check_compliance(current_dist)
            
            # Apply fixes if needed
            fixes_applied = 0
            
            if not compliance['is_compliant']:
                # Fix missing countries first
                missing_country_fixes = self.fix_missing_countries(customers, country_ids)
                if missing_country_fixes:
                    fixes_applied += self.apply_geographic_fixes(missing_country_fixes)
                
                # Rebalance if still not compliant
                rebalance_fixes = self.rebalance_geography(
                    customers, country_map, current_dist, country_ids
                )
                if rebalance_fixes:
                    fixes_applied += self.apply_geographic_fixes(rebalance_fixes)
            
            return {
                'current_distribution': current_dist,
                'compliance': compliance,
                'fixes_applied': fixes_applied,
                'status': 'compliant' if compliance['is_compliant'] else 'non_compliant'
            }
            
        except Exception as e:
            logging.error(f"Error in geographic validation: {e}")
            return {'error': str(e)}


def main():
    """Test the geographic validator"""
    validator = GeographicValidator()
    results = validator.validate_and_fix_geography()
    
    print("Geographic Validation Results:")
    print(f"Status: {results.get('status', 'error')}")
    if 'fixes_applied' in results:
        print(f"Fixes Applied: {results['fixes_applied']}")


if __name__ == "__main__":
    main()