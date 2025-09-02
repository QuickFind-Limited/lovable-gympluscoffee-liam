import fetch from 'node-fetch';

const supabaseUrl = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const anonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testFilters() {
  console.log('Testing filter data endpoint...\n');
  
  // Test fetching categories
  console.log('1. Fetching categories:');
  try {
    const response = await fetch(`${supabaseUrl}/functions/v1/odoo-filters-data`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${anonKey}`,
      },
      body: JSON.stringify({ filter_type: 'categories' })
    });
    
    if (!response.ok) {
      console.error(`  ❌ Error (${response.status}):`, await response.text());
    } else {
      const data = await response.json();
      console.log(`  ✅ Success! Found ${data.categories?.length || 0} categories`);
      if (data.categories) {
        data.categories.slice(0, 5).forEach(cat => {
          console.log(`     - ID: ${cat.id}, Name: ${cat.name}`);
        });
      }
    }
  } catch (error) {
    console.error(`  ❌ Exception:`, error.message);
  }
  
  // Test fetching products with category filter
  console.log('\n2. Testing product search with category filter:');
  try {
    const response = await fetch(`${supabaseUrl}/functions/v1/odoo-simple-test`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${anonKey}`,
      },
      body: JSON.stringify({
        search: '',
        offset: 0,
        limit: 5,
        category: 1, // Test with category ID 1
        vendor: null
      })
    });
    
    if (!response.ok) {
      console.error(`  ❌ Error (${response.status}):`, await response.text());
    } else {
      const data = await response.json();
      console.log(`  Response:`, JSON.stringify(data, null, 2));
    }
  } catch (error) {
    console.error(`  ❌ Exception:`, error.message);
  }
  
  // Test max price
  console.log('\n3. Fetching max price:');
  try {
    const response = await fetch(`${supabaseUrl}/functions/v1/odoo-filters-data`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${anonKey}`,
      },
      body: JSON.stringify({ filter_type: 'max_price' })
    });
    
    if (!response.ok) {
      console.error(`  ❌ Error (${response.status}):`, await response.text());
    } else {
      const data = await response.json();
      console.log(`  ✅ Max price:`, data.max_price);
    }
  } catch (error) {
    console.error(`  ❌ Exception:`, error.message);
  }
}

testFilters().catch(console.error);