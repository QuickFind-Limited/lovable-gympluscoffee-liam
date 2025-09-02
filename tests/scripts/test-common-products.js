// Test script to find common products
const SUPABASE_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testCommonProducts() {
  const searchTerms = ['oil', 'food', 'dog', 'cat', 'chicken', 'feed', 'seed'];
  
  for (const term of searchTerms) {
    try {
      console.log(`\n=== Searching for "${term}" ===`);
      
      const response = await fetch(`${SUPABASE_URL}/functions/v1/odoo-simple-test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${ANON_KEY}`,
        },
        body: JSON.stringify({
          search: term,
          offset: 0,
          limit: 10
        })
      });
      
      const data = await response.json();
      
      if (data.products && data.products.length > 0) {
        console.log(`Found ${data.products.length} products for "${term}":`);
        data.products.forEach(p => {
          console.log(`- ID: ${p.id}, Name: "${p.name || p.display_name}", Price: $${p.list_price || 0}`);
        });
      } else {
        console.log(`No products found for "${term}"`);
      }
      
      // Small delay between requests
      await new Promise(resolve => setTimeout(resolve, 200));
      
    } catch (error) {
      console.error(`Error searching for "${term}":`, error);
    }
  }
}

testCommonProducts();