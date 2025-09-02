# Task: Odoo Migration Phase 3 - Minimal Frontend Updates

## Objective
Update the React frontend to use the new Odoo-backed edge functions with minimal changes, keeping the same UI/UX.

## Context
- Edge functions handle all Odoo integration
- Supabase client still used for auth
- Minimal code changes required
- Same UI components and behavior

## Requirements

### 1. Update Search Hooks
Modify the hooks to call new edge functions:

```typescript
// src/hooks/useOpenAISearch.ts
// Update the vector-search call to odoo-product-search
const performSearch = async (parsedQuery: ParsedQuery) => {
  try {
    // Change this:
    // const { data, error } = await supabase.functions.invoke('vector-search', {
    
    // To this:
    const { data, error } = await supabase.functions.invoke('odoo-product-search', {
      body: { 
        parsed_query: parsedQuery,
        search_type: 'multi'
      }
    });
    
    if (error) throw error;
    
    // Transform results to match existing structure
    const products = data.results.flatMap(result => 
      result.products.map(p => ({
        ...p,
        requested_quantity: result.requested_quantity
      }))
    );
    
    return products;
  } catch (error) {
    console.error('Search error:', error);
    throw error;
  }
};
```

### 2. Update Product Fetching
Replace direct Supabase queries with edge function calls:

```typescript
// src/hooks/useInfiniteProducts.ts
// Replace Supabase query with edge function
const fetchProducts = async ({ pageParam = 0 }) => {
  // Change from:
  // const { data, error } = await supabase
  //   .from('products')
  //   .select('*')
  //   .range(pageParam, pageParam + PAGE_SIZE - 1);
  
  // To:
  const { data, error } = await supabase.functions.invoke('odoo-products', {
    body: {
      limit: PAGE_SIZE,
      offset: pageParam
    }
  });
  
  if (error) throw error;
  return data;
};

// src/pages/ProductDetails.tsx
// Update single product fetch
const fetchProduct = async (id: string) => {
  // Change from:
  // const { data, error } = await supabase
  //   .from('products')
  //   .select('*')
  //   .eq('id', id)
  //   .single();
  
  // To:
  const response = await supabase.functions.invoke(`odoo-products/${id}`);
  if (response.error) throw response.error;
  return response.data;
};
```

### 3. Update Order Creation
Modify order submission to use edge function:

```typescript
// src/components/payment/PaymentFormSection.tsx
// or wherever orders are created

const createOrder = async (orderData: any) => {
  // Transform cart items to Odoo format
  const items = cart.map(item => ({
    product_id: item.id,
    quantity: item.quantity,
    price: item.price
  }));
  
  // Call edge function instead of Supabase
  const { data, error } = await supabase.functions.invoke('odoo-orders', {
    body: {
      items,
      shipping_address: orderData.shipping_address,
      // other order data
    }
  });
  
  if (error) throw error;
  
  // Order created successfully
  return data;
};
```

### 4. Update Category Fetching
```typescript
// src/components/products/ProductFilters.tsx
// or wherever categories are used

const fetchCategories = async () => {
  const { data, error } = await supabase.functions.invoke('odoo-categories');
  
  if (error) throw error;
  
  // Transform if needed to match existing structure
  return data;
};
```

### 5. Handle Image URLs
Since Odoo returns base64 images, they're already converted to data URLs in the edge functions:

```typescript
// No changes needed in components
// Edge functions already transform:
// image_1920: "base64string..."
// To:
// image_url: "data:image/png;base64,base64string..."
```

### 6. Update Search Suggestions
```typescript
// src/components/search/SearchSuggestions.tsx
const fetchSuggestions = async (query: string) => {
  const { data, error } = await supabase.functions.invoke('odoo-search-suggestions', {
    body: { query }
  });
  
  if (error) return [];
  
  return data.suggestions;
};
```

## Environment Variables
No new environment variables needed! The frontend still uses:
```env
VITE_SUPABASE_URL=...
VITE_SUPABASE_ANON_KEY=...
```

## Testing Checklist
- [ ] Product catalog loads
- [ ] Search returns results
- [ ] Product details display
- [ ] Add to cart works
- [ ] Order creation successful
- [ ] Order history shows
- [ ] Categories filter properly
- [ ] Search suggestions appear

## Minimal Changes Summary

1. **Search Hook**: Change `vector-search` to `odoo-product-search`
2. **Product Queries**: Replace `.from('products')` with `.functions.invoke('odoo-products')`
3. **Order Creation**: Use edge function instead of database insert
4. **Categories**: Fetch from edge function
5. **Everything Else**: Stays the same!

## Implementation Steps

1. Update search hooks first (test search)
2. Update product fetching (test browsing)
3. Update order creation (test checkout)
4. Update categories (test filtering)
5. Full end-to-end testing

## Notes
- No UI changes required
- No new dependencies
- Edge functions handle all transformations
- Auth flow remains unchanged
- Same error handling patterns