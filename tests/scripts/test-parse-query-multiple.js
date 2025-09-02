// Test the parse-query edge function with multiple products
const SUPABASE_URL = 'https://rumaiumnoobdyzdxuumt.supabase.co';
const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ1bWFpdW1ub29iZHl6ZHh1dW10Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM1NzU2NTIsImV4cCI6MjA2OTE1MTY1Mn0.QjVlWhix7oY5JFh2BtZIpnOYu1XNZqCUURruHhUJZS8';

async function testParseQuery(query) {
  try {
    console.log(`\nTesting parse-query with: "${query}"`);
    console.log('='.repeat(50));
    
    const response = await fetch(`${SUPABASE_URL}/functions/v1/parse-query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${ANON_KEY}`,
      },
      body: JSON.stringify({ query })
    });

    const result = await response.json();
    console.log('Response status:', response.status);
    
    if (result && result.intent) {
      console.log('\nParsed result:');
      console.log('- Intent:', result.intent);
      console.log('- Is specific order:', result.is_specific_order);
      console.log('- Products count:', result.products.length);
      console.log('\nProducts:');
      result.products.forEach((product, index) => {
        console.log(`  ${index + 1}. "${product.product_description}" - Quantity: ${product.quantity}`);
      });
    } else {
      console.log('Full response:', JSON.stringify(result, null, 2));
    }
  } catch (error) {
    console.error('Test failed:', error);
  }
}

// Test various queries
async function runTests() {
  // Test 1: Single product with quantity
  await testParseQuery("I need 3 red rugs");
  
  // Test 2: Multiple different products
  await testParseQuery("I need 3 red rugs and 2 blue mats");
  
  // Test 3: Multiple products with different quantities
  await testParseQuery("Get me 5 black rugs, 2 white runners, and 1 grey doormat");
  
  // Test 4: Simple multiple request
  await testParseQuery("I want red and blue rugs");
}

runTests();