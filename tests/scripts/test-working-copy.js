// Test the new working copy function
const SUPABASE_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testWorkingCopy() {
  try {
    console.log('Testing new working copy function with "acra"...');
    
    const response = await fetch(`${SUPABASE_URL}/functions/v1/odoo-search-working`, {
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
      console.log('\nSUCCESS! Working copy found products:');
      data.products.forEach(p => {
        console.log(`- ID: ${p.id}, Name: "${p.name}", Display: "${p.display_name}"`);
      });
    } else {
      console.log('No products found');
      console.log('Available keys:', Object.keys(data));
    }
    
    // Also test multi-search
    console.log('\n=== Testing multi-search ===');
    const multiResponse = await fetch(`${SUPABASE_URL}/functions/v1/odoo-search-working`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${ANON_KEY}`,
      },
      body: JSON.stringify({
        search_type: 'multi',
        parsed_query: {
          products: [
            { product_description: 'acralube', quantity: 1 },
            { product_description: 'adjustable', quantity: 2 }
          ]
        }
      })
    });
    
    const multiData = await multiResponse.json();
    console.log('Multi-search results:', multiData.results ? multiData.results.length : 0, 'items');
    if (multiData.results) {
      multiData.results.forEach((result, idx) => {
        console.log(`Item ${idx + 1} (${result.query.product_description}): ${result.products.length} products found`);
        if (result.products.length > 0) {
          console.log(`  First match: ${result.products[0].name}`);
        }
      });
    }
    
  } catch (error) {
    console.error('Error testing working copy:', error);
  }
}

testWorkingCopy();