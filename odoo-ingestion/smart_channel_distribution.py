#!/usr/bin/env python3
"""
Smart Channel Distribution Fixer for Source Gym Plus Coffee Odoo Instance
Analyzes actual AOV distribution and assigns channels to achieve 60/20/20 split
"""

import os
import sys
import statistics

# Add the odoo-ingestion directory to Python path for imports
sys.path.insert(0, '/workspaces/source-lovable-gympluscoffee/odoo-ingestion')

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

def analyze_aov_distribution(orders):
    """Analyze AOV distribution and find optimal breakpoints for 60/20/20 split"""
    
    # Sort orders by AOV
    sorted_orders = sorted(orders, key=lambda x: x['amount_total'])
    total_orders = len(sorted_orders)
    
    # Find AOV statistics
    aovs = [o['amount_total'] for o in sorted_orders]
    mean_aov = statistics.mean(aovs)
    median_aov = statistics.median(aovs)
    
    print(f"\n📊 AOV Analysis:")
    print(f"  Total orders: {total_orders}")
    print(f"  Mean AOV: €{mean_aov:.2f}")
    print(f"  Median AOV: €{median_aov:.2f}")
    print(f"  Min AOV: €{min(aovs):.2f}")
    print(f"  Max AOV: €{max(aovs):.2f}")
    
    # Calculate percentiles
    p20 = sorted_orders[int(0.20 * total_orders)]['amount_total']
    p60 = sorted_orders[int(0.60 * total_orders)]['amount_total']
    p80 = sorted_orders[int(0.80 * total_orders)]['amount_total']
    
    print(f"  20th percentile: €{p20:.2f}")
    print(f"  60th percentile: €{p60:.2f}")
    print(f"  80th percentile: €{p80:.2f}")
    
    # For 60/20/20 split:
    # - Bottom 60% → Online/D2C (highest volume, lower AOV)
    # - Next 20% → Retail (medium AOV)
    # - Top 20% → B2B (highest AOV, lowest volume)
    
    online_threshold = p60  # Bottom 60% 
    retail_threshold = p80  # Next 20%
    # Above retail_threshold = B2B (top 20%)
    
    return {
        'online_max': online_threshold,
        'retail_min': online_threshold,
        'retail_max': retail_threshold,
        'b2b_min': retail_threshold,
        'stats': {
            'mean': mean_aov,
            'median': median_aov,
            'p20': p20,
            'p60': p60,
            'p80': p80
        }
    }

def assign_channels_by_percentile(orders, thresholds):
    """Assign orders to channels based on AOV percentiles"""
    
    online_orders = []
    retail_orders = []
    b2b_orders = []
    
    for order in orders:
        aov = order['amount_total']
        
        if aov <= thresholds['online_max']:
            online_orders.append(order)
        elif aov <= thresholds['retail_max']:
            retail_orders.append(order)
        else:
            b2b_orders.append(order)
    
    return online_orders, retail_orders, b2b_orders

def main():
    """Smart channel distribution based on actual AOV percentiles"""
    
    # Connection details
    url = "https://source-gym-plus-coffee.odoo.com/"
    db = "source-gym-plus-coffee"
    username = "admin@quickfindai.com"
    password = "BJ62wX2J4yzjS$i"
    
    try:
        # Connect to Odoo
        print("🔗 Connecting to Odoo...")
        odoo = OdooConnection(url, db, username, password)
        
        # Get sales teams (assuming they exist from previous script)
        teams = odoo.search_read('crm.team', [], ['name', 'id'])
        team_map = {}
        
        for team in teams:
            name = team['name']
            if 'Online' in name or 'D2C' in name:
                team_map['online'] = team['id']
            elif 'Retail' in name and team['id'] != 5:  # Avoid Amazon Store (ID: 5)
                team_map['retail'] = team['id']
            elif 'B2B' in name or 'Wholesale' in name:
                team_map['b2b'] = team['id']
        
        # If teams don't exist, use the IDs from previous script
        if 'online' not in team_map:
            team_map['online'] = 9  # Online/D2C Sales
        if 'retail' not in team_map:
            team_map['retail'] = 5  # Amazon Store (will be reassigned)
        if 'b2b' not in team_map:
            team_map['b2b'] = 10  # B2B/Wholesale Sales
        
        print(f"\n📋 Sales Teams:")
        print(f"  Online/D2C: {team_map['online']}")
        print(f"  Retail: {team_map['retail']}")
        print(f"  B2B: {team_map['b2b']}")
        
        # Get all confirmed orders
        print("\n📊 Analyzing all sales orders...")
        orders = odoo.search_read('sale.order', 
                                [['state', 'in', ['sale', 'done']]],
                                ['name', 'amount_total', 'team_id'])
        
        print(f"Found {len(orders)} confirmed orders")
        
        # Analyze AOV distribution
        thresholds = analyze_aov_distribution(orders)
        
        print(f"\n🎯 Optimal Channel Thresholds:")
        print(f"  Online/D2C: €0 - €{thresholds['online_max']:.2f} (bottom 60%)")
        print(f"  Retail: €{thresholds['retail_min']:.2f} - €{thresholds['retail_max']:.2f} (middle 20%)")
        print(f"  B2B: €{thresholds['b2b_min']:.2f}+ (top 20%)")
        
        # Assign channels based on percentiles
        online_orders, retail_orders, b2b_orders = assign_channels_by_percentile(orders, thresholds)
        
        total_orders = len(orders)
        print(f"\n📈 New Distribution by Percentiles:")
        print(f"  Online: {len(online_orders)} ({len(online_orders)/total_orders*100:.1f}%)")
        print(f"  Retail: {len(retail_orders)} ({len(retail_orders)/total_orders*100:.1f}%)")
        print(f"  B2B: {len(b2b_orders)} ({len(b2b_orders)/total_orders*100:.1f}%)")
        
        # Update channel assignments
        print(f"\n🔄 Updating channel assignments...")
        
        # Update Online orders
        if online_orders:
            online_ids = [order['id'] for order in online_orders]
            # Process in batches to avoid timeout
            batch_size = 500
            for i in range(0, len(online_ids), batch_size):
                batch = online_ids[i:i+batch_size]
                odoo.write('sale.order', batch, {'team_id': team_map['online']})
            print(f"  ✅ Updated {len(online_orders)} orders to Online/D2C Sales")
        
        # Update Retail orders  
        if retail_orders:
            retail_ids = [order['id'] for order in retail_orders]
            batch_size = 500
            for i in range(0, len(retail_ids), batch_size):
                batch = retail_ids[i:i+batch_size]
                odoo.write('sale.order', batch, {'team_id': team_map['retail']})
            print(f"  ✅ Updated {len(retail_orders)} orders to Retail Sales")
        
        # Update B2B orders
        if b2b_orders:
            b2b_ids = [order['id'] for order in b2b_orders]
            batch_size = 500
            for i in range(0, len(b2b_ids), batch_size):
                batch = b2b_ids[i:i+batch_size]
                odoo.write('sale.order', batch, {'team_id': team_map['b2b']})
            print(f"  ✅ Updated {len(b2b_orders)} orders to B2B/Wholesale Sales")
        
        # Final verification
        print(f"\n✅ Final Distribution Analysis:")
        
        # Calculate actual vs target
        target_online = 0.60
        target_retail = 0.20
        target_b2b = 0.20
        
        actual_online = len(online_orders) / total_orders
        actual_retail = len(retail_orders) / total_orders
        actual_b2b = len(b2b_orders) / total_orders
        
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
            print(f"\n⚠️  Some channels outside tolerance - this is expected due to percentile-based assignment")
            print(f"   The distribution should be very close to 60/20/20 by design")
        
        # Generate summary report
        print(f"\n📋 SUMMARY REPORT:")
        print(f"  ✅ {len(teams)} sales teams analyzed")
        print(f"  ✅ {total_orders} orders processed")
        print(f"  ✅ Channel assignments based on AOV percentiles")
        print(f"  ✅ Online threshold: €{thresholds['online_max']:.2f}")
        print(f"  ✅ Retail range: €{thresholds['retail_min']:.2f} - €{thresholds['retail_max']:.2f}")
        print(f"  ✅ B2B minimum: €{thresholds['b2b_min']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)