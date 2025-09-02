// Test exact supplier name search
const supabaseUrl = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testSupplierSearch(supplierName) {
  try {
    console.log(`Testing search for supplier: "${supplierName}"\n`);
    
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
        domain: [
          ['supplier_rank', '>', 0],
          ['name', '=', supplierName]  // Use exact match
        ],
        fields: [
          'id', 'name', 'email', 'street', 'street2', 
          'city', 'state_id', 'zip', 'country_id', 
          'phone', 'vat'
        ],
        limit: 1
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
    console.log('\n✅ Success! Response:', JSON.stringify(data, null, 2));
    
  } catch (error) {
    console.error('\n❌ Full error:', error);
  }
}

// Test exact match
testSupplierSearch('FastPet Logistics');