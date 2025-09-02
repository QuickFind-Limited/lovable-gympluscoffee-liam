// Debug script to compare XML-RPC serialization
const xmlrpc = require('xmlrpc');

// Test what the working Node.js library generates
console.log('=== NODE.JS XMLRPC LIBRARY XML OUTPUT ===');

// Create a custom client that logs the XML being sent
const originalRequest = require('http').request;
require('http').request = function(options, callback) {
  const req = originalRequest.call(this, options, callback);
  const originalWrite = req.write;
  req.write = function(data) {
    if (typeof data === 'string' && data.includes('<methodCall>')) {
      console.log('Node.js xmlrpc XML:\n', data);
    }
    return originalWrite.call(this, data);
  };
  return req;
};

async function testNodejsXmlrpc() {
  try {
    const config = {
      url: 'https://source-animalfarmacy.odoo.com',
      db: 'source-animalfarmacy',
      username: 'admin@quickfindai.com',
      password: 'BJ62wX2J4yzjS$i'
    };

    // Authenticate first
    const common = xmlrpc.createClient({ url: `${config.url}/xmlrpc/2/common` });
    const uid = await new Promise((resolve, reject) => {
      common.methodCall('authenticate', [config.db, config.username, config.password, {}], (err, result) => {
        if (err) reject(err);
        else resolve(result);
      });
    });

    console.log('✅ Authenticated, UID:', uid);

    // Now make the search_read call and capture XML
    const object = xmlrpc.createClient({ url: `${config.url}/xmlrpc/2/object` });
    
    console.log('\n🔵 Making search_read call (this will show the XML)...');
    
    const products = await new Promise((resolve, reject) => {
      object.methodCall('execute_kw', [
        config.db, uid, config.password,
        'product.supplierinfo', 'search_read',
        [[['partner_id', '=', 25]]],  // domain wrapped in array
        {'fields': ['id', 'product_name'], 'limit': 3}  // options object
      ], (err, result) => {
        if (err) reject(err);
        else resolve(result);
      });
    });

    console.log(`\n✅ Got ${products.length} products`);
    
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

testNodejsXmlrpc();