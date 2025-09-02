
# Geographic Expansion Script

import xmlrpc.client
import random

def create_diverse_customers():
    # Connection setup
    url = 'https://source-gym-plus-coffee.odoo.com/'
    db = 'source-gym-plus-coffee'
    username = 'admin@quickfindai.com'
    password = 'BJ62wX2J4yzjS$i'
    
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    uid = common.authenticate(db, username, password, {})
    
    # Get country and state IDs
    countries = models.execute_kw(db, uid, password, 'res.country', 'search_read',
                                [[]], {'fields': ['name', 'id']})
    states = models.execute_kw(db, uid, password, 'res.country.state', 'search_read',
                             [[]], {'fields': ['name', 'id', 'country_id']})
    
    # Define diverse locations
    diverse_locations = [
        {'city': 'Miami', 'state_name': 'Florida'},
        {'city': 'Austin', 'state_name': 'Texas'},
        {'city': 'Denver', 'state_name': 'Colorado'},
        {'city': 'Seattle', 'state_name': 'Washington'},
        {'city': 'Boston', 'state_name': 'Massachusetts'},
        {'city': 'Atlanta', 'state_name': 'Georgia'},
        {'city': 'Phoenix', 'state_name': 'Arizona'},
        {'city': 'Portland', 'state_name': 'Oregon'}
    ]
    
    # Create customers in each location
    for location in diverse_locations:
        # Find state ID
        state_id = None
        for state in states:
            if location['state_name'].lower() in state['name'].lower():
                state_id = state['id']
                break
        
        # Create 3-5 customers per location
        for i in range(random.randint(3, 5)):
            customer_data = {
                'name': f"Customer {location['city']} {i+1}",
                'email': f"customer.{location['city'].lower()}.{i+1}@example.com",
                'city': location['city'],
                'state_id': state_id,
                'country_id': 233,  # USA
                'is_company': False
            }
            
            try:
                customer_id = models.execute_kw(db, uid, password, 'res.partner', 'create', [customer_data])
                print(f"Created customer in {location['city']}: {customer_id}")
            except Exception as e:
                print(f"Error creating customer in {location['city']}: {e}")

if __name__ == "__main__":
    create_diverse_customers()
