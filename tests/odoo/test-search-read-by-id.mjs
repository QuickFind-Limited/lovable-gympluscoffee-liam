import fetch from 'node-fetch';

const ODOO_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co/functions/v1/odoo';
const AUTH_TOKEN = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testSearchReadById() {
  console.log('=== Testing Alternative Approach with search_read ===\n');

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': AUTH_TOKEN,
    'x-application-name': 'animal-farmacy',
    'apikey': AUTH_TOKEN.replace('Bearer ', '')
  };

  try {
    // Use search_read with domain filter for specific ID
    console.log('Using search_read to get order 41 with partner_id:');
    const response = await fetch(ODOO_URL, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        method: 'search_read',
        model: 'purchase.order',
        domain: [['id', '=', 41]],
        fields: ['id', 'name', 'partner_id', 'order_line', 'state', 'amount_total'],
        limit: 1
      })
    });

    const data = await response.json();
    console.log('Response:', JSON.stringify(data, null, 2));
    
    if (data.orders && data.orders.length > 0) {
      const order = data.orders[0];
      console.log('\nOrder found:');
      console.log('- ID:', order.id);
      console.log('- Name:', order.name);
      console.log('- Partner:', order.partner_id);
      console.log('- Lines:', order.order_line);
    }
  } catch (error) {
    console.error('Error:', error);
  }
}

testSearchReadById();