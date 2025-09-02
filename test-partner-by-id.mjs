// Test getting partner by ID
const supabaseUrl = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testPartnerById() {
  try {
    console.log('Testing read partner by ID 25 (FastPet Logistics)...\n');
    
    const response = await fetch(`${supabaseUrl}/functions/v1/purchase-orders`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${supabaseAnonKey}`,
        'x-application-name': 'animal-farmacy',
        'apikey': supabaseAnonKey
      },
      body: JSON.stringify({
        method: 'read',
        model: 'res.partner',
        ids: [25],
        fields: [
          'id', 'name', 'email', 'street', 'street2', 
          'city', 'state_id', 'zip', 'country_id', 
          'phone', 'vat', 'supplier_rank'
        ]
      })
    });
    
    const text = await response.text();
    console.log('Response status:', response.status);
    
    if (!response.ok) {
      console.error('\n❌ ERROR Response:');
      console.error(text);
      return;
    }
    
    const data = JSON.parse(text);
    console.log('\n✅ Success! Partner data:', JSON.stringify(data, null, 2));
    
  } catch (error) {
    console.error('\n❌ Full error:', error);
  }
}

testPartnerById();