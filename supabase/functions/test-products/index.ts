import { serve } from 'https://deno.land/std@0.190.0/http/server.ts';
import { OdooClient } from '../_shared/odoo-client.ts';
import { corsHeaders, getCorsHeaders } from '../_shared/cors.ts';

serve(async (req: Request) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const odoo = new OdooClient();
    await odoo.connect();

    // First, check if product.supplierinfo exists and has data
    const supplierInfos = await odoo.searchRead(
      'product.supplierinfo',
      [], // No domain filter
      ['id', 'partner_id', 'product_id', 'product_name', 'product_code'], // Basic fields
      0,
      10 // Just get first 10
    );

    console.log(`Found ${supplierInfos.length} supplier infos`);

    // Also check product.product
    const products = await odoo.searchRead(
      'product.product',
      [], // No domain filter
      ['id', 'name', 'default_code', 'seller_ids'], // Basic fields
      0,
      10 // Just get first 10
    );

    console.log(`Found ${products.length} products`);

    return new Response(
      JSON.stringify({
        supplierInfos: supplierInfos,
        supplierInfoCount: supplierInfos.length,
        products: products,
        productCount: products.length
      }),
      {
        headers: {
          ...getCorsHeaders(req.headers.get('origin')),
          'Content-Type': 'application/json',
        },
      }
    );
  } catch (error) {
    console.error('Error:', error);
    return new Response(
      JSON.stringify({ 
        error: error.message || 'Failed to fetch products',
        details: error.stack 
      }),
      {
        status: 500,
        headers: {
          ...getCorsHeaders(req.headers.get('origin')),
          'Content-Type': 'application/json',
        },
      }
    );
  }
});