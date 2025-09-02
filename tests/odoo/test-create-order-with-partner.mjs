import fetch from 'node-fetch';

const ODOO_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co/functions/v1/odoo';
const AUTH_TOKEN = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function createOrderWithPartner() {
  console.log('=== Creating Purchase Order with Partner ===\n');

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': AUTH_TOKEN,
    'x-application-name': 'animal-farmacy',
    'apikey': AUTH_TOKEN.replace('Bearer ', '')
  };

  try {
    // First get products
    console.log('1. Getting products...');
    const productsResponse = await fetch(ODOO_URL, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        method: 'search_read',
        model: 'product.product',
        domain: [['purchase_ok', '=', true]],
        fields: ['id', 'name'],
        limit: 5
      })
    });

    const productsData = await productsResponse.json();
    const products = productsData.products || [];
    console.log(`Found ${products.length} products`);

    if (products.length === 0) {
      console.log('No products found!');
      return;
    }

    // Create a new order with a partner
    console.log('\n2. Creating purchase order with partner...');
    
    const now = new Date();
    const dateOrder = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
    
    const createResponse = await fetch(ODOO_URL, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        method: 'create',
        model: 'purchase.order',
        data: {
          partner_id: 21, // Global Pet Supplies
          date_order: dateOrder,
          order_line: [
            [0, 0, {
              product_id: products[0].id,
              name: products[0].name,
              product_qty: 10,
              price_unit: 15.99,
              product_uom_id: 1,
              date_planned: dateOrder
            }]
          ]
        }
      })
    });

    const createData = await createResponse.json();
    console.log('Create response:', createData);

    if (createData.id) {
      console.log(`\n3. Created order ID: ${createData.id}`);
      
      // Now fetch it back with partner_id
      console.log('\n4. Fetching created order...');
      const fetchResponse = await fetch(ODOO_URL, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          method: 'search_read',
          model: 'purchase.order',
          domain: [['id', '=', createData.id]],
          fields: ['id', 'name', 'partner_id', 'state', 'amount_total']
        })
      });

      const fetchData = await fetchResponse.json();
      console.log('Fetched order:', JSON.stringify(fetchData, null, 2));
    }

  } catch (error) {
    console.error('Error:', error.message);
  }
}

createOrderWithPartner();