#!/usr/bin/env python3
"""
Customer Data Generator for Gym+Coffee
Generates 35,000 realistic customer records with proper segmentation and distribution
"""

import json
import random
from datetime import datetime, timedelta
from faker import Faker
from typing import List, Dict, Any

# Initialize Faker with multiple locales
fake_us = Faker('en_US')
fake_uk = Faker('en_GB')
fake_au = Faker('en_AU')
fake_ie = Faker('en_IE')

# Configuration constants
TOTAL_CUSTOMERS = 35000
B2B_COUNT = 150

# Customer segment distribution
SEGMENT_DISTRIBUTION = {
    'VIP': 0.05,        # 5%
    'Loyal': 0.15,      # 15% 
    'Regular': 0.30,    # 30%
    'One-Time': 0.50    # 50%
}

# Geographic distribution
GEO_DISTRIBUTION = {
    'UK': 0.50,    # 50%
    'US': 0.20,    # 20%
    'AU': 0.20,    # 20%
    'IE': 0.10     # 10%
}

# Product categories for Gym+Coffee
PRODUCT_CATEGORIES = [
    'Activewear', 'Casual Wear', 'Accessories', 'Footwear', 'Outerwear', 'Underwear'
]

# Clothing sizes
SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL']

# Purchase channels
CHANNELS = ['Online', 'Store', 'Mobile App']

# UK Cities
UK_CITIES = [
    'London', 'Manchester', 'Birmingham', 'Liverpool', 'Bristol', 'Sheffield',
    'Leeds', 'Edinburgh', 'Glasgow', 'Cardiff', 'Newcastle', 'Brighton',
    'Oxford', 'Cambridge', 'Bath', 'York', 'Exeter', 'Canterbury'
]

# US Cities  
US_CITIES = [
    'New York', 'Los Angeles', 'Chicago', 'Houston', 'Philadelphia', 'Phoenix',
    'San Antonio', 'San Diego', 'Dallas', 'San Jose', 'Austin', 'Jacksonville',
    'San Francisco', 'Columbus', 'Charlotte', 'Fort Worth', 'Indianapolis', 'Seattle'
]

# Australian Cities
AU_CITIES = [
    'Sydney', 'Melbourne', 'Brisbane', 'Perth', 'Adelaide', 'Gold Coast',
    'Newcastle', 'Canberra', 'Central Coast', 'Wollongong', 'Geelong', 'Hobart'
]

# Irish Cities
IE_CITIES = [
    'Dublin', 'Cork', 'Limerick', 'Galway', 'Waterford', 'Drogheda',
    'Dundalk', 'Swords', 'Bray', 'Navan', 'Ennis', 'Kilkenny'
]

def get_faker_and_cities(country: str):
    """Return appropriate Faker instance and city list for country"""
    if country == 'UK':
        return fake_uk, UK_CITIES
    elif country == 'US':
        return fake_us, US_CITIES
    elif country == 'AU':
        return fake_au, AU_CITIES
    elif country == 'IE':
        return fake_ie, IE_CITIES
    else:
        return fake_us, US_CITIES

