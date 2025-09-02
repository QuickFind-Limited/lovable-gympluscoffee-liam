// Test the simple test function
const SUPABASE_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testSimpleFunction() {
  try {
    console.log('Testing simple Odoo function...');
    
    const response = await fetch(`${SUPABASE_URL}/functions/v1/test-simple-odoo`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${ANON_KEY}`,
      },
      body: JSON.stringify({})
    });
    
    console.log('Response status:', response.status);
    
    const data = await response.json();
    console.log('Response data:', JSON.stringify(data, null, 2));
    
    if (data.results && data.results.length > 0) {
      console.log('SUCCESS! Found products with simple function!');
      data.results.forEach(p => {
        console.log(`- ID: ${p.id}, Name: "${p.name}", Display: "${p.display_name}"`);
      });
    } else {
      console.log('Still no products found :(');
    }
    
  } catch (error) {
    console.error('Error testing simple function:', error);
  }
}

testSimpleFunction();