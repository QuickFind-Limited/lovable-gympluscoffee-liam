// Test fetching FastPet Logistics supplier data
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

async function testFastPetSupplier() {
  try {
    console.log('Testing FastPet Logistics supplier data fetch...\n');
    
    // Search for FastPet Logistics by name
    console.log('1. Searching for FastPet Logistics...');
    const searchResult = await makeRequest({
      method: 'search_read',
      model: 'res.partner',
      domain: [
        ['supplier_rank', '>', 0],
        ['name', 'ilike', 'FastPet']
      ],
      fields: ['id', 'name', 'email', 'street', 'city', 'country_id', 'phone'],
      limit: 5
    });
    
    console.log('Search result:', searchResult);
    
    if (searchResult.partners && searchResult.partners.length > 0) {
      const fastPet = searchResult.partners[0];
      console.log('\n✅ Found FastPet Logistics!');
      console.log('ID:', fastPet.id);
      console.log('Name:', fastPet.name);
      console.log('Email:', fastPet.email || 'Not set');
      console.log('Address:', fastPet.street || 'Not set');
      console.log('City:', fastPet.city || 'Not set');
      console.log('Country:', fastPet.country_id ? fastPet.country_id[1] : 'Not set');
      console.log('Phone:', fastPet.phone || 'Not set');
      
      // Get full details
      console.log('\n2. Fetching full supplier details...');
      const detailResult = await makeRequest({
        method: 'read',
        model: 'res.partner',
        ids: [fastPet.id],
        fields: [
          'id', 'name', 'email', 'street', 'street2', 
          'city', 'state_id', 'zip', 'country_id', 
          'phone', 'mobile', 'vat', 'is_company'
        ]
      });
      
      if (detailResult && detailResult[0]) {
        console.log('\nFull supplier details:', JSON.stringify(detailResult[0], null, 2));
      }
    } else {
      console.log('❌ FastPet Logistics not found in Odoo');
    }
    
  } catch (error) {
    console.error('Error:', error);
  }
}

testFastPetSupplier();