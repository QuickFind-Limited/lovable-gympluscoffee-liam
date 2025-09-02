// Direct test of edge function
const supabaseUrl = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testEdgeFunction() {
  try {
    console.log('Testing purchase-orders edge function...\n');
    
    // Test basic partner search
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
        domain: [['is_company', '=', true]],
        fields: ['id', 'name'],
        limit: 5
      })
    });

    console.log('Response status:', response.status);
    const text = await response.text();
    console.log('Response body:', text);
    
    if (response.ok) {
      const data = JSON.parse(text);
      console.log('\nPartners found:', data?.partners || []);
    }

  } catch (error) {
    console.error('Test failed:', error);
  }
}

testEdgeFunction();