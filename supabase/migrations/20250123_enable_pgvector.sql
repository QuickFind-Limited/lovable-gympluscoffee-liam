-- Enable pgvector extension for vector similarity search
-- This extension provides vector data type and similarity search operators
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify pgvector is installed (this will show in migration output)
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- Create a function to validate vector dimensions
CREATE OR REPLACE FUNCTION validate_vector_dimension(v vector, expected_dim integer)
RETURNS boolean AS $$
BEGIN
    RETURN array_length(v::real[], 1) = expected_dim;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Create custom index access method settings for optimal HNSW performance
-- Based on latest pgvector best practices for production workloads
-- HNSW provides millisecond query latency with high recall
SET max_parallel_maintenance_workers = 7; -- Optimize index building
SET maintenance_work_mem = '2GB'; -- Allocate memory for index operations

-- Add comment for documentation
COMMENT ON EXTENSION vector IS 'pgvector enables vector similarity search for AI embeddings in PostgreSQL';