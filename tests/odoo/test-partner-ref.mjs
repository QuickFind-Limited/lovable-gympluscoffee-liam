import fetch from 'node-fetch';

const ODOO_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co/functions/v1/odoo';
const AUTH_TOKEN = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testPartnerRef() {
  console.log('=== Testing partner_ref Field ===\n');

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': AUTH_TOKEN,
    'x-application-name': 'animal-farmacy',
    'apikey': AUTH_TOKEN.replace('Bearer ', '')
  };

  try {
    // Test partner_ref field
    console.log('Fetching orders with partner_ref:');
    const response = await fetch(ODOO_URL, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        method: 'search_read',
        model: 'purchase.order',
        fields: ['id', 'name', 'state', 'date_order', 'amount_total', 'partner_ref'],
        limit: 5,
        order: 'date_order desc'
      })
    });

    const data = await response.json();
    console.log(`Found ${data.orders?.length || 0} orders\n`);
    
    if (data.orders && data.orders.length > 0) {
      data.orders.forEach(order => {
        console.log(`Order ${order.name}:`);
        console.log(`  partner_ref: ${order.partner_ref}`);
        console.log(`  total: £${order.amount_total}`);
        console.log('');
      });
    }
  } catch (error) {
    console.error('Error:', error);
  }
}

testPartnerRef();