#!/usr/bin/env python3
"""
Geographic Distribution Fixer for Odoo Customers
===============================================

This script fixes the geographic distribution of customers to meet requirements:
- UK: 50% (cities: London, Manchester, Birmingham, Liverpool, Bristol)
- US: 20% (cities: New York, Los Angeles, Chicago, Houston, Phoenix)
- AU: 20% (cities: Sydney, Melbourne, Brisbane, Perth, Adelaide)
- IE: 10% (cities: Dublin, Cork, Limerick, Galway, Waterford)
"""

import xmlrpc.client
import ssl
import random
from collections import defaultdict, Counter
import math

# Odoo Connection Configuration
ODOO_URL = 'https://source-gym-plus-coffee.odoo.com/'
ODOO_DB = 'source-gym-plus-coffee'
ODOO_USERNAME = 'admin@quickfindai.com'
ODOO_PASSWORD = 'BJ62wX2J4yzjS$i'

# Target Distribution Requirements
TARGET_DISTRIBUTION = {
    'UK': {
        'percentage': 0.50,
        'code': 'GB',
        'cities': ['London', 'Manchester', 'Birmingham', 'Liverpool', 'Bristol']
    },
    'US': {
        'percentage': 0.20,
        'code': 'US', 
        'cities': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix']
    },
    'AU': {
        'percentage': 0.20,
        'code': 'AU',
        'cities': ['Sydney', 'Melbourne', 'Brisbane', 'Perth', 'Adelaide']
    },
    'IE': {
        'percentage': 0.10,
        'code': 'IE',
        'cities': ['Dublin', 'Cork', 'Limerick', 'Galway', 'Waterford']
    }
}

class OdooConnection:
    def __init__(self):
        self.url = ODOO_URL
        self.db = ODOO_DB
        self.username = ODOO_USERNAME
        self.password = ODOO_PASSWORD
        self.uid = None
        self.models = None
        
        # Create SSL context that doesn't verify certificates (for development)
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
    def connect(self):
        """Establish connection to Odoo"""
        try:
            # Common endpoint for authentication
            common = xmlrpc.client.ServerProxy(
                f'{self.url}xmlrpc/2/common', 
                context=self.ssl_context
            )
            
            # Authenticate
            self.uid = common.authenticate(self.db, self.username, self.password, {})
            
            if not self.uid:
                raise Exception("Authentication failed")
                
            # Object endpoint for operations
            self.models = xmlrpc.client.ServerProxy(
                f'{self.url}xmlrpc/2/object',
                context=self.ssl_context
            )
            
            print(f"✅ Connected to Odoo as user ID: {self.uid}")
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {str(e)}")
            return False
    
    def search_read(self, model, domain, fields=None, limit=None):
        """Search and read records"""
        kwargs = {}
        if fields is not None:
            kwargs['fields'] = fields
        if limit is not None:
            kwargs['limit'] = limit
            
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model, 'search_read',
            [domain],
            kwargs
        )
    
    def search_count(self, model, domain):
        """Count records matching domain"""
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model, 'search_count',
            [domain]
        )
    
    def write(self, model, ids, values):
        """Update records"""
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model, 'write',
            [ids, values]
        )

