// Debug script to test our custom XML-RPC client and see what XML it generates
import { createClient } from './supabase/functions/_shared/xmlrpc-client.ts';

async function testCustomXmlrpc() {
  try {
    console.log('=== TESTING CUSTOM XML-RPC CLIENT ===');
    
    const config = {
      url: 'https://source-animalfarmacy.odoo.com',
      db: 'source-animalfarmacy',
      username: 'admin@quickfindai.com',
      password: 'BJ62wX2J4yzjS$i'
    };

    // Test authentication first
    console.log('🔵 Testing authentication...');
    const common = createClient(`${config.url}/xmlrpc/2/common`);
    
    const uid = await common.methodCall('authenticate', [
      config.db,
      config.username,
      config.password,
      {}
    ]);

    console.log('✅ Authenticated, UID:', uid);

    // Test the problematic search_read call
    console.log('\n🔵 Testing search_read call...');
    const object = createClient(`${config.url}/xmlrpc/2/object`);
    
    const domain = [['partner_id', '=', 25]];
    const fields = ['id', 'product_name'];
    const options = { fields: fields, limit: 3 };
    
    console.log('Parameters:');
    console.log('- domain:', JSON.stringify(domain));
    console.log('- fields:', JSON.stringify(fields));
    console.log('- options:', JSON.stringify(options));
    
    const result = await object.methodCall('execute_kw', [
      config.db,
      uid,
      config.password,
      'product.supplierinfo',
      'search_read',
      [domain],  // args: domain wrapped in array
      options    // kwargs: options as separate parameter
    ]);

    console.log(`\n✅ Got ${result?.length || 0} products`);
    if (result && result.length > 0) {
      console.log('First product:', JSON.stringify(result[0], null, 2));
    }
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    console.error('Stack:', error.stack);
  }
}

testCustomXmlrpc();