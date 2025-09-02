import fetch from 'node-fetch';

const supabaseUrl = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const anonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testOpenAISearch() {
  console.log('Testing OpenAI Search Updated function...');
  
  const testQueries = [
    'dog food',
    'cat treats',
    'pet toys',
    'fish tank',
    'bird cage'
  ];
  
  for (const query of testQueries) {
    console.log(`\n\nTesting query: "${query}"`);
    
    try {
      const response = await fetch(`${supabaseUrl}/functions/v1/openai-search-updated`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${anonKey}`,
        },
        body: JSON.stringify({ query })
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`  ❌ Error (${response.status}):`, errorText);
        continue;
      }
      
      const data = await response.json();
      console.log(`  ✅ Success!`);
      console.log(`  Total results: ${data.totalResults}`);
      console.log(`  Products returned: ${data.products?.length || 0}`);
      console.log(`  Search type used: ${data.debug?.searchType || 'unknown'}`);
      console.log(`  Parse query used: ${data.debug?.parsedUsed || false}`);
      
      if (data.products && data.products.length > 0) {
        console.log(`  First 3 products:`);
        data.products.slice(0, 3).forEach((product, i) => {
          console.log(`    ${i + 1}. ${product.name || product.display_name} - $${product.list_price}`);
        });
      }
      
      if (data.suggestions && data.suggestions.length > 0) {
        console.log(`  Suggestions:`, data.suggestions);
      }
    } catch (error) {
      console.error(`  ❌ Exception:`, error.message);
    }
  }
}

// Test the catalog function directly
async function testCatalogFunction() {
  console.log('\n\nTesting Catalog V2 function directly...');
  
  try {
    const response = await fetch(`${supabaseUrl}/functions/v1/odoo-catalog-v2`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${anonKey}`,
      },
      body: JSON.stringify({
        search: 'dog',
        offset: 0,
        limit: 5,
        category: null
      })
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`  ❌ Error (${response.status}):`, errorText);
      return;
    }
    
    const data = await response.json();
    console.log(`  ✅ Success!`);
    console.log(`  Total count: ${data.total_count}`);
    console.log(`  Products returned: ${data.products?.length || 0}`);
    
    if (data.products && data.products.length > 0) {
      console.log(`  Products:`);
      data.products.forEach((product, i) => {
        console.log(`    ${i + 1}. ${product.name || product.display_name} (ID: ${product.id}) - $${product.list_price}`);
      });
    }
  } catch (error) {
    console.error(`  ❌ Exception:`, error.message);
  }
}

async function main() {
  await testCatalogFunction();
  await testOpenAISearch();
}

main().catch(console.error);