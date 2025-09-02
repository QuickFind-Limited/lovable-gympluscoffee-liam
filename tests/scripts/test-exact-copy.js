// Test calling odoo-product-search with the exact same request that works in debug function
const SUPABASE_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testExactCopy() {
  try {
    // Test both the working test function and the main function side by side
    
    console.log('=== TESTING WORKING FUNCTION (test-simple-odoo) ===');
    const workingResponse = await fetch(`${SUPABASE_URL}/functions/v1/test-simple-odoo`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${ANON_KEY}`,
      },
      body: JSON.stringify({})
    });
    
    const workingData = await workingResponse.json();
    console.log('Working function result:', workingData.count, 'products found');
    if (workingData.results && workingData.results.length > 0) {
      workingData.results.forEach(p => {
        console.log(`  - ${p.name} (ID: ${p.id})`);
      });
    }
    
    console.log('\\n=== TESTING MAIN FUNCTION (odoo-product-search) ===');
    const mainResponse = await fetch(`${SUPABASE_URL}/functions/v1/odoo-product-search`, {
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
    
    const mainData = await mainResponse.json();
    console.log('Main function result:', mainData.products ? mainData.products.length : 0, 'products found');
    if (mainData.products && mainData.products.length > 0) {
      mainData.products.forEach(p => {
        console.log(`  - ${p.name} (ID: ${p.id})`);
      });
    }
    
    console.log('\\n=== COMPARISON ===');
    console.log('Working function found:', workingData.count || 0, 'products');
    console.log('Main function found:', mainData.products ? mainData.products.length : 0, 'products');
    
    if (workingData.count > 0 && (!mainData.products || mainData.products.length === 0)) {
      console.log('ERROR: Working function finds products but main function does not!');
      
      // Show the exact domain used by working function
      console.log('Working function domain:', JSON.stringify(workingData.domain));
      
      // Show any error from main function
      if (mainData.error) {
        console.log('Main function error:', mainData.error);
      }
    }
    
  } catch (error) {
    console.error('Error in comparison test:', error);
  }
}

testExactCopy();