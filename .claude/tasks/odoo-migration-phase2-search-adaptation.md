# Task: Odoo Migration Phase 2 - Adapt Search Service in Edge Functions

## Objective
Modify the existing OpenAI search edge functions to work with Odoo's search capabilities while maintaining the multi-product natural language parsing.

## Context
- Current edge functions: `parse-query`, `openai-search`, `vector-search`
- Keep AI parsing for natural language queries
- Replace vector search with Odoo keyword search
- Maintain existing search UX

## Requirements

### 1. Update Parse Query Function
Keep the existing `parse-query` function mostly unchanged as it handles the AI parsing well:

```typescript
// supabase/functions/parse-query/index.ts
// This stays mostly the same - it parses queries like:
// "I need 5 blue shirts and 3 red pants for dogs"
// Into structured format:
{
  products: [
    { type: "shirts", color: "blue", quantity: 5 },
    { type: "pants", color: "red", quantity: 3 }
  ],
  context: "for dogs"
}
```

### 2. Create New Odoo Search Function
Replace `vector-search` with `odoo-product-search`:

```typescript
// supabase/functions/odoo-product-search/index.ts
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { corsHeaders } from '../_shared/cors.ts'
import { OdooClient } from '../_shared/odoo-client.ts'

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    const { parsed_query, search_type = 'multi' } = await req.json();
    const odoo = new OdooClient();
    
    if (search_type === 'single') {
      // Simple keyword search
      const { query } = parsed_query;
      const products = await searchProducts(odoo, query);
      
      return new Response(JSON.stringify({ products }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
    
    // Multi-product search from parsed query
    const searchResults = [];
    
    for (const item of parsed_query.products) {
      const products = await searchProductsByAttributes(odoo, item);
      
      // Score and rank results
      const scoredProducts = products.map(p => ({
        ...p,
        relevance_score: calculateRelevance(p, item),
        requested_quantity: item.quantity
      }));
      
      // Sort by relevance
      scoredProducts.sort((a, b) => b.relevance_score - a.relevance_score);
      
      searchResults.push({
        query: item,
        products: scoredProducts.slice(0, 5), // Top 5 matches
        requested_quantity: item.quantity
      });
    }
    
    return new Response(JSON.stringify({ 
      results: searchResults,
      original_query: parsed_query 
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
    
  } catch (error) {
    console.error('Search error:', error);
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
});

async function searchProducts(odoo: OdooClient, query: string) {
  const domain = [
    '|', '|', '|', '|',
    ['name', 'ilike', query],
    ['display_name', 'ilike', query],
    ['description_sale', 'ilike', query],
    ['default_code', 'ilike', query],
    ['categ_id.name', 'ilike', query]
  ];
  
  return await odoo.execute('product.product', 'search_read', [
    domain,
    {
      fields: ['id', 'name', 'display_name', 'description_sale', 
               'list_price', 'categ_id', 'image_1920', 'default_code'],
      limit: 20
    }
  ]);
}

async function searchProductsByAttributes(odoo: OdooClient, item: any) {
  // Build search terms from parsed attributes
  const terms = [];
  if (item.type) terms.push(item.type);
  if (item.color) terms.push(item.color);
  if (item.size) terms.push(item.size);
  if (item.material) terms.push(item.material);
  if (item.brand) terms.push(item.brand);
  
  // Create complex domain with OR conditions
  let domain = [];
  
  // First try to find products matching all terms
  if (terms.length > 1) {
    // Search for products containing multiple terms
    const andConditions = terms.map(term => [
      '|', '|',
      ['name', 'ilike', term],
      ['display_name', 'ilike', term],
      ['description_sale', 'ilike', term]
    ]);
    
    // Flatten and combine with AND logic
    domain = ['&'.repeat(terms.length - 1), ...andConditions.flat()];
  } else if (terms.length === 1) {
    // Single term search
    domain = [
      '|', '|', '|',
      ['name', 'ilike', terms[0]],
      ['display_name', 'ilike', terms[0]],
      ['description_sale', 'ilike', terms[0]],
      ['default_code', 'ilike', terms[0]]
    ];
  }
  
  let products = await odoo.execute('product.product', 'search_read', [
    domain,
    {
      fields: ['id', 'name', 'display_name', 'description_sale', 
               'list_price', 'categ_id', 'image_1920', 'default_code'],
      limit: 20
    }
  ]);
  
  // If no results with AND, try OR search
  if (products.length === 0 && terms.length > 1) {
    const orConditions = terms.map(term => [
      '|', '|',
      ['name', 'ilike', term],
      ['display_name', 'ilike', term],
      ['description_sale', 'ilike', term]
    ]).flat();
    
    domain = ['|'.repeat(terms.length * 3 - 1), ...orConditions];
    
    products = await odoo.execute('product.product', 'search_read', [
      domain,
      {
        fields: ['id', 'name', 'display_name', 'description_sale', 
                 'list_price', 'categ_id', 'image_1920', 'default_code'],
        limit: 30
      }
    ]);
  }
  
  return products;
}

function calculateRelevance(product: any, searchItem: any): number {
  let score = 0;
  const name = (product.display_name || product.name || '').toLowerCase();
  const description = (product.description_sale || '').toLowerCase();
  
  // Check each attribute
  if (searchItem.type && name.includes(searchItem.type.toLowerCase())) {
    score += 40; // Type match is most important
  }
  if (searchItem.type && description.includes(searchItem.type.toLowerCase())) {
    score += 20;
  }
  
  if (searchItem.color) {
    if (name.includes(searchItem.color.toLowerCase())) score += 30;
    if (description.includes(searchItem.color.toLowerCase())) score += 15;
  }
  
  if (searchItem.size) {
    if (name.includes(searchItem.size.toLowerCase())) score += 20;
    if (description.includes(searchItem.size.toLowerCase())) score += 10;
  }
  
  if (searchItem.material) {
    if (name.includes(searchItem.material.toLowerCase())) score += 20;
    if (description.includes(searchItem.material.toLowerCase())) score += 10;
  }
  
  // Bonus for exact matches
  const searchTerms = [searchItem.type, searchItem.color, searchItem.size]
    .filter(Boolean)
    .join(' ')
    .toLowerCase();
    
  if (name === searchTerms) score += 50;
  
  return score;
}
```

### 3. Update OpenAI Search Function
Modify `openai-search` to use the new Odoo search:

```typescript
// supabase/functions/openai-search/index.ts
// Update the function to call odoo-product-search instead of vector-search

// Change this line:
// const { data: searchResults } = await supabaseClient.functions.invoke('vector-search', ...)

// To:
const { data: searchResults } = await supabaseClient.functions.invoke('odoo-product-search', {
  body: { 
    parsed_query: parsedQuery,
    search_type: 'multi'
  }
});
```

### 4. Add Search Suggestions Function
```typescript
// supabase/functions/odoo-search-suggestions/index.ts
serve(async (req) => {
  try {
    const { query } = await req.json();
    const odoo = new OdooClient();
    
    // Quick search for autocomplete
    const products = await odoo.execute('product.product', 'search_read', [
      [['name', 'ilike', query]],
      {
        fields: ['id', 'name', 'display_name'],
        limit: 10,
        order: 'name'
      }
    ]);
    
    const suggestions = products.map(p => ({
      id: p.id,
      name: p.display_name || p.name,
      type: 'product'
    }));
    
    return new Response(JSON.stringify({ suggestions }), {
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

## Testing Strategy

### Test Cases
1. **Single Product**: "dog shampoo"
2. **Multi-Product**: "5 collars and 3 leashes"
3. **With Attributes**: "large blue dog beds"
4. **Complex Query**: "I need supplies for grooming 10 dogs"
5. **No Results**: Handle gracefully

### Performance Targets
- Search response < 500ms
- Relevant results in top 5
- Fallback to broader search if no exact matches

## Deployment
```bash
# Deploy updated functions
supabase functions deploy parse-query
supabase functions deploy openai-search
supabase functions deploy odoo-product-search
supabase functions deploy odoo-search-suggestions
```

## Notes
- Keep existing AI parsing logic
- Transform Odoo products to match frontend expectations
- Consider relevance scoring for better results
- Monitor search quality metrics