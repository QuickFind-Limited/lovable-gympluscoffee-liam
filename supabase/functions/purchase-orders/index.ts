import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { OdooClient } from "../_shared/odoo-client.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type, x-application-name',
  'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE',
};

serve(async (req) => {
  console.log('Edge function called with method:', req.method);
  console.log('Headers:', Object.fromEntries(req.headers.entries()));
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    // Parse request body
    let requestBody;
    try {
      requestBody = await req.json();
    } catch (parseError) {
      console.error('Failed to parse request body:', parseError);
      return new Response(
        JSON.stringify({ error: 'Invalid JSON in request body' }),
        { 
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      );
    }
    
    const { method, model, domain, fields, limit, order, ids, data } = requestBody;
    console.log('Request:', { method, model, data });

    // Initialize Odoo client (it already has credentials)
    const odoo = new OdooClient();
    await odoo.connect();

    let result;

    switch (method) {
      case 'search_read':
        // Handle order parameter properly
        const options: any = { limit: limit || 100 };
        if (order) {
          // For purchase orders, convert our simple order to Odoo format
          if (order === 'date_order desc') {
            options.order = 'date_order desc';
          } else {
            options.order = order;
          }
        }
        
        // For purchase orders, we need to include order_line to get the IDs
        let fieldsToUse = fields;
        
        result = await odoo.searchRead(model, domain || [], fieldsToUse || [], 0, options.limit);
        
        // Special handling for different models
        if (model === 'purchase.order') {
          // Log what we got from Odoo
          console.log('Purchase order from Odoo:', JSON.stringify(result[0], null, 2));
          
          // Return orders as-is without modifying fields
          return new Response(
            JSON.stringify({ orders: result }),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
          );
        } else if (model === 'res.partner') {
          return new Response(
            JSON.stringify({ partners: result }),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
          );
        } else if (model === 'product.product') {
          return new Response(
            JSON.stringify({ products: result }),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
          );
        } else if (model === 'purchase.order.line') {
          return new Response(
            JSON.stringify({ lines: result }),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
          );
        }
        break;

      case 'read':
        result = await odoo.execute(model, 'read', [ids || [], fields || []]);
        
        if (model === 'purchase.order.line') {
          return new Response(
            JSON.stringify({ lines: result }),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
          );
        } else {
          // Return the raw result for other models
          return new Response(
            JSON.stringify(result),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
          );
        }
        break;

      case 'create':
        console.log('Create request:', { model, data });
        
        // Validate and prepare data for Odoo
        if (model === 'purchase.order') {
          // Ensure required fields
          if (!data.partner_id) {
            throw new Error('partner_id is required for purchase orders');
          }
          
          // Transform order_line data if present
          if (data.order_line && Array.isArray(data.order_line)) {
            // Calculate date_planned (7 days from order date)
            const orderDate = new Date(data.date_order || new Date());
            const datePlanned = new Date(orderDate);
            datePlanned.setDate(datePlanned.getDate() + 7);
            const formattedDatePlanned = `${datePlanned.getFullYear()}-${String(datePlanned.getMonth() + 1).padStart(2, '0')}-${String(datePlanned.getDate()).padStart(2, '0')} ${String(datePlanned.getHours()).padStart(2, '0')}:${String(datePlanned.getMinutes()).padStart(2, '0')}:${String(datePlanned.getSeconds()).padStart(2, '0')}`;
            
            data.order_line = data.order_line.map((line: any) => {
              // Odoo expects order lines in a specific format: (0, 0, {...})
              console.log('Processing order line:', JSON.stringify(line, null, 2));
              const quantity = line.product_qty || line.quantity || 1;
              console.log(`Line quantity: ${quantity} (from product_qty: ${line.product_qty}, quantity: ${line.quantity})`);
              
              const transformedLine = [0, 0, {
                product_id: line.product_id,
                name: line.name || '',
                product_qty: quantity, // Use product_qty for purchase.order.line
                price_unit: line.price_unit || 0,
                product_uom_id: line.product_uom_id || line.product_uom || 1, // Use product_uom_id for Odoo 18.4
                date_planned: formattedDatePlanned
              }];
              
              console.log('Transformed line:', JSON.stringify(transformedLine, null, 2));
              return transformedLine;
            });
          }
          
          console.log('Transformed purchase order data:', JSON.stringify(data, null, 2));
        }
        
        console.log('About to execute create with model:', model);
        console.log('Final data being sent to Odoo:', JSON.stringify(data, null, 2));
        result = await odoo.execute(model, 'create', [data]);
        console.log('Odoo create result:', result);
        return new Response(
          JSON.stringify({ id: result }),
          { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        );

      case 'write':
        // Update records
        const values = requestBody.values || data || {};
        result = await odoo.execute(model, 'write', [ids || [], values]);
        return new Response(
          JSON.stringify({ success: result }),
          { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        );

      case 'button_confirm':
        // Special method for confirming purchase orders
        result = await odoo.execute(model, 'button_confirm', ids || []);
        return new Response(
          JSON.stringify({ success: true }),
          { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        );

      case 'fields_get':
        // Get field definitions for a model
        const attributes = requestBody.attributes || ['string', 'type', 'help', 'readonly', 'required'];
        result = await odoo.execute(model, 'fields_get', [[], attributes]);
        return new Response(
          JSON.stringify({ fields: result }),
          { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        );

      default:
        throw new Error(`Unsupported method: ${method}`);
    }

    return new Response(
      JSON.stringify({ result }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('Odoo API error:', error);
    console.error('Error stack:', error.stack);
    
    // More detailed error response
    const errorResponse = {
      error: error.message || 'Unknown error',
      details: error.stack || '',
      type: error.constructor.name
    };
    
    return new Response(
      JSON.stringify(errorResponse),
      { 
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    );
  }
});