class GeographicDistributionFixer:
    def __init__(self):
        self.odoo = OdooConnection()
        self.country_mapping = {}
        
    def connect(self):
        """Connect to Odoo"""
        return self.odoo.connect()
    
    def get_country_mapping(self):
        """Get country ID mapping for target countries"""
        try:
            countries = self.odoo.search_read(
                'res.country',
                [['code', 'in', ['GB', 'US', 'AU', 'IE']]],
                ['name', 'code']
            )
            
            for country in countries:
                self.country_mapping[country['code']] = country['id']
            
            print("🌍 Country mapping:")
            for code, country_id in self.country_mapping.items():
                print(f"   {code}: {country_id}")
                
            return True
            
        except Exception as e:
            print(f"❌ Failed to get country mapping: {str(e)}")
            return False
    
    def analyze_current_distribution(self):
        """Analyze current customer distribution"""
        try:
            # Get all customers
            customers = self.odoo.search_read(
                'res.partner',
                [['is_company', '=', False], ['customer_rank', '>', 0]],
                ['name', 'country_id', 'city']
            )
            
            total_customers = len(customers)
            print(f"📊 Total customers: {total_customers}")
            
            if total_customers == 0:
                print("⚠️ No customers found!")
                return None
            
            # Count by country
            country_counts = Counter()
            customers_without_country = []
            
            for customer in customers:
                if customer['country_id']:
                    country_counts[customer['country_id'][0]] += 1
                else:
                    customers_without_country.append(customer['id'])
            
            print(f"📍 Customers without country: {len(customers_without_country)}")
            
            # Show current distribution
            print("\n📊 Current Distribution:")
            for country_id, count in country_counts.most_common():
                percentage = (count / total_customers) * 100
                country_code = self.get_country_code_by_id(country_id)
                print(f"   {country_code or 'Unknown'} ({country_id}): {count} customers ({percentage:.1f}%)")
            
            return {
                'total_customers': total_customers,
                'customers': customers,
                'country_counts': country_counts,
                'customers_without_country': customers_without_country
            }
            
        except Exception as e:
            print(f"❌ Failed to analyze distribution: {str(e)}")
            return None
    
    def get_country_code_by_id(self, country_id):
        """Get country code by ID"""
        for code, cid in self.country_mapping.items():
            if cid == country_id:
                return code
        return None
    
    def calculate_target_counts(self, total_customers):
        """Calculate how many customers each country should have"""
        targets = {}
        
        for country, config in TARGET_DISTRIBUTION.items():
            target_count = math.floor(total_customers * config['percentage'])
            targets[country] = {
                'count': target_count,
                'country_id': self.country_mapping[config['code']],
                'cities': config['cities']
            }
        
        # Adjust for rounding differences
        total_assigned = sum(t['count'] for t in targets.values())
        if total_assigned < total_customers:
            # Add remaining customers to UK (largest group)
            remaining = total_customers - total_assigned
            targets['UK']['count'] += remaining
        
        print("\n🎯 Target Distribution:")
        for country, target in targets.items():
            percentage = (target['count'] / total_customers) * 100
            print(f"   {country}: {target['count']} customers ({percentage:.1f}%)")
        
        return targets
    
    def fix_distribution(self, analysis, targets):
        """Fix the geographic distribution"""
        try:
            customers = analysis['customers']
            current_counts = analysis['country_counts']
            
            # Create list of customers that need to be reassigned
            customers_to_update = []
            
            # First, collect customers that need country updates
            for customer in customers:
                current_country_id = customer['country_id'][0] if customer['country_id'] else None
                current_country_code = self.get_country_code_by_id(current_country_id) if current_country_id else None
                
                # Add customers without country or from non-target countries
                if not current_country_id or current_country_code not in [c['code'] for c in TARGET_DISTRIBUTION.values()]:
                    customers_to_update.append(customer)
            
            # Also collect customers from over-represented countries
            for country, config in TARGET_DISTRIBUTION.items():
                country_id = self.country_mapping[config['code']]
                current_count = current_counts.get(country_id, 0)
                target_count = targets[country]['count']
                
                if current_count > target_count:
                    # Need to move some customers from this country
                    excess = current_count - target_count
                    country_customers = [c for c in customers if c['country_id'] and c['country_id'][0] == country_id]
                    customers_to_move = random.sample(country_customers, min(excess, len(country_customers)))
                    customers_to_update.extend(customers_to_move)
            
            print(f"\n🔄 Customers to reassign: {len(customers_to_update)}")
            
            # Shuffle for random distribution
            random.shuffle(customers_to_update)
            
            # Assign customers to countries based on targets
            assignments = []
            customer_idx = 0
            
            for country, target in targets.items():
                country_id = target['country_id']
                current_count = current_counts.get(country_id, 0)
                needed = target['count'] - current_count
                
                if needed > 0 and customer_idx < len(customers_to_update):
                    print(f"   📍 Assigning {min(needed, len(customers_to_update) - customer_idx)} customers to {country}")
                    
                    for i in range(min(needed, len(customers_to_update) - customer_idx)):
                        customer = customers_to_update[customer_idx]
                        city = random.choice(target['cities'])
                        
                        assignments.append({
                            'customer_id': customer['id'],
                            'customer_name': customer['name'],
                            'country': country,
                            'country_id': country_id,
                            'city': city
                        })
                        customer_idx += 1
            
            # Execute updates in batches
            batch_size = 10
            updated_count = 0
            
            print(f"\n🔄 Updating {len(assignments)} customer records...")
            
            for i in range(0, len(assignments), batch_size):
                batch = assignments[i:i + batch_size]
                
                for assignment in batch:
                    try:
                        self.odoo.write(
                            'res.partner',
                            [assignment['customer_id']],
                            {
                                'country_id': assignment['country_id'],
                                'city': assignment['city']
                            }
                        )
                        updated_count += 1
                        
                        if updated_count % 5 == 0:
                            print(f"   ✅ Updated {updated_count}/{len(assignments)} customers...")
                            
                    except Exception as e:
                        print(f"   ❌ Failed to update {assignment['customer_name']}: {str(e)}")
            
            print(f"✅ Successfully updated {updated_count} customers")
            return True
            
        except Exception as e:
            print(f"❌ Failed to fix distribution: {str(e)}")
            return False
    
    def verify_distribution(self):
        """Verify the final distribution"""
        print("\n🔍 Verifying final distribution...")
        analysis = self.analyze_current_distribution()
        
        if analysis:
            total = analysis['total_customers']
            current_counts = analysis['country_counts']
            
            print("\n✅ Final Distribution:")
            for country, config in TARGET_DISTRIBUTION.items():
                country_id = self.country_mapping[config['code']]
                count = current_counts.get(country_id, 0)
                percentage = (count / total) * 100
                target_percentage = config['percentage'] * 100
                
                status = "✅" if abs(percentage - target_percentage) < 2 else "⚠️"
                print(f"   {status} {country}: {count} customers ({percentage:.1f}%) - Target: {target_percentage:.1f}%")
        
        return analysis
    
    def run(self):
        """Main execution function"""
        print("🚀 Starting Geographic Distribution Fixer")
        print("=" * 50)
        
        # Connect to Odoo
        if not self.connect():
            return False
        
        # Get country mapping
        if not self.get_country_mapping():
            return False
        
        # Analyze current distribution
        analysis = self.analyze_current_distribution()
        if not analysis:
            return False
        
        # Calculate target counts
        targets = self.calculate_target_counts(analysis['total_customers'])
        
        # Fix distribution
        if not self.fix_distribution(analysis, targets):
            return False
        
        # Verify results
        self.verify_distribution()
        
        print("\n🎉 Geographic distribution fix completed!")
        return True

def main():
    """Main function"""
    fixer = GeographicDistributionFixer()
    success = fixer.run()
    
    if success:
        print("\n✅ All geographic distribution fixes completed successfully!")
    else:
        print("\n❌ Some issues occurred during the process.")

if __name__ == "__main__":
    main()