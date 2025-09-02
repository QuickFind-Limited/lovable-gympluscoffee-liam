import fetch from 'node-fetch';

const ODOO_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co/functions/v1/odoo';
const AUTH_TOKEN = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testSimpleOrders() {
  console.log('=== Testing Simple Order Fetch ===\n');

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': AUTH_TOKEN,
    'x-application-name': 'animal-farmacy',
    'apikey': AUTH_TOKEN.replace('Bearer ', '')
  };

  // Test 1: Just ID and name (this worked before)
  console.log('1. Fetching with just id and name:');
  try {
    const response1 = await fetch(ODOO_URL, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        method: 'search_read',
        model: 'purchase.order',
        fields: ['id', 'name'],
        limit: 10
      })
    });

    const data1 = await response1.json();
    console.log(`Found ${data1.orders?.length || 0} orders`);
    if (data1.orders?.length > 0) {
      console.log('First order:', data1.orders[0]);
    }
  } catch (error) {
    console.error('Error:', error.message);
  }

  // Test 2: Add fields one by one
  const fieldsToTest = [
    ['id', 'name', 'state'],
    ['id', 'name', 'state', 'date_order'],
    ['id', 'name', 'state', 'date_order', 'amount_total'],
    ['id', 'name', 'state', 'date_order', 'amount_total', 'order_line'],
    ['id', 'name', 'state', 'date_order', 'amount_total', 'order_line', 'amount_untaxed'],
    ['id', 'name', 'state', 'date_order', 'amount_total', 'order_line', 'amount_untaxed', 'amount_tax']
  ];

  for (const fields of fieldsToTest) {
    console.log(`\n2. Testing with fields: [${fields.join(', ')}]`);
    try {
      const response = await fetch(ODOO_URL, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          method: 'search_read',
          model: 'purchase.order',
          fields: fields,
          limit: 2
        })
      });

      const data = await response.json();
      console.log(`- Found ${data.orders?.length || 0} orders`);
    } catch (error) {
      console.error('- Error:', error.message);
    }
  }
}

testSimpleOrders();