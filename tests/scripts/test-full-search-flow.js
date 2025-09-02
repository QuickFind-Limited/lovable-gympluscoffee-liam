// Test the full search flow: openai-search-updated -> parse-query -> odoo-product-search
const SUPABASE_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testFullSearchFlow() {
  try {
    console.log('Testing full search flow with "I want acralube"...');
    
    const response = await fetch(`${SUPABASE_URL}/functions/v1/openai-search-updated`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${ANON_KEY}`,
      },
      body: JSON.stringify({
        query: 'I want acralube'
      })
    });
    
    console.log('Response status:', response.status);
    console.log('Response headers:', Object.fromEntries(response.headers.entries()));
    
    const data = await response.json();
    console.log('Raw response data:', JSON.stringify(data, null, 2));
    
    if (data.products) {
      console.log('Products type:', typeof data.products);
      console.log('Products count:', data.products.length);
      console.log('Is array?', Array.isArray(data.products));
      
      if (data.products.length > 0) {
        console.log('First product:', data.products[0]);
      }
    }
    
    if (data.debug) {
      console.log('Debug info:', data.debug);
    }
    
  } catch (error) {
    console.error('Error testing:', error);
  }
}

testFullSearchFlow();