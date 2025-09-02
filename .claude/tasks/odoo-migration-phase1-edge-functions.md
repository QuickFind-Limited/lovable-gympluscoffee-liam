# Task: Odoo Migration Phase 1 - Supabase Edge Functions for Odoo Integration

## Objective
Create Supabase Edge Functions that interface between the React frontend and Odoo backend, replacing direct Supabase database calls while keeping everything in the same project.

## Context
- Use Supabase Edge Functions to keep secrets secure
- Maintain existing Supabase Auth
- No separate API server needed - simpler for demo
- Leverage existing Supabase infrastructure

## Requirements

### 1. Edge Function Setup
Create new edge functions in `/supabase/functions/`:

```
/supabase/functions/
├── odoo-products/
│   └── index.ts       # Product search and listing
├── odoo-categories/
│   └── index.ts       # Category hierarchy
├── odoo-orders/
│   └── index.ts       # Order creation and management
└── _shared/
    ├── odoo-client.ts # Shared Odoo connection logic
    └── auth.ts        # Supabase auth validation
```

### 2. Shared Odoo Client
```typescript
// supabase/functions/_shared/odoo-client.ts
import { createClient } from 'https://deno.land/x/xmlrpc/mod.ts';

export class OdooClient {
  private url: string;
  private db: string;
  private username: string;
  private password: string;
  private uid?: number;

  constructor() {
    this.url = Deno.env.get('ODOO_URL')!;
    this.db = Deno.env.get('ODOO_DATABASE')!;
    this.username = Deno.env.get('ODOO_USERNAME')!;
    this.password = Deno.env.get('ODOO_PASSWORD')!;
  }

  async connect() {
    const common = createClient(`${this.url}/xmlrpc/2/common`);
    this.uid = await common.call('authenticate', [
      this.db, this.username, this.password, {}
    ]);
    return this.uid;
  }

  async execute(model: string, method: string, args: any[]) {
    if (!this.uid) await this.connect();
    const models = createClient(`${this.url}/xmlrpc/2/object`);
    return models.call('execute_kw', [
      this.db, this.uid, this.password,
      model, method, ...args
    ]);
  }
}
```

### 3. Product Edge Functions

#### `odoo-products/index.ts`
```typescript
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { corsHeaders } from '../_shared/cors.ts'
import { OdooClient } from '../_shared/odoo-client.ts'
import { requireAuth } from '../_shared/auth.ts'

serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    // Validate auth
    const user = await requireAuth(req);
    
    const url = new URL(req.url);
    const id = url.pathname.split('/').pop();
    
    const odoo = new OdooClient();
    
    // GET /odoo-products/:id
    if (id && id !== 'odoo-products') {
      const product = await odoo.execute('product.product', 'read', [
        [parseInt(id)],
        { fields: ['name', 'display_name', 'description_sale', 
                   'list_price', 'categ_id', 'image_1920'] }
      ]);
      
      return new Response(JSON.stringify(product[0]), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
    
    // GET /odoo-products with search
    const search = url.searchParams.get('search');
    const limit = parseInt(url.searchParams.get('limit') || '20');
    const offset = parseInt(url.searchParams.get('offset') || '0');
    
    let domain = [];
    if (search) {
      domain = [
        '|', '|', '|',
        ['name', 'ilike', search],
        ['description_sale', 'ilike', search],
        ['default_code', 'ilike', search],
        ['categ_id.name', 'ilike', search]
      ];
    }
    
    const products = await odoo.execute('product.product', 'search_read', [
      domain,
      {
        fields: ['name', 'display_name', 'description_sale', 
                 'list_price', 'categ_id', 'image_1920'],
        limit,
        offset,
        order: 'name'
      }
    ]);
    
    // Transform for frontend
    const transformed = products.map(transformProduct);
    
    return new Response(JSON.stringify(transformed), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
    
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
});

function transformProduct(odooProduct: any) {
  return {
    id: odooProduct.id,
    name: odooProduct.display_name || odooProduct.name,
    description: odooProduct.description_sale || '',
    price: odooProduct.list_price,
    image_url: odooProduct.image_1920 
      ? `data:image/png;base64,${odooProduct.image_1920}`
      : '/placeholder.svg',
    category_id: odooProduct.categ_id?.[0],
    category_name: odooProduct.categ_id?.[1]
  };
}
```

### 4. Order Edge Functions

#### `odoo-orders/index.ts`
```typescript
serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    const user = await requireAuth(req);
    const odoo = new OdooClient();
    
    // POST /odoo-orders - Create order
    if (req.method === 'POST') {
      const { items, shipping_address } = await req.json();
      
      // Find or create partner based on user email
      const partners = await odoo.execute('res.partner', 'search_read', [
        [['email', '=', user.email]],
        { fields: ['id'], limit: 1 }
      ]);
      
      let partnerId = partners[0]?.id;
      if (!partnerId) {
        partnerId = await odoo.execute('res.partner', 'create', [{
          name: user.email.split('@')[0],
          email: user.email,
          customer_rank: 1
        }]);
      }
      
      // Create sale order
      const orderId = await odoo.execute('sale.order', 'create', [{
        partner_id: partnerId,
        state: 'draft'
      }]);
      
      // Add order lines
      for (const item of items) {
        await odoo.execute('sale.order.line', 'create', [{
          order_id: orderId,
          product_id: item.product_id,
          product_uom_qty: item.quantity,
          price_unit: item.price
        }]);
      }
      
      // Confirm order
      await odoo.execute('sale.order', 'action_confirm', [[orderId]]);
      
      // Get created order
      const order = await odoo.execute('sale.order', 'read', [
        [orderId],
        { fields: ['name', 'state', 'amount_total', 'date_order'] }
      ]);
      
      return new Response(JSON.stringify(order[0]), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
    
    // GET /odoo-orders - List orders
    if (req.method === 'GET') {
      const partners = await odoo.execute('res.partner', 'search', [
        [['email', '=', user.email]]
      ]);
      
      if (!partners.length) {
        return new Response(JSON.stringify([]), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
      
      const orders = await odoo.execute('sale.order', 'search_read', [
        [['partner_id', '=', partners[0]]],
        {
          fields: ['name', 'state', 'amount_total', 'date_order'],
          order: 'date_order desc'
        }
      ]);
      
      return new Response(JSON.stringify(orders), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
    
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
});
```

### 5. Multi-Product Search Function
```typescript
// supabase/functions/odoo-search/index.ts
serve(async (req) => {
  if (req.method !== 'POST') {
    return new Response('Method not allowed', { status: 405 });
  }

  try {
    const user = await requireAuth(req);
    const { parsed_query } = await req.json();
    const odoo = new OdooClient();
    
    const results = [];
    
    // Search for each product in the parsed query
    for (const item of parsed_query.products) {
      // Build search terms
      const searchTerms = [
        item.type,
        item.color,
        item.size,
        item.material
      ].filter(Boolean);
      
      // Create domain
      const domainParts = searchTerms.map(term => [
        '|', '|',
        ['name', 'ilike', term],
        ['description_sale', 'ilike', term],
        ['default_code', 'ilike', term]
      ]).flat();
      
      const products = await odoo.execute('product.product', 'search_read', [
        domainParts,
        {
          fields: ['name', 'display_name', 'description_sale', 
                   'list_price', 'categ_id', 'image_1920'],
          limit: 10
        }
      ]);
      
      results.push({
        query: item,
        products: products.map(transformProduct),
        requested_quantity: item.quantity
      });
    }
    
    return new Response(JSON.stringify({ results }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
    
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
});
```

## Environment Variables
Add to Supabase dashboard:
```
ODOO_URL=https://source-animalfarmacy.odoo.com
ODOO_DATABASE=source-animalfarmacy
ODOO_USERNAME=admin@quickfindai.com
ODOO_PASSWORD=BJ62wX2J4yzjS$i
```

## Deployment
```bash
# Deploy all functions
supabase functions deploy odoo-products
supabase functions deploy odoo-categories
supabase functions deploy odoo-orders
supabase functions deploy odoo-search
```

## Success Criteria
- All product searches work through edge functions
- Orders created in app appear in Odoo
- Secrets stay secure in Supabase
- Frontend requires minimal changes
- Single project deployment

## Notes
- Use Deno's XML-RPC library for Odoo communication
- Keep response structures similar to current Supabase
- Handle Odoo connection errors gracefully
- Consider caching for production