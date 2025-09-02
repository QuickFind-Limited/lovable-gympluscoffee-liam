import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE',
};

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { query } = await req.json();
    
    if (!query) {
      return new Response(
        JSON.stringify({ error: 'Query parameter is required' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // Step 1: Authenticate with Odoo
    const odooUrl = 'https://source-animalfarmacy.odoo.com';
    const db = 'source-animalfarmacy';
    const username = 'admin@quickfindai.com';
    const password = 'BJ62wX2J4yzjS$i';

    const authResponse = await fetch(`${odooUrl}/jsonrpc`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'call',
        params: {
          service: 'common',
          method: 'authenticate',
          args: [db, username, password, {}]
        },
        id: Math.random()
      })
    });

    const authData = await authResponse.json();
    const uid = authData.result;

    if (!uid) {
      throw new Error('Authentication failed');
    }

    // Step 2: Search products
    const searchResponse = await fetch(`${odooUrl}/jsonrpc`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'call',
        params: {
          service: 'object',
          method: 'execute_kw',
          args: [
            db,
            uid,
            password,
            'product.product',
            'search_read',
            [[['name', 'ilike', query]]],
            {
              fields: ['id', 'name', 'display_name', 'list_price', 'default_code', 'qty_available', 'seller_ids', 'categ_id'],
              limit: 20
            }
          ]
        },
        id: Math.random()
      })
    });

    const searchData = await searchResponse.json();
    const products = searchData.result || [];

    // Step 3: Get unique seller IDs
    const sellerIds = new Set();
    products.forEach(product => {
      if (product.seller_ids && Array.isArray(product.seller_ids)) {
        product.seller_ids.forEach(id => sellerIds.add(id));
      }
    });

    // Step 4: Fetch supplier info if there are seller IDs
    let supplierInfo = {};
    if (sellerIds.size > 0) {
      const supplierResponse = await fetch(`${odooUrl}/jsonrpc`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          jsonrpc: '2.0',
          method: 'call',
          params: {
            service: 'object',
            method: 'execute_kw',
            args: [
              db,
              uid,
              password,
              'product.supplierinfo',
              'search_read',
              [[['id', 'in', Array.from(sellerIds)]]],
              {
                fields: ['id', 'partner_id', 'product_name', 'min_qty', 'price']
              }
            ]
          },
          id: Math.random()
        })
      });

      const supplierData = await supplierResponse.json();
      const supplierRecords = supplierData.result || [];
      
      // Create a map of seller ID to supplier info
      supplierRecords.forEach(record => {
        supplierInfo[record.id] = {
          id: record.partner_id ? record.partner_id[0] : null,
          name: record.partner_id ? record.partner_id[1] : 'Unknown Supplier',
          min_qty: record.min_qty || 1,
          price: record.price || 0
        };
      });
    }

    // Step 5: Transform products with supplier information
    const transformedProducts = products.map(product => {
      // Get the first supplier info if available
      let supplierName = 'Unknown Supplier';
      let supplierId = null;
      
      if (product.seller_ids && product.seller_ids.length > 0) {
        const firstSellerId = product.seller_ids[0];
        if (supplierInfo[firstSellerId]) {
          supplierName = supplierInfo[firstSellerId].name;
          supplierId = supplierInfo[firstSellerId].id;
        }
      }

      return {
        ...product,
        supplier_id: supplierId,
        supplier_name: supplierName,
        vendor: supplierName, // For compatibility
        supplier: supplierName // For compatibility
      };
    });

    return new Response(
      JSON.stringify({ 
        products: transformedProducts,
        images_available: true,
        image_endpoint: 'product-images'
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
    
  } catch (error) {
    console.error('Error:', error);
    return new Response(
      JSON.stringify({ error: error.message }),
      { 
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    );
  }
});