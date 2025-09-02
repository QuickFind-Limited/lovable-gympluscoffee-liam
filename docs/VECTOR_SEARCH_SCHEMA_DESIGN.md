# Vector Search Database Schema Design

## Overview

This document outlines the database schema design for implementing vector similarity search for PoundFun products using PostgreSQL with pgvector extension. The design supports semantic search on 4,818+ products from the Shopify catalog.

## Key Design Decisions

### 1. pgvector Extension Choice

**Decision**: Enable pgvector extension for vector similarity search
- **Rationale**: Native PostgreSQL extension with excellent Supabase support
- **Version**: Latest available (verified during migration)
- **Benefits**: Seamless integration, no external dependencies, production-ready

### 2. Vector Dimensions

**Decision**: Use 1024 dimensions for embeddings
- **Model**: Jina embeddings v3 (jina-embeddings-v3)
- **Rationale**: 
  - Jina v3 provides high-quality embeddings
  - 1024 dimensions offer richer semantic representation than 768
  - Acceptable trade-off between accuracy and performance
  - Supported by pgvector without issues

### 3. Index Strategy

**Decision**: HNSW (Hierarchical Navigable Small World) indexes
- **Configuration**:
  ```sql
  WITH (m = 16, ef_construction = 64)
  ```
- **Rationale**:
  - Millisecond query latency (crucial for user experience)
  - Very high recall rates
  - Better for production workloads than IVFFlat
  - Memory usage is acceptable for our dataset size

### 4. Dual Embedding Strategy

**Decision**: Two separate embedding columns
1. **description_embedding**: Title + Description
2. **combined_embedding**: Title + Vendor + Product Type + Tags

**Rationale**:
- Different search contexts require different semantic spaces
- Allows flexibility in search strategies
- Enables A/B testing of different approaches
- Minimal storage overhead for significant flexibility

### 5. Schema Structure

#### Main Tables

1. **products** (Main catalog)
   - All Shopify fields preserved
   - Vector columns for embeddings
   - Full-text search support
   - Proper typing and constraints

2. **product_images** (One-to-many)
   - Separate table for scalability
   - Position-based ordering
   - CDN-ready URL storage

3. **product_variants** (Pricing/Inventory)
   - SKU and barcode support
   - Inventory tracking ready
   - Multiple option support

4. **product_options** (Customization)
   - Flexible option storage
   - Array-based values
   - Position ordering

### 6. Search Functions

**Implemented Search Strategies**:

1. **Pure Vector Search** (`search_products_similarity`)
   - Direct similarity search
   - Configurable threshold
   - Strategy selection (description vs combined)

2. **Hybrid Search** (`search_products_hybrid`)
   - Combines vector and keyword search
   - Weighted scoring (70% vector, 30% text)
   - Best of both worlds approach

### 7. Performance Optimizations

1. **Indexes**:
   - HNSW for vectors (fast similarity)
   - GIN for arrays (tags)
   - GIN for full-text search
   - B-tree for filtering columns

2. **Parallel Processing**:
   ```sql
   SET max_parallel_maintenance_workers = 7;
   SET maintenance_work_mem = '2GB';
   ```

3. **Automatic Updates**:
   - Trigger-based search_text maintenance
   - No manual sync required

### 8. Analytics & Monitoring

**Analytics Tables**:
1. **vector_search_analytics**: Query performance tracking
2. **search_click_analytics**: User behavior tracking
3. **search_embedding_cache**: Popular query caching

**Benefits**:
- Performance monitoring (p50, p95, p99 metrics)
- Search quality improvement data
- Cache optimization opportunities
- User behavior insights

### 9. Security & Access

**RLS (Row Level Security)**:
- Products: Public read, authenticated write
- Analytics: Service role write, authenticated read
- Proper separation of concerns

### 10. Scalability Considerations

1. **Partitioning Ready**: ID-based structure supports future partitioning
2. **Batch Processing**: Import scripts handle 4,818+ products efficiently
3. **Connection Pooling**: Supabase handles automatically
4. **CDN Integration**: Image URLs ready for CDN caching

## Migration Order

1. `20250123_enable_pgvector.sql` - Enable extension
2. `20250123_products_with_vectors.sql` - Main schema
3. `20250123_vector_search_analytics.sql` - Analytics layer

## Performance Targets

- **Search Latency**: < 200ms (95th percentile)
- **Index Build Time**: < 5 minutes for full dataset
- **Embedding Generation**: Batch processing via Jina API
- **Concurrent Users**: 100+ without degradation

## Future Enhancements

1. **Multi-language Support**: Additional embedding models
2. **Image Similarity**: Visual search capabilities
3. **Personalization**: User-specific embeddings
4. **Auto-reindexing**: Based on performance metrics

## Validation Queries

```sql
-- Verify pgvector installation
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan 
FROM pg_stat_user_indexes 
WHERE indexname LIKE '%hnsw%';

-- Monitor search performance
SELECT * FROM search_performance_metrics 
ORDER BY hour DESC LIMIT 10;
```

## Best Practices Applied

1. **Latest pgvector optimizations** (2025 best practices)
2. **HNSW over IVFFlat** for production workloads
3. **Proper dimension validation** functions
4. **Comprehensive analytics** from day one
5. **Hybrid search** for flexibility
6. **Caching strategy** for popular queries
7. **Batch processing** for large datasets
8. **Full Shopify schema** preservation