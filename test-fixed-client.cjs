// Test the FIXED OdooClient searchRead method
const xmlrpc = require('xmlrpc');

class FixedOdooClient {
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
    // Always include fields to avoid memory errors
    const fieldsToUse = fields.length > 0 ? fields : ['id', 'name'];
    
    console.log(`\n🔵 FixedOdooClient.searchRead: ${model} with domain:`, JSON.stringify(domain));
    console.log(`Fields:`, fieldsToUse, `Offset:`, offset, `Limit:`, limit);
    
    // FIXED: Use direct XML-RPC call with correct parameter structure
    if (!this.uid) {
      await this.connect();
    }

    const object = this.createClient(`${this.url}/xmlrpc/2/object`);
    console.log('📞 Making XML-RPC call with structure:');
    console.log('- Parameter 1-5: db, uid, password, model, method');
    console.log('- Parameter 6: [domain] (args array)');
    console.log('- Parameter 7: options object (separate parameter)');
    
    const result = await object.methodCall('execute_kw', [
      this.db,
      this.uid,
      this.password,
      model,
      'search_read',
      [domain],  // args[0] = domain wrapped in array
      {          // Second parameter = options object (NOT inside args array!)
        fields: fieldsToUse,
        offset: offset,
        limit: limit
      }
    ]);
    
    console.log(`✅ FixedOdooClient.searchRead result:`, result?.length || 0, 'records');
    if (result && result.length > 0) {
      console.log('First result:', JSON.stringify(result[0], null, 2));
    }
    return result || [];
  }
}

async function testFixedClient() {
  try {
    console.log('🔵 Testing FIXED OdooClient searchRead...');
    
    const odoo = new FixedOdooClient();
    await odoo.connect();
    console.log('✅ Connected to Odoo');

    // Test the FIXED searchRead method
    const supplierId = 25;
    console.log(`\n🔵 Testing FIXED searchRead for supplier ${supplierId}...`);
    
    const products = await odoo.searchRead(
      'product.supplierinfo',
      [['partner_id', '=', parseInt(supplierId)]],
      ['id', 'product_id', 'product_name', 'product_code', 'price', 'min_qty', 'delay'],
      0,
      5
    );

    console.log(`\n🎉 FIXED searchRead returned ${products.length} products!`);
    if (products.length > 0) {
      console.log('SUCCESS! First 2 products:', JSON.stringify(products.slice(0, 2), null, 2));
    } else {
      console.log('❌ Still no products returned');
    }

  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

testFixedClient();