// Test the simplest possible search like the debug function
const SUPABASE_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testSimpleSearch() {
  try {
    console.log('Testing simple search with "acra" term...');
    
    const response = await fetch(`${SUPABASE_URL}/functions/v1/odoo-product-search`, {
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
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Error response:', errorText);
      return;
    }
    
    const data = await response.json();
    console.log('Raw response:', JSON.stringify(data, null, 2));
    
    if (data.products && data.products.length > 0) {
      console.log('SUCCESS! Found products:');
      data.products.forEach(p => {
        console.log(`- ID: ${p.id}, Name: "${p.name}", Display: "${p.display_name}"`);
      });
    } else {
      console.log('No products found :(');
    }
    
  } catch (error) {
    console.error('Error testing simple search:', error);
  }
}

testSimpleSearch();