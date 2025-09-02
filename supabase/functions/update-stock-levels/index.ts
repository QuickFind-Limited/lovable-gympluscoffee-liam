import { serve } from 'https://deno.land/std@0.190.0/http/server.ts';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type, x-application-name',
  'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE',
};

serve(async (req: Request) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { productId, newMinLevel } = await req.json();

    if (!productId || newMinLevel === undefined) {
      throw new Error('Missing required parameters: productId and newMinLevel');
    }

    // Odoo connection details
    const odooUrl = 'https://source-gym-plus-coffee.odoo.com';
    const db = 'source-gym-plus-coffee';
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
      throw new Error('Failed to authenticate with Odoo');
    }
    const uid = parseInt(uidMatch[1]);

    // Step 2: Read the current product to get its name (simplified)
    const readRequest = `<?xml version="1.0"?>
<methodCall>
  <methodName>execute_kw</methodName>
  <params>
    <param><value><string>${db}</string></value></param>
    <param><value><int>${uid}</int></value></param>
    <param><value><string>${password}</string></value></param>
    <param><value><string>product.supplierinfo</string></value></param>
    <param><value><string>read</string></value></param>
    <param><value><array><data>
      <value><array><data>
        <value><int>${productId}</int></value>
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
    
    // Check if the response is an empty array (product not found)
    if (readXml.includes('<value><array><data></data></array></value>') || 
        readXml.includes('<value><array><data/></value>')) {
      throw new Error(`Product with ID ${productId} not found in Odoo`);
    }
    
    // Parse the product name - simplified parsing
    let productName = '';
    const nameMatch = readXml.match(/<member>\s*<name>product_name<\/name>\s*<value>(?:<string>(.*?)<\/string>|<boolean>0<\/boolean>)<\/value>\s*<\/member>/s);
    
    if (nameMatch) {
      if (nameMatch[0].includes('<boolean>0</boolean>')) {
        productName = '';  // Product has no name
      } else if (nameMatch[1]) {
        productName = nameMatch[1];
      }
    }

    // Update or add metadata
    let updatedName: string;
    if (productName && productName.includes('|META|')) {
      // Parse and update existing metadata
      const parts = productName.split('|META|');
      const cleanName = parts[0].trim();
      const metadataStr = parts[1] ? parts[1].trim() : '{}';
      
      try {
        // Handle Python dict format
        const jsonStr = metadataStr.replace(/'/g, '"');
        const metadata = JSON.parse(jsonStr);
        metadata.minimum_level = newMinLevel;
        
        // Convert back to Python dict format
        const metadataDict = JSON.stringify(metadata).replace(/"/g, "'");
        updatedName = `${cleanName} |META|${metadataDict}`;
      } catch (e) {
        // If parsing fails, just append new metadata
        const metadata = { minimum_level: newMinLevel };
        const metadataDict = JSON.stringify(metadata).replace(/"/g, "'");
        updatedName = `${cleanName} |META|${metadataDict}`;
      }
    } else {
      // Add new metadata
      const metadata = {
        pack_size: 1,
        minimum_level: newMinLevel,
        qty_available: 0,
        virtual_available: 0
      };
      const metadataDict = JSON.stringify(metadata).replace(/"/g, "'");
      updatedName = `${productName} |META|${metadataDict}`.trim();
    }

    // Step 3: Update the product
    const updateRequest = `<?xml version="1.0"?>
<methodCall>
  <methodName>execute_kw</methodName>
  <params>
    <param><value><string>${db}</string></value></param>
    <param><value><int>${uid}</int></value></param>
    <param><value><string>${password}</string></value></param>
    <param><value><string>product.supplierinfo</string></value></param>
    <param><value><string>write</string></value></param>
    <param><value><array><data>
      <value><array><data>
        <value><int>${productId}</int></value>
      </data></array></value>
      <value><struct>
        <member>
          <name>product_name</name>
          <value><string>${updatedName.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&apos;')}</string></value>
        </member>
      </struct></value>
    </data></array></value></param>
  </params>
</methodCall>`;

    const updateResponse = await fetch(`${odooUrl}/xmlrpc/2/object`, {
      method: 'POST',
      headers: {
        'Content-Type': 'text/xml',
        'Accept': 'text/xml',
      },
      body: updateRequest,
    });

    const updateXml = await updateResponse.text();
    
    // Check if update was successful
    if (updateXml.includes('<boolean>1</boolean>')) {
      return new Response(
        JSON.stringify({
          success: true,
          message: `Updated minimum level to ${newMinLevel}`,
          productId,
          newMinLevel
        }),
        {
          headers: {
            ...corsHeaders,
            'Content-Type': 'application/json',
          },
        }
      );
    } else {
      throw new Error('Update failed in Odoo');
    }

  } catch (error) {
    console.error('Error:', error);
    return new Response(
      JSON.stringify({ 
        success: false,
        error: error.message || 'Failed to update minimum level',
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