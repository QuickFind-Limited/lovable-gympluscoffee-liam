import fetch from 'node-fetch';

const ODOO_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co/functions/v1/odoo';
const AUTH_TOKEN = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testCurrentState() {
  console.log('=== Testing Current State ===\n');

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': AUTH_TOKEN,
    'x-application-name': 'animal-farmacy',
    'apikey': AUTH_TOKEN.replace('Bearer ', '')
  };

  try {
    // Test what we're currently fetching
    console.log('1. Fetching orders with current fields:');
    const response = await fetch(ODOO_URL, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        method: 'search_read',
        model: 'purchase.order',
        fields: ['id', 'name', 'state', 'date_order', 'amount_total', 'amount_untaxed', 'amount_tax'],
        limit: 3,
        order: 'date_order desc'
      })
    });

    const data = await response.json();
    console.log(`Found ${data.orders?.length || 0} orders`);
    
    if (data.orders && data.orders.length > 0) {
      console.log('\nOrder data structure:');
      data.orders.forEach(order => {
        console.log(`\nOrder ${order.name}:`);
        Object.entries(order).forEach(([key, value]) => {
          console.log(`  ${key}: ${JSON.stringify(value)}`);
        });
      });
    }
  } catch (error) {
    console.error('Error:', error);
  }
}

testCurrentState();