def generate_company_names() -> List[str]:
    """Generate realistic company names for B2B customers"""
    company_types = [
        'Fitness Studio', 'Gym', 'Health Club', 'Wellness Center', 'Sports Club',
        'Athletic Center', 'Training Facility', 'Boxing Gym', 'Yoga Studio',
        'Pilates Studio', 'CrossFit Box', 'Dance Studio', 'Martial Arts Academy',
        'Corporate Wellness', 'Sports Team', 'Athletic Department', 'Fitness Retailer'
    ]
    
    prefixes = [
        'Elite', 'Prime', 'Peak', 'Core', 'Vital', 'Active', 'Dynamic', 'Power',
        'Fit', 'Strong', 'Pure', 'Total', 'Ultimate', 'Pro', 'Athletic', 'Metro',
        'Urban', 'Central', 'Premier', 'Platinum', 'Gold', 'Diamond', 'Elite'
    ]
    
    suffixes = [
        'Fitness', 'Wellness', 'Athletics', 'Performance', 'Training', 'Health',
        'Sports', 'Gym', 'Studio', 'Club', 'Center', 'Academy', 'Institute'
    ]
    
    companies = set()
    
    # Generate type-based names
    for _ in range(B2B_COUNT // 2):
        company_type = random.choice(company_types)
        city = random.choice(UK_CITIES + US_CITIES + AU_CITIES + IE_CITIES)
        companies.add(f"{city} {company_type}")
    
    # Generate prefix-suffix combinations
    while len(companies) < B2B_COUNT:
        prefix = random.choice(prefixes)
        suffix = random.choice(suffixes)
        companies.add(f"{prefix} {suffix}")
    
    return list(companies)[:B2B_COUNT]

def calculate_segments():
    """Calculate exact number of customers per segment"""
    segments = {}
    remaining = TOTAL_CUSTOMERS - B2B_COUNT
    
    for segment, percentage in SEGMENT_DISTRIBUTION.items():
        count = int(remaining * percentage)
        segments[segment] = count
    
    # Adjust for rounding errors
    total_assigned = sum(segments.values())
    if total_assigned < remaining:
        segments['Regular'] += remaining - total_assigned
    
    return segments

def calculate_geography():
    """Calculate exact number of customers per country"""
    geography = {}
    total_b2c = TOTAL_CUSTOMERS - B2B_COUNT
    
    for country, percentage in GEO_DISTRIBUTION.items():
        count = int(total_b2c * percentage)
        geography[country] = count
    
    # Adjust for rounding errors
    total_assigned = sum(geography.values())
    if total_assigned < total_b2c:
        geography['UK'] += total_b2c - total_assigned
    
    return geography

def generate_registration_date():
    """Generate registration date between Dec 2023 and Sep 2024"""
    start_date = datetime(2023, 12, 1)
    end_date = datetime(2024, 9, 30)
    
    delta = end_date - start_date
    random_days = random.randrange(delta.days)
    return (start_date + timedelta(days=random_days)).strftime('%Y-%m-%d')

def generate_first_purchase_date(registration_date: str):
    """Generate first purchase date within 30 days of registration"""
    reg_date = datetime.strptime(registration_date, '%Y-%m-%d')
    days_after = random.randint(0, 30)
    return (reg_date + timedelta(days=days_after)).strftime('%Y-%m-%d')

def generate_phone(country: str, faker_instance):
    """Generate phone number based on country"""
    if country == 'UK':
        return f"+44 {faker_instance.phone_number()}"
    elif country == 'US':
        return f"+1 {faker_instance.phone_number()}"
    elif country == 'AU':
        return f"+61 {faker_instance.phone_number()}"
    elif country == 'IE':
        return f"+353 {faker_instance.phone_number()}"
    return faker_instance.phone_number()

def determine_repeat_buyer_status(segment: str) -> tuple:
    """Determine if customer is repeat buyer and frequency based on segment"""
    repeat_probabilities = {
        'VIP': 0.95,
        'Loyal': 0.85,
        'Regular': 0.40,
        'One-Time': 0.05
    }
    
    is_repeat = random.random() < repeat_probabilities[segment]
    
    if is_repeat:
        frequency_mapping = {
            'VIP': random.randint(8, 15),      # 8-15 purchases per year
            'Loyal': random.randint(4, 8),     # 4-8 purchases per year
            'Regular': random.randint(2, 4),   # 2-4 purchases per year
            'One-Time': random.randint(1, 2)   # 1-2 purchases per year
        }
        frequency = frequency_mapping[segment]
    else:
        frequency = 1
    
    return is_repeat, frequency

def generate_b2c_customers():
    """Generate B2C customer records"""
    customers = []
    customer_id = 1
    used_emails = set()  # Track used emails to ensure uniqueness
    
    # Calculate distributions
    segments = calculate_segments()
    geography = calculate_geography()
    
    print(f"Generating B2C customers:")
    print(f"Segments: {segments}")
    print(f"Geography: {geography}")
    
    # Generate customers by country and segment
    for country, country_count in geography.items():
        faker_instance, cities = get_faker_and_cities(country)
        
        # Distribute customers across segments for this country
        country_segments = {}
        total_segments = sum(segments.values())
        
        for segment, segment_count in segments.items():
            country_segments[segment] = int((segment_count / total_segments) * country_count)
        
        # Adjust for rounding
        assigned = sum(country_segments.values())
        if assigned < country_count:
            country_segments['Regular'] += country_count - assigned
        
        for segment, count in country_segments.items():
            for _ in range(count):
                is_repeat, frequency = determine_repeat_buyer_status(segment)
                registration_date = generate_registration_date()
                
                # Generate unique email
                email = faker_instance.email()
                attempts = 0
                while email in used_emails and attempts < 100:
                    email = faker_instance.email()
                    attempts += 1
                
                # If still not unique after 100 attempts, make it unique
                if email in used_emails:
                    base_email = email.split('@')
                    email = f"{base_email[0]}{customer_id}@{base_email[1]}"
                
                used_emails.add(email)
                
                customer = {
                    'customer_id': f"CUS{customer_id:06d}",
                    'first_name': faker_instance.first_name(),
                    'last_name': faker_instance.last_name(),
                    'email': email,
                    'phone': generate_phone(country, faker_instance),
                    'type': 'Consumer',
                    'segment': segment,
                    'registration_date': registration_date,
                    'first_purchase_date': generate_first_purchase_date(registration_date),
                    'city': random.choice(cities),
                    'country': country,
                    'preferred_size': random.choice(SIZES),
                    'preferred_category': random.choice(PRODUCT_CATEGORIES),
                    'preferred_channel': random.choice(CHANNELS),
                    'is_repeat_buyer': is_repeat,
                    'purchase_frequency': frequency if is_repeat else 1,
                    'payment_terms': 'Immediate'
                }
                
                customers.append(customer)
                customer_id += 1
    
    return customers, used_emails

def generate_b2b_customers(used_emails=None):
    """Generate B2B customer records"""
    if used_emails is None:
        used_emails = set()
    
    customers = []
    company_names = generate_company_names()
    
    # Distribute B2B customers across countries
    b2b_geography = {
        'UK': int(B2B_COUNT * 0.60),    # 60% UK
        'US': int(B2B_COUNT * 0.20),    # 20% US  
        'AU': int(B2B_COUNT * 0.15),    # 15% AU
        'IE': int(B2B_COUNT * 0.05)     # 5% IE
    }
    
    # Adjust for rounding
    assigned = sum(b2b_geography.values())
    if assigned < B2B_COUNT:
        b2b_geography['UK'] += B2B_COUNT - assigned
    
    customer_id = TOTAL_CUSTOMERS - B2B_COUNT + 1
    company_index = 0
    
    for country, count in b2b_geography.items():
        faker_instance, cities = get_faker_and_cities(country)
        
        for _ in range(count):
            registration_date = generate_registration_date()
            
            # Generate unique email
            email = faker_instance.email()
            attempts = 0
            while email in used_emails and attempts < 100:
                email = faker_instance.email()
                attempts += 1
            
            # If still not unique after 100 attempts, make it unique
            if email in used_emails:
                base_email = email.split('@')
                email = f"{base_email[0]}{customer_id}@{base_email[1]}"
            
            used_emails.add(email)
            
            customer = {
                'customer_id': f"B2B{customer_id:06d}",
                'first_name': faker_instance.first_name(),
                'last_name': faker_instance.last_name(),
                'email': email,
                'phone': generate_phone(country, faker_instance),
                'type': 'B2B',
                'segment': 'Wholesale',
                'company_name': company_names[company_index],
                'registration_date': registration_date,
                'first_purchase_date': generate_first_purchase_date(registration_date),
                'city': random.choice(cities),
                'country': country,
                'preferred_size': 'Mixed',
                'preferred_category': 'Mixed',
                'preferred_channel': 'B2B Portal',
                'is_repeat_buyer': True,
                'purchase_frequency': random.randint(12, 24),  # 12-24 orders per year
                'payment_terms': 'Net 30',
                'monthly_quota': random.randint(5000, 25000)  # £5k-£25k monthly quota
            }
            
            customers.append(customer)
            customer_id += 1
            company_index += 1
    
    return customers, used_emails

def generate_all_customers():
    """Generate all customer records"""
    print("Starting customer data generation...")
    print(f"Target: {TOTAL_CUSTOMERS:,} total customers")
    print(f"B2C Customers: {TOTAL_CUSTOMERS - B2B_COUNT:,}")
    print(f"B2B Customers: {B2B_COUNT:,}")
    print()
    
    # Generate B2C customers
    b2c_customers, used_emails = generate_b2c_customers()
    print(f"Generated {len(b2c_customers):,} B2C customers")
    
    # Generate B2B customers with unique emails
    b2b_customers, _ = generate_b2b_customers(used_emails)
    print(f"Generated {len(b2b_customers):,} B2B customers")
    
    # Combine all customers
    all_customers = b2c_customers + b2b_customers
    
    # Shuffle to mix B2C and B2B customers
    random.shuffle(all_customers)
    
    return all_customers

def validate_data(customers: List[Dict[str, Any]]):
    """Validate generated customer data"""
    print("\nValidating generated data...")
    
    # Basic counts
    total = len(customers)
    b2c_count = len([c for c in customers if c['type'] == 'Consumer'])
    b2b_count = len([c for c in customers if c['type'] == 'B2B'])
    
    print(f"Total customers: {total:,}")
    print(f"B2C customers: {b2c_count:,}")
    print(f"B2B customers: {b2b_count:,}")
    
    # Segment distribution
    segments = {}
    for customer in customers:
        segment = customer['segment']
        segments[segment] = segments.get(segment, 0) + 1
    
    print("\nSegment distribution:")
    for segment, count in segments.items():
        percentage = (count / total) * 100
        print(f"  {segment}: {count:,} ({percentage:.1f}%)")
    
    # Geographic distribution
    countries = {}
    for customer in customers:
        country = customer['country']
        countries[country] = countries.get(country, 0) + 1
    
    print("\nGeographic distribution:")
    for country, count in countries.items():
        percentage = (count / total) * 100
        print(f"  {country}: {count:,} ({percentage:.1f}%)")
    
    # Repeat buyer analysis
    repeat_buyers = len([c for c in customers if c['is_repeat_buyer']])
    repeat_percentage = (repeat_buyers / total) * 100
    
    print(f"\nRepeat buyers: {repeat_buyers:,} ({repeat_percentage:.1f}%)")
    
    # Unique emails check
    emails = set(c['email'] for c in customers)
    print(f"Unique emails: {len(emails):,} (should match total)")
    
    print("\nValidation complete!")

if __name__ == "__main__":
    # Set random seed for reproducible results
    random.seed(42)
    Faker.seed(42)
    
    # Generate customers
    customers = generate_all_customers()
    
    # Validate data
    validate_data(customers)
    
    # Save to JSON file
    output_file = "/workspaces/source-lovable-gympluscoffee/odoo-ingestion/generated_customers.json"
    
    print(f"\nSaving customer data to {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(customers, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully saved {len(customers):,} customer records!")
    
    # Generate summary statistics
    summary = {
        'generation_timestamp': datetime.now().isoformat(),
        'total_customers': len(customers),
        'b2c_customers': len([c for c in customers if c['type'] == 'Consumer']),
        'b2b_customers': len([c for c in customers if c['type'] == 'B2B']),
        'repeat_buyers': len([c for c in customers if c['is_repeat_buyer']]),
        'countries': list(set(c['country'] for c in customers)),
        'segments': list(set(c['segment'] for c in customers)),
        'date_range': {
            'start': '2023-12-01',
            'end': '2024-09-30'
        }
    }
    
    summary_file = "/workspaces/source-lovable-gympluscoffee/odoo-ingestion/customer_generation_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Summary saved to {summary_file}")