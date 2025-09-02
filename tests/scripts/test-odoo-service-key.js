// Test odoo-product-search with service role key
const SUPABASE_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const SERVICE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Mzk3MTQ4MiwiZXhwIjoyMDY5NTQ3NDgyfQ.QYVdeKW3BvqOWYcF8L_mjpNjX-wTQFDfEFi0FtHO5pI';

async function testOdooWithServiceKey() {
  try {
    console.log('Testing odoo-product-search with service key and "acralube"...');
    
    const response = await fetch(`${SUPABASE_URL}/functions/v1/odoo-product-search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${SERVICE_KEY}`,
      },
      body: JSON.stringify({
        query: 'acralube',
        search_type: 'single'
      })
    });
    
    console.log('Response status:', response.status);
    
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
    
  } catch (error) {
    console.error('Error testing:', error);
  }
}

testOdooWithServiceKey();