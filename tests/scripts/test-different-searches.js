// Test different search terms to see what's in the Odoo database
const SUPABASE_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testSearchTerm(term) {
  try {
    console.log(`\\n=== Testing "${term}" ===`);
    
    const response = await fetch(`${SUPABASE_URL}/functions/v1/odoo-product-search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${ANON_KEY}`,
      },
      body: JSON.stringify({
        query: term,
        search_type: 'single'
      })
    });
    
    const data = await response.json();
    console.log(`Results: ${data.products ? data.products.length : 0} products found`);
    
    if (data.products && data.products.length > 0) {
      console.log('First few products:');
      data.products.slice(0, 3).forEach(p => {
        console.log(`- ${p.display_name || p.name} (ID: ${p.id})`);
      });
    }
    
  } catch (error) {
    console.error(`Error testing "${term}":`, error.message);
  }
}

async function runTests() {
  const searchTerms = [
    'acralube',
    'Acralube',
    'ACRALUBE',
    '5Ltr',
    'lube',
    'oil',
    'product',
    'a', // Very broad search
    ''   // Empty search to see if it returns anything
  ];
  
  for (const term of searchTerms) {
    await testSearchTerm(term);
    await new Promise(resolve => setTimeout(resolve, 500)); // Small delay between requests
  }
}

runTests();