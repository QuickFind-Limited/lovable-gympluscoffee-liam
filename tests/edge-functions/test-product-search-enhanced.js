// Test script for product-search-enhanced edge function
const SUPABASE_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjkxNDczODUsImV4cCI6MjA0NDcyMzM4NX0.K30AQNnPWJhK-yLEQX7NGXeJ_v2KqCUAON2FdOMhBeE';

async function testProductSearch(query) {
  console.log(`\n🔍 Testing search for: "${query}"`);
  
  try {
    const response = await fetch(`${SUPABASE_URL}/functions/v1/product-search-enhanced`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
      },
      body: JSON.stringify({ query })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    
    console.log(`\n✅ Found ${data.products?.length || 0} products\n`);
    
    if (data.products && data.products.length > 0) {
      data.products.slice(0, 3).forEach((product, index) => {
        console.log(`Product ${index + 1}:`);
        console.log(`  Name: ${product.name || product.display_name}`);
        console.log(`  Supplier: ${product.supplier || product.supplier_name || product.vendor || 'Not found'}`);
        console.log(`  Price: $${product.list_price || 0}`);
        console.log(`  Has supplier info: ${product.supplier_name ? 'YES ✓' : 'NO ✗'}`);
        console.log('');
      });
    }
    
    // Check if any products still have "Odoo Product" as supplier
    const odooProductCount = data.products?.filter(p => 
      p.supplier === 'Odoo Product' || 
      p.supplier_name === 'Odoo Product' || 
      p.vendor === 'Odoo Product'
    ).length || 0;
    
    if (odooProductCount > 0) {
      console.log(`⚠️  WARNING: ${odooProductCount} products still have "Odoo Product" as supplier!`);
    } else {
      console.log('✅ No products have "Odoo Product" as supplier - Fix is working!');
    }
    
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

// Run tests
async function runTests() {
  console.log('=== Testing Product Search Enhanced Edge Function ===\n');
  
  await testProductSearch('acralube');
  await testProductSearch('I need acralube');
  await testProductSearch('oil');
  await testProductSearch('cream');
}

runTests();