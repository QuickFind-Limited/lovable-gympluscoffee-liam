import { serve } from 'https://deno.land/std@0.190.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';
import { OdooClient } from "../_shared/odoo-client.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type, x-application-name',
  'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE',
};

serve(async (req: Request) => {
  // Allow public access for read-only operations
  // This edge function doesn't modify data, just reads supplier info
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const url = new URL(req.url);
    const withProducts = url.searchParams.get('withProducts') === 'true';
    const supplierId = url.searchParams.get('supplierId');
    const offset = parseInt(url.searchParams.get('offset') || '0');
    const limit = parseInt(url.searchParams.get('limit') || '10');

    // Initialize Odoo client
    const odoo = new OdooClient();
    await odoo.connect();

    // If fetching products for a specific supplier
    if (supplierId) {
      console.log(`🔵 Fetching products for supplier ${supplierId}, offset: ${offset}, limit: ${limit}`);
      
      // First test searchCount to confirm it works
      const totalCount = await odoo.searchCount(
        'product.supplierinfo',
        [['partner_id', '=', parseInt(supplierId)]]
      );
      console.log(`🔍 SearchCount result: ${totalCount} products found`);
      
      // Now test searchRead with detailed logging
      console.log(`🔵 Calling searchRead with parameters:`);
      console.log(`- model: product.supplierinfo`);
      console.log(`- domain: ${JSON.stringify([['partner_id', '=', parseInt(supplierId)]])}`); 
      console.log(`- fields: ${JSON.stringify(['id', 'product_id', 'product_name', 'product_code', 'price', 'min_qty', 'delay'])}`); 
      console.log(`- offset: ${offset}, limit: ${limit}`);
      
      // Fetch supplier info WITHOUT product_tmpl_id (it causes empty results)
      console.log(`🔍 Fetching supplier products (without product_tmpl_id to avoid empty results)`);
      const products = await odoo.searchRead(
        'product.supplierinfo',
        [['partner_id', '=', parseInt(supplierId)]],
        ['id', 'product_name', 'product_code', 'price', 'min_qty', 'delay'], // Removed product_tmpl_id - it causes empty results!
        offset,
        limit
      );
      console.log(`✅ SearchRead result: Found ${products.length} products for supplier ${supplierId}`);
      
      if (products.length === 0) {
        console.log(`⚠️  WARNING: SearchRead returned empty array despite searchCount showing ${totalCount} products`);
        console.log(`🔍 This indicates a parameter serialization issue in the XML-RPC client`);
      }

      // Parse metadata from product names if present
      for (const product of products) {
        // Check if product name contains metadata
        if (product.product_name && product.product_name.includes('|META|')) {
          const parts = product.product_name.split('|META|');
          if (parts.length === 2) {
            // Extract the clean product name
            product.product_name = parts[0].trim();
            
            // Parse the metadata
            try {
              // The metadata might be a Python dict string, convert to JSON
              let metadataStr = parts[1].trim();
              // Replace Python dict format with JSON format
              metadataStr = metadataStr.replace(/'/g, '"');
              
              const metadata = JSON.parse(metadataStr);
              
              // Apply metadata to product
              if (metadata.pack_size !== undefined) product.pack_size = metadata.pack_size;
              if (metadata.minimum_level !== undefined) product.minimum_level = metadata.minimum_level;
              if (metadata.qty_available !== undefined) product.qty_available = metadata.qty_available;
              if (metadata.virtual_available !== undefined) product.virtual_available = metadata.virtual_available;
              
              console.log(`📦 Parsed metadata for product ${product.id}:`, metadata);
            } catch (e) {
              console.log(`⚠️  Could not parse metadata for product ${product.id}:`, e);
              // Set defaults if metadata parsing fails
              product.qty_available = 0;
              product.virtual_available = 0;
              product.minimum_level = 10;
              product.pack_size = 1;
            }
          }
        } else {
          // Set defaults if no metadata
          product.qty_available = 0;
          product.virtual_available = 0;
          product.minimum_level = 10;
          product.pack_size = 1;
        }
        
        // Ensure min_qty has a default
        if (!product.min_qty) product.min_qty = 1;
        if (!product.price) product.price = 0;
        if (!product.delay) product.delay = 0;
      }

      // Use the totalCount we already fetched above

      console.log(`Returning response: ${products.length} products, total: ${totalCount}`);
      
      return new Response(
        JSON.stringify({
          data: products,
          total: totalCount,
          page: Math.floor(offset / limit),
          pageSize: limit,
          hasMore: offset + limit < totalCount
        }),
        {
          headers: {
            ...corsHeaders,
            'Content-Type': 'application/json',
          },
        }
      );
    }

    // Get suppliers - FIXED VERSION: Use individual parameters for search method
    const supplierIds = await odoo.execute('res.partner', 'search', [
      [['supplier_rank', '>', 0]],
      offset,  // Pass offset and limit as separate parameters
      limit
    ]);

    // Read supplier details
    let suppliers: any[] = [];
    if (supplierIds.length > 0) {
      suppliers = await odoo.execute('res.partner', 'read', [
        supplierIds,
        ['id', 'name', 'email', 'phone', 'city', 'supplier_rank']
      ]);

      // If withProducts, get product count for each supplier
      if (withProducts && suppliers.length > 0) {
        console.log(`Getting product counts for ${suppliers.length} suppliers`);
        for (const supplier of suppliers) {
          const productCount = await odoo.searchCount(
            'product.supplierinfo',
            [['partner_id', '=', supplier.id]]
          );
          console.log(`Supplier ${supplier.name} (ID: ${supplier.id}) has ${productCount} products`);
          supplier.product_count = productCount;
          supplier.products = []; // Empty array for now, filled when expanded
        }
      }
    }

    // Get total count
    const totalCount = await odoo.searchCount(
      'res.partner',
      [['supplier_rank', '>', 0]]
    );

    return new Response(
      JSON.stringify({
        suppliers: suppliers,
        pagination: {
          offset,
          limit,
          total: totalCount,
          hasMore: offset + limit < totalCount
        }
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
        error: error.message || 'Failed to fetch from Odoo',
        details: error.stack
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