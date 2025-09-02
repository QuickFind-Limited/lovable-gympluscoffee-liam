import { serve } from 'https://deno.land/std@0.190.0/http/server.ts';
import { OdooClient } from '../_shared/odoo-client.ts';
import { corsHeaders, getCorsHeaders } from '../_shared/cors.ts';

serve(async (req: Request) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const odoo = new OdooClient();
    await odoo.connect();

    // Test different approaches
    const results = {
      searchCount: 0,
      searchIds: [],
      searchReadResults: [],
      directSearch: [],
      templateSearch: [],
      searchWithOffset: [],
      pythonStyleSearch: [],
      rawExecuteKw: []
    };

    // 1. Count products
    results.searchCount = await odoo.searchCount('product.product', []);
    
    // 2. Basic search
    results.searchIds = await odoo.execute('product.product', 'search', [[], 0, 10]);
    
    // 3. Search read
    results.searchReadResults = await odoo.searchRead(
      'product.product',
      [],
      ['id', 'name', 'default_code'],
      0,
      10
    );
    
    // 4. Direct execute with search_read
    results.directSearch = await odoo.execute('product.product', 'search_read', [
      [],
      ['id', 'name'],
      0,
      10
    ]);
    
    // 5. Product templates
    results.templateSearch = await odoo.searchRead(
      'product.template',
      [],
      ['id', 'name', 'default_code'],
      0,
      10
    );
    
    // 6. Search with specific offset format
    results.searchWithOffset = await odoo.execute('product.product', 'search_read', [
      [],
      {
        fields: ['id', 'name'],
        offset: 0,
        limit: 10
      }
    ]);
    
    // 7. Try Python-style parameters (matching what works in Python)
    try {
      const object = (odoo as any).object || await (async () => {
        const { createClient } = await import('../_shared/xmlrpc-client.ts');
        return createClient(`${(odoo as any).url}/xmlrpc/2/object`);
      })();
      
      results.pythonStyleSearch = await object.methodCall('execute_kw', [
        (odoo as any).db || 'source-animalfarmacy',
        (odoo as any).uid || await odoo.connect(),
        (odoo as any).password || 'BJ62wX2J4yzjS$i',
        'product.product',
        'search_read',
        [[]],
        {'limit': 5}
      ]);
    } catch (e) {
      results.pythonStyleSearch = { error: e.message };
    }
    
    // 8. Try raw execute_kw with different parameter structures
    try {
      results.rawExecuteKw = await odoo.execute('product.product', 'search_read', [
        [],
        {'limit': 5, 'fields': ['id', 'name']}
      ]);
    } catch (e) {
      results.rawExecuteKw = { error: e.message };
    }

    return new Response(
      JSON.stringify(results, null, 2),
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
        error: error.message || 'Failed to test searchRead',
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