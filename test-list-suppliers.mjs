// Test listing all suppliers in Odoo
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
    console.error('Full error response:', text);
    throw new Error(`HTTP ${response.status}: ${text}`);
  }
  return JSON.parse(text);
}

async function listAllSuppliers() {
  try {
    console.log('Listing all suppliers in Odoo...\n');
    
    const result = await makeRequest({
      method: 'search_read',
      model: 'res.partner',
      domain: [['supplier_rank', '>', 0]],
      fields: ['id', 'name', 'email', 'street', 'city', 'phone'],
      limit: 20,
      order: 'name'
    });
    
    console.log(`Found ${result.partners?.length || 0} suppliers\n`);
    
    if (result.partners && result.partners.length > 0) {
      console.log('Suppliers:');
      result.partners.forEach(supplier => {
        console.log(`\n- ${supplier.name} (ID: ${supplier.id})`);
        if (supplier.email) console.log(`  Email: ${supplier.email}`);
        if (supplier.street) console.log(`  Address: ${supplier.street}`);
        if (supplier.city) console.log(`  City: ${supplier.city}`);
        if (supplier.phone) console.log(`  Phone: ${supplier.phone}`);
      });
    }
    
  } catch (error) {
    console.error('Error:', error.message);
  }
}

listAllSuppliers();