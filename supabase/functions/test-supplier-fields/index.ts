import { serve } from 'https://deno.land/std@0.190.0/http/server.ts';
import { OdooClient } from "../_shared/odoo-client.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
};

serve(async (req: Request) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const url = new URL(req.url);
    const testCase = url.searchParams.get('test') || 'all';
    const supplierId = 144; // Express Apparel Wholesale Group

    console.log(`🔵 Testing field combination: ${testCase}`);

    // Initialize Odoo client
    const odoo = new OdooClient();
    await odoo.connect();

    let fields: string[] = [];
    
    // Test different field combinations
    switch(testCase) {
      case 'minimal':
        // Just ID
        fields = ['id'];
        break;
      
      case 'basic':
        // Basic fields without product_tmpl_id
        fields = ['id', 'product_name', 'product_code'];
        break;
        
      case 'with_tmpl':
        // Add product_tmpl_id
        fields = ['id', 'product_name', 'product_code', 'product_tmpl_id'];
        break;
        
      case 'with_price':
        // Add price fields
        fields = ['id', 'product_name', 'product_code', 'price', 'min_qty'];
        break;
        
      case 'with_delay':
        // Add delay field
        fields = ['id', 'product_name', 'product_code', 'price', 'min_qty', 'delay'];
        break;
        
      case 'all':
        // All fields we use
        fields = ['id', 'product_tmpl_id', 'product_name', 'product_code', 'price', 'min_qty', 'delay'];
        break;
        
      default:
        fields = ['id'];
    }

    console.log(`🔍 Testing fields: ${JSON.stringify(fields)}`);

    // Fetch supplier info
    const products = await odoo.searchRead(
      'product.supplierinfo',
      [['partner_id', '=', supplierId]],
      fields,
      0,
      3
    );

    console.log(`✅ SearchRead returned ${products.length} products`);

    return new Response(
      JSON.stringify({
        testCase,
        fields,
        productCount: products.length,
        products: products,
        success: true
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
        error: error.message || 'Failed to test fields',
        stack: error.stack,
        success: false
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