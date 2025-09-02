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
    const supplierId = 144; // Express Apparel Wholesale Group

    // Initialize Odoo client
    const odoo = new OdooClient();
    await odoo.connect();

    // Test each field individually to find the problematic one
    const fieldTests = [
      { name: 'id_only', fields: ['id'] },
      { name: 'with_product_name', fields: ['id', 'product_name'] },
      { name: 'with_product_code', fields: ['id', 'product_name', 'product_code'] },
      { name: 'with_price', fields: ['id', 'product_name', 'product_code', 'price'] },
      { name: 'with_min_qty', fields: ['id', 'product_name', 'product_code', 'price', 'min_qty'] },
      { name: 'with_delay', fields: ['id', 'product_name', 'product_code', 'price', 'min_qty', 'delay'] },
      { name: 'with_product_tmpl_id', fields: ['id', 'product_tmpl_id', 'product_name', 'product_code', 'price', 'min_qty', 'delay'] },
    ];

    const results = [];

    for (const test of fieldTests) {
      console.log(`Testing: ${test.name} with fields: ${JSON.stringify(test.fields)}`);
      
      try {
        const products = await odoo.searchRead(
          'product.supplierinfo',
          [['partner_id', '=', supplierId]],
          test.fields,
          0,
          2
        );
        
        results.push({
          test: test.name,
          fields: test.fields,
          success: true,
          count: products.length,
          sample: products.length > 0 ? products[0] : null
        });
        
        console.log(`✅ ${test.name}: Found ${products.length} products`);
      } catch (error: any) {
        results.push({
          test: test.name,
          fields: test.fields,
          success: false,
          error: error.message
        });
        
        console.log(`❌ ${test.name}: Error - ${error.message}`);
      }
    }

    // Now test removing fields one by one from the full set
    const allFields = ['id', 'product_tmpl_id', 'product_name', 'product_code', 'price', 'min_qty', 'delay'];
    const removalTests = [];
    
    for (let i = 0; i < allFields.length; i++) {
      const testFields = allFields.filter((_, index) => index !== i);
      const removedField = allFields[i];
      
      console.log(`Testing without: ${removedField}`);
      
      try {
        const products = await odoo.searchRead(
          'product.supplierinfo',
          [['partner_id', '=', supplierId]],
          testFields,
          0,
          2
        );
        
        removalTests.push({
          removedField,
          remainingFields: testFields,
          success: true,
          count: products.length
        });
        
        console.log(`✅ Without ${removedField}: Found ${products.length} products`);
      } catch (error: any) {
        removalTests.push({
          removedField,
          remainingFields: testFields,
          success: false,
          error: error.message
        });
        
        console.log(`❌ Without ${removedField}: Error - ${error.message}`);
      }
    }

    return new Response(
      JSON.stringify({
        additionTests: results,
        removalTests: removalTests,
        summary: {
          workingFields: results.filter(r => r.success && r.count > 0).map(r => r.test),
          failedFields: results.filter(r => !r.success).map(r => r.test),
          emptyResults: results.filter(r => r.success && r.count === 0).map(r => r.test)
        }
      }, null, 2),
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
        stack: error.stack
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