-- Add numeric price columns to products table
ALTER TABLE public.products 
ADD COLUMN IF NOT EXISTS price_min NUMERIC(10,2),
ADD COLUMN IF NOT EXISTS price_max NUMERIC(10,2);

-- Update existing products with numeric prices extracted from unit_price
UPDATE public.products
SET 
    price_min = CASE 
        WHEN unit_price ~ '^\$?[0-9]+\.?[0-9]*$' THEN 
            CAST(REGEXP_REPLACE(unit_price, '[^0-9.]', '', 'g') AS NUMERIC)
        ELSE NULL 
    END,
    price_max = CASE 
        WHEN unit_price ~ '^\$?[0-9]+\.?[0-9]*$' THEN 
            CAST(REGEXP_REPLACE(unit_price, '[^0-9.]', '', 'g') AS NUMERIC)
        ELSE NULL 
    END
WHERE price_min IS NULL OR price_max IS NULL;

-- Create index on price columns for better query performance
CREATE INDEX IF NOT EXISTS idx_products_price_min ON products(price_min);
CREATE INDEX IF NOT EXISTS idx_products_price_max ON products(price_max);

-- Update the search functions to use the new columns directly
CREATE OR REPLACE FUNCTION search_products_similarity(
    query_embedding TEXT,
    search_strategy TEXT DEFAULT 'description',
    similarity_threshold FLOAT DEFAULT 0.0,
    max_results INTEGER DEFAULT 20
)
RETURNS TABLE (
    product_id UUID,
    title TEXT,
    handle TEXT,
    description TEXT,
    vendor TEXT,
    product_type TEXT,
    tags TEXT[],
    price_min NUMERIC,
    price_max NUMERIC,
    url TEXT,
    similarity_score FLOAT
)
LANGUAGE plpgsql
AS $$
DECLARE
    embedding_vector vector(1024);
    embedding_column TEXT;
BEGIN
    -- Convert text to vector
    embedding_vector := query_embedding::vector(1024);
    
    -- Determine which embedding column to use
    IF search_strategy = 'combined' THEN
        embedding_column := 'embedding_combined';
    ELSE
        embedding_column := 'embedding';
    END IF;
    
    -- Dynamic query based on strategy
    RETURN QUERY EXECUTE format('
        SELECT 
            p.id as product_id,
            p.name as title,
            p.handle,
            p.body_html as description,
            p.vendor,
            p.product_type,
            p.tags,
            p.price_min,
            p.price_max,
            p.image as url,
            1 - (p.%I <=> $1) as similarity_score
        FROM public.products p
        WHERE p.%I IS NOT NULL
        AND (1 - (p.%I <=> $1)) > $2
        ORDER BY p.%I <=> $1
        LIMIT $3',
        embedding_column, embedding_column, embedding_column, embedding_column
    )
    USING embedding_vector, similarity_threshold, max_results;
END;
$$;

-- Update the hybrid search function as well
CREATE OR REPLACE FUNCTION search_products_hybrid(
    query_embedding TEXT,
    keyword_query TEXT,
    search_strategy TEXT DEFAULT 'description',
    similarity_threshold FLOAT DEFAULT 0.0,
    max_results INTEGER DEFAULT 20
)
RETURNS TABLE (
    product_id UUID,
    title TEXT,
    handle TEXT,
    description TEXT,
    vendor TEXT,
    product_type TEXT,
    tags TEXT[],
    price_min NUMERIC,
    price_max NUMERIC,
    url TEXT,
    similarity_score FLOAT,
    text_rank REAL,
    combined_score FLOAT
)
LANGUAGE plpgsql
AS $$
DECLARE
    embedding_vector vector(1024);
    embedding_column TEXT;
BEGIN
    -- Convert text to vector
    embedding_vector := query_embedding::vector(1024);
    
    -- Determine which embedding column to use
    IF search_strategy = 'combined' THEN
        embedding_column := 'embedding_combined';
    ELSE
        embedding_column := 'embedding';
    END IF;
    
    -- Hybrid search combining vector similarity and full-text search
    RETURN QUERY EXECUTE format('
        WITH vector_search AS (
            SELECT 
                p.id,
                1 - (p.%I <=> $1) as similarity
            FROM public.products p
            WHERE p.%I IS NOT NULL
            AND (1 - (p.%I <=> $1)) > $3
        ),
        text_search AS (
            SELECT 
                p.id,
                ts_rank(p.search_text, websearch_to_tsquery($2)) as rank
            FROM public.products p
            WHERE p.search_text @@ websearch_to_tsquery($2)
        ),
        combined AS (
            SELECT 
                COALESCE(v.id, t.id) as product_id,
                COALESCE(v.similarity, 0) as similarity_score,
                COALESCE(t.rank, 0) as text_rank,
                -- Combined score: 70%% vector similarity + 30%% text relevance
                (COALESCE(v.similarity, 0) * 0.7 + COALESCE(t.rank, 0) * 0.3) as combined_score
            FROM vector_search v
            FULL OUTER JOIN text_search t ON v.id = t.id
        )
        SELECT 
            c.product_id,
            p.name as title,
            p.handle,
            p.body_html as description,
            p.vendor,
            p.product_type,
            p.tags,
            p.price_min,
            p.price_max,
            p.image as url,
            c.similarity_score,
            c.text_rank,
            c.combined_score
        FROM combined c
        JOIN public.products p ON p.id = c.product_id
        WHERE c.combined_score > 0
        ORDER BY c.combined_score DESC
        LIMIT $4',
        embedding_column, embedding_column, embedding_column
    )
    USING embedding_vector, keyword_query, similarity_threshold, max_results;
END;
$$;