// Test the fixed odoo-product-search function
const SUPABASE_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testFixedSearch() {
  try {
    console.log('=== TESTING FIXED odoo-product-search (without image_1920 field) ===\n');
    
    // Test 1: Search for "acra" (should find Acralube)
    console.log('Test 1: Searching for "acra"...');
    const response1 = await fetch(`${SUPABASE_URL}/functions/v1/odoo-product-search`, {
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
    
    console.log('Response status:', response1.status);
    const data1 = await response1.json();
    console.log('Response data:', JSON.stringify(data1, null, 2));
    
    if (data1.products && data1.products.length > 0) {
      console.log('\n✅ SUCCESS! Found', data1.products.length, 'products:');
      data1.products.forEach(p => {
        console.log(`  - ID: ${p.id}, Name: "${p.name}"`);
      });
    } else {
      console.log('\n❌ No products found');
    }
    
    console.log('\n' + '='.repeat(80) + '\n');
    
    // Test 2: Search for "adjustable" 
    console.log('Test 2: Searching for "adjustable"...');
    const response2 = await fetch(`${SUPABASE_URL}/functions/v1/odoo-product-search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${ANON_KEY}`,
      },
      body: JSON.stringify({
        query: 'adjustable',
        search_type: 'single'
      })
    });
    
    console.log('Response status:', response2.status);
    const data2 = await response2.json();
    
    if (data2.products && data2.products.length > 0) {
      console.log('\n✅ Found', data2.products.length, 'products:');
      data2.products.forEach(p => {
        console.log(`  - ID: ${p.id}, Name: "${p.name}"`);
      });
    } else {
      console.log('\n❌ No products found');
    }
    
    console.log('\n' + '='.repeat(80) + '\n');
    
    // Test 3: Search for full product name
    console.log('Test 3: Searching for "Acralube 5Ltr"...');
    const response3 = await fetch(`${SUPABASE_URL}/functions/v1/odoo-product-search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${ANON_KEY}`,
      },
      body: JSON.stringify({
        query: 'Acralube 5Ltr',
        search_type: 'single'
      })
    });
    
    console.log('Response status:', response3.status);
    const data3 = await response3.json();
    
    if (data3.products && data3.products.length > 0) {
      console.log('\n✅ Found', data3.products.length, 'products:');
      data3.products.forEach(p => {
        console.log(`  - ID: ${p.id}, Name: "${p.name}"`);
      });
    } else {
      console.log('\n❌ No products found');
    }
    
  } catch (error) {
    console.error('Error testing search:', error);
  }
}

testFixedSearch();