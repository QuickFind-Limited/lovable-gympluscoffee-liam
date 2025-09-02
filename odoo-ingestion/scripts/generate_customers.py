#!/usr/bin/env python3
"""
Customer Generation Script Using DataCo Patterns

This script generates realistic customer data based on patterns from the DataCo Supply Chain dataset.
It creates Odoo-compatible customer records (res.partner) with proper segmentation, geography, 
and demographic patterns.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, List, Any, Optional
import json
import random
from faker import Faker

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CustomerGenerator:
    """Generates realistic customer data based on DataCo patterns"""
    
    def __init__(self, dataco_file: str, output_dir: str = "data/transformed", num_customers: int = 1000):
        self.dataco_file = Path(dataco_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.num_customers = num_customers
        
        # Initialize Faker for different locales based on DataCo patterns
        self.faker_locales = {
            'US': Faker('en_US'),
            'CA': Faker('en_CA'), 
            'GB': Faker('en_GB'),
            'AU': Faker('en_AU'),
            'DE': Faker('de_DE'),
            'FR': Faker('fr_FR'),
            'ES': Faker('es_ES'),
            'IT': Faker('it_IT'),
            'NL': Faker('nl_NL'),
            'default': Faker()
        }
        
        # Customer segments from DataCo
        self.customer_segments = ['Consumer', 'Corporate', 'Home Office']
        
        # Load DataCo patterns
        self.dataco_patterns = None
        self.geographic_patterns = None
        self.customer_behavior_patterns = None
    
    def load_dataco_patterns(self) -> None:
        """Load and analyze DataCo data for pattern extraction"""
        logger.info(f"Loading DataCo patterns from {self.dataco_file}")
        
        try:
            # Read DataCo data
            df = pd.read_csv(self.dataco_file, encoding='latin-1')
            self.dataco_patterns = df
            
            # Analyze geographic patterns
            self.geographic_patterns = self._analyze_geographic_patterns(df)
            
            # Analyze customer behavior patterns
            self.customer_behavior_patterns = self._analyze_customer_behavior(df)
            
            logger.info(f"Loaded {len(df)} DataCo records for pattern analysis")
            
        except Exception as e:
            logger.error(f"Error loading DataCo patterns: {e}")
            # Create fallback patterns
            self._create_fallback_patterns()
    
    def _analyze_geographic_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze geographic distribution patterns from DataCo"""
        patterns = {}
        
        try:
            # Country distribution
            country_dist = df['Customer Country'].value_counts(normalize=True).to_dict()
            patterns['country_distribution'] = country_dist
            
            # State/City patterns by country
            patterns['location_by_country'] = {}
            
            for country in df['Customer Country'].unique():
                if pd.notna(country):
                    country_data = df[df['Customer Country'] == country]
                    
                    states = country_data['Customer State'].value_counts(normalize=True).head(10).to_dict()
                    cities = country_data['Customer City'].value_counts(normalize=True).head(20).to_dict()
                    
                    patterns['location_by_country'][country] = {
                        'states': states,
                        'cities': cities
                    }
            
            # Market distribution
            if 'Market' in df.columns:
                patterns['market_distribution'] = df['Market'].value_counts(normalize=True).to_dict()
            
            logger.info("Geographic patterns analyzed successfully")
            
        except Exception as e:
            logger.warning(f"Error analyzing geographic patterns: {e}")
            patterns = self._get_default_geographic_patterns()
        
        return patterns
    
    def _analyze_customer_behavior(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze customer behavior patterns from DataCo"""
        patterns = {}
        
        try:
            # Customer segment distribution
            segment_dist = df['Customer Segment'].value_counts(normalize=True).to_dict()
            patterns['segment_distribution'] = segment_dist
            
            # Sales patterns by segment
            patterns['sales_by_segment'] = {}
            for segment in df['Customer Segment'].unique():
                if pd.notna(segment):
                    segment_data = df[df['Customer Segment'] == segment]
                    patterns['sales_by_segment'][segment] = {
                        'avg_sales': segment_data['Sales per customer'].mean(),
                        'median_sales': segment_data['Sales per customer'].median(),
                        'std_sales': segment_data['Sales per customer'].std()
                    }
            
            # Order patterns
            if 'Order Item Quantity' in df.columns:
                patterns['quantity_patterns'] = {
                    'mean': df['Order Item Quantity'].mean(),
                    'std': df['Order Item Quantity'].std(),
                    'distribution': df['Order Item Quantity'].value_counts(normalize=True).head(10).to_dict()
                }
            
            # Delivery preferences
            if 'Shipping Mode' in df.columns:
                patterns['shipping_preferences'] = df['Shipping Mode'].value_counts(normalize=True).to_dict()
            
            logger.info("Customer behavior patterns analyzed successfully")
            
        except Exception as e:
            logger.warning(f"Error analyzing customer behavior: {e}")
            patterns = self._get_default_behavior_patterns()
        
        return patterns
    
    def _create_fallback_patterns(self) -> None:
        """Create fallback patterns when DataCo data is not available"""
        logger.info("Creating fallback patterns")
        
        self.geographic_patterns = self._get_default_geographic_patterns()
        self.customer_behavior_patterns = self._get_default_behavior_patterns()
    
    def _get_default_geographic_patterns(self) -> Dict[str, Any]:
        """Default geographic patterns"""
        return {
            'country_distribution': {
                'EE. UU.': 0.40,  # US
                'Canada': 0.15,
                'United Kingdom': 0.12,
                'Australia': 0.10,
                'Germany': 0.08,
                'France': 0.05,
                'Other': 0.10
            },
            'market_distribution': {
                'USCA': 0.55,     # US & Canada
                'Europe': 0.30,
                'Pacific Asia': 0.15
            }
        }
    
    def _get_default_behavior_patterns(self) -> Dict[str, Any]:
        """Default customer behavior patterns"""
        return {
            'segment_distribution': {
                'Consumer': 0.60,
                'Corporate': 0.25,
                'Home Office': 0.15
            },
            'sales_by_segment': {
                'Consumer': {'avg_sales': 250, 'median_sales': 180, 'std_sales': 120},
                'Corporate': {'avg_sales': 850, 'median_sales': 650, 'std_sales': 450},
                'Home Office': {'avg_sales': 420, 'median_sales': 320, 'std_sales': 200}
            }
        }
    
    def generate_customers(self) -> pd.DataFrame:
        """Generate customer data based on DataCo patterns"""
        logger.info(f"Generating {self.num_customers} customers")
        
        customers = []
        
        # Distribution calculations
        country_weights = list(self.geographic_patterns.get('country_distribution', {}).values())
        countries = list(self.geographic_patterns.get('country_distribution', {}).keys())
        
        segment_weights = list(self.customer_behavior_patterns.get('segment_distribution', {}).values())
        segments = list(self.customer_behavior_patterns.get('segment_distribution', {}).keys())
        
        for i in range(self.num_customers):
            # Select country based on DataCo patterns
            country = np.random.choice(countries, p=country_weights) if countries and country_weights else 'EE. UU.'
            
            # Select customer segment
            segment = np.random.choice(segments, p=segment_weights) if segments and segment_weights else 'Consumer'
            
            # Select appropriate Faker locale
            locale_key = self._get_locale_for_country(country)
            faker = self.faker_locales.get(locale_key, self.faker_locales['default'])
            
            # Generate basic customer data
            customer = self._generate_customer_record(faker, country, segment, i + 1)
            
            # Add behavioral patterns
            customer.update(self._add_behavior_patterns(segment))
            
            customers.append(customer)
        
        df_customers = pd.DataFrame(customers)
        logger.info(f"Generated {len(df_customers)} customer records")
        
        return df_customers
    
    def _generate_customer_record(self, faker: Faker, country: str, segment: str, customer_id: int) -> Dict[str, Any]:
        """Generate individual customer record"""
        
        # Corporate vs individual logic
        is_company = segment == 'Corporate'
        
        if is_company:
            name = faker.company()
            contact_name = faker.name()
        else:
            name = faker.name()
            contact_name = name
        
        # Generate address data
        address_data = self._generate_address(faker, country)
        
        # Generate contact data
        email = self._generate_email(name if not is_company else contact_name, faker)
        phone = faker.phone_number()
        mobile = faker.phone_number() if random.random() < 0.7 else ''
        
        # Customer record
        customer = {
            'external_id': f'gym_coffee_customer_{customer_id:06d}',
            'name': name,
            'is_company': is_company,
            'customer_rank': self._get_customer_rank(segment),
            'supplier_rank': 0,  # Not suppliers
            'category_id': self._get_customer_category(segment),
            
            # Contact information
            'email': email,
            'phone': phone,
            'mobile': mobile,
            'website': faker.url() if is_company and random.random() < 0.3 else '',
            
            # Address information
            'street': address_data['street'],
            'street2': address_data.get('street2', ''),
            'city': address_data['city'],
            'state_id': address_data['state'],
            'zip': address_data['zip'],
            'country_id': self._normalize_country_code(country),
            
            # Business information
            'vat': self._generate_vat(country, is_company),
            'industry_id': self._get_industry(segment),
            'ref': f'CUST-{customer_id:06d}',
            
            # Odoo specific fields
            'customer': True,
            'supplier': False,
            'active': True,
            'lang': self._get_language_for_country(country),
            'tz': self._get_timezone_for_country(country),
            'company_id': 1,
            
            # Additional fields
            'title': faker.prefix() if not is_company else '',
            'function': faker.job() if not is_company else '',
            'comment': f'Generated customer - Segment: {segment}',
            
            # Dates
            'create_date': self._generate_creation_date(),
            'signup_type': 'manual',
            'signup_token': '',
        }
        
        return customer
    
    def _generate_address(self, faker: Faker, country: str) -> Dict[str, str]:
        """Generate realistic address based on country"""
        return {
            'street': faker.street_address(),
            'street2': faker.secondary_address() if random.random() < 0.3 else '',
            'city': faker.city(),
            'state': faker.state_abbr() if country in ['EE. UU.', 'Canada'] else faker.state(),
            'zip': faker.postcode()
        }
    
    def _generate_email(self, name: str, faker: Faker) -> str:
        """Generate realistic email based on name"""
        # Clean name for email
        clean_name = ''.join(c.lower() for c in name if c.isalnum() or c.isspace()).replace(' ', '.')
        
        domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'company.com']
        domain = random.choice(domains)
        
        # Add some variation
        if random.random() < 0.3:
            clean_name += str(random.randint(1, 999))
        
        return f"{clean_name}@{domain}"
    
    def _add_behavior_patterns(self, segment: str) -> Dict[str, Any]:
        """Add behavioral patterns based on segment"""
        behavior_data = self.customer_behavior_patterns.get('sales_by_segment', {}).get(segment, {})
        
        # Generate expected purchase behavior
        avg_sales = behavior_data.get('avg_sales', 250)
        std_sales = behavior_data.get('std_sales', 100)
        
        # Generate expected annual spend (with some randomness)
        expected_annual_spend = max(50, np.random.normal(avg_sales, std_sales))
        
        return {
            'expected_annual_spend': round(expected_annual_spend, 2),
            'preferred_shipping': self._get_preferred_shipping(segment),
            'credit_limit': self._calculate_credit_limit(segment, expected_annual_spend),
            'payment_terms': self._get_payment_terms(segment),
            'discount_eligibility': self._get_discount_eligibility(segment)
        }
    
    def _get_customer_rank(self, segment: str) -> int:
        """Get customer rank based on segment"""
        rank_map = {
            'Consumer': 1,
            'Home Office': 2,
            'Corporate': 3
        }
        return rank_map.get(segment, 1)
    
    def _get_customer_category(self, segment: str) -> str:
        """Get customer category external ID"""
        category_map = {
            'Consumer': 'gym_coffee_cat_consumer',
            'Home Office': 'gym_coffee_cat_home_office', 
            'Corporate': 'gym_coffee_cat_corporate'
        }
        return category_map.get(segment, 'gym_coffee_cat_consumer')
    
    def _normalize_country_code(self, country: str) -> str:
        """Convert country name to ISO code"""
        country_map = {
            'EE. UU.': 'US',
            'United States': 'US',
            'Canada': 'CA',
            'United Kingdom': 'GB',
            'Australia': 'AU',
            'Germany': 'DE',
            'France': 'FR',
            'Spain': 'ES',
            'Italy': 'IT',
            'Netherlands': 'NL',
            'Puerto Rico': 'PR'
        }
        return country_map.get(country, 'US')
    
    def _get_locale_for_country(self, country: str) -> str:
        """Get Faker locale for country"""
        locale_map = {
            'EE. UU.': 'US',
            'United States': 'US',
            'Canada': 'CA',
            'United Kingdom': 'GB',
            'Australia': 'AU',
            'Germany': 'DE',
            'France': 'FR',
            'Spain': 'ES',
            'Italy': 'IT',
            'Netherlands': 'NL'
        }
        return locale_map.get(country, 'default')
    
    def _get_language_for_country(self, country: str) -> str:
        """Get language code for country"""
        lang_map = {
            'EE. UU.': 'en_US',
            'Canada': 'en_US',
            'United Kingdom': 'en_US',
            'Australia': 'en_US', 
            'Germany': 'de_DE',
            'France': 'fr_FR',
            'Spain': 'es_ES',
            'Italy': 'it_IT',
            'Netherlands': 'nl_NL'
        }
        return lang_map.get(country, 'en_US')
    
    def _get_timezone_for_country(self, country: str) -> str:
        """Get timezone for country"""
        tz_map = {
            'EE. UU.': 'America/New_York',
            'Canada': 'America/Toronto',
            'United Kingdom': 'Europe/London',
            'Australia': 'Australia/Sydney',
            'Germany': 'Europe/Berlin',
            'France': 'Europe/Paris',
            'Spain': 'Europe/Madrid',
            'Italy': 'Europe/Rome',
            'Netherlands': 'Europe/Amsterdam'
        }
        return tz_map.get(country, 'UTC')
    
    def _generate_vat(self, country: str, is_company: bool) -> str:
        """Generate VAT number for companies"""
        if not is_company or random.random() < 0.3:  # Not all companies have VAT
            return ''
        
        country_code = self._normalize_country_code(country)
        
        if country_code == 'US':
            return f"{random.randint(10, 99)}-{random.randint(1000000, 9999999)}"
        elif country_code in ['DE', 'FR', 'ES', 'IT', 'NL', 'GB']:
            return f"{country_code}{random.randint(100000000, 999999999)}"
        else:
            return f"{country_code}{random.randint(1000000, 9999999)}"
    
    def _get_industry(self, segment: str) -> str:
        """Get industry based on segment"""
        if segment == 'Corporate':
            industries = ['retail', 'fitness', 'healthcare', 'education', 'technology']
            return f"gym_coffee_industry_{random.choice(industries)}"
        return ''
    
    def _get_preferred_shipping(self, segment: str) -> str:
        """Get preferred shipping method"""
        shipping_prefs = {
            'Consumer': ['Standard Class', 'First Class'],
            'Home Office': ['Standard Class', 'Second Class'],
            'Corporate': ['Standard Class', 'First Class', 'Same Day']
        }
        return random.choice(shipping_prefs.get(segment, ['Standard Class']))
    
    def _calculate_credit_limit(self, segment: str, expected_spend: float) -> float:
        """Calculate credit limit based on segment and expected spend"""
        multipliers = {
            'Consumer': 2.0,
            'Home Office': 3.0,
            'Corporate': 5.0
        }
        
        base_limit = expected_spend * multipliers.get(segment, 2.0)
        return round(max(500, base_limit), 2)
    
    def _get_payment_terms(self, segment: str) -> str:
        """Get payment terms based on segment"""
        terms_map = {
            'Consumer': 'immediate_payment',
            'Home Office': 'net_15',
            'Corporate': 'net_30'
        }
        return terms_map.get(segment, 'immediate_payment')
    
    def _get_discount_eligibility(self, segment: str) -> bool:
        """Get discount eligibility"""
        eligibility_rates = {
            'Consumer': 0.3,
            'Home Office': 0.6,
            'Corporate': 0.9
        }
        return random.random() < eligibility_rates.get(segment, 0.3)
    
    def _generate_creation_date(self) -> str:
        """Generate realistic creation date"""
        # Customers created in last 2 years with higher probability for recent dates
        days_ago = int(np.random.exponential(180))  # Exponential distribution favors recent
        days_ago = min(days_ago, 730)  # Cap at 2 years
        
        creation_date = datetime.now() - timedelta(days=days_ago)
        return creation_date.isoformat()
    
    def create_customer_categories(self) -> pd.DataFrame:
        """Create customer categories for Odoo"""
        categories = [
            {
                'external_id': 'gym_coffee_cat_consumer',
                'name': 'Consumer',
                'color': 2,  # Green
                'active': True
            },
            {
                'external_id': 'gym_coffee_cat_home_office',
                'name': 'Home Office',
                'color': 3,  # Blue
                'active': True
            },
            {
                'external_id': 'gym_coffee_cat_corporate',
                'name': 'Corporate',
                'color': 5,  # Purple
                'active': True
            }
        ]
        
        return pd.DataFrame(categories)
    
    def export_to_csv(self, customers_df: pd.DataFrame, categories_df: pd.DataFrame) -> None:
        """Export customer data to CSV files"""
        
        # Export customers
        customers_file = self.output_dir / 'odoo_customers.csv'
        customers_df.to_csv(customers_file, index=False)
        logger.info(f"Exported {len(customers_df)} customers to {customers_file}")
        
        # Export categories
        categories_file = self.output_dir / 'odoo_customer_categories.csv'
        categories_df.to_csv(categories_file, index=False)
        logger.info(f"Exported {len(categories_df)} customer categories to {categories_file}")
    
    def run_generation(self) -> None:
        """Run the complete customer generation process"""
        logger.info("Starting customer generation based on DataCo patterns")
        
        # Load DataCo patterns
        self.load_dataco_patterns()
        
        # Generate customers
        customers_df = self.generate_customers()
        categories_df = self.create_customer_categories()
        
        # Export data
        self.export_to_csv(customers_df, categories_df)
        
        # Create summary
        summary = {
            'generation_date': datetime.now().isoformat(),
            'total_customers': len(customers_df),
            'customer_categories': len(categories_df),
            'segment_distribution': customers_df.groupby('category_id').size().to_dict(),
            'country_distribution': customers_df.groupby('country_id').size().to_dict(),
            'patterns_source': str(self.dataco_file) if self.dataco_patterns is not None else 'fallback'
        }
        
        summary_file = self.output_dir / 'customer_generation_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info("Customer generation completed successfully")
        logger.info(f"Summary: {summary}")


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate customers based on DataCo patterns')
    parser.add_argument('--dataco', default='../data/dataco/DataCoSupplyChainDataset.csv',
                       help='DataCo dataset file path')
    parser.add_argument('--output', default='../data/transformed',
                       help='Output directory for generated files')
    parser.add_argument('--count', type=int, default=1000,
                       help='Number of customers to generate')
    
    args = parser.parse_args()
    
    # Create generator and run
    generator = CustomerGenerator(args.dataco, args.output, args.count)
    generator.run_generation()


if __name__ == "__main__":
    main()