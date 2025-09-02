import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';
import { z } from 'https://deno.land/x/zod@v3.22.4/mod.ts';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE',
};

// Request schema
const ImageRequestSchema = z.object({
  product_ids: z.array(z.number()).min(1).max(20), // Limit to prevent huge requests
  image_size: z.enum(['image_128', 'image_256', 'image_512', 'image_1024']).default('image_256')
});

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

// Parse image data from XML
function parseImageStruct(structXml: string, imageField: string): any {
  const result: any = {};
  
  // Extract all members
  const memberRegex = /<member>\s*<name>(.*?)<\/name>\s*<value>([\s\S]*?)<\/value>\s*<\/member>/g;
  let match;
  
  while ((match = memberRegex.exec(structXml)) !== null) {
    const name = match[1];
    const valueXml = match[2];
    
    // We only need id and the image field
    if (name === 'id') {
      const intMatch = valueXml.match(/<int>(\d+)<\/int>/);
      result.id = intMatch ? parseInt(intMatch[1], 10) : 0;
    } else if (name === imageField) {
      const strMatch = valueXml.match(/<string>(.*?)<\/string>/);
      result[imageField] = strMatch ? strMatch[1] : '';
    }
  }
  
  return result;
}

// Parse array of image data from XML response
function parseImageArray(xml: string, imageField: string): any[] {
  const images = [];
  
  // Find the array data section
  const arrayMatch = xml.match(/<array><data>([\s\S]*?)<\/data><\/array>/);
  if (!arrayMatch) return [];
  
  const arrayData = arrayMatch[1];
  
  // Extract all struct values
  const structRegex = /<value><struct>([\s\S]*?)<\/struct><\/value>/g;
  let match;
  
  while ((match = structRegex.exec(arrayData)) !== null) {
    const imageData = parseImageStruct(match[1], imageField);
    if (imageData.id && imageData[imageField]) {
      images.push({
        id: imageData.id,
        image: imageData[imageField]
      });
    }
  }
  
  return images;
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const body = await req.json();
    const validatedData = ImageRequestSchema.parse(body);
    
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
    
    // Step 2: Fetch images for specific products
    const readXml = buildXmlRequest('execute_kw', [
      'source-animalfarmacy',
      uid,
      'BJ62wX2J4yzjS$i',
      'product.product',
      'read',
      [
        validatedData.product_ids,
        ['id', validatedData.image_size] // Only fetch ID and requested image size
      ]
    ]);
    
    const readResponse = await fetch('https://source-animalfarmacy.odoo.com/xmlrpc/2/object', {
      method: 'POST',
      headers: { 'Content-Type': 'text/xml' },
      body: readXml
    });
    
    const readText = await readResponse.text();
    
    // Parse the image data
    const images = parseImageArray(readText, validatedData.image_size);
    
    // Transform to match frontend expectations
    const imageMap: Record<string, string> = {};
    images.forEach(img => {
      imageMap[img.id] = img.image ? `data:image/png;base64,${img.image}` : '';
    });
    
    return new Response(
      JSON.stringify({ 
        images: imageMap,
        size: validatedData.image_size 
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
    
  } catch (error) {
    console.error('Error in odoo-product-images:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    
    return new Response(
      JSON.stringify({ error: errorMessage }),
      { 
        status: error instanceof z.ZodError ? 400 : 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    );
  }
});