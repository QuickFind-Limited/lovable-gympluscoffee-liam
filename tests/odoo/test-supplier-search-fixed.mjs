// Test supplier search with various approaches
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

async function testSupplierSearch() {
  try {
    console.log('Testing supplier search...\n');
    
    // Test 1: Get suppliers using supplier_rank
    console.log('1. Testing supplier_rank filter...');
    try {
      const result1 = await makeRequest({
        method: 'search_read',
        model: 'res.partner',
        domain: [['supplier_rank', '>', 0]],
        fields: ['id', 'name', 'supplier_rank'],
        limit: 5
      });
      console.log('Suppliers with supplier_rank > 0:', result1.partners || []);
    } catch (e) {
      console.error('supplier_rank test failed:', e.message);
    }
    
    // Test 2: Search by name with ilike
    console.log('\n2. Testing name search with ilike...');
    try {
      const result2 = await makeRequest({
        method: 'search_read',
        model: 'res.partner',
        domain: [['name', 'ilike', 'pet']],
        fields: ['id', 'name'],
        limit: 5
      });
      console.log('Partners with "pet" in name:', result2.partners || []);
    } catch (e) {
      console.error('ilike search failed:', e.message);
    }
    
    // Test 3: Combined search (alternative syntax)
    console.log('\n3. Testing combined search for supplier named "Impala"...');
    try {
      const result3 = await makeRequest({
        method: 'search_read',
        model: 'res.partner',
        domain: [['name', '=', 'Impala']],
        fields: ['id', 'name', 'email', 'street', 'city', 'supplier_rank'],
        limit: 1
      });
      console.log('Exact match for "Impala":', result3.partners || []);
    } catch (e) {
      console.error('Combined search failed:', e.message);
    }
    
    // Test 4: Get all partners and filter client-side
    console.log('\n4. Getting all partners to check available suppliers...');
    try {
      const result4 = await makeRequest({
        method: 'search_read',
        model: 'res.partner',
        domain: [['is_company', '=', true]],
        fields: ['id', 'name', 'supplier_rank', 'customer_rank'],
        limit: 20
      });
      console.log('All companies:', result4.partners?.map(p => ({
        id: p.id,
        name: p.name,
        supplier_rank: p.supplier_rank,
        customer_rank: p.customer_rank
      })) || []);
    } catch (e) {
      console.error('Get all partners failed:', e.message);
    }

  } catch (error) {
    console.error('Test failed:', error);
  }
}

testSupplierSearch();