# Instruction: Intelligent Query Parser with GPT-4.1 and Vector Search Integration

## Goal

Implement an intelligent natural language query parser using OpenAI GPT-4.1 that converts user queries into structured product fields, then uses those fields to perform vector search and populate purchase orders with the best matching products and quantities.

## Existing files

- src/components/dashboard/SearchBar.tsx
- src/pages/Dashboard.tsx
- src/pages/OrderSummary.tsx
- src/pages/PurchaseOrderEditor.tsx
- src/hooks/useVectorSearch.ts
- src/hooks/useOpenAISearch.ts (TO BE REPLACED)
- src/utils/searchClient.ts (TO BE REPLACED) 
- src/types/search.types.ts
- supabase/functions/vector-search/index.ts
- supabase/functions/openai-search/index.ts (TO BE REMOVED)
- supabase/.env

### New file to create

- src/hooks/useOpenAIQueryParser.ts
- src/types/queryParser.types.ts
- supabase/functions/parse-query/index.ts
- src/components/search/IntelligentSearchResults.tsx

## Grouped tasks

### OpenAI Query Parser Implementation 

> Create GPT-4.1 powered query parser that converts natural language to structured product fields

- Create minimal TypeScript interfaces for structured query output matching actual frontend needs:
  ```typescript
  {
    // Essential fields only (based on actual purchase order form)
    product_description: string,  // Main product description for vector search (e.g., "Premium Cotton T-Shirt Size M")
    quantity: number,            // Requested quantity (e.g., 50)
    supplier: string,            // Preferred supplier/vendor (e.g., "Fashion Forward", "Impala")
    
    // Optional but useful for search refinement
    size_specification?: string, // Size info if mentioned (e.g., "Size M", "9 US womens")
    product_type?: string,       // Category if clear (e.g., "sandals", "t-shirt")
    price_max?: number,          // Maximum price if mentioned
    
    // Search strategy hint
    search_strategy: 'semantic' | 'combined' | 'hybrid'
  }
  ```
- Build Supabase edge function `parse-query` that calls OpenAI GPT-4.1 with strict JSON schema enforcement
- Implement comprehensive error handling and graceful fallbacks for OpenAI API failures
- Add Zod schema validation to ensure GPT-4.1 output matches expected structure exactly
- Create React hook `useOpenAIQueryParser` with caching, retry logic, and state management

### Vector Search Integration

> Connect parsed query fields with existing vector search system for intelligent product matching

- Modify vector search edge function to accept structured query parameters from OpenAI parser
- Implement query field mapping to vector search filters (vendor, product_type, price_min/max)
- Add logic to use parsed description field as main search term for semantic similarity
- Enhance search strategy selection based on query structure and complexity
- Create fallback to keyword search if structured parsing fails

### Frontend Search Flow Updates

> Update SearchBar and Dashboard to use intelligent query processing instead of direct navigation

- Modify SearchBar component to trigger query parsing before navigation
- Add loading states and user feedback during query processing and search
- Update Dashboard handleNavigateToOrderSummary to use parsed query results
- Implement real-time search suggestions based on parsed intent
- Add search performance monitoring for OpenAI + vector search pipeline

### Legacy OpenAI Search System Removal

> Remove and replace existing OpenAI search implementation with new GPT-4.1 parser + vector search

- Remove Supabase edge function `supabase/functions/openai-search/index.ts` completely
- Replace `src/utils/searchClient.ts` to use new query parser + vector search pipeline
- Update `src/hooks/useOpenAISearch.ts` to use new `useOpenAIQueryParser` + `useVectorSearch` combination
- Remove references to old `/api/openai-search` endpoint throughout codebase
- Ensure Dashboard component imports are updated to use new search hooks
- Test that old search functionality is completely replaced without breaking existing flows

### Purchase Order Population

> Automatically populate purchase order fields with best matching products and parsed quantities

- Extract essential fields from parsed query for order prefill using simple field mapping:
  - `product_description` → Search term for vector search to find best product match
  - `quantity` → OrderItem.quantity (direct mapping to quantity input field)
  - `supplier` → Filter and prioritize products from preferred supplier
  - `size_specification` → Include in search description for better matching
  - `price_max` → Filter products within budget if specified
- Implement simple best match selection from vector search results:
  - Use `product_description` + `size_specification` as search query
  - Filter by `supplier` if specified
  - Filter by `price_max` if specified
  - Take top result with highest similarity score
  - Set quantity to parsed `quantity` value
- Update OrderSummary to auto-populate products based on search results and parsed data
- Add confirmation dialog showing parsed intent and selected products before order creation
- Create intelligent quantity adjustment based on minimum order quantities, carton sizes, and parsed intent

## Validation checkpoints

- OpenAI GPT-4.1 successfully parses natural language queries like "I need 50 sandals from Impala size 9 US womens" into simple JSON:
  ```json
  {
    "product_description": "sandals size 9 US womens",
    "quantity": 50,
    "supplier": "Impala",
    "size_specification": "9 US womens",
    "product_type": "sandals",
    "search_strategy": "hybrid"
  }
  ```
- Vector search receives parsed `product_description` and returns relevant products with high similarity scores
- SearchBar triggers intelligent processing instead of direct navigation to order summary
- Purchase order automatically populates with: Product name, Quantity (50), Supplier (Impala), Price from matched product
- End-to-end flow works from natural language input to populated purchase order within 3-5 seconds
- Fallback mechanisms handle OpenAI API failures gracefully by using existing search functionality

## Estimations

- Confidence: 8/10 (High - leveraging existing vector search infrastructure with proven OpenAI structured output patterns)
- Time to implement: 6-8 hours (2 hours for OpenAI parser, 2 hours for integration, 2-3 hours for frontend updates, 1-2 hours for testing and refinement)

## Guidance
- Use perplexity as much as you can. For every bug you encounter and for every doubt you have!