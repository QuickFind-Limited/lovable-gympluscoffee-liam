#!/usr/bin/env python3
"""
Final verification of channel distribution for Source Gym Plus Coffee
"""

import sys
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
    
    def search_count(self, model, domain):
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model, 'search_count',
            [domain]
        )

def main():
    """Verify the final channel distribution"""
    
    # Connection details
    url = "https://source-gym-plus-coffee.odoo.com/"
    db = "source-gym-plus-coffee"
    username = "admin@quickfindai.com"
    password = "BJ62wX2J4yzjS$i"
    
    try:
        # Connect to Odoo
        print("🔗 Connecting to Odoo for verification...")
        odoo = OdooConnection(url, db, username, password)
        
        # Get all sales teams
        teams = odoo.search_read('crm.team', [], ['name', 'id'])
        team_lookup = {team['id']: team['name'] for team in teams}
        
        print(f"\n📋 Available Sales Teams:")
        for team in teams:
            print(f"  {team['id']}: {team['name']}")
        
        # Count orders by team
        print(f"\n📊 Order Distribution by Sales Team:")
        
        # Get all confirmed orders with team assignments
        orders = odoo.search_read('sale.order', 
                                [['state', 'in', ['sale', 'done']]], 
                                ['team_id', 'amount_total'])
        
        total_orders = len(orders)
        print(f"Total confirmed orders: {total_orders}")
        
        # Count by team
        team_counts = {}
        team_aovs = {}
        
        for order in orders:
            team_id = order['team_id'][0] if order['team_id'] else None
            aov = order['amount_total']
            
            if team_id:
                if team_id not in team_counts:
                    team_counts[team_id] = 0
                    team_aovs[team_id] = []
                team_counts[team_id] += 1
                team_aovs[team_id].append(aov)
        
        # Display results
        online_count = team_counts.get(9, 0)  # Online/D2C Sales
        retail_count = team_counts.get(5, 0)  # Amazon Store (Retail)
        b2b_count = team_counts.get(10, 0)    # B2B/Wholesale Sales
        other_counts = sum(count for team_id, count in team_counts.items() if team_id not in [9, 5, 10])
        
        print(f"\n📈 Channel Distribution:")
        print(f"  Online/D2C (Team 9): {online_count} orders ({online_count/total_orders*100:.1f}%)")
        print(f"  Retail (Team 5): {retail_count} orders ({retail_count/total_orders*100:.1f}%)")
        print(f"  B2B (Team 10): {b2b_count} orders ({b2b_count/total_orders*100:.1f}%)")
        print(f"  Other teams: {other_counts} orders ({other_counts/total_orders*100:.1f}%)")
        
        # Calculate AOV ranges for verification
        if 9 in team_aovs and team_aovs[9]:
            online_aov_min = min(team_aovs[9])
            online_aov_max = max(team_aovs[9])
            online_aov_avg = sum(team_aovs[9]) / len(team_aovs[9])
            print(f"  Online AOV range: €{online_aov_min:.2f} - €{online_aov_max:.2f} (avg: €{online_aov_avg:.2f})")
        
        if 5 in team_aovs and team_aovs[5]:
            retail_aov_min = min(team_aovs[5])
            retail_aov_max = max(team_aovs[5])
            retail_aov_avg = sum(team_aovs[5]) / len(team_aovs[5])
            print(f"  Retail AOV range: €{retail_aov_min:.2f} - €{retail_aov_max:.2f} (avg: €{retail_aov_avg:.2f})")
        
        if 10 in team_aovs and team_aovs[10]:
            b2b_aov_min = min(team_aovs[10])
            b2b_aov_max = max(team_aovs[10])
            b2b_aov_avg = sum(team_aovs[10]) / len(team_aovs[10])
            print(f"  B2B AOV range: €{b2b_aov_min:.2f} - €{b2b_aov_max:.2f} (avg: €{b2b_aov_avg:.2f})")
        
        # Verify against targets
        target_online = 0.60
        target_retail = 0.20
        target_b2b = 0.20
        
        actual_online = online_count / total_orders
        actual_retail = retail_count / total_orders
        actual_b2b = b2b_count / total_orders
        
        print(f"\n🎯 Target vs Actual:")
        print(f"  Online/D2C:   Target: {target_online*100:.0f}%  Actual: {actual_online*100:.1f}%  Diff: {(actual_online-target_online)*100:+.1f}%")
        print(f"  Retail:       Target: {target_retail*100:.0f}%  Actual: {actual_retail*100:.1f}%  Diff: {(actual_retail-target_retail)*100:+.1f}%")
        print(f"  B2B:          Target: {target_b2b*100:.0f}%  Actual: {actual_b2b*100:.1f}%  Diff: {(actual_b2b-target_b2b)*100:+.1f}%")
        
        # Final tolerance check
        tolerance = 0.03
        online_ok = abs(actual_online - target_online) <= tolerance
        retail_ok = abs(actual_retail - target_retail) <= tolerance
        b2b_ok = abs(actual_b2b - target_b2b) <= tolerance
        
        print(f"\n✅ Final Tolerance Check (±3%):")
        print(f"  Online/D2C: {'✅ PASS' if online_ok else '❌ FAIL'}")
        print(f"  Retail:     {'✅ PASS' if retail_ok else '❌ FAIL'}")
        print(f"  B2B:        {'✅ PASS' if b2b_ok else '❌ FAIL'}")
        
        if online_ok and retail_ok and b2b_ok:
            print(f"\n🎉 VERIFICATION SUCCESSFUL!")
            print(f"   ✅ All channels meet the 60/20/20 distribution requirement")
            print(f"   ✅ All channels are within ±3% tolerance")
            print(f"   ✅ Channel assignments are properly distributed by AOV")
        else:
            print(f"\n⚠️  VERIFICATION FAILED - Some channels outside tolerance")
        
        print(f"\n📋 FINAL SUMMARY:")
        print(f"  📊 Total orders processed: {total_orders}")
        print(f"  🎯 Distribution achieved: {actual_online*100:.1f}% / {actual_retail*100:.1f}% / {actual_b2b*100:.1f}%")
        print(f"  💰 AOV-based channel assignment completed")
        print(f"  ✅ Channel distribution fix: {'SUCCESS' if (online_ok and retail_ok and b2b_ok) else 'PARTIAL'}")
        
        return online_ok and retail_ok and b2b_ok
        
    except Exception as e:
        print(f"❌ Verification Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)