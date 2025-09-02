import fetch from 'node-fetch';

const ODOO_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co/functions/v1/odoo';
const AUTH_TOKEN = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function verifyFix() {
  console.log('=== Verifying Order Fetch Fix ===\n');

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': AUTH_TOKEN,
    'x-application-name': 'animal-farmacy',
    'apikey': AUTH_TOKEN.replace('Bearer ', '')
  };

  try {
    // Test 1: Fetch orders WITHOUT order_line field
    console.log('1. Fetching orders without order_line field:');
    const response = await fetch(ODOO_URL, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        method: 'search_read',
        model: 'purchase.order',
        fields: ['id', 'name', 'state', 'date_order', 'amount_total', 'amount_untaxed', 'amount_tax'],
        limit: 10,
        order: 'date_order desc'
      })
    });

    const data = await response.json();
    console.log(`Found ${data.orders?.length || 0} orders`);
    
    if (data.orders && data.orders.length > 0) {
      console.log('\nFirst order:', {
        id: data.orders[0].id,
        name: data.orders[0].name,
        state: data.orders[0].state,
        total: data.orders[0].amount_total
      });
      
      // Test 2: For the first order, get its details with partner info
      const orderId = data.orders[0].id;
      console.log(`\n2. Fetching order ${orderId} details with read method:`);
      
      const detailResponse = await fetch(ODOO_URL, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          method: 'read',
          model: 'purchase.order',
          ids: [orderId],
          fields: ['id', 'name', 'partner_id', 'state', 'date_order', 'amount_total', 'order_line']
        })
      });
      
      const detailData = await detailResponse.json();
      const orderDetail = Array.isArray(detailData) ? detailData[0] : detailData.orders?.[0];
      
      if (orderDetail) {
        console.log('Order details:');
        console.log('- Partner:', orderDetail.partner_id);
        console.log('- Order lines:', orderDetail.order_line);
        
        // Test 3: If we have order lines, fetch their details
        if (orderDetail.order_line && orderDetail.order_line.length > 0) {
          console.log(`\n3. Fetching details for ${orderDetail.order_line.length} order lines:`);
          
          const linesResponse = await fetch(ODOO_URL, {
            method: 'POST',
            headers,
            body: JSON.stringify({
              method: 'read',
              model: 'purchase.order.line',
              ids: orderDetail.order_line,
              fields: ['id', 'product_id', 'name', 'product_qty', 'price_unit']
            })
          });
          
          const linesData = await linesResponse.json();
          const lines = linesData?.lines || [];
          
          console.log(`Found ${lines.length} lines:`);
          lines.forEach((line, idx) => {
            console.log(`  Line ${idx + 1}:`, {
              product: line.product_id,
              qty: line.product_qty,
              price: line.price_unit
            });
          });
        }
      }
    }
  } catch (error) {
    console.error('Error:', error);
  }
}

verifyFix();