import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';
import { corsHeaders } from '../_shared/cors.ts';
import { createClient } from '../_shared/xmlrpc-client.ts';

serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    // Get environment variables
    const ODOO_URL = Deno.env.get('ODOO_URL') || '';
    const ODOO_DATABASE = Deno.env.get('ODOO_DATABASE') || '';
    const ODOO_USERNAME = Deno.env.get('ODOO_USERNAME') || '';
    const ODOO_PASSWORD = Deno.env.get('ODOO_PASSWORD') || '';

    // Remove trailing slash
    const cleanUrl = ODOO_URL.replace(/\/$/, '');

    const results = {
      environment: {
        ODOO_URL: ODOO_URL,
        ODOO_URL_CLEANED: cleanUrl,
        ODOO_DATABASE: ODOO_DATABASE,
        ODOO_USERNAME: ODOO_USERNAME,
        ODOO_PASSWORD: ODOO_PASSWORD ? '***SET***' : 'NOT SET',
      },
      steps: []
    };

    // Step 1: Try to connect to common endpoint
    try {
      const commonUrl = `${cleanUrl}/xmlrpc/2/common`;
      results.steps.push({
        step: 'common_endpoint',
        url: commonUrl,
        status: 'attempting'
      });
      
      const common = createClient(commonUrl);
      const version = await common.methodCall('version', []);
      
      results.steps.push({
        step: 'version_check',
        result: version,
        status: 'success'
      });
    } catch (error) {
      results.steps.push({
        step: 'common_endpoint_error',
        error: error.message,
        stack: error.stack,
        status: 'failed'
      });
    }

    // Step 2: Try authentication
    try {
      const commonUrl = `${cleanUrl}/xmlrpc/2/common`;
      const common = createClient(commonUrl);
      
      results.steps.push({
        step: 'authentication',
        status: 'attempting'
      });
      
      const uid = await common.methodCall('authenticate', [
        ODOO_DATABASE,
        ODOO_USERNAME,
        ODOO_PASSWORD,
        {}
      ]);
      
      results.steps.push({
        step: 'authentication_result',
        uid: uid,
        status: uid ? 'success' : 'failed'
      });

      // Step 3: Try a simple query if authenticated
      if (uid) {
        try {
          const objectUrl = `${cleanUrl}/xmlrpc/2/object`;
          const object = createClient(objectUrl);
          
          const count = await object.methodCall('execute_kw', [
            ODOO_DATABASE,
            uid,
            ODOO_PASSWORD,
            'product.product',
            'search_count',
            [[['sale_ok', '=', true]]]
          ]);
          
          results.steps.push({
            step: 'product_count',
            count: count,
            status: 'success'
          });
        } catch (error) {
          results.steps.push({
            step: 'product_query_error',
            error: error.message,
            status: 'failed'
          });
        }
      }
    } catch (error) {
      results.steps.push({
        step: 'authentication_error',
        error: error.message,
        stack: error.stack,
        status: 'failed'
      });
    }

    return new Response(
      JSON.stringify(results, null, 2),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200
      }
    );

  } catch (error) {
    return new Response(
      JSON.stringify({ 
        error: 'Internal server error',
        message: error.message,
        stack: error.stack
      }, null, 2),
      { 
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    );
  }
});