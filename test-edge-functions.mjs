// Quick test to verify edge functions are working
const supabaseUrl = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testPurchaseOrdersFunction() {
  console.log('Testing purchase-orders edge function...\n');
  
  try {
    const response = await fetch(`${supabaseUrl}/functions/v1/purchase-orders`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${supabaseAnonKey}`,
        'x-application-name': 'animal-farmacy',
        'apikey': supabaseAnonKey
      },
      body: JSON.stringify({
        method: 'search_read',
        model: 'res.partner',
        domain: [['supplier_rank', '>', 0]],
        fields: ['id', 'name', 'email', 'street', 'city'],
        limit: 5
      })
    });

    const text = await response.text();
    console.log('Response status:', response.status);
    
    if (response.ok) {
      const data = JSON.parse(text);
      console.log('✅ SUCCESS! Edge function is working.\n');
      console.log('Suppliers found:', data.partners?.length || 0);
      if (data.partners && data.partners.length > 0) {
        console.log('\nFirst few suppliers:');
        data.partners.slice(0, 3).forEach(s => {
          console.log(`- ${s.name} (ID: ${s.id})`);
        });
      }
    } else {
      console.log('❌ ERROR:', text);
    }
  } catch (error) {
    console.error('❌ Request failed:', error.message);
  }
}

async function testProductSearch() {
  console.log('\n\nTesting product-search edge function...\n');
  
  try {
    const response = await fetch(`${supabaseUrl}/functions/v1/product-search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${supabaseAnonKey}`,
        'apikey': supabaseAnonKey
      },
      body: JSON.stringify({
        query: 'oil',
        search_type: 'single'
      })
    });

    const text = await response.text();
    console.log('Response status:', response.status);
    
    if (response.ok) {
      const data = JSON.parse(text);
      console.log('✅ SUCCESS! Product search is working.\n');
      console.log('Products found:', data.products?.length || 0);
      if (data.products && data.products.length > 0) {
        console.log('\nFirst few products:');
        data.products.slice(0, 3).forEach(p => {
          console.log(`- ${p.name} (Price: $${p.list_price})`);
        });
      }
    } else {
      console.log('❌ ERROR:', text);
    }
  } catch (error) {
    console.error('❌ Request failed:', error.message);
  }
}

// Run tests
testPurchaseOrdersFunction().then(() => testProductSearch());