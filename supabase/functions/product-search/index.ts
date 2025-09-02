import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';
import { OdooClient } from "../_shared/odoo-client.ts";

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
    const body = await req.json();
    const { query, search_type = 'single' } = body;
    
    if (search_type !== 'single' || !query) {
      return new Response(
        JSON.stringify({ error: 'Single search with query required' }),
        { 
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      );
    }
    
    // Initialize Odoo client
    const odoo = new OdooClient();
    await odoo.connect();
    
    // Search products (WITHOUT image_1920!)
    const products = await odoo.searchRead(
      'product.product',
      [['name', 'ilike', query]],
      ['id', 'name', 'display_name', 'list_price', 'default_code', 'qty_available'],
      0,
      20
    );
    
    return new Response(
      JSON.stringify({ 
        products,
        images_available: true, // Indicate that images can be fetched separately
        image_endpoint: 'product-images'
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
    
  } catch (error: any) {
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