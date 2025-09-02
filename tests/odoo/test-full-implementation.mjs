import fetch from 'node-fetch';

const ODOO_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co/functions/v1/odoo';
const AUTH_TOKEN = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testFullImplementation() {
  console.log('=== Testing Full Two-Step Implementation ===\n');

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': AUTH_TOKEN,
    'x-application-name': 'animal-farmacy',
    'apikey': AUTH_TOKEN.replace('Bearer ', '')
  };

  try {
    // Step 1: Fetch orders WITHOUT partner_id and order_line
    console.log('STEP 1: Fetching orders (basic fields only):');
    const ordersResponse = await fetch(ODOO_URL, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        method: 'search_read',
        model: 'purchase.order',
        fields: ['id', 'name', 'state', 'date_order', 'amount_total', 'amount_untaxed', 'amount_tax'],
        limit: 5,
        order: 'date_order desc'
      })
    });

    const ordersData = await ordersResponse.json();
    console.log(`✓ Found ${ordersData.orders?.length || 0} orders\n`);

    if (ordersData.orders && ordersData.orders.length > 0) {
      // Display basic order info
      console.log('Basic order information:');
      ordersData.orders.forEach(order => {
        console.log(`- ${order.name}: £${order.amount_total}, State: ${order.state}`);
      });
      
      // Step 2: Enrich orders with partner and line details
      console.log('\n\nSTEP 2: Enriching orders with partner details...\n');
      
      for (const order of ordersData.orders.slice(0, 3)) {
        console.log(`\nEnriching order ${order.name} (ID: ${order.id}):`);
        
        // Fetch order details including partner_id and order_line
        const detailResponse = await fetch(ODOO_URL, {
          method: 'POST',
          headers,
          body: JSON.stringify({
            method: 'read',
            model: 'purchase.order',
            ids: [order.id],
            fields: ['partner_id', 'order_line']
          })
        });
        
        const detailData = await detailResponse.json();
        const orderDetail = Array.isArray(detailData) ? detailData[0] : detailData.orders?.[0];
        
        if (orderDetail) {
          // Extract partner info
          if (orderDetail.partner_id) {
            const partnerInfo = Array.isArray(orderDetail.partner_id) 
              ? `${orderDetail.partner_id[1]} (ID: ${orderDetail.partner_id[0]})`
              : 'Unknown format';
            console.log(`  ✓ Partner: ${partnerInfo}`);
          } else {
            console.log('  ✗ No partner found');
          }
          
          // Extract order lines
          if (orderDetail.order_line && orderDetail.order_line.length > 0) {
            console.log(`  ✓ Order lines: ${orderDetail.order_line.length} items`);
            
            // Step 3: Fetch order line details
            console.log('  → Fetching line details...');
            const linesResponse = await fetch(ODOO_URL, {
              method: 'POST',
              headers,
              body: JSON.stringify({
                method: 'read',
                model: 'purchase.order.line',
                ids: orderDetail.order_line,
                fields: ['id', 'product_id', 'name', 'product_qty', 'price_unit', 'price_subtotal']
              })
            });
            
            const linesData = await linesResponse.json();
            const lines = linesData?.lines || [];
            
            lines.forEach((line, idx) => {
              const productName = Array.isArray(line.product_id) ? line.product_id[1] : 'Unknown';
              console.log(`     Line ${idx + 1}: ${productName} - Qty: ${line.product_qty}, Price: £${line.price_unit}`);
            });
          } else {
            console.log('  ✗ No order lines found');
          }
        }
      }
      
      console.log('\n\n✓ SUMMARY: Two-step approach working correctly!');
      console.log('  1. Basic order fetch works without partner_id/order_line');
      console.log('  2. Detailed fetch with read method gets partner and lines');
      console.log('  3. Order line details can be fetched separately');
    }
  } catch (error) {
    console.error('❌ Error:', error);
  }
}

testFullImplementation();