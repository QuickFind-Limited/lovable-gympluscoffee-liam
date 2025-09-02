import { serve } from 'https://deno.land/std@0.190.0/http/server.ts';
import { OdooClient } from '../_shared/odoo-client.ts';
import { corsHeaders, getCorsHeaders } from '../_shared/cors.ts';

interface SupplierFilter {
  search?: string;
  offset?: number;
  limit?: number;
  withProducts?: boolean;
}

serve(async (req: Request) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const odoo = new OdooClient();
    await odoo.connect();

    // Parse query parameters
    const url = new URL(req.url);
    const search = url.searchParams.get('search') || '';
    const offset = parseInt(url.searchParams.get('offset') || '0');
    const limit = parseInt(url.searchParams.get('limit') || '50');
    const withProducts = url.searchParams.get('withProducts') === 'true';
    const supplierId = url.searchParams.get('supplierId');

    console.log('Fetching suppliers with params:', { search, offset, limit, withProducts, supplierId });

    // If supplierId is provided, fetch products for that specific supplier
    if (supplierId) {
      console.log(`Fetching products for supplier ID: ${supplierId}`);
      
      // Get supplier products from product.supplierinfo
      const supplierProducts = await odoo.searchRead(
        'product.supplierinfo',
        [['partner_id', '=', parseInt(supplierId)]],
        ['id', 'product_id', 'product_name', 'product_code', 'price', 'min_qty', 'delay'],
        offset,
        limit
      );

      console.log(`Found ${supplierProducts.length} supplier products`);

      // Get full product details if we have product IDs
      const productIds = supplierProducts
        .filter((sp: any) => sp.product_id && sp.product_id[0])
        .map((sp: any) => sp.product_id[0]);

      let products: any[] = [];
      if (productIds.length > 0) {
        products = await odoo.searchRead(
          'product.product',
          [['id', 'in', productIds]],
          ['id', 'name', 'default_code', 'list_price', 'standard_price', 'qty_available', 'uom_id'],
          0,
          productIds.length
        );
      }

      console.log(`Found ${products.length} product details`);

      // Combine supplier info with product details
      const enrichedProducts = supplierProducts.map((sp: any) => {
        const product = products.find((p: any) => p.id === (sp.product_id && sp.product_id[0]));
        return {
          ...sp,
          productDetails: product || null
        };
      });

      // Get total count for pagination
      const totalCount = await odoo.execute('product.supplierinfo', 'search_count', [
        [['partner_id', '=', parseInt(supplierId)]]
      ]);

      return new Response(
        JSON.stringify({
          data: enrichedProducts,
          total: totalCount,
          page: Math.floor(offset / limit),
          pageSize: limit,
          hasMore: offset + limit < totalCount
        }),
        {
          headers: {
            ...getCorsHeaders(req.headers.get('origin')),
            'Content-Type': 'application/json',
          },
        }
      );
    }

    // Build domain for supplier search
    // In Odoo, suppliers are res.partner records with supplier_rank > 0
    const domain: Array<[string, string, number | boolean | string]> = [
      ['supplier_rank', '>', 0],
      ['active', '=', true]
    ];

    // Add search filter if provided
    if (search) {
      domain.push(['name', 'ilike', search]);
    }

    // Fields to fetch for suppliers - test with basic contact fields
    const supplierFields = [
      'id',
      'name',
      'supplier_rank',
      'email',
      'phone',
      'city'
    ];

    // Fetch suppliers
    const suppliers = await odoo.searchRead(
      'res.partner',
      domain,
      supplierFields,
      offset,
      limit
    );

    console.log(`Found ${suppliers.length} suppliers`);
    if (suppliers.length > 0) {
      console.log('First supplier data:', JSON.stringify(suppliers[0], null, 2));
    }

    // If withProducts is true, fetch product information for each supplier
    let suppliersWithProducts = suppliers;
    if (withProducts && suppliers.length > 0) {
      // For each supplier, fetch their product information
      suppliersWithProducts = await Promise.all(suppliers.map(async (supplier) => {
        try {
          // Get products from this supplier
          // In Odoo, supplier info is typically stored in product.supplierinfo
          const supplierInfoDomain = [['partner_id', '=', supplier.id]];
          const supplierInfos = await odoo.searchRead(
            'product.supplierinfo',
            supplierInfoDomain,
            [
              'id',
              'product_id',
              'product_name',
              'product_code',
              'min_qty',
              'price',
              'delay',
              'currency_id'
            ],
            0,
            100 // Limit products per supplier
          );

          // Get product details for each supplier info
          const productsWithDetails = await Promise.all(supplierInfos.map(async (info) => {
            if (info.product_id && info.product_id[0]) {
              try {
                const products = await odoo.searchRead(
                  'product.product',
                  [['id', '=', info.product_id[0]]],
                  ['id', 'name', 'default_code', 'qty_available', 'virtual_available', 'list_price'],
                  0,
                  1
                );

                if (products.length > 0) {
                  return {
                    ...info,
                    product_details: products[0]
                  };
                }
              } catch (error) {
                console.error(`Error fetching product ${info.product_id[0]}:`, error);
              }
            }
            return info;
          }));

          return {
            ...supplier,
            products: productsWithDetails,
            product_count: productsWithDetails.length
          };
        } catch (error) {
          console.error(`Error fetching products for supplier ${supplier.id}:`, error);
          return {
            ...supplier,
            products: [],
            product_count: 0
          };
        }
      }));
    }

    // Get total count for pagination
    const countDomain = [...domain];
    const totalCount = await odoo.execute('res.partner', 'search_count', [countDomain]);

    return new Response(
      JSON.stringify({
        suppliers: suppliersWithProducts,
        pagination: {
          offset,
          limit,
          total: totalCount,
          hasMore: offset + limit < totalCount
        }
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
        error: error.message || 'Failed to fetch suppliers',
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