#!/usr/bin/env python3
"""
Irish Market Enhancement Data for Transaction Generation
Provides realistic Irish market data for Gym+Coffee transactions.

Agent: Transaction Generator
Enhanced realistic data for Irish retail market.
"""

import random

class IrishMarketData:
    """Enhanced Irish market data for realistic transaction generation"""
    
    # Irish cities and regions with population weights
    IRISH_LOCATIONS = {
        'Dublin': {
            'weight': 0.35,
            'areas': ['Dublin 1', 'Dublin 2', 'Dublin 4', 'Dublin 6', 'Dublin 8', 'Dún Laoghaire', 'Swords', 'Blanchardstown'],
            'postcodes': ['D01', 'D02', 'D04', 'D06', 'D08', 'A96', 'K67', 'D15']
        },
        'Cork': {
            'weight': 0.15,
            'areas': ['Cork City Centre', 'Ballincollig', 'Carrigaline', 'Midleton'],
            'postcodes': ['T12', 'T45', 'P43', 'P25']
        },
        'Galway': {
            'weight': 0.10,
            'areas': ['Galway City', 'Salthill', 'Oranmore', 'Tuam'],
            'postcodes': ['H91', 'H54', 'H65', 'H54']
        },
        'Limerick': {
            'weight': 0.08,
            'areas': ['Limerick City', 'Castletroy', 'Newcastle West'],
            'postcodes': ['V94', 'V42', 'V42']
        },
        'Waterford': {
            'weight': 0.07,
            'areas': ['Waterford City', 'Tramore', 'Dungarvan'],
            'postcodes': ['X91', 'X91', 'X35']
        },
        'Other': {
            'weight': 0.25,
            'areas': ['Sligo', 'Drogheda', 'Dundalk', 'Wexford', 'Kilkenny', 'Athlone', 'Letterkenny'],
            'postcodes': ['F91', 'A92', 'A91', 'Y35', 'R95', 'N37', 'F92']
        }
    }
    
    # Irish phone number patterns
    PHONE_PATTERNS = [
        '+353 1 {area}',    # Dublin landline
        '+353 21 {area}',   # Cork landline
        '+353 91 {area}',   # Galway landline
        '+353 61 {area}',   # Limerick landline
        '+353 51 {area}',   # Waterford landline
        '+353 87 {mobile}', # Vodafone mobile
        '+353 86 {mobile}', # Three mobile
        '+353 85 {mobile}', # Eir mobile
        '+353 83 {mobile}', # Three mobile
    ]
    
    # Common Irish names for realistic customers
    IRISH_FIRST_NAMES = [
        'Aoife', 'Caoimhe', 'Ciara', 'Eimear', 'Fiona', 'Grainne', 'Niamh', 'Orna', 'Roisin', 'Siobhan',
        'Aisling', 'Clodagh', 'Deirdre', 'Maeve', 'Orla', 'Saoirse', 'Sinead', 'Tara', 'Una',
        'Aidan', 'Cian', 'Colm', 'Conor', 'Darragh', 'Eoin', 'Fionn', 'Oisin', 'Padraig', 'Ruairi',
        'Brendan', 'Cillian', 'Donal', 'Fergal', 'Liam', 'Niall', 'Ronan', 'Sean', 'Tadhg',
        'Brian', 'Cathal', 'Declan', 'Emmet', 'Kevin', 'Michael', 'Patrick', 'Shane', 'Thomas'
    ]
    
    IRISH_SURNAMES = [
        'Murphy', 'Kelly', 'O\'Sullivan', 'Walsh', 'Smith', 'O\'Brien', 'Byrne', 'Ryan', 'O\'Connor', 'O\'Neill',
        'O\'Reilly', 'Doyle', 'McCarthy', 'Gallagher', 'O\'Doherty', 'Kennedy', 'Lynch', 'Murray', 'Quinn', 'Moore',
        'McLoughlin', 'O\'Carroll', 'Connolly', 'Daly', 'O\'Connell', 'Wilson', 'Dunne', 'Griffin', 'Farrell', 'Fitzpatrick',
        'Healy', 'Malone', 'Power', 'Burke', 'Kavanagh', 'McDonald', 'Nolan', 'Brennan', 'Brady', 'Sweeney'
    ]
    
    # Irish company names for B2B customers
    IRISH_COMPANIES = [
        'Fitness Ireland Ltd',
        'Gym Solutions Cork',
        'Active Life Galway',
        'Dublin Sports Co',
        'West Coast Fitness',
        'Elite Training Dublin',
        'Healthy Living Ltd',
        'Irish Wellness Group',
        'Munster Gym Supply',
        'Connacht Active',
        'Leinster Sports Hub',
        'Ulster Fitness Co',
        'Pure Gym Ireland',
        'National Health Club',
        'Premier Fitness Ltd'
    ]
    
    # Common Irish streets
    IRISH_STREETS = [
        'Main Street', 'High Street', 'Church Street', 'Market Street', 'Patrick Street',
        'O\'Connell Street', 'Grafton Street', 'Henry Street', 'Dame Street', 'Nassau Street',
        'Parnell Street', 'Abbey Street', 'Temple Lane', 'College Green', 'Stephen\'s Green',
        'Cork Street', 'Thomas Street', 'Francis Street', 'Kevin Street', 'George\'s Street'
    ]
    
    # Irish email domains
    EMAIL_DOMAINS = [
        'gmail.com', 'hotmail.com', 'yahoo.ie', 'eircom.net', 'ucd.ie', 'tcd.ie',
        'outlook.com', 'live.ie', 'btinternet.com', 'vodafone.ie'
    ]
    
    # Payment preferences in Ireland
    PAYMENT_PREFERENCES = {
        'online': {
            'visa': 0.35,
            'mastercard': 0.30,
            'paypal': 0.20,
            'laser': 0.08,  # Irish debit card
            'american_express': 0.04,
            'revolut': 0.03
        },
        'retail': {
            'contactless': 0.45,
            'chip_pin': 0.35,
            'cash': 0.18,
            'mobile_payment': 0.02
        }
    }
    
    # Irish VAT rates
    VAT_RATES = {
        'clothing': 0.23,      # Standard rate
        'accessories': 0.23,   # Standard rate
        'sports_equipment': 0.23  # Standard rate
    }
    
    # Shipping carriers popular in Ireland
    IRISH_CARRIERS = [
        'An Post',      # National postal service
        'DPD Ireland',  # Popular courier
        'Fastway',      # Irish courier service
        'DHL Ireland',  # International courier
        'UPS Ireland',  # International courier
        'Hermes Ireland' # Parcel delivery
    ]
    
    # Irish retail store names for Gym+Coffee
    GYM_COFFEE_STORES = {
        'Dublin': [
            'Gym+Coffee Grafton Street',
            'Gym+Coffee Stephen\'s Green',
            'Gym+Coffee Temple Bar',
            'Gym+Coffee Dundrum Town Centre',
            'Gym+Coffee Blanchardstown Centre'
        ],
        'Cork': [
            'Gym+Coffee Patrick Street',
            'Gym+Coffee Merchant\'s Quay',
            'Gym+Coffee Wilton Shopping Centre'
        ],
        'Galway': [
            'Gym+Coffee Shop Street',
            'Gym+Coffee Eyre Square Centre'
        ],
        'Limerick': [
            'Gym+Coffee O\'Connell Street',
            'Gym+Coffee Crescent Shopping Centre'
        ],
        'Other': [
            'Gym+Coffee Waterford',
            'Gym+Coffee Sligo',
            'Gym+Coffee Athlone'
        ]
    }
    
    @classmethod
    def generate_irish_name(cls) -> str:
        """Generate realistic Irish name"""
        first_name = random.choice(cls.IRISH_FIRST_NAMES)
        surname = random.choice(cls.IRISH_SURNAMES)
        return f"{first_name} {surname}"
    
    @classmethod 
    def generate_irish_company_name(cls) -> str:
        """Generate realistic Irish company name"""
        return random.choice(cls.IRISH_COMPANIES)
    
    @classmethod
    def generate_irish_address(cls, city: str = None) -> dict:
        """Generate realistic Irish address"""
        if not city:
            city = random.choices(
                list(cls.IRISH_LOCATIONS.keys()),
                weights=[loc['weight'] for loc in cls.IRISH_LOCATIONS.values()]
            )[0]
        
        location_data = cls.IRISH_LOCATIONS[city]
        area = random.choice(location_data['areas'])
        postcode = random.choice(location_data['postcodes']) + ' ' + random.choice(['A123', 'B456', 'C789', 'D012'])
        
        street_number = random.randint(1, 999)
        street_name = random.choice(cls.IRISH_STREETS)
        
        return {
            'street': f"{street_number} {street_name}",
            'area': area,
            'city': city,
            'county': cls.get_county_for_city(city),
            'postcode': postcode,
            'country': 'Ireland'
        }
    
    @classmethod
    def get_county_for_city(cls, city: str) -> str:
        """Get county for Irish city"""
        county_mapping = {
            'Dublin': 'Co. Dublin',
            'Cork': 'Co. Cork', 
            'Galway': 'Co. Galway',
            'Limerick': 'Co. Limerick',
            'Waterford': 'Co. Waterford'
        }
        return county_mapping.get(city, 'Ireland')
    
    @classmethod
    def generate_irish_phone(cls) -> str:
        """Generate realistic Irish phone number"""
        pattern = random.choice(cls.PHONE_PATTERNS)
        
        if '{area}' in pattern:
            area_code = ''.join([str(random.randint(0, 9)) for _ in range(7)])
            return pattern.format(area=area_code)
        elif '{mobile}' in pattern:
            mobile_number = ''.join([str(random.randint(0, 9)) for _ in range(7)])
            return pattern.format(mobile=mobile_number)
        
        return pattern
    
    @classmethod
    def generate_irish_email(cls, name: str = None) -> str:
        """Generate realistic Irish email address"""
        if not name:
            name = cls.generate_irish_name()
        
        # Convert name to email format
        name_parts = name.lower().replace('\'', '').replace(' ', '.')
        domain = random.choice(cls.EMAIL_DOMAINS)
        
        # Add random numbers sometimes
        if random.random() < 0.3:
            name_parts += str(random.randint(1, 99))
        
        return f"{name_parts}@{domain}"
    
    @classmethod
    def get_store_for_location(cls, city: str) -> str:
        """Get appropriate Gym+Coffee store for location"""
        if city in cls.GYM_COFFEE_STORES:
            return random.choice(cls.GYM_COFFEE_STORES[city])
        else:
            return random.choice(cls.GYM_COFFEE_STORES['Other'])
    
    @classmethod
    def get_shipping_carrier(cls) -> str:
        """Get realistic Irish shipping carrier"""
        return random.choice(cls.IRISH_CARRIERS)

