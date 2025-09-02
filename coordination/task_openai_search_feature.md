# Instruction: Implement OpenAI-Powered Flexible Search Feature

## Goal

Replace the existing hardcoded search functionality with an AI-powered flexible search using OpenAI's API through a Supabase Edge Function. This will enable intelligent, natural language search across orders, invoices, suppliers, and analytics with semantic understanding and fuzzy matching capabilities.

## Existing files

- src/components/dashboard/SearchBar.tsx
- src/components/dashboard/SearchDialog.tsx
- src/pages/Dashboard.tsx
- src/pages/OrderSummary.tsx
- .env.local

### New files to create

- supabase/functions/openai-search/index.ts
- src/hooks/useOpenAISearch.ts
- src/types/search.types.ts
- src/utils/searchClient.ts

## Grouped tasks

### Phase 1: Supabase Branch & Environment Setup

> Set up development branch and configure OpenAI API key in Supabase secrets

- Create Supabase development branch using their CLI/dashboard
- Extract OpenAI API key from .env.local (sk-proj-...)
- Set OPENAI_API_KEY in Supabase secrets for the branch
- Verify branch creation and secret configuration

### Phase 2: Edge Function Development

> Create Supabase Edge Function for OpenAI-powered search

- Create openai-search edge function with TypeScript
- Implement request validation and rate limiting
- Set up OpenAI client with proper error handling
- Design search prompt engineering for:
  - Product/order matching
  - Natural language understanding
  - Multi-category search (orders, invoices, suppliers, analytics)
- Implement response formatting and data structuring
- Add comprehensive error handling and logging

### Phase 3: Database Integration

> Connect edge function with existing Supabase data

- Query relevant tables (orders, invoices, suppliers, products)
- Implement vector embeddings for semantic search (optional enhancement)
- Create search result ranking algorithm
- Add pagination support for large result sets
- Ensure proper RLS policies for search access

### Phase 4: Frontend Integration

> Update React components to use the new search API

- Create useOpenAISearch custom hook with React Query
- Update SearchBar component to trigger AI search
- Transform SearchDialog from hardcoded to dynamic results
- Implement loading states and error handling
- Add search result highlighting and relevance scoring
- Update OrderSummary page to handle AI-generated queries

### Phase 5: Testing & Optimization

> Validate functionality and optimize performance

- Test various natural language queries
- Verify search accuracy across all categories
- Implement caching strategy for common queries
- Add analytics tracking for search usage
- Performance optimization and response time monitoring
- Edge case handling and fallback mechanisms

## Validation checkpoints

- Supabase branch successfully created with OpenAI API key configured
- Edge function responds to test queries with proper authentication
- Search results match or exceed quality of hardcoded implementation
- Natural language queries produce relevant results
- All existing search touchpoints updated and functional
- Response times under 2 seconds for typical queries
- Error handling gracefully manages API failures
- Security: API key not exposed, rate limiting in place

## Estimations

- Confidence: High (85%) - Clear requirements with existing patterns in codebase
- Time to implement: 4-6 hours for complete implementation