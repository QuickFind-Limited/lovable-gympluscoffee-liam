# Instruction: Multi-Product Natural Language Query Parser

## Goal

Enable users to request multiple products in a single natural language query, where each product is parsed with its own description and quantity, then matched via parallel vector search to populate the purchase order with all requested items.

## Existing files

- supabase/functions/parse-query/index.ts
- src/hooks/useOpenAIQueryParser.ts
- src/hooks/useVectorSearch.ts
- src/components/dashboard/SearchBar.tsx
- src/pages/OrderSummary.tsx
- src/types/queryParser.types.ts

### New file to create

- None required - updating existing files

## Grouped tasks

### Update OpenAI Schema for Multi-Product Support

> Modify the parse-query edge function to extract multiple products from natural language

- Update Zod schema to return array of products instead of single product
- Each product should have: product_description and quantity fields
- Update OpenAI prompt to identify and separate multiple products in query
- Handle edge cases like shared quantities (e.g., "3 shirts and pants" = 3 of each)

### Enhance Query Parser Hook

> Update the frontend hook to handle multi-product responses

- Update TypeScript types to support array of parsed products
- Modify parsedQueryToVectorSearchParams to handle multiple products
- Update error handling for partial parsing failures

### Implement Parallel Vector Search

> Execute vector searches for all products simultaneously

- Create new function for batch vector search operations
- Use Promise.all to run searches in parallel for performance
- Handle partial failures (some products found, others not)
- Aggregate results while maintaining product-to-result mapping

### Update SearchBar Integration

> Modify SearchBar to process multi-product results

- Update handleSearch to iterate through parsed products array
- Perform vector search for each product description
- Combine all search results before storing in sessionStorage
- Maintain requested quantities for each matched product

### Update Order Display Logic

> Ensure OrderSummary correctly displays all matched products

- Update handleSearchResults to process array of products
- Preserve individual quantities from parsing
- Handle cases where some products aren't found
- Display all successful matches in the purchase order

## Validation checkpoints

- Query "I need 5 blue shirts and 3 red pants" parses into 2 products
- Query "10 sandals, 5 hats, and 2 bags" parses into 3 products
- Each product triggers its own vector search
- All searches run in parallel (not sequentially)
- Products that match are added with correct quantities
- Products that don't match are reported to user
- Order displays all found products with their quantities
- Complex queries like "a dozen shirts and a pair of shoes" parse correctly
- Queries with mixed formats work: "I want 3 blue shirts, red dress, and 5 hats"
- Performance remains fast with parallel execution

## Estimations

- Confidence: High (90%) - Building on existing infrastructure
- Time to implement: 3-4 hours