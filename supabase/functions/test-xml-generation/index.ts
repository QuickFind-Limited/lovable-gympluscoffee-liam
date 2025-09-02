import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';
import { corsHeaders } from '../_shared/cors.ts';

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    // Mock the XML generation like odoo-client would do it
    const domain = [['sale_ok', '=', true]];
    const fields = ['id', 'name', 'list_price'];
    const options = { offset: 0, limit: 2 };
    
    // Build XML for the execute_kw call
    const params = [
      'source-animalfarmacy',  // database
      2,                       // uid
      'password',              // password
      'product.product',       // model
      'search_read',          // method
      [domain, fields, options] // args
    ];
    
    const result = {
      description: 'XML that would be sent for search_read',
      method: 'execute_kw',
      params: params,
      formatted_params: {
        database: params[0],
        uid: params[1],
        password: '***',
        model: params[3],
        method: params[4],
        args: params[5]
      },
      xml_structure: `
<?xml version="1.0"?>
<methodCall>
  <methodName>execute_kw</methodName>
  <params>
    <param><value><string>source-animalfarmacy</string></value></param>
    <param><value><int>2</int></value></param>
    <param><value><string>password</string></value></param>
    <param><value><string>product.product</string></value></param>
    <param><value><string>search_read</string></value></param>
    <param><value><array><data>
      <!-- domain array -->
      <value><array><data>
        <value><array><data>
          <value><string>sale_ok</string></value>
          <value><string>=</string></value>
          <value><boolean>1</boolean></value>
        </data></array></value>
      </data></array></value>
      <!-- fields array -->
      <value><array><data>
        <value><string>id</string></value>
        <value><string>name</string></value>
        <value><string>list_price</string></value>
      </data></array></value>
      <!-- options struct -->
      <value><struct>
        <member>
          <name>offset</name>
          <value><int>0</int></value>
        </member>
        <member>
          <name>limit</name>
          <value><int>2</int></value>
        </member>
      </struct></value>
    </data></array></value></param>
  </params>
</methodCall>`
    };

    return new Response(
      JSON.stringify(result, null, 2),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200
      }
    );

  } catch (error) {
    return new Response(
      JSON.stringify({ 
        error: 'Internal server error',
        message: error.message
      }, null, 2),
      { 
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    );
  }
});