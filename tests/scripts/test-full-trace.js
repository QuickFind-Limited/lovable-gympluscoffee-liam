// Test with full trace logging
const SUPABASE_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testFullTrace() {
  try {
    console.log('=== TESTING WITH FULL TRACE ===\n');
    
    // Test 1: Working test mode
    console.log('Test 1: Working test mode (should match test-simple-odoo)');
    const response1 = await fetch(`${SUPABASE_URL}/functions/v1/debug-full-trace`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${ANON_KEY}`,
      },
      body: JSON.stringify({
        function_type: 'working_test'
      })
    });
    
    const data1 = await response1.json();
    console.log('Result count:', data1.result_count);
    console.log('\nLOGS:');
    data1.logs.forEach(log => console.log(log));
    
    console.log('\n' + '='.repeat(80) + '\n');
    
    // Test 2: Regular search mode
    console.log('Test 2: Regular search mode (same as odoo-product-search)');
    const response2 = await fetch(`${SUPABASE_URL}/functions/v1/debug-full-trace`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${ANON_KEY}`,
      },
      body: JSON.stringify({
        function_type: 'search',
        query: 'acra'
      })
    });
    
    const data2 = await response2.json();
    console.log('Result count:', data2.result_count);
    console.log('\nLOGS:');
    data2.logs.forEach(log => console.log(log));
    
    console.log('\n=== COMPARISON ===');
    console.log('Working test found:', data1.result_count, 'products');
    console.log('Regular search found:', data2.result_count, 'products');
    
  } catch (error) {
    console.error('Error in full trace test:', error);
  }
}

testFullTrace();