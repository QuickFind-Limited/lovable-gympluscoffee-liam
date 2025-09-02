# Instruction: Implement OpenAI-Powered Search Feature

## Goal

Replace the current hardcoded search implementation with a hybrid AI-powered search using OpenAI API through a Supabase Edge Function. OpenAI will interpret natural language queries and match them against actual products in the database, returning real product data with proper images, prices, and quantities.

## Existing files

- src/pages/Dashboard.tsx
- src/pages/OrderSummary.tsx
- src/components/dashboard/SearchBar.tsx
- src/components/dashboard/SearchDialog.tsx
- .env.local

### New file to create

- supabase/functions/openai-search/index.ts
- src/hooks/useOpenAISearch.ts
- src/types/search.types.ts
- src/utils/searchClient.ts

## Grouped tasks

### Supabase Setup

> Configure Supabase branch and secrets for OpenAI integration

- Create development branch in Supabase project
- Extract OpenAI API key from .env.local file
- Set OPENAI_API_KEY in Supabase branch secrets
- Verify edge function deployment capability

### Edge Function Implementation

> Create hybrid search endpoint with OpenAI for query understanding

- Initialize edge function with proper CORS and auth handling
- Implement OpenAI client for natural language understanding
- Create prompt to extract search intent (product type, supplier, quantity, size, etc.)
- Match AI interpretation against actual database products
- Return real product records with existing images and data
- Implement error handling and rate limiting

### Database Integration

> Create product catalog and connect with AI search

- Create Supabase migrations for products and suppliers tables
- Migrate existing frontend hardcoded data to database tables
- Use data from OrderSummary.tsx hardcoded arrays (Fashion Forward, Comme Avant, etc.)
- Keep same structure as current frontend (name, image, supplier, price, etc.)
- Use OpenAI to parse query intent (e.g., "sandals from Impala size 9")
- Query database with AI-extracted criteria (product_type='sandals', supplier='Impala', size='9')
- Return actual product records, not AI-generated data
- Implement relevance scoring based on match quality
- Ensure proper RLS policies for secure data access

### Frontend Integration

> Update React components to use new search API

- Create useOpenAISearch hook with React Query integration
- Replace Dashboard.tsx keyword matching (lines 128-183) with API call
- Update OrderSummary.tsx to fetch and display dynamic results
- Transform SearchDialog.tsx from static to dynamic search
- Add loading states and error boundaries

### Testing and Optimization

> Validate hybrid search functionality

- Test natural language queries: "I need sandals from Impala size 9"
- Verify AI correctly extracts: {type: "sandals", supplier: "Impala", size: "9"}
- Confirm database returns actual Impala sandals with real images/prices
- Test edge cases where AI interpretation might be ambiguous
- Implement caching for common query patterns
- Create fallback to keyword search if OpenAI fails
- Ensure all returned data comes from database, not AI generation

## Validation checkpoints

- Supabase edge function responds with proper authentication
- Natural language queries are correctly interpreted by OpenAI
- Search returns actual database products with real images and data
- No AI-generated product information (only database records)
- Response time under 2 seconds for typical queries
- Fallback to simple search works when OpenAI is unavailable
- All product images come from existing URLs in database
- Quantities and prices are from database, not AI-generated

## Estimations

- Confidence: High (90%)
- Time to implement: 4-6 hours