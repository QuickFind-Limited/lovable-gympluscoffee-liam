// Test finding the specific Acralube product by ID and then by search
const SUPABASE_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testSpecificProduct() {
  try {
    console.log('Testing if we can find the Acralube product (ID 45)...');
    
    // First, try to find it by searching for products with ID 45
    const response = await fetch(`${SUPABASE_URL}/functions/v1/odoo-product-search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${ANON_KEY}`,
      },
      body: JSON.stringify({
        // Use multi search to test our actual search path
        parsed_query: {
          products: [{
            product_description: "45", // Try searching by ID
            quantity: 1
          }]
        },
        search_type: 'multi'
      })
    });
    
    console.log('Response status:', response.status);
    const data = await response.json();
    console.log('Search by ID "45":', JSON.stringify(data, null, 2));
    
    // Try various terms that might match "Acralube 5Ltr"
    const searchTerms = ['Acralube', 'acralube', '5Ltr', '5', 'Ltr', 'AcraLube'];
    
    for (const term of searchTerms) {
      console.log(`\\n=== Testing "${term}" ===`);
      
      const testResponse = await fetch(`${SUPABASE_URL}/functions/v1/odoo-product-search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${ANON_KEY}`,
        },
        body: JSON.stringify({
          query: term,
          search_type: 'single'
        })
      });
      
      const testData = await testResponse.json();
      console.log(`Results for "${term}": ${testData.products ? testData.products.length : 0} products`);
      
      if (testData.products && testData.products.length > 0) {
        console.log('Found products:');
        testData.products.forEach(p => {
          console.log(`- ID: ${p.id}, Name: "${p.name}", Display: "${p.display_name}"`);
        });
      }
      
      await new Promise(resolve => setTimeout(resolve, 300)); // Small delay
    }
    
  } catch (error) {
    console.error('Error testing specific product:', error);
  }
}

testSpecificProduct();