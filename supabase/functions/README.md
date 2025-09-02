# Supabase Edge Functions

This directory contains all the Edge Functions for the Animal Farmacy application.

## Active Functions (Production Use)

These functions are actively used by the application:

- **product-images** - Fetches product images from Odoo
- **product-search** - Main product search functionality with Odoo integration
- **product-catalog** - Product listing API for catalog browsing and infinite scroll
- **supplier-list-legacy** - Legacy supplier data endpoint (deprecated, use supplier-catalog)
- **supplier-catalog** - Primary supplier and product data endpoint
- **ai-product-search** - AI-powered natural language search using OpenAI
- **search-query-parser** - Parses natural language queries into structured search parameters
- **purchase-orders** - Manages purchase order creation and retrieval from Odoo

## Test Functions

These functions are kept for testing and debugging purposes:

- **test-odoo** - Basic Odoo connection testing
- **test-products** - Product data structure testing
- **test-searchread** - Tests Odoo's search_read functionality
- **test-xml-generation** - Tests XML-RPC request generation
- **test-xml-import** - Tests XML parsing utilities

## Utility Functions

These functions provide utility operations:

- **sync-supplier-products** - Synchronizes product-supplier relationships in database
- **update-stock-levels** - Updates minimum stock levels for products
- **generate-search-embeddings** - Generates vector embeddings for semantic search

## Debug Functions (Development Only)

- **debug-odoo-connection** - Detailed connection debugging for Odoo
- **debug-odoo-products** - Product data debugging
- **debug-xml-response** - XML-RPC response debugging

## Missing Functions

- **odoo-filters-data** - Referenced in code but not implemented. Needs to be created for product filtering functionality.

## Running Tests

### Prerequisites

1. Start Supabase locally:
```bash
supabase start
```

2. Ensure environment variables are set:
- `OPENAI_API_KEY` - For the parse-query function
- `JINA_API_KEY` - For the vector-search function (optional, will fallback to keyword search)

### Individual Function Tests

#### Test Parse Query Function
```bash
cd supabase/functions
deno run --allow-net test-parse-query.ts
```

This tests various natural language queries and validates the parsing results.

#### Test Vector Search Function
```bash
cd supabase/functions
deno run --allow-net test-vector-search.ts
```

This tests:
- Basic search without similarity threshold (now defaults to 0/null)
- Search with specific similarity threshold
- Search with filters
- Pagination
- Error handling

### Integration Test

```bash
cd supabase/functions
deno run --allow-net test-integration.ts
```

This tests the complete flow:
1. Natural language query → Parse Query function
2. Parsed result → Vector Search function
3. Search results → Purchase order simulation

## Key Changes

### Similarity Threshold Update
The vector search function now accepts an optional `similarity_threshold`:
- If not provided, it defaults to 0 (no filtering by similarity)
- This allows returning all results ranked by similarity without a hard cutoff
- You can still provide a threshold (0-1) to filter results

### Example API Calls

#### Parse Query
```bash
curl -X POST http://localhost:54321/functions/v1/parse-query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -d '{"query": "I need 10 boxes of printer paper from 3M"}'
```

#### Vector Search (without similarity threshold)
```bash
curl -X POST http://localhost:54321/functions/v1/vector-search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -d '{
    "query": "printer paper",
    "strategy": "hybrid",
    "max_results": 10
  }'
```

#### Vector Search (with similarity threshold)
```bash
curl -X POST http://localhost:54321/functions/v1/vector-search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -d '{
    "query": "printer paper",
    "strategy": "hybrid",
    "similarity_threshold": 0.7,
    "max_results": 10
  }'
```

## Deployment

Deploy functions to production:

```bash
supabase functions deploy parse-query
supabase functions deploy vector-search
```

## Monitoring

- Check function logs: `supabase functions logs parse-query`
- Monitor search analytics in the `search_analytics` table
- Track performance metrics in response `performance` field