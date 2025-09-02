# Fix: Supplier Name Display Issue

## Problem Description
When searching for products using the dashboard search bar (e.g., "I need acralube"), all products were displaying "Odoo Product" as the supplier/vendor name instead of showing the actual supplier name.

## Root Cause Analysis

### Issue Location
The vendor/supplier field was hardcoded to "Odoo Product" in multiple places:

1. **`/src/hooks/useVectorSearch.ts`**
   - Line 420: `vendor: 'Odoo Product'`
   - Line 434: `supplier: 'Odoo Product'`

2. **`/src/utils/searchClient.ts`**
   - Line 83: `supplier: 'Odoo Product'`

3. **`/src/hooks/useProductSearch.ts`**
   - Line 121: `vendor: 'Odoo Product'`

4. **`/src/hooks/useInfiniteOdooProducts.ts`**
   - Line 119: `vendor: 'Odoo Product'`

### Why It Happened
The original product search edge function (`product-search`) was only fetching basic product fields:
```typescript
['id', 'name', 'display_name', 'list_price', 'default_code', 'qty_available']
```

It was NOT fetching the `seller_ids` field which links products to their suppliers in Odoo.

## Solution Implemented

### 1. Created Enhanced Edge Function
Created `/supabase/functions/product-search-enhanced/index.ts` that:
- Fetches products with `seller_ids` field
- Queries `product.supplierinfo` model to get supplier details
- Returns products with actual supplier names

### 2. Updated Frontend Code
Updated all hardcoded "Odoo Product" references to use dynamic supplier data:
```typescript
// Old code:
vendor: 'Odoo Product',

// New code:
vendor: product.vendor || product.supplier_name || product.supplier || 'Unknown Supplier',
```

### 3. Updated Search Hook
Modified `useVectorSearch.ts` to use the new edge function:
```typescript
const response = await fetch(`${supabaseUrl}/functions/v1/product-search-enhanced`, {
```

## Files Modified

1. **Created:**
   - `/supabase/functions/product-search-enhanced/index.ts`

2. **Modified:**
   - `/src/hooks/useVectorSearch.ts`
   - `/src/utils/searchClient.ts`
   - `/src/hooks/useProductSearch.ts`
   - `/src/hooks/useInfiniteOdooProducts.ts`

## Testing

### Manual Testing Steps
1. Start the development server: `npm run dev`
2. Navigate to the Dashboard
3. Search for "I need acralube" in the search bar
4. Verify that products show actual supplier names (not "Odoo Product")

### Verification
- Check Network tab for `product-search-enhanced` request
- Response should include `supplier_name` field with actual supplier names
- UI should display these supplier names in search results
- When creating purchase orders, the correct supplier should be used

## Edge Cases Handled
- Products without supplier info show "Unknown Supplier"
- Products with multiple suppliers use the first supplier
- Fallback chain: `vendor` → `supplier_name` → `supplier` → "Unknown Supplier"

## Impact on Purchase Orders
When creating an order from search results:
1. The system now correctly uses the first product's actual supplier
2. Purchase orders will show the correct vendor name
3. Orders sent to suppliers will have accurate supplier information

## Future Improvements
1. Consider caching supplier information for better performance
2. Handle multiple suppliers per product more elegantly
3. Add supplier logos/images to search results