# Enhanced product data for Gym+Coffee
ENHANCED_GYM_COFFEE_PRODUCTS = [
    {
        'sku': 'GC001-BLA-S',
        'name': 'Essential Hoodie - Black',
        'category': 'hoodies',
        'list_price': 79.95,
        'cost': 32.00,
        'seasonal_multiplier': 1.2  # Higher demand in winter
    },
    {
        'sku': 'GC001-GRY-S',
        'name': 'Essential Hoodie - Grey',
        'category': 'hoodies', 
        'list_price': 79.95,
        'cost': 32.00,
        'seasonal_multiplier': 1.2
    },
    {
        'sku': 'GC002-WHT-M',
        'name': 'Classic Tee - White',
        'category': 't-shirts',
        'list_price': 34.95,
        'cost': 14.00,
        'seasonal_multiplier': 0.9  # Lower demand in winter
    },
    {
        'sku': 'GC003-NVY-L',
        'name': 'Performance Leggings - Navy',
        'category': 'leggings',
        'list_price': 64.95,
        'cost': 26.00,
        'seasonal_multiplier': 1.1  # Consistent year-round
    },
    {
        'sku': 'GC004-BLA-OS',
        'name': 'Logo Cap - Black',
        'category': 'accessories',
        'list_price': 24.95,
        'cost': 10.00,
        'seasonal_multiplier': 1.0
    },
    {
        'sku': 'GC005-GRN-M',
        'name': 'Gym Shorts - Green',
        'category': 'shorts',
        'list_price': 44.95,
        'cost': 18.00,
        'seasonal_multiplier': 0.7  # Much lower in winter
    }
]

if __name__ == "__main__":
    # Test Irish market data generation
    print("🇮🇪 Testing Irish Market Data Generation")
    print("=" * 50)
    
    # Test name generation
    for i in range(5):
        name = IrishMarketData.generate_irish_name()
        email = IrishMarketData.generate_irish_email(name)
        phone = IrishMarketData.generate_irish_phone()
        address = IrishMarketData.generate_irish_address()
        
        print(f"Customer {i+1}:")
        print(f"  Name: {name}")
        print(f"  Email: {email}")
        print(f"  Phone: {phone}")
        print(f"  Address: {address['street']}, {address['area']}, {address['city']}, {address['postcode']}")
        print()
    
    # Test company generation
    print("B2B Customers:")
    for i in range(3):
        company = IrishMarketData.generate_irish_company_name()
        address = IrishMarketData.generate_irish_address()
        store = IrishMarketData.get_store_for_location(address['city'])
        
        print(f"  Company: {company}")
        print(f"  Location: {address['city']}")
        print(f"  Nearest Store: {store}")
        print()