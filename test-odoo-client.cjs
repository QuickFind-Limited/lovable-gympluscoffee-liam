// Test the OdooClient class directly with same parameters as edge function
const xmlrpc = require('xmlrpc');

// Simulate the OdooClient class  
class OdooClient {
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

  async execute(model, method, args) {
    if (!this.uid) {
      await this.connect();
    }

    console.log(`OdooClient.execute: ${model}.${method}`);
    console.log('Args:', JSON.stringify(args, null, 2));

    const object = this.createClient(`${this.url}/xmlrpc/2/object`);
    const result = await object.methodCall('execute_kw', [
      this.db,
      this.uid,
      this.password,
      model,
      method,
      args
    ]);
    
    console.log('OdooClient.execute result length:', result?.length || 'null/undefined');
    if (result && result.length > 0) {
      console.log('First result:', JSON.stringify(result[0], null, 2));
    }
    return result;
  }

  async searchRead(model, domain = [], fields = [], offset = 0, limit = 100) {
    // Always include fields to avoid memory errors
    const fieldsToUse = fields.length > 0 ? fields : ['id', 'name'];
    
    console.log(`\n🔵 OdooClient.searchRead: ${model} with domain:`, JSON.stringify(domain));
    console.log(`Fields:`, fieldsToUse, `Offset:`, offset, `Limit:`, limit);
    
    // This is exactly what the edge function does
    const result = await this.execute(model, 'search_read', [
      domain,  // domain as first parameter
      {        // options as second parameter object
        fields: fieldsToUse,
        offset: offset,
        limit: limit
      }
    ]);
    
    console.log(`OdooClient.searchRead result:`, result?.length || 0, 'records');
    return result || [];
  }

  async searchCount(model, domain = []) {
    return await this.execute(model, 'search_count', [domain]);
  }
}

async function testOdooClient() {
  try {
    console.log('🔵 Testing OdooClient searchRead (same as edge function)...');
    
    const odoo = new OdooClient();
    await odoo.connect();
    console.log('✅ Connected to Odoo');

    // Test the exact same call as in supplier-catalog edge function
    const supplierId = 25;
    console.log(`\n🔵 Testing searchRead for supplier ${supplierId}...`);
    
    // This is EXACTLY what the edge function does (line 49-55)
    const products = await odoo.searchRead(
      'product.supplierinfo',
      [['partner_id', '=', parseInt(supplierId)]],
      ['id', 'product_id', 'product_name', 'product_code', 'price', 'min_qty', 'delay'],
      0,
      10
    );

    console.log(`\n✅ searchRead returned ${products.length} products`);
    if (products.length > 0) {
      console.log('First 2 products:', JSON.stringify(products.slice(0, 2), null, 2));
    } else {
      console.log('❌ NO PRODUCTS RETURNED - This is the bug!');
    }

    // Also test searchCount for comparison
    console.log(`\n🔵 Testing searchCount for comparison...`);
    const count = await odoo.searchCount(
      'product.supplierinfo', 
      [['partner_id', '=', parseInt(supplierId)]]
    );
    console.log(`✅ searchCount returned: ${count} products`);

    // Test with minimal fields
    console.log(`\n🔵 Testing searchRead with minimal fields...`);
    const minimalProducts = await odoo.searchRead(
      'product.supplierinfo',
      [['partner_id', '=', parseInt(supplierId)]],
      ['id', 'partner_id'],
      0,
      5
    );
    console.log(`✅ Minimal searchRead returned ${minimalProducts.length} products`);

  } catch (error) {
    console.error('❌ Error:', error.message);
    console.error('Stack:', error.stack);
  }
}

testOdooClient();