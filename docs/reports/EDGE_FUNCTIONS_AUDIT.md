# Supabase Edge Functions Audit Report

## Currently Used Edge Functions (8 total)

These functions are actively being called in the codebase and must be kept:

1. **odoo-filters-data** - Used in ProductFilters.tsx for categories, prices, and vendors
2. **odoo-product-images** - Used for fetching product images (referenced dynamically)
3. **odoo-search-working** - Main search functionality in useProductSearch and useVectorSearch
4. **odoo-simple-test** - Used in useInfiniteOdooProducts for product listing
5. **odoo-suppliers** - Used in useOdooSuppliers (with legacy code)
6. **odoo-suppliers-final** - Primary supplier endpoint in useOdooSuppliers and useOdooSupplierProducts
7. **openai-search-updated** - Used in searchClient.ts for AI-powered search
8. **parse-query** - Used in useOpenAIQueryParser for query parsing

## Unused Edge Functions (37 total) - CAN BE DELETED

These functions are not referenced anywhere in the codebase:

### Debug Functions (12)
- debug-odoo
- debug-odoo-connection
- debug-odoo-products
- debug-parse-response
- debug-raw-response
- debug-xml-generation
- debug-xml-response
- odoo-suppliers-debug
- odoo-test-xml

### Test Functions (9)
- check-all-products
- check-products
- test-odoo
- test-products
- test-searchread
- test-searchread-standalone
- test-xml-generation
- test-xml-import
- create-test-relationships

### Deprecated/Old Versions (13)
- odoo (generic - replaced by specific functions)
- odoo-catalog-v2 (not used)
- odoo-categories (not used)
- odoo-orders (not used)
- odoo-product-search (replaced by odoo-search-working)
- odoo-product-search-v2 (replaced by odoo-search-working)
- odoo-products (replaced by odoo-simple-test)
- odoo-search-final (replaced by odoo-search-working)
- odoo-search-suggestions (not used)
- odoo-suppliers-enhanced (replaced by odoo-suppliers-final)
- odoo-suppliers-inline (replaced by odoo-suppliers-final)
- odoo-suppliers-standalone (replaced by odoo-suppliers-final)
- odoo-suppliers-working (replaced by odoo-suppliers-final)
- openai-search (replaced by openai-search-updated)

### Utility Functions (3)
- create-relationships-direct
- create-supplier-relationships
- create-supplier-relationships-standalone
- update-odoo-min-level

### Other Unused (2)
- generate-embeddings
- vector-search

## Recommendations

1. **Keep all 8 used functions** - They are critical for the application
2. **Delete all 37 unused functions** to reduce complexity and deployment size
3. **Consider consolidating** odoo-suppliers and odoo-suppliers-final if possible
4. **Document the purpose** of each remaining function in their index.ts files

## Deletion Command

To remove all unused functions at once:

```bash
# Backup first
cp -r supabase/functions supabase/functions.backup

# Remove unused functions
rm -rf supabase/functions/{check-all-products,check-products,create-relationships-direct,create-supplier-relationships,create-supplier-relationships-standalone,create-test-relationships,debug-odoo,debug-odoo-connection,debug-odoo-products,debug-parse-response,debug-raw-response,debug-xml-generation,debug-xml-response,generate-embeddings,odoo,odoo-catalog-v2,odoo-categories,odoo-orders,odoo-product-search,odoo-product-search-v2,odoo-products,odoo-search-final,odoo-search-suggestions,odoo-suppliers-debug,odoo-suppliers-enhanced,odoo-suppliers-inline,odoo-suppliers-standalone,odoo-suppliers-working,odoo-test-xml,openai-search,test-odoo,test-products,test-searchread,test-searchread-standalone,test-xml-generation,test-xml-import,update-odoo-min-level,vector-search}
```

## Note on odoo-filters-data

This function is referenced in the code but doesn't exist in the functions directory. This needs to be either:
1. Created if it's needed
2. Removed from the code if it's not needed