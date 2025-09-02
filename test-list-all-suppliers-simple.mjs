// Test listing all suppliers without name filter
const supabaseUrl = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function listAllSuppliers() {
  try {
    console.log('Listing all suppliers...\n');
    
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
        fields: ['id', 'name'],
        limit: 30
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
      console.log('\nSuppliers:');
      data.partners.forEach((supplier) => {
        console.log(`- ${supplier.name} (ID: ${supplier.id})`);
      });
      
      // Find FastPet
      const fastpet = data.partners.find(s => s.name.toLowerCase().includes('fastpet'));
      if (fastpet) {
        console.log('\n✅ Found FastPet:', fastpet.name, 'with ID:', fastpet.id);
      } else {
        console.log('\n❌ FastPet not found in the list');
      }
    }
    
  } catch (error) {
    console.error('\n❌ Full error:', error);
  }
}

listAllSuppliers();