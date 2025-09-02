// Test simple supplier search
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
          ['name', '=ilike', '%' + supplierName + '%']  // Use proper ilike syntax
        ],
        fields: [
          'id', 'name', 'email', 'street', 'street2', 
          'city', 'state_id', 'zip', 'country_id', 
          'phone', 'vat'
        ],
        limit: 5
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
    console.log('\n✅ Success! Found', data.partners?.length || 0, 'suppliers');
    
    if (data.partners && data.partners.length > 0) {
      console.log('\nSupplier details:');
      data.partners.forEach((supplier, idx) => {
        console.log(`\n${idx + 1}. ${supplier.name} (ID: ${supplier.id})`);
        console.log('   Email:', supplier.email || 'Not set');
        console.log('   Phone:', supplier.phone || 'Not set');
        console.log('   Address:', supplier.street || 'Not set');
        console.log('   City:', supplier.city || 'Not set');
        console.log('   Country:', supplier.country_id ? supplier.country_id[1] : 'Not set');
      });
    }
    
  } catch (error) {
    console.error('\n❌ Full error:', error);
  }
}

// Test different search patterns
async function runTests() {
  console.log('=== Testing supplier search patterns ===\n');
  
  // Test exact match
  await testSupplierSearch('FastPet Logistics');
  
  console.log('\n' + '='.repeat(50) + '\n');
  
  // Test partial match
  await testSupplierSearch('FastPet');
  
  console.log('\n' + '='.repeat(50) + '\n');
  
  // Test case insensitive
  await testSupplierSearch('fastpet');
}

runTests();