// Test the fixed search function
const SUPABASE_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testFixed() {
  try {
    console.log('Testing fixed search function with "acra"...');
    
    const response = await fetch(`${SUPABASE_URL}/functions/v1/odoo-product-search-fixed`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${ANON_KEY}`,
      },
      body: JSON.stringify({
        query: 'acra',
        search_type: 'single'
      })
    });
    
    console.log('Response status:', response.status);
    
    const data = await response.json();
    console.log('Response data:', JSON.stringify(data, null, 2));
    
    if (data.products && data.products.length > 0) {
      console.log('SUCCESS! Fixed function found products:');
      data.products.forEach(p => {
        console.log(`- ID: ${p.id}, Name: "${p.name}", Display: "${p.display_name}"`);
      });
    } else {
      console.log('Still no products found :(');
    }
    
    // Also test with Acralube
    console.log('=== Testing with "Acralube" ===');
    const response2 = await fetch(`${SUPABASE_URL}/functions/v1/odoo-product-search-fixed`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${ANON_KEY}`,
      },
      body: JSON.stringify({
        query: 'Acralube',
        search_type: 'single'
      })
    });
    
    const data2 = await response2.json();
    console.log('Acralube search results:', data2.products ? data2.products.length : 0, 'products');
    if (data2.products && data2.products.length > 0) {
      data2.products.forEach(p => {
        console.log(`- ${p.name} (ID: ${p.id})`);
      });
    }
    
  } catch (error) {
    console.error('Error testing fixed function:', error);
  }
}

testFixed();