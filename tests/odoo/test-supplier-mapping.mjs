// Test supplier mapping and data fetching
const supabaseUrl = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function makeRequest(body) {
  const response = await fetch(`${supabaseUrl}/functions/v1/purchase-orders`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${supabaseAnonKey}`,
      'x-application-name': 'animal-farmacy',
      'apikey': supabaseAnonKey
    },
    body: JSON.stringify(body)
  });

  const text = await response.text();
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${text}`);
  }
  return JSON.parse(text);
}

async function testSupplierMapping() {
  try {
    console.log('Testing supplier mapping and data fetching...\n');
    
    // Get all suppliers
    console.log('1. Fetching all available suppliers...');
    const suppliersResult = await makeRequest({
      method: 'search_read',
      model: 'res.partner',
      domain: [['supplier_rank', '>', 0]],
      fields: ['id', 'name', 'email', 'street', 'city', 'country_id', 'phone'],
      limit: 20
    });
    
    console.log('Suppliers result:', suppliersResult);
    console.log('Available suppliers:');
    if (suppliersResult.partners && suppliersResult.partners.length > 0) {
      suppliersResult.partners.forEach(s => {
        console.log(`\n- ${s.name} (ID: ${s.id})`);
        if (s.email) console.log(`  Email: ${s.email}`);
        if (s.street) console.log(`  Address: ${s.street}`);
        if (s.city) console.log(`  City: ${s.city}`);
        if (s.country_id) console.log(`  Country: ${Array.isArray(s.country_id) ? s.country_id[1] : s.country_id}`);
        if (s.phone) console.log(`  Phone: ${s.phone}`);
      });
    } else {
      console.log('No suppliers found');
    }
    
    // Test fetching a specific supplier
    if (suppliersResult.partners?.length > 0) {
      const testSupplier = suppliersResult.partners[0];
      console.log(`\n2. Testing getSupplierById for "${testSupplier.name}" (ID: ${testSupplier.id})...`);
      
      const detailResult = await makeRequest({
        method: 'read',
        model: 'res.partner',
        ids: [testSupplier.id],
        fields: [
          'id', 'name', 'email', 'street', 'street2', 
          'city', 'state_id', 'zip', 'country_id', 
          'phone', 'mobile', 'vat'
        ]
      });
      
      if (detailResult && detailResult[0]) {
        console.log('Detailed supplier info:', JSON.stringify(detailResult[0], null, 2));
      }
    }
    
    // Suggested mappings for common supplier names
    console.log('\n3. Suggested supplier mappings:');
    console.log('   "Impala" -> Could map to "Global Pet Supplies" or create new');
    console.log('   "Fashion Forward" -> Could map to "European Pet Distributors" or create new');
    
  } catch (error) {
    console.error('Test failed:', error);
  }
}

testSupplierMapping();