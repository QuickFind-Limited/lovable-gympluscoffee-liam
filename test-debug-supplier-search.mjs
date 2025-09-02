// Debug supplier search step by step
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

async function debugSupplierSearch() {
  try {
    console.log('=== Debugging Supplier Search ===\n');
    
    // 1. Test basic partner search without supplier filter
    console.log('1. Testing basic partner search (no supplier filter)...');
    const allPartners = await makeRequest({
      method: 'search_read',
      model: 'res.partner',
      domain: [],
      fields: ['id', 'name', 'supplier_rank'],
      limit: 10
    });
    console.log(`   Found ${allPartners.partners?.length || 0} partners`);
    if (allPartners.partners?.length > 0) {
      console.log('   First few:', allPartners.partners.slice(0, 3).map(p => 
        `${p.name} (supplier_rank: ${p.supplier_rank})`
      ));
    }
    
    // 2. Test with supplier filter
    console.log('\n2. Testing with supplier_rank filter...');
    const suppliers = await makeRequest({
      method: 'search_read',
      model: 'res.partner',
      domain: [['supplier_rank', '>', 0]],
      fields: ['id', 'name', 'supplier_rank'],
      limit: 10
    });
    console.log(`   Found ${suppliers.partners?.length || 0} suppliers`);
    if (suppliers.partners?.length > 0) {
      console.log('   Suppliers:', suppliers.partners.map(p => 
        `${p.name} (rank: ${p.supplier_rank})`
      ));
    }
    
    // 3. Test name search on all partners
    console.log('\n3. Testing name search (FastPet) on all partners...');
    const nameSearch = await makeRequest({
      method: 'search_read',
      model: 'res.partner',
      domain: [['name', 'ilike', 'FastPet']],
      fields: ['id', 'name', 'supplier_rank'],
      limit: 10
    });
    console.log(`   Found ${nameSearch.partners?.length || 0} matches`);
    if (nameSearch.partners?.length > 0) {
      console.log('   Matches:', nameSearch.partners.map(p => 
        `${p.name} (supplier_rank: ${p.supplier_rank})`
      ));
    }
    
    // 4. Test combined search
    console.log('\n4. Testing combined supplier + name search...');
    const combined = await makeRequest({
      method: 'search_read',
      model: 'res.partner',
      domain: [
        ['supplier_rank', '>', 0],
        ['name', 'ilike', 'FastPet']
      ],
      fields: ['id', 'name', 'supplier_rank'],
      limit: 10
    });
    console.log(`   Found ${combined.partners?.length || 0} matches`);
    
    // 5. Look for FastPet by ID 25
    console.log('\n5. Testing read by ID 25 (FastPet Logistics)...');
    try {
      const byId = await makeRequest({
        method: 'read',
        model: 'res.partner',
        ids: [25],
        fields: ['id', 'name', 'supplier_rank', 'email', 'phone']
      });
      console.log('   Result:', byId);
    } catch (e) {
      console.log('   Error:', e.message);
    }
    
  } catch (error) {
    console.error('Error:', error);
  }
}

debugSupplierSearch();