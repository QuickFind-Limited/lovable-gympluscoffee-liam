// Test script to find all products
const SUPABASE_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testAllProducts() {
  try {
    console.log('=== Getting all products (no search filter) ===');
    
    const response = await fetch(`${SUPABASE_URL}/functions/v1/odoo-simple-test`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${ANON_KEY}`,
      },
      body: JSON.stringify({
        search: '', // Empty search to get all products
        offset: 0,
        limit: 50
      })
    });
    
    const data = await response.json();
    console.log('Response data:', JSON.stringify(data, null, 2));
    
    if (data.products && data.products.length > 0) {
      console.log(`\nFound ${data.products.length} products total:`);
      data.products.forEach((p, index) => {
        console.log(`${index + 1}. ID: ${p.id}, Name: "${p.name || p.display_name}", Price: $${p.list_price || 0}`);
      });
    } else {
      console.log('No products found');
    }
    
  } catch (error) {
    console.error('Error fetching products:', error);
  }
}

testAllProducts();