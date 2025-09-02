import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';
import { OdooClient } from '../_shared/odoo-client.ts';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE',
};

// Build XML-RPC request (fixed version from product-search)
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

// Parse product struct from XML
function parseStruct(structXml: string): any {
  const result: any = {};
  
  // Extract all members
  const memberRegex = /<member>\s*<name>(.*?)<\/name>\s*<value>([\s\S]*?)<\/value>\s*<\/member>/g;
  let match;
  
  while ((match = memberRegex.exec(structXml)) !== null) {
    const name = match[1];
    const valueXml = match[2];
    
    // Parse the value based on type
    if (valueXml.includes('<int>')) {
      const intMatch = valueXml.match(/<int>(\d+)<\/int>/);
      result[name] = intMatch ? parseInt(intMatch[1], 10) : 0;
    } else if (valueXml.includes('<string>')) {
      const strMatch = valueXml.match(/<string>(.*?)<\/string>/);
      result[name] = strMatch ? strMatch[1] : '';
    } else if (valueXml.includes('<double>')) {
      const dblMatch = valueXml.match(/<double>([\d.]+)<\/double>/);
      result[name] = dblMatch ? parseFloat(dblMatch[1]) : 0;
    } else if (valueXml.includes('<array>')) {
      // Handle categ_id array [id, name] with flexible whitespace
      const arrayDataMatch = valueXml.match(/<array>\s*<data>([\s\S]*?)<\/data>\s*<\/array>/);
      if (arrayDataMatch) {
        const arrayData = arrayDataMatch[1];
        const idMatch = arrayData.match(/<value>\s*<int>(\d+)<\/int>\s*<\/value>/);
        const nameMatch = arrayData.match(/<value>\s*<string>(.*?)<\/string>\s*<\/value>/);
        if (idMatch && nameMatch) {
          result[name] = [parseInt(idMatch[1]), nameMatch[1]];
        }
      }
    }
  }
  
  return result;
}

// Parse array of products from XML response
function parseProductArray(xml: string): any[] {
  const products = [];
  
  // First find the methodResponse params section
  const paramsMatch = xml.match(/<params>\s*<param>\s*<value>([\s\S]*?)<\/value>\s*<\/param>\s*<\/params>/);
  if (!paramsMatch) return [];
  
  const paramValue = paramsMatch[1];
  
  // Extract products by finding each <value><struct>...<\/struct><\/value> pattern
  // We need to be careful with nested structures
  let currentPos = 0;
  
  while (true) {
    const structStart = paramValue.indexOf('<value><struct>', currentPos);
    if (structStart === -1) break;
    
    const structEnd = paramValue.indexOf('</struct></value>', structStart);
    if (structEnd === -1) break;
    
    const structContent = paramValue.substring(structStart + '<value><struct>'.length, structEnd);
    const product = parseStruct(structContent);
    
    if (product.id) {
      products.push(product);
    }
    
    currentPos = structEnd + '</struct></value>'.length;
  }
  
  return products;
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const body = await req.json();
    const { offset = 0, limit = 20, search = '', category = null, vendor = null } = body;
    
    // Step 1: Authenticate using shared OdooClient
    const client = new OdooClient();
    const uid = await client.connect();
    
    if (!uid) {
      throw new Error('Authentication failed');
    }
    
    // Get credentials from environment
    const odooUrl = Deno.env.get('ODOO_URL')?.replace(/\/$/, '');
    const odooDb = Deno.env.get('ODOO_DATABASE');
    const odooPassword = Deno.env.get('ODOO_PASSWORD');
    
    // Step 2: Build search domain
    const domain: any[] = [];
    if (search) {
      domain.push(['name', 'ilike', search]);
    }
    if (category) {
      domain.push(['categ_id', '=', category]);
    }
    
    // Step 3: Get total count
    const countXml = buildXmlRequest('execute_kw', [
      odooDb,
      uid,
      odooPassword,
      'product.product',
      'search_count',
      [domain]
    ]);

    const countResponse = await fetch(`${odooUrl}/xmlrpc/2/object`, {
      method: 'POST',
      headers: { 'Content-Type': 'text/xml' },
      body: countXml
    });

    const countText = await countResponse.text();
    const countMatch = countText.match(/<int>(\d+)<\/int>/);
    const totalCount = countMatch ? parseInt(countMatch[1], 10) : 0;
    
    // Step 4: Search products
    const searchXml = buildXmlRequest('execute_kw', [
      odooDb,
      uid,
      odooPassword,
      'product.product',
      'search_read',
      [
        domain,
        ['id', 'name', 'display_name', 'list_price', 'default_code', 'qty_available', 'categ_id']
      ],
      { offset, limit, order: 'name' }
    ]);
    
    const searchResponse = await fetch(`${odooUrl}/xmlrpc/2/object`, {
      method: 'POST',
      headers: { 'Content-Type': 'text/xml' },
      body: searchXml
    });
    
    const searchText = await searchResponse.text();
    
    // Use the proven parsing logic from product-search function
    const products = parseProductArray(searchText);
    
    return new Response(
      JSON.stringify({ 
        products,
        total_count: totalCount,
        offset,
        limit,
        images_available: true,
        image_endpoint: 'product-images'
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