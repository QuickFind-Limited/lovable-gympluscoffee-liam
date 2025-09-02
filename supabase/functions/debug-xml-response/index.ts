import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE',
};

// Simple XML builder for Odoo
function buildXmlRequest(method: string, params: any[]): string {
  const encodeValue = (value: any): string => {
    if (value === null || value === undefined) {
      return '<nil/>';
    }
    if (typeof value === 'boolean') {
      return `<boolean>${value ? '1' : '0'}</boolean>`;
    }
    if (typeof value === 'number') {
      if (Number.isInteger(value)) {
        return `<int>${value}</int>`;
      }
      return `<double>${value}</double>`;
    }
    if (typeof value === 'string') {
      return `<string>${escapeXml(value)}</string>`;
    }
    if (Array.isArray(value)) {
      const items = value.map(v => `<value>${encodeValue(v)}</value>`).join('');
      return `<array><data>${items}</data></array>`;
    }
    if (typeof value === 'object') {
      const members = Object.entries(value).map(([k, v]) => 
        `<member><name>${k}</name><value>${encodeValue(v)}</value></member>`
      ).join('');
      return `<struct>${members}</struct>`;
    }
    return `<string>${escapeXml(String(value))}</string>`;
  };

  const escapeXml = (str: string): string => {
    return str.replace(/[<>&'"]/g, (c) => {
      switch (c) {
        case '<': return '&lt;';
        case '>': return '&gt;';
        case '&': return '&amp;';
        case "'": return '&apos;';
        case '"': return '&quot;';
        default: return c;
      }
    });
  };

  const paramXml = params.map(p => `<param><value>${encodeValue(p)}</value></param>`).join('');
  
  return `<?xml version="1.0" encoding="UTF-8"?>
<methodCall>
  <methodName>${method}</methodName>
  <params>${paramXml}</params>
</methodCall>`;
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const body = await req.json();
    const { query = 'acra' } = body;
    
    // Step 1: Authenticate
    const authXml = buildXmlRequest('authenticate', [
      'source-animalfarmacy',
      'admin@quickfindai.com',
      'BJ62wX2J4yzjS$i',
      {}
    ]);
    
    const authResponse = await fetch('https://source-animalfarmacy.odoo.com/xmlrpc/2/common', {
      method: 'POST',
      headers: { 'Content-Type': 'text/xml' },
      body: authXml
    });
    
    const authText = await authResponse.text();
    
    // Extract UID from auth response
    const uidMatch = authText.match(/<int>(\d+)<\/int>/);
    const uid = uidMatch ? parseInt(uidMatch[1], 10) : null;
    
    if (!uid) {
      throw new Error('Authentication failed');
    }
    
    // Step 2: Search products (WITHOUT image_1920!)
    const searchXml = buildXmlRequest('execute_kw', [
      'source-animalfarmacy',
      uid,
      'BJ62wX2J4yzjS$i',
      'product.product',
      'search_read',
      [
        [['name', 'ilike', query]],
        ['id', 'name', 'display_name', 'list_price']
      ],
      { offset: 0, limit: 20 }
    ]);
    
    const searchResponse = await fetch('https://source-animalfarmacy.odoo.com/xmlrpc/2/object', {
      method: 'POST',
      headers: { 'Content-Type': 'text/xml' },
      body: searchXml
    });
    
    const searchText = await searchResponse.text();
    
    // Return raw XML for debugging
    return new Response(
      JSON.stringify({ 
        uid,
        searchRequestSize: searchXml.length,
        searchResponseSize: searchText.length,
        rawResponse: searchText.substring(0, 2000) + (searchText.length > 2000 ? '...[TRUNCATED]' : '')
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