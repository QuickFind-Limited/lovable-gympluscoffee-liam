import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';
import { corsHeaders } from '../_shared/cors.ts';

const ODOO_URL = Deno.env.get('ODOO_URL') || 'https://source-gym-plus-coffee.odoo.com/';
const ODOO_DB = Deno.env.get('ODOO_DATABASE') || 'source-gym-plus-coffee';
const ODOO_USERNAME = Deno.env.get('ODOO_USERNAME') || 'admin@quickfindai.com';
const ODOO_PASSWORD = Deno.env.get('ODOO_PASSWORD') || 'BJ62wX2J4yzjS$i';

interface ProductMOQRequest {
  id: string | number;
  name: string;
  supplier?: string;
}

interface MOQData {
  productId: string | number;
  productName: string;
  moq: number;
  supplier?: string;
  price?: number;
  source: 'odoo' | 'default' | 'fallback';
}

/**
 * Fetch MOQ (Minimum Order Quantity) data from Odoo
 * Queries the product.supplierinfo model for min_qty fields
 */
Deno.serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    const { products }: { products: ProductMOQRequest[] } = await req.json();

    if (!products || !Array.isArray(products) || products.length === 0) {
      return new Response(
        JSON.stringify({ 
          error: 'Invalid request: products array is required',
          moqData: []
        }),
        { 
          status: 400, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      );
    }

    console.log(`Fetching MOQ data for ${products.length} products`);

    // Authenticate with Odoo
    const authenticateResponse = await fetch(`${ODOO_URL}/web/session/authenticate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'call',
        params: {
          db: ODOO_DB,
          login: ODOO_USERNAME,
          password: ODOO_PASSWORD
        },
        id: Math.random()
      })
    });

    if (!authenticateResponse.ok) {
      throw new Error(`Odoo authentication failed: ${authenticateResponse.statusText}`);
    }

    const authData = await authenticateResponse.json();
    
    if (authData.error) {
      throw new Error(`Odoo authentication error: ${authData.error.message}`);
    }

    const uid = authData.result?.uid;
    if (!uid) {
      throw new Error('Failed to get user ID from Odoo authentication');
    }

    // Extract product names for search
    const productNames = products.map(p => p.name);
    
    // Build search domain - search by product name in product.supplierinfo
    const searchDomain = [
      ['product_name', 'ilike', productNames.join('|')]
    ];

    // Fetch MOQ data from product.supplierinfo
    const searchResponse = await fetch(`${ODOO_URL}/web/dataset/call_kw`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Cookie': authenticateResponse.headers.get('set-cookie') || ''
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'call',
        params: {
          model: 'product.supplierinfo',
          method: 'search_read',
          args: [searchDomain],
          kwargs: {
            fields: ['id', 'product_id', 'product_name', 'product_code', 'partner_id', 'min_qty', 'price', 'delay'],
            limit: 100
          }
        },
        id: Math.random()
      })
    });

    if (!searchResponse.ok) {
      throw new Error(`Odoo search failed: ${searchResponse.statusText}`);
    }

    const searchData = await searchResponse.json();
    
    if (searchData.error) {
      throw new Error(`Odoo search error: ${searchData.error.message}`);
    }

    const supplierInfoRecords = searchData.result || [];
    console.log(`Found ${supplierInfoRecords.length} supplier info records`);

    // Process MOQ data
    const moqData: MOQData[] = [];

    for (const product of products) {
      // Find matching supplier info record
      const supplierInfo = supplierInfoRecords.find((record: any) => 
        record.product_name && 
        (record.product_name.toLowerCase().includes(product.name.toLowerCase()) ||
         product.name.toLowerCase().includes(record.product_name.toLowerCase()))
      );

      if (supplierInfo && supplierInfo.min_qty && supplierInfo.min_qty > 0) {
        moqData.push({
          productId: product.id,
          productName: product.name,
          moq: Math.ceil(supplierInfo.min_qty), // Round up to ensure integer
          supplier: supplierInfo.partner_id ? supplierInfo.partner_id[1] : product.supplier,
          price: supplierInfo.price || undefined,
          source: 'odoo' as const
        });
      } else {
        // Fallback to default MOQ of 1
        moqData.push({
          productId: product.id,
          productName: product.name,
          moq: 1,
          supplier: product.supplier,
          source: 'default' as const
        });
      }
    }

    console.log(`Processed MOQ data for ${moqData.length} products`);

    return new Response(
      JSON.stringify({
        success: true,
        moqData,
        recordsFound: supplierInfoRecords.length,
        timestamp: new Date().toISOString()
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    );

  } catch (error) {
    console.error('Error fetching MOQ data:', error);
    
    return new Response(
      JSON.stringify({ 
        error: error.message || 'Internal server error',
        success: false,
        moqData: [],
        timestamp: new Date().toISOString()
      }),
      { 
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    );
  }
});