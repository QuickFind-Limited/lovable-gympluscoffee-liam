#!/usr/bin/env python3
"""
Channel Distribution Fixer for Source Gym Plus Coffee Odoo Instance
"""

import os
import sys

# Add the odoo-ingestion directory to Python path for imports
sys.path.insert(0, '/workspaces/source-lovable-gympluscoffee/odoo-ingestion')

try:
    from odoo_connection import OdooConnection
except ImportError:
    print("Could not import OdooConnection. Creating basic connection...")
    import xmlrpc.client
    
    class OdooConnection:
        def __init__(self, url, db, username, password):
            self.url = url
            self.db = db
            self.username = username
            self.password = password
            
            # Establish connection
            common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
            self.uid = common.authenticate(db, username, password, {})
            if not self.uid:
                raise Exception("Authentication failed")
            
            self.models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
            print(f"✅ Connected to Odoo as user ID: {self.uid}")
        
        def search_read(self, model, domain, fields=None, limit=None):
            options = {}
            if fields is not None:
                options['fields'] = fields
            if limit is not None:
                options['limit'] = limit
            
            return self.models.execute_kw(
                self.db, self.uid, self.password,
                model, 'search_read',
                [domain], 
                options
            )
        
        def search(self, model, domain, limit=None):
            options = {}
            if limit is not None:
                options['limit'] = limit
            
            return self.models.execute_kw(
                self.db, self.uid, self.password,
                model, 'search',
                [domain],
                options
            )
        
        def read(self, model, ids, fields=None):
            options = {}
            if fields is not None:
                options['fields'] = fields
            
            return self.models.execute_kw(
                self.db, self.uid, self.password,
                model, 'read',
                [ids],
                options
            )
        
        def write(self, model, ids, values):
            return self.models.execute_kw(
                self.db, self.uid, self.password,
                model, 'write',
                [ids, values]
            )
        
        def create(self, model, values):
            return self.models.execute_kw(
                self.db, self.uid, self.password,
                model, 'create',
                [values]
            )
        
        def search_count(self, model, domain):
            return self.models.execute_kw(
                self.db, self.uid, self.password,
                model, 'search_count',
                [domain]
            )

def main():
    """Fix channel distribution for sales orders"""
    
    # Connection details
    url = "https://source-gym-plus-coffee.odoo.com/"
    db = "source-gym-plus-coffee"
    username = "admin@quickfindai.com"
    password = "BJ62wX2J4yzjS$i"
    
    try:
        # Connect to Odoo
        print("🔗 Connecting to Odoo...")
        odoo = OdooConnection(url, db, username, password)
        
        # Step 1: Check existing sales teams
        print("\n📋 Step 1: Checking existing sales teams...")
        teams = odoo.search_read('crm.team', [], ['name', 'id'])
        
        print(f"Found {len(teams)} sales teams:")
        for team in teams:
            print(f"  - {team['name']} (ID: {team['id']})")
        
        # Required teams
        required_teams = {
            'Online/D2C Sales': None,
            'Retail Sales': None, 
            'B2B/Wholesale Sales': None
        }
        
        # Map existing teams
        for team in teams:
            name = team['name']
            if 'Online' in name or 'D2C' in name or 'E-commerce' in name:
                required_teams['Online/D2C Sales'] = team['id']
            elif 'Retail' in name or 'Store' in name:
                required_teams['Retail Sales'] = team['id']
            elif 'B2B' in name or 'Wholesale' in name:
                required_teams['B2B/Wholesale Sales'] = team['id']
        
        # Create missing teams
        print("\n🏗️ Creating missing sales teams...")
        for team_name, team_id in required_teams.items():
            if team_id is None:
                new_team_id = odoo.create('crm.team', {'name': team_name})
                required_teams[team_name] = new_team_id
                print(f"  ✅ Created: {team_name} (ID: {new_team_id})")
            else:
                print(f"  ✅ Exists: {team_name} (ID: {team_id})")
        
        # Step 2: Analyze current orders
        print("\n📊 Step 2: Analyzing current sales orders...")
        orders = odoo.search_read('sale.order', 
                                [['state', 'in', ['sale', 'done']]],
                                ['name', 'amount_total', 'team_id'])
        
        print(f"Found {len(orders)} confirmed orders")
        
        # Categorize orders by AOV
        online_orders = []    # AOV €90-120
        retail_orders = []    # AOV €70-100  
        b2b_orders = []       # AOV €500+
        other_orders = []
        
        for order in orders:
            aov = order['amount_total']
            if 90 <= aov <= 120:
                online_orders.append(order)
            elif 70 <= aov <= 100:
                retail_orders.append(order)
            elif aov >= 500:
                b2b_orders.append(order)
            else:
                other_orders.append(order)
        
        total_orders = len(orders)
        print(f"\n📈 Order distribution by AOV:")
        print(f"  Online (€90-120): {len(online_orders)} ({len(online_orders)/total_orders*100:.1f}%)")
        print(f"  Retail (€70-100): {len(retail_orders)} ({len(retail_orders)/total_orders*100:.1f}%)")
        print(f"  B2B (€500+): {len(b2b_orders)} ({len(b2b_orders)/total_orders*100:.1f}%)")
        print(f"  Other: {len(other_orders)} ({len(other_orders)/total_orders*100:.1f}%)")
        
        # Step 3: Update channel assignments
        print(f"\n🔄 Step 3: Updating channel assignments...")
        
        # Update Online orders
        if online_orders:
            online_ids = [order['id'] for order in online_orders]
            odoo.write('sale.order', online_ids, {'team_id': required_teams['Online/D2C Sales']})
            print(f"  ✅ Updated {len(online_orders)} orders to Online/D2C Sales")
        
        # Update Retail orders  
        if retail_orders:
            retail_ids = [order['id'] for order in retail_orders]
            odoo.write('sale.order', retail_ids, {'team_id': required_teams['Retail Sales']})
            print(f"  ✅ Updated {len(retail_orders)} orders to Retail Sales")
        
        # Update B2B orders
        if b2b_orders:
            b2b_ids = [order['id'] for order in b2b_orders]
            odoo.write('sale.order', b2b_ids, {'team_id': required_teams['B2B/Wholesale Sales']})
            print(f"  ✅ Updated {len(b2b_orders)} orders to B2B/Wholesale Sales")
        
        # Step 4: Verify final distribution
        print(f"\n✅ Step 4: Verifying final distribution...")
        
        # Calculate target vs actual
        target_online = 0.60
        target_retail = 0.20
        target_b2b = 0.20
        
        actual_online = len(online_orders) / total_orders
        actual_retail = len(retail_orders) / total_orders
        actual_b2b = len(b2b_orders) / total_orders
        
        print(f"\n📊 Final Distribution Analysis:")
        print(f"  Online/D2C:   Target: {target_online*100:.0f}%  Actual: {actual_online*100:.1f}%  Diff: {(actual_online-target_online)*100:+.1f}%")
        print(f"  Retail:       Target: {target_retail*100:.0f}%  Actual: {actual_retail*100:.1f}%  Diff: {(actual_retail-target_retail)*100:+.1f}%")
        print(f"  B2B:          Target: {target_b2b*100:.0f}%  Actual: {actual_b2b*100:.1f}%  Diff: {(actual_b2b-target_b2b)*100:+.1f}%")
        
        # Check tolerance (±3%)
        tolerance = 0.03
        online_ok = abs(actual_online - target_online) <= tolerance
        retail_ok = abs(actual_retail - target_retail) <= tolerance
        b2b_ok = abs(actual_b2b - target_b2b) <= tolerance
        
        print(f"\n🎯 Tolerance Check (±3%):")
        print(f"  Online/D2C: {'✅ PASS' if online_ok else '❌ FAIL'}")
        print(f"  Retail:     {'✅ PASS' if retail_ok else '❌ FAIL'}")
        print(f"  B2B:        {'✅ PASS' if b2b_ok else '❌ FAIL'}")
        
        if online_ok and retail_ok and b2b_ok:
            print("\n🎉 SUCCESS: All channels are within tolerance!")
        else:
            print("\n⚠️  WARNING: Some channels are outside tolerance range")
            print("   This may be due to the AOV ranges not perfectly matching the 60/20/20 split")
            print("   Consider adjusting AOV ranges or creating additional rules")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)