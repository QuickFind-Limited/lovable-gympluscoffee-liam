// Test the debug function to see what products exist in Odoo
const SUPABASE_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testDebugFunction() {
  try {
    console.log('Testing debug function to see what products exist...');
    
    const response = await fetch(`${SUPABASE_URL}/functions/v1/debug-odoo-products`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${ANON_KEY}`,
      },
      body: JSON.stringify({})
    });
    
    console.log('Response status:', response.status);
    const data = await response.json();
    console.log('Debug results:', JSON.stringify(data, null, 2));
    
  } catch (error) {
    console.error('Error testing debug function:', error);
  }
}

testDebugFunction();