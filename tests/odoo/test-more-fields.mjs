import fetch from 'node-fetch';

const ODOO_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co/functions/v1/odoo';
const AUTH_TOKEN = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testMoreFields() {
  console.log('=== Testing More Fields One by One ===\n');

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': AUTH_TOKEN,
    'x-application-name': 'animal-farmacy',
    'apikey': AUTH_TOKEN.replace('Bearer ', '')
  };

  // Fields to test one by one
  const fieldsToTest = [
    'company_id',
    'currency_id', 
    'user_id',
    'origin',
    'notes',
    'invoice_count',
    'amount_tax',
    'amount_untaxed',
    'date_approve',
    'date_planned'
  ];

  try {
    for (const field of fieldsToTest) {
      console.log(`\nTesting field: ${field}`);
      
      const response = await fetch(ODOO_URL, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          method: 'search_read',
          model: 'purchase.order',
          fields: ['id', 'name', field],
          limit: 1
        })
      });

      const data = await response.json();
      
      if (data.orders && data.orders.length > 0) {
        console.log(`✓ WORKS - Found ${data.orders.length} order`);
        console.log(`  ${field}: ${JSON.stringify(data.orders[0][field])}`);
      } else {
        console.log(`✗ RETURNS 0 ORDERS`);
      }
    }
  } catch (error) {
    console.error('Error:', error);
  }
}

testMoreFields();