import fetch from 'node-fetch';

const ODOO_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co/functions/v1/odoo';
const AUTH_TOKEN = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testReadMethod() {
  console.log('=== Testing Read Method Response ===\n');

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': AUTH_TOKEN,
    'x-application-name': 'animal-farmacy',
    'apikey': AUTH_TOKEN.replace('Bearer ', '')
  };

  try {
    // Test read method for order 41 (P00043)
    console.log('Testing read method for order 41 (P00043):');
    const response = await fetch(ODOO_URL, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        method: 'read',
        model: 'purchase.order',
        ids: [41],
        fields: ['partner_id', 'order_line']
      })
    });

    const data = await response.json();
    console.log('Raw response:', JSON.stringify(data, null, 2));
    
    // Test with no fields (all fields)
    console.log('\n\nTesting read method with no fields specified:');
    const response2 = await fetch(ODOO_URL, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        method: 'read',
        model: 'purchase.order',
        ids: [41],
        fields: []
      })
    });

    const data2 = await response2.json();
    console.log('Response keys:', Object.keys(data2[0] || data2));
    if (data2[0]) {
      console.log('partner_id:', data2[0].partner_id);
      console.log('order_line:', data2[0].order_line);
    }
  } catch (error) {
    console.error('Error:', error);
  }
}

testReadMethod();