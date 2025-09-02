import { serve } from 'https://deno.land/std@0.190.0/http/server.ts';
import { OdooClient } from './_shared/odoo-client.ts';
import { corsHeaders, getCorsHeaders } from './_shared/cors.ts';

serve(async (req: Request) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const odoo = new OdooClient();
    await odoo.connect();

    // First, let's just get all partners to see what we have
    const partners = await odoo.searchRead(
      'res.partner',
      [], // No domain filter
      ['id', 'name', 'supplier_rank', 'email', 'city'], // Basic fields
      0,
      10 // Just get first 10
    );

    console.log(`Found ${partners.length} partners`);

    return new Response(
      JSON.stringify({
        partners: partners,
        count: partners.length
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
        error: error.message || 'Failed to fetch partners',
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