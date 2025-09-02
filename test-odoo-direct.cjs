// Direct Odoo XML-RPC test to find the issue
const xmlrpc = require('xmlrpc');

const config = {
  url: 'https://source-animalfarmacy.odoo.com',
  db: 'source-animalfarmacy',
  username: 'admin@quickfindai.com',
  password: 'BJ62wX2J4yzjS$i'
};

async function testOdooDirectly() {
  try {
    console.log('🔵 Testing direct Odoo XML-RPC connection...');
    
    // Step 1: Authenticate
    const common = xmlrpc.createClient({ url: `${config.url}/xmlrpc/2/common` });
    const uid = await new Promise((resolve, reject) => {
      common.methodCall('authenticate', [config.db, config.username, config.password, {}], (err, result) => {
        if (err) reject(err);
        else resolve(result);
      });
    });
    
    console.log('✅ Authentication successful, UID:', uid);
    
    // Step 2: Test search_count (this works)
    const object = xmlrpc.createClient({ url: `${config.url}/xmlrpc/2/object` });
    const count = await new Promise((resolve, reject) => {
      object.methodCall('execute_kw', [
        config.db, uid, config.password,
        'product.supplierinfo', 'search_count',
        [[['partner_id', '=', 25]]]  // Test with supplier 25
      ], (err, result) => {
        if (err) reject(err);
        else resolve(result);
      });
    });
    
    console.log('✅ search_count result:', count, 'products for supplier 25');
    
    // Step 3: Test search_read with MINIMAL parameters (this should work)
    console.log('🔵 Testing search_read with minimal parameters...');
    const products1 = await new Promise((resolve, reject) => {
      object.methodCall('execute_kw', [
        config.db, uid, config.password,
        'product.supplierinfo', 'search_read',
        [[['partner_id', '=', 25]]],  // Just domain
        {'fields': ['id'], 'limit': 3}  // Minimal fields
      ], (err, result) => {
        if (err) reject(err);
        else resolve(result);
      });
    });
    
    console.log('✅ search_read (minimal):', products1.length, 'products:', JSON.stringify(products1.slice(0, 2), null, 2));
    
    // Step 4: Test search_read with MORE fields
    console.log('🔵 Testing search_read with more fields...');
    const products2 = await new Promise((resolve, reject) => {
      object.methodCall('execute_kw', [
        config.db, uid, config.password,
        'product.supplierinfo', 'search_read',
        [[['partner_id', '=', 25]]],
        {'fields': ['id', 'partner_id', 'product_id', 'product_name'], 'limit': 3}
      ], (err, result) => {
        if (err) reject(err);
        else resolve(result);
      });
    });
    
    console.log('✅ search_read (more fields):', products2.length, 'products:', JSON.stringify(products2.slice(0, 2), null, 2));
    
    // Step 5: Test WITHOUT options object (alternative format)
    console.log('🔵 Testing search_read without options object...');
    const products3 = await new Promise((resolve, reject) => {
      object.methodCall('execute_kw', [
        config.db, uid, config.password,
        'product.supplierinfo', 'search_read',
        [[['partner_id', '=', 25]], ['id', 'partner_id'], 0, 3]  // domain, fields, offset, limit as separate params
      ], (err, result) => {
        if (err) reject(err);
        else resolve(result);
      });
    });
    
    console.log('✅ search_read (separate params):', products3.length, 'products:', JSON.stringify(products3.slice(0, 2), null, 2));
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    console.error('Stack:', error.stack);
  }
}

testOdooDirectly();