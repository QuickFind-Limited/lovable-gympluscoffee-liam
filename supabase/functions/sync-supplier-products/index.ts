import { serve } from 'https://deno.land/std@0.190.0/http/server.ts';
import { OdooClient } from '../_shared/odoo-client.ts';
import { corsHeaders, getCorsHeaders } from '../_shared/cors.ts';

serve(async (req: Request) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const odoo = new OdooClient();
    await odoo.connect();

    // First, get all products
    const products = await odoo.searchRead(
      'product.product',
      [],
      ['id', 'name', 'default_code', 'product_tmpl_id'],
      0,
      1000
    );

    console.log(`Found ${products.length} products`);

    // Get all suppliers
    const suppliers = await odoo.searchRead(
      'res.partner',
      [['supplier_rank', '>', 0]],
      ['id', 'name'],
      0,
      100
    );

    console.log(`Found ${suppliers.length} suppliers`);

    // Check existing relationships
    const existingRelationships = await odoo.searchRead(
      'product.supplierinfo',
      [],
      ['id', 'partner_id', 'product_id', 'product_tmpl_id'],
      0,
      1000
    );

    console.log(`Found ${existingRelationships.length} existing relationships`);

    // Create a mapping strategy: assign products to suppliers based on a pattern
    // This is a simple distribution - in real world, this would be based on business logic
    const createdRelationships = [];
    const errors = [];

    if (products.length > 0 && suppliers.length > 0) {
      // Distribute products among suppliers
      for (let i = 0; i < products.length; i++) {
        const product = products[i];
        const supplierIndex = i % suppliers.length; // Round-robin distribution
        const supplier = suppliers[supplierIndex];

        // Skip if relationship already exists
        const existingRelation = existingRelationships.find(rel => 
          rel.product_id && rel.product_id[0] === product.id &&
          rel.partner_id && rel.partner_id[0] === supplier.id
        );

        if (existingRelation) {
          console.log(`Relationship already exists for product ${product.name} and supplier ${supplier.name}`);
          continue;
        }

        try {
          // Create supplier info record
          const supplierInfoData = {
            partner_id: supplier.id,
            product_tmpl_id: product.product_tmpl_id ? product.product_tmpl_id[0] : null,
            product_id: product.id,
            product_name: product.name,
            product_code: product.default_code || '',
            min_qty: 1.0,
            price: Math.random() * 100 + 10, // Random price between 10-110
            delay: Math.floor(Math.random() * 14) + 1, // Random delay 1-14 days
          };

          const newRelationshipId = await odoo.create('product.supplierinfo', supplierInfoData);
          
          createdRelationships.push({
            id: newRelationshipId,
            product: product.name,
            supplier: supplier.name,
            data: supplierInfoData
          });

          console.log(`Created relationship: ${product.name} -> ${supplier.name}`);
        } catch (error) {
          console.error(`Error creating relationship for product ${product.name}:`, error);
          errors.push({
            product: product.name,
            supplier: supplier.name,
            error: error.message
          });
        }
      }
    }

    return new Response(
      JSON.stringify({
        summary: {
          productsFound: products.length,
          suppliersFound: suppliers.length,
          existingRelationships: existingRelationships.length,
          newRelationshipsCreated: createdRelationships.length,
          errors: errors.length
        },
        createdRelationships: createdRelationships,
        errors: errors,
        products: products.slice(0, 10), // First 10 products for review
        suppliers: suppliers
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
        error: error.message || 'Failed to create supplier relationships',
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