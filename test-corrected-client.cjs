// Test the CORRECTED OdooClient searchRead method
const xmlrpc = require('xmlrpc');

// Simulate the corrected Supabase XmlRpcClient
class CorrectedSupabaseClient {
  constructor() {
    this.url = 'https://source-animalfarmacy.odoo.com';
    this.db = 'source-animalfarmacy';
    this.username = 'admin@quickfindai.com';
    this.password = 'BJ62wX2J4yzjS$i';
    this.uid = null;
  }

  createClient(endpoint) {
    return {
      methodCall: (method, params) => {
        return new Promise((resolve, reject) => {
          const client = xmlrpc.createClient({ url: endpoint });
          client.methodCall(method, params, (err, result) => {
            if (err) reject(err);
            else resolve(result);
          });
        });
      }
    };
  }

  async connect() {
    if (this.uid) return this.uid;

    const common = this.createClient(`${this.url}/xmlrpc/2/common`);
    this.uid = await common.methodCall('authenticate', [
      this.db,
      this.username,
      this.password,
      {}
    ]);

    if (!this.uid) {
      throw new Error('Authentication failed');
    }

    return this.uid;
  }

  async searchRead(model, domain = [], fields = [], offset = 0, limit = 100) {
    const fieldsToUse = fields.length > 0 ? fields : ['id', 'name'];
    
    console.log(`\n🔵 CORRECTED searchRead: ${model} with domain:`, JSON.stringify(domain));
    console.log(`Fields:`, fieldsToUse, `Offset:`, offset, `Limit:`, limit);
    
    if (!this.uid) {
      await this.connect();
    }

    const object = this.createClient(`${this.url}/xmlrpc/2/object`);
    
    console.log('📞 CORRECTED XML-RPC call parameters:');
    console.log('1. db:', this.db);
    console.log('2. uid:', this.uid);
    console.log('3. password: ***');
    console.log('4. model:', model);
    console.log('5. method: search_read');
    console.log('6. domain (NOT wrapped):', JSON.stringify(domain));
    console.log('7. options:', JSON.stringify({ fields: fieldsToUse, offset, limit }));
    
    const result = await object.methodCall('execute_kw', [
      this.db,
      this.uid,
      this.password,
      model,
      'search_read',
      domain,    // CORRECTED: domain not wrapped in extra array
      {          // options as separate parameter
        fields: fieldsToUse,
        offset: offset,
        limit: limit
      }
    ]);
    
    console.log(`✅ CORRECTED searchRead result:`, result?.length || 0, 'records');
    if (result && result.length > 0) {
      console.log('First result:', JSON.stringify(result[0], null, 2));
    }
    return result || [];
  }
}

async function testCorrectedClient() {
  try {
    console.log('🔵 Testing CORRECTED searchRead (fixed domain wrapping)...');
    
    const odoo = new CorrectedSupabaseClient();
    await odoo.connect();
    console.log('✅ Connected to Odoo');

    // Test the CORRECTED searchRead method
    const supplierId = 25;
    const domain = [['partner_id', '=', parseInt(supplierId)]];
    
    console.log(`\n🔵 Testing CORRECTED searchRead for supplier ${supplierId}...`);
    console.log('Domain before passing:', JSON.stringify(domain));
    
    const products = await odoo.searchRead(
      'product.supplierinfo',
      domain,  // Pass domain directly, don't wrap it
      ['id', 'product_id', 'product_name', 'product_code', 'price'],
      0,
      5
    );

    console.log(`\n🎉 CORRECTED searchRead returned ${products.length} products!`);
    if (products.length > 0) {
      console.log('🎯 SUCCESS! Products found:', JSON.stringify(products.slice(0, 2), null, 2));
    } else {
      console.log('❌ Still no products returned');
    }

  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

testCorrectedClient();