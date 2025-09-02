// Test the working odoo-search function
const SUPABASE_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testWorkingSearch() {
  try {
    console.log('=== TESTING odoo-search-working ===\n');
    
    // Test searching for "acra"
    console.log('Searching for "acra"...');
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
      console.log('\n✅ SUCCESS! Found', data.products.length, 'products:');
      data.products.forEach(p => {
        console.log(`  - ID: ${p.id}, Name: "${p.name}"`);
        console.log(`    Display: "${p.display_name}"`);
        console.log(`    Price: ${p.list_price}`);
        console.log(`    Code: ${p.default_code || 'N/A'}`);
        console.log(`    Stock: ${p.qty_available || 0}`);
      });
    } else {
      console.log('\n❌ No products found');
    }
    
  } catch (error) {
    console.error('Error testing working search:', error);
  }
}

testWorkingSearch();