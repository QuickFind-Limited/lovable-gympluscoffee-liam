// Test direct read call to see actual response
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
  console.log('Raw response:', text);
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${text}`);
  }
  return JSON.parse(text);
}

async function testDirectRead() {
  try {
    console.log('Testing direct read for FastPet (ID 25)...\n');
    
    const result = await makeRequest({
      method: 'read',
      model: 'res.partner',
      ids: [25],
      fields: ['id', 'name', 'email']
    });
    
    console.log('\nParsed result:', result);
    console.log('Type:', typeof result);
    console.log('Is array?', Array.isArray(result));
    
  } catch (error) {
    console.error('Error:', error);
  }
}

testDirectRead();