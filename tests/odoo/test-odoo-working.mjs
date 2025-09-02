import fetch from 'node-fetch';

const ODOO_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co/functions/v1/odoo';
const AUTH_TOKEN = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testWorkingApproach() {
  console.log('=== Testing Working Odoo Approach ===\n');

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': AUTH_TOKEN,
    'x-application-name': 'animal-farmacy',
    'apikey': AUTH_TOKEN.replace('Bearer ', '')
  };

  try {
    // Step 1: Fetch orders WITHOUT partner_id
    console.log('1. Fetching orders without partner_id...');
    const ordersResponse = await fetch(ODOO_URL, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        method: 'search_read',
        model: 'purchase.order',
        fields: ['id', 'name', 'state', 'date_order', 'amount_total', 'order_line'],
        limit: 5
      })
    });

    const ordersData = await ordersResponse.json();
    console.log(`Found ${ordersData.orders?.length || 0} orders\n`);

    if (ordersData.orders && ordersData.orders.length > 0) {
      console.log('Orders:', ordersData.orders.map(o => ({ id: o.id, name: o.name, total: o.amount_total })));
      
      // Step 2: For each order, try to get partner info using execute
      console.log('\n2. Fetching partner info for each order...\n');
      
      for (const order of ordersData.orders.slice(0, 3)) {
        console.log(`\nOrder ${order.name} (ID: ${order.id}):`);
        
        // Try different approaches to get partner info
        
        // Approach A: Use execute method
        try {
          const execResponse = await fetch(ODOO_URL, {
            method: 'POST',
            headers,
            body: JSON.stringify({
              method: 'read',
              model: 'purchase.order',
              ids: [order.id],
              fields: []  // Empty means all fields
            })
          });
          
          const execData = await execResponse.json();
          console.log('Execute read result:', JSON.stringify(execData, null, 2));
        } catch (error) {
          console.log('Execute error:', error.message);
        }
      }
    }
  } catch (error) {
    console.error('Error:', error);
  }
}

testWorkingApproach();