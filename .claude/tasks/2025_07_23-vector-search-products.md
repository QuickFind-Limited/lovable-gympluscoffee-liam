# Instruction: Implement Vector Similarity Search for PoundFun Products

## Goal

Replace current hardcoded product search with a robust vector similarity search system using Supabase pgvector, enabling semantic search on product descriptions and metadata from the PoundFun Shopify product catalog.

## Existing files

- supabase/migrations/20250123_products.sql
- supabase/migrations/20250123_search_analytics.sql
- supabase/functions/openai-search/index.ts
- src/hooks/useOpenAISearch.ts
- src/pages/OrderSummary.tsx
- src/types/search.types.ts

### New files to create

- supabase/migrations/20250123_enable_pgvector.sql
- supabase/migrations/20250123_products_with_vectors.sql
- supabase/functions/generate-embeddings/index.ts
- supabase/functions/vector-search/index.ts
- scripts/import-poundfun-products.ts
- scripts/generate-product-embeddings.ts
- src/hooks/useVectorSearch.ts

## Grouped tasks

### Database Schema Design

> Design and implement PostgreSQL schema with pgvector support for semantic search

- Enable pgvector extension in Supabase database
- Create comprehensive products table with all Shopify fields:
  - id (bigint primary key)
  - shopify_id (bigint unique)
  - title (text)
  - handle (text unique)
  - description (text)
  - vendor (text)
  - product_type (text)
  - tags (text[])
  - status (text)
  - created_at (timestamptz)
  - updated_at (timestamptz)
  - published_at (timestamptz)
  - url (text)
  - price_min (decimal)
  - price_max (decimal)
  - description_embedding (vector(1024))
  - combined_embedding (vector(1024))
- Create product_images table for one-to-many relationship
- Create product_variants table for pricing and inventory
- Create product_options table for customization options
- Add indexes for vector similarity search (ivfflat or hnsw)
- Add GIN indexes for tags array search
- Add text search indexes for full-text search fallback

### Data Import Pipeline

> Build robust import system for 4818+ products from JSON export

- Create Node.js script to parse poundfun_products_20250723_151901.json
- Handle nested data structures (images, variants, options)
- Implement batch insert with error handling and retry logic
- Add progress tracking and logging
- Validate data integrity and handle missing fields
- Generate unique SKUs where missing
- Clean and sanitize HTML descriptions
- Extract and normalize tags

### Embedding Generation System

> Implement Jina AI embeddings for semantic search capabilities

- Create edge function to generate embeddings using Jina API (jina-embeddings-v3)
- Utilize JINA_API_KEY from Supabase edge function secrets
- Combine multiple fields for rich embeddings:
  - Title + description for description_embedding
  - Title + vendor + product_type + tags for combined_embedding
- Implement rate limiting for Jina API calls (max 2048 texts per request)
- Handle Jina's 8192 token limit per text
- Add retry logic with exponential backoff
- Store embeddings efficiently in pgvector format (expected 512-1024 dimensions)
- Create batch processing script for initial embedding generation
- Add webhook/trigger for new product embedding generation

### Vector Search Implementation

> Build high-performance vector search edge function

- Create edge function for similarity search with multiple strategies:
  - Semantic search using description embeddings
  - Combined field search for broader matches
  - Hybrid search combining vector and keyword matching
- Implement query embedding generation
- Add filtering capabilities:
  - Price range filtering
  - Product type filtering
  - Vendor filtering
  - Tag-based filtering
  - Availability filtering
- Implement result ranking and relevance scoring
- Add pagination support for large result sets
- Include fallback to keyword search if vector search fails
- Return structured results with similarity scores

### Frontend Integration

> Update React components to use new vector search

- Create useVectorSearch hook with React Query
- Update search interface to support natural language queries
- Add search suggestions based on popular queries
- Implement search result highlighting
- Add filters UI for price, category, vendor
- Display similarity scores and relevance indicators
- Add "similar products" feature using vector similarity
- Implement search analytics tracking

### Performance Optimization

> Ensure system can handle production load efficiently

- Implement caching strategy for popular searches
- Add database connection pooling
- Optimize vector index parameters
- Implement query result caching
- Add CDN caching for product images
- Monitor and log search performance metrics
- Set up alerting for slow queries

## Validation checkpoints

- pgvector extension successfully enabled and version confirmed
- All 4818 products imported with complete data integrity
- Embeddings generated for 100% of products
- Vector search returns relevant results for test queries:
  - "birthday party decorations for kids"
  - "school supplies under £10"
  - "outdoor summer toys"
  - "arts and crafts materials"
- Search performance under 200ms for 95th percentile
- Frontend displays results with proper formatting and images
- Filters work correctly and update results dynamically
- Search analytics properly tracks all queries
- System handles concurrent users without degradation

## Estimations

- Confidence: 8/10
- Time to implement: 16-20 hours
  - Database schema: 2 hours
  - Data import: 3-4 hours
  - Embedding generation: 3-4 hours
  - Vector search function: 3-4 hours
  - Frontend integration: 3-4 hours
  - Testing and optimization: 2 hours

  ## Guidance
  - Use Perplexity as much as you can to always get the latest data available for documentation or anything! Always do that for every doubt and bug you encounter and before starting as well.
  