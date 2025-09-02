// Test Odoo connection directly with minimal domain to see if there are ANY products
const SUPABASE_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testOdooDirectConnection() {
  try {
    console.log('Testing minimal search to see if there are ANY products in Odoo...');
    
    // Test with minimal constraints - just search for any product
    const response = await fetch(`${SUPABASE_URL}/functions/v1/odoo-product-search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${ANON_KEY}`,
      },
      body: JSON.stringify({
        // Use multi search with very generic term
        parsed_query: {
          products: [{
            product_description: "any product",
            quantity: 1
          }]
        },
        search_type: 'multi'
      })
    });
    
    console.log('Response status:', response.status);
    const data = await response.json();
    console.log('Raw response:', JSON.stringify(data, null, 2));
    
    if (data.results && data.results.length > 0) {
      const totalProducts = data.results.reduce((sum, result) => sum + (result.products ? result.products.length : 0), 0);
      console.log(`Total products found: ${totalProducts}`);
      
      if (totalProducts > 0) {
        console.log('Sample products:');
        data.results.forEach(result => {
          if (result.products && result.products.length > 0) {
            result.products.slice(0, 3).forEach(p => {
              console.log(`- ${p.display_name || p.name} (ID: ${p.id}, Price: ${p.list_price})`);
            });
          }
        });
      }
    }
    
  } catch (error) {
    console.error('Error testing Odoo:', error);
  }
}

testOdooDirectConnection();