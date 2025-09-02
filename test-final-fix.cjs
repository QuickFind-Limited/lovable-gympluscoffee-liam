// Test the EXACT same structure as the working Node.js direct test
const xmlrpc = require('xmlrpc');

async function testExactWorkingStructure() {
  try {
    console.log('🔵 Testing EXACT same structure as working direct test...');
    
    const config = {
      url: 'https://source-animalfarmacy.odoo.com',
      db: 'source-animalfarmacy',
      username: 'admin@quickfindai.com',
      password: 'BJ62wX2J4yzjS$i'
    };

    // Step 1: Authenticate (same as working test)
    const common = xmlrpc.createClient({ url: `${config.url}/xmlrpc/2/common` });
    const uid = await new Promise((resolve, reject) => {
      common.methodCall('authenticate', [config.db, config.username, config.password, {}], (err, result) => {
        if (err) reject(err);
        else resolve(result);
      });
    });
    
    console.log('✅ Authentication successful, UID:', uid);

    // Step 2: Test the EXACT call that works in direct test (line 44-53)
    const object = xmlrpc.createClient({ url: `${config.url}/xmlrpc/2/object` });
    console.log('🔵 Making EXACT same call as working direct test...');
    console.log('Parameters:');
    console.log('- db:', config.db);
    console.log('- uid:', uid);
    console.log('- password: ***');
    console.log('- model: product.supplierinfo');
    console.log('- method: search_read');
    console.log('- args: [[["partner_id", "=", 25]]]');
    console.log('- options: {"fields": ["id", "product_name"], "limit": 3}');

    const products = await new Promise((resolve, reject) => {
      object.methodCall('execute_kw', [
        config.db, uid, config.password,
        'product.supplierinfo', 'search_read',
        [[['partner_id', '=', 25]]],  // EXACT same as line 47 in working test
        {'fields': ['id', 'product_name'], 'limit': 3}  // EXACT same as line 48
      ], (err, result) => {
        if (err) reject(err);
        else resolve(result);
      });
    });

    console.log(`\n🎉 SUCCESS! Found ${products.length} products:`);
    console.log(JSON.stringify(products, null, 2));

    // Now test what the Supabase edge function is probably sending
    console.log('\n🔵 Now testing what Supabase edge function sends...');
    console.log('This should match the structure above to work');

    // The domain from the edge function call
    const supplierDomain = [['partner_id', '=', 25]];
    const edgeFields = ['id', 'product_id', 'product_name', 'product_code', 'price', 'min_qty', 'delay'];
    
    console.log('Edge function would send:');
    console.log('- args: [supplierDomain] =', JSON.stringify([supplierDomain]));
    console.log('- options:', JSON.stringify({fields: edgeFields, offset: 0, limit: 10}));

    const edgeProducts = await new Promise((resolve, reject) => {
      object.methodCall('execute_kw', [
        config.db, uid, config.password,
        'product.supplierinfo', 'search_read',
        [supplierDomain],  // This is what my fixed code sends
        {fields: edgeFields, offset: 0, limit: 10}
      ], (err, result) => {
        if (err) reject(err);
        else resolve(result);
      });
    });

    console.log(`\n🎯 Edge function structure result: ${edgeProducts.length} products`);
    if (edgeProducts.length > 0) {
      console.log('✅ SUCCESS! This should work in the edge function too!');
      console.log('First product:', JSON.stringify(edgeProducts[0], null, 2));
    } else {
      console.log('❌ Still no products - there must be another issue');
    }

  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

testExactWorkingStructure();