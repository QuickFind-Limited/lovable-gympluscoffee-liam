# Supabase Edge Function Rename Plan

## Current Names → New Names

### Production Functions
1. `odoo-simple-test` → `product-catalog`
   - Purpose: Lists products for catalog/browsing
   
2. `odoo-search-working` → `product-search`
   - Purpose: Main product search functionality
   
3. `odoo-product-images` → `product-images`
   - Purpose: Fetches product images
   
4. `odoo-suppliers` → `supplier-list-legacy` (mark as deprecated)
   - Purpose: Legacy supplier listing
   
5. `odoo-suppliers-final` → `supplier-catalog`
   - Purpose: Primary supplier and product data
   
6. `openai-search-updated` → `ai-product-search`
   - Purpose: AI-powered natural language search
   
7. `parse-query` → `search-query-parser`
   - Purpose: Parses natural language into search parameters

### Test Functions (Keep as-is with test- prefix)
- `test-odoo`
- `test-products`
- `test-searchread`
- `test-xml-generation`
- `test-xml-import`

### Utility Functions
1. `create-supplier-relationships` → `sync-supplier-products`
   - Purpose: Syncs product-supplier relationships
   
2. `update-odoo-min-level` → `update-stock-levels`
   - Purpose: Updates minimum stock levels
   
3. `generate-embeddings` → `generate-search-embeddings`
   - Purpose: Creates vector embeddings for search

### Debug Functions (Keep as-is with debug- prefix)
- `debug-odoo-connection`
- `debug-odoo-products`
- `debug-xml-response`

## Files to Update

### Hooks
- `/src/hooks/useInfiniteOdooProducts.ts`
- `/src/hooks/useOdooProductImages.ts`
- `/src/hooks/useOdooSuppliers.ts`
- `/src/hooks/useOdooSupplierProducts.ts`
- `/src/hooks/useOpenAIQueryParser.ts`
- `/src/hooks/useProductSearch.ts`
- `/src/hooks/useVectorSearch.ts`

### Utils
- `/src/utils/searchClient.ts`

### Components
- `/src/components/products/ProductFilters.tsx`