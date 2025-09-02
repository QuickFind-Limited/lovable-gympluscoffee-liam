import { serve } from 'https://deno.land/std@0.190.0/http/server.ts';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type, x-application-name',
  'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE',
};

// Parse XML struct into object
function parseStruct(structXml) {
  const obj = {};
  
  // Match all members in the struct
  const memberRegex = /<member>\s*<name>(.*?)<\/name>\s*<value>(.*?)<\/value>\s*<\/member>/gs;
  let match;
  
  while ((match = memberRegex.exec(structXml)) !== null) {
    const name = match[1];
    const valueXml = match[2];
    
    // Parse the value
    if (valueXml.includes('<string>')) {
      const stringMatch = valueXml.match(/<string>(.*?)<\/string>/s);
      obj[name] = stringMatch ? stringMatch[1] : '';
    } else if (valueXml.includes('<int>')) {
      const intMatch = valueXml.match(/<int>(\d+)<\/int>/);
      obj[name] = intMatch ? parseInt(intMatch[1]) : 0;
    } else if (valueXml.includes('<double>')) {
      const doubleMatch = valueXml.match(/<double>([\d.-]+)<\/double>/);
      obj[name] = doubleMatch ? parseFloat(doubleMatch[1]) : 0;
    } else if (valueXml.includes('<boolean>')) {
      const boolMatch = valueXml.match(/<boolean>([01])<\/boolean>/);
      obj[name] = boolMatch ? boolMatch[1] === '1' : false;
    } else if (valueXml.includes('<array>')) {
      // Handle arrays (like product_id)
      const arrayValues = [];
      const valueMatches = valueXml.matchAll(/<value>(.*?)<\/value>/gs);
      for (const valMatch of valueMatches) {
        const innerXml = valMatch[1];
        if (innerXml.includes('<int>')) {
          const intMatch = innerXml.match(/<int>(\d+)<\/int>/);
          if (intMatch) arrayValues.push(parseInt(intMatch[1]));
        } else if (innerXml.includes('<string>')) {
          const stringMatch = innerXml.match(/<string>(.*?)<\/string>/s);
          if (stringMatch) arrayValues.push(stringMatch[1]);
        }
      }
      obj[name] = arrayValues;
    } else if (valueXml.includes('<nil/>')) {
      obj[name] = null;
    }
  }
  
  return obj;
}

// Parse array of structs from XML response
function parseStructArray(xml) {
  const results = [];
  
  // Match all struct blocks
  const structRegex = /<value><struct>(.*?)<\/struct><\/value>/gs;
  let match;
  
  while ((match = structRegex.exec(xml)) !== null) {
    const structXml = match[1];
    results.push(parseStruct(structXml));
  }
  
  return results;
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const url = new URL(req.url);
    const withProducts = url.searchParams.get('withProducts') === 'true';
    const supplierId = url.searchParams.get('supplierId');
    const offset = parseInt(url.searchParams.get('offset') || '0');
    const limit = parseInt(url.searchParams.get('limit') || '10');

    console.log('Request params:', { withProducts, supplierId, offset, limit });

    // Odoo connection details
    const odooUrl = 'https://source-animalfarmacy.odoo.com';
    const db = 'source-animalfarmacy';
    const username = 'admin@quickfindai.com';
    const password = 'BJ62wX2J4yzjS$i';

    // Step 1: Authenticate
    const authRequest = `<?xml version="1.0"?>
<methodCall>
  <methodName>authenticate</methodName>
  <params>
    <param><value><string>${db}</string></value></param>
    <param><value><string>${username}</string></value></param>
    <param><value><string>${password}</string></value></param>
    <param><value><struct></struct></value></param>
  </params>
</methodCall>`;

    const authResponse = await fetch(`${odooUrl}/xmlrpc/2/common`, {
      method: 'POST',
      headers: {
        'Content-Type': 'text/xml',
        'Accept': 'text/xml',
      },
      body: authRequest,
    });

    const authXml = await authResponse.text();
    const uidMatch = authXml.match(/<value><int>(\d+)<\/int><\/value>/);
    if (!uidMatch) {
      throw new Error('Failed to authenticate');
    }
    const uid = parseInt(uidMatch[1]);
    console.log('Authenticated with UID:', uid);

    // If fetching products for a specific supplier
    if (supplierId) {
      console.log('Fetching products for supplier:', supplierId);
      const productSearchRequest = `<?xml version="1.0"?>
<methodCall>
  <methodName>execute_kw</methodName>
  <params>
    <param><value><string>${db}</string></value></param>
    <param><value><int>${uid}</int></value></param>
    <param><value><string>${password}</string></value></param>
    <param><value><string>product.supplierinfo</string></value></param>
    <param><value><string>search_read</string></value></param>
    <param><value><array><data>
      <value><array><data>
        <value><array><data>
          <value><string>partner_id</string></value>
          <value><string>=</string></value>
          <value><int>${parseInt(supplierId)}</int></value>
        </data></array></value>
      </data></array></value>
    </data></array></value></param>
    <param><value><struct>
      <member>
        <name>fields</name>
        <value><array><data>
          <value><string>id</string></value>
          <value><string>product_id</string></value>
          <value><string>product_name</string></value>
          <value><string>product_code</string></value>
          <value><string>price</string></value>
          <value><string>min_qty</string></value>
          <value><string>delay</string></value>
        </data></array></value>
      </member>
      <member>
        <name>offset</name>
        <value><int>${offset}</int></value>
      </member>
      <member>
        <name>limit</name>
        <value><int>${limit}</int></value>
      </member>
    </struct></value></param>
  </params>
</methodCall>`;

      const productResponse = await fetch(`${odooUrl}/xmlrpc/2/object`, {
        method: 'POST',
        headers: {
          'Content-Type': 'text/xml',
          'Accept': 'text/xml',
        },
        body: productSearchRequest,
      });

      const productXml = await productResponse.text();
      const products = parseStructArray(productXml);
      console.log('Found products:', products.length);

      // Parse metadata from product names
      for (const product of products) {
        // Extract metadata from product_name if it contains |META|
        if (product.product_name && product.product_name.includes('|META|')) {
          const parts = product.product_name.split('|META|');
          if (parts.length === 2) {
            // Update product_name to clean version
            product.product_name = parts[0].trim();
            
            // Parse JSON metadata
            try {
              const metadata = JSON.parse(parts[1]);
              product.qty_available = metadata.qty_available || 0;
              product.virtual_available = metadata.virtual_available || 0;
              product.minimum_level = metadata.minimum_level || null;
              product.pack_size = metadata.pack_size || 1;
            } catch (e) {
              console.error('Error parsing metadata:', e);
              // Fallback values
              product.qty_available = 0;
              product.virtual_available = 0;
              product.minimum_level = null;
              product.pack_size = 1;
            }
          }
        } else {
          // Fallback for products without metadata
          product.qty_available = 0;
          product.virtual_available = 0;
          product.minimum_level = null;
          product.pack_size = 1;
        }
      }

      // Get total count
      const countRequest = `<?xml version="1.0"?>
<methodCall>
  <methodName>execute_kw</methodName>
  <params>
    <param><value><string>${db}</string></value></param>
    <param><value><int>${uid}</int></value></param>
    <param><value><string>${password}</string></value></param>
    <param><value><string>product.supplierinfo</string></value></param>
    <param><value><string>search_count</string></value></param>
    <param><value><array><data>
      <value><array><data>
        <value><array><data>
          <value><string>partner_id</string></value>
          <value><string>=</string></value>
          <value><int>${parseInt(supplierId)}</int></value>
        </data></array></value>
      </data></array></value>
    </data></array></value></param>
  </params>
</methodCall>`;

      const countResponse = await fetch(`${odooUrl}/xmlrpc/2/object`, {
        method: 'POST',
        headers: {
          'Content-Type': 'text/xml',
          'Accept': 'text/xml',
        },
        body: countRequest,
      });

      const countXml = await countResponse.text();
      const countMatch = countXml.match(/<value><int>(\d+)<\/int><\/value>/);
      const totalCount = countMatch ? parseInt(countMatch[1]) : 0;

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

    // Step 2: Search for supplier IDs
    console.log('Searching for suppliers...');
    const searchRequest = `<?xml version="1.0"?>
<methodCall>
  <methodName>execute_kw</methodName>
  <params>
    <param><value><string>${db}</string></value></param>
    <param><value><int>${uid}</int></value></param>
    <param><value><string>${password}</string></value></param>
    <param><value><string>res.partner</string></value></param>
    <param><value><string>search</string></value></param>
    <param><value><array><data>
      <value><array><data>
        <value><array><data>
          <value><string>supplier_rank</string></value>
          <value><string>&gt;</string></value>
          <value><int>0</int></value>
        </data></array></value>
      </data></array></value>
    </data></array></value></param>
    <param><value><int>${offset}</int></value></param>
    <param><value><int>${limit}</int></value></param>
  </params>
</methodCall>`;

    const searchResponse = await fetch(`${odooUrl}/xmlrpc/2/object`, {
      method: 'POST',
      headers: {
        'Content-Type': 'text/xml',
        'Accept': 'text/xml',
      },
      body: searchRequest,
    });

    const searchXml = await searchResponse.text();
    
    // Parse supplier IDs
    const supplierIds = [];
    const idMatches = searchXml.matchAll(/<value><int>(\d+)<\/int><\/value>/g);
    for (const match of idMatches) {
      supplierIds.push(parseInt(match[1]));
    }
    console.log('Found supplier IDs:', supplierIds);

    // Step 3: Read supplier details
    let suppliers = [];
    if (supplierIds.length > 0) {
      const readRequest = `<?xml version="1.0"?>
<methodCall>
  <methodName>execute_kw</methodName>
  <params>
    <param><value><string>${db}</string></value></param>
    <param><value><int>${uid}</int></value></param>
    <param><value><string>${password}</string></value></param>
    <param><value><string>res.partner</string></value></param>
    <param><value><string>read</string></value></param>
    <param><value><array><data>
      <value><array><data>
        ${supplierIds.map(id => `<value><int>${id}</int></value>`).join('')}
      </data></array></value>
      <value><array><data>
        <value><string>id</string></value>
        <value><string>name</string></value>
        <value><string>email</string></value>
        <value><string>phone</string></value>
        <value><string>city</string></value>
        <value><string>supplier_rank</string></value>
      </data></array></value>
    </data></array></value></param>
  </params>
</methodCall>`;

      const readResponse = await fetch(`${odooUrl}/xmlrpc/2/object`, {
        method: 'POST',
        headers: {
          'Content-Type': 'text/xml',
          'Accept': 'text/xml',
        },
        body: readRequest,
      });

      const readXml = await readResponse.text();
      suppliers = parseStructArray(readXml);
      console.log('Got supplier details for', suppliers.length, 'suppliers');

      // If withProducts, get product count for each supplier
      if (withProducts && suppliers.length > 0) {
        console.log('Getting product counts for suppliers...');
        for (const supplier of suppliers) {
          const productCountRequest = `<?xml version="1.0"?>
<methodCall>
  <methodName>execute_kw</methodName>
  <params>
    <param><value><string>${db}</string></value></param>
    <param><value><int>${uid}</int></value></param>
    <param><value><string>${password}</string></value></param>
    <param><value><string>product.supplierinfo</string></value></param>
    <param><value><string>search_count</string></value></param>
    <param><value><array><data>
      <value><array><data>
        <value><array><data>
          <value><string>partner_id</string></value>
          <value><string>=</string></value>
          <value><int>${supplier.id}</int></value>
        </data></array></value>
      </data></array></value>
    </data></array></value></param>
  </params>
</methodCall>`;

          const countResponse = await fetch(`${odooUrl}/xmlrpc/2/object`, {
            method: 'POST',
            headers: {
              'Content-Type': 'text/xml',
              'Accept': 'text/xml',
            },
            body: productCountRequest,
          });

          const countXml = await countResponse.text();
          const countMatch = countXml.match(/<value><int>(\d+)<\/int><\/value>/);
          supplier.product_count = countMatch ? parseInt(countMatch[1]) : 0;
          supplier.products = []; // Empty array for now, filled when expanded
          console.log(`Supplier ${supplier.name} has ${supplier.product_count} products`);
        }
      }
    }

    // Get total count
    const totalCountRequest = `<?xml version="1.0"?>
<methodCall>
  <methodName>execute_kw</methodName>
  <params>
    <param><value><string>${db}</string></value></param>
    <param><value><int>${uid}</int></value></param>
    <param><value><string>${password}</string></value></param>
    <param><value><string>res.partner</string></value></param>
    <param><value><string>search_count</string></value></param>
    <param><value><array><data>
      <value><array><data>
        <value><array><data>
          <value><string>supplier_rank</string></value>
          <value><string>&gt;</string></value>
          <value><int>0</int></value>
        </data></array></value>
      </data></array></value>
    </data></array></value></param>
  </params>
</methodCall>`;

    const totalCountResponse = await fetch(`${odooUrl}/xmlrpc/2/object`, {
      method: 'POST',
      headers: {
        'Content-Type': 'text/xml',
        'Accept': 'text/xml',
      },
      body: totalCountRequest,
    });

    const totalCountXml = await totalCountResponse.text();
    const totalMatch = totalCountXml.match(/<value><int>(\d+)<\/int><\/value>/);
    const totalCount = totalMatch ? parseInt(totalMatch[1]) : 0;

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
  } catch (error) {
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