import { serve } from 'https://deno.land/std@0.190.0/http/server.ts';
import { OdooClient } from "../_shared/odoo-client.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type, x-application-name',
  'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE',
};

serve(async (req: Request) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const url = new URL(req.url);
    const withProducts = url.searchParams.get('withProducts') === 'true';
    const supplierId = url.searchParams.get('supplierId');
    const offset = parseInt(url.searchParams.get('offset') || '0');
    const limit = parseInt(url.searchParams.get('limit') || '10');

    // Initialize Odoo client
    const odoo = new OdooClient();
    await odoo.connect();

    // If fetching products for a specific supplier
    if (supplierId) {
      console.log(`Fetching products for supplier ${supplierId}, offset: ${offset}, limit: ${limit}`);
      const products = await odoo.searchRead(
        'product.supplierinfo',
        [['partner_id', '=', parseInt(supplierId)]],
        ['id', 'product_id', 'product_name', 'product_code', 'price', 'min_qty', 'delay'],
        offset,
        limit
      );
      console.log(`Found ${products.length} products for supplier ${supplierId}`);

      // Parse metadata from product names
      for (const product of products) {
        // Extract metadata from product_name if it contains |META|
        if (product.product_name && product.product_name.includes('|META|')) {
          const parts = product.product_name.split('|META|');
          if (parts.length === 2) {
            // Update product_name to clean version
            product.product_name = parts[0].trim();
            
            // Parse JSON metadata
            try {
              const metadata = JSON.parse(parts[1]);
              product.qty_available = metadata.qty_available || 0;
              product.virtual_available = metadata.virtual_available || 0;
              product.minimum_level = metadata.minimum_level || null;
              product.pack_size = metadata.pack_size || 1;
            } catch (e) {
              console.error('Error parsing metadata:', e);
              // Fallback values
              product.qty_available = 0;
              product.virtual_available = 0;
              product.minimum_level = null;
              product.pack_size = 1;
            }
          }
        } else {
          // Fallback for products without metadata
          product.qty_available = 0;
          product.virtual_available = 0;
          product.minimum_level = null;
          product.pack_size = 1;
        }
      }

      // Get total count
      const totalCount = await odoo.searchCount(
        'product.supplierinfo',
        [['partner_id', '=', parseInt(supplierId)]]
      );

      return new Response(
        JSON.stringify({
          data: products,
          total: totalCount,
          page: Math.floor(offset / limit),
          pageSize: limit,
          hasMore: offset + limit < totalCount
        }),
        {
          headers: {
            ...corsHeaders,
            'Content-Type': 'application/json',
          },
        }
      );
    }

    // Get suppliers - FIXED VERSION: Use individual parameters for search method
    const supplierIds = await odoo.execute('res.partner', 'search', [
      [['supplier_rank', '>', 0]],
      offset,  // Pass offset and limit as separate parameters
      limit
    ]);

    // Read supplier details
    let suppliers: any[] = [];
    if (supplierIds.length > 0) {
      suppliers = await odoo.execute('res.partner', 'read', [
        supplierIds,
        ['id', 'name', 'email', 'phone', 'city', 'supplier_rank']
      ]);

      // If withProducts, get product count for each supplier
      if (withProducts && suppliers.length > 0) {
        console.log(`Getting product counts for ${suppliers.length} suppliers`);
        for (const supplier of suppliers) {
          const productCount = await odoo.searchCount(
            'product.supplierinfo',
            [['partner_id', '=', supplier.id]]
          );
          console.log(`Supplier ${supplier.name} (ID: ${supplier.id}) has ${productCount} products`);
          supplier.product_count = productCount;
          supplier.products = []; // Empty array for now, filled when expanded
        }
      }
    }

    // Get total count
    const totalCount = await odoo.searchCount(
      'res.partner',
      [['supplier_rank', '>', 0]]
    );

    return new Response(
      JSON.stringify({
        suppliers: suppliers,
        pagination: {
          offset,
          limit,
          total: totalCount,
          hasMore: offset + limit < totalCount
        }
      }),
      {
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
        },
      }
    );
  } catch (error: any) {
    console.error('Error:', error);
    return new Response(
      JSON.stringify({ 
        error: error.message || 'Failed to fetch from Odoo',
        details: error.stack
      }),
      {
        status: 500,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
        },
      }
    );
  }
});