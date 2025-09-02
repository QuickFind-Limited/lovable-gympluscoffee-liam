-- Drop existing products table and recreate with full Shopify schema + vector support
-- This migration creates a comprehensive product catalog with semantic search capabilities

-- First, drop existing constraints and tables in correct order
DROP TABLE IF EXISTS public.products CASCADE;
DROP TABLE IF EXISTS public.suppliers CASCADE;

-- Create comprehensive products table with all Shopify fields
CREATE TABLE public.products (
    -- Primary identifiers
    id BIGSERIAL PRIMARY KEY,
    shopify_id BIGINT UNIQUE NOT NULL,
    
    -- Core product fields
    title TEXT NOT NULL,
    handle TEXT UNIQUE NOT NULL,
    description TEXT,
    vendor TEXT NOT NULL,
    product_type TEXT,
    tags TEXT[] DEFAULT '{}',
    status TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    published_at TIMESTAMPTZ,
    shopify_created_at TIMESTAMPTZ,
    shopify_updated_at TIMESTAMPTZ,
    
    -- URL and pricing
    url TEXT,
    price_min DECIMAL(10, 2),
    price_max DECIMAL(10, 2),
    
    -- Vector embeddings for semantic search (1024 dimensions for Jina v3)
    description_embedding vector(1024),
    combined_embedding vector(1024),
    
    -- Search optimization fields
    search_text TSVECTOR,
    
    -- Metadata
    import_batch TEXT,
    last_indexed_at TIMESTAMPTZ
);

-- Create product images table (one-to-many relationship)
CREATE TABLE public.product_images (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    shopify_image_id BIGINT UNIQUE,
    src TEXT NOT NULL,
    alt TEXT,
    position INTEGER DEFAULT 1,
    width INTEGER,
    height INTEGER,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    
    -- Ensure proper ordering
    UNIQUE(product_id, position)
);

-- Create product variants table for pricing and inventory
CREATE TABLE public.product_variants (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    shopify_variant_id BIGINT UNIQUE,
    title TEXT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    compare_at_price DECIMAL(10, 2),
    sku TEXT,
    barcode TEXT,
    inventory_quantity INTEGER,
    available BOOLEAN DEFAULT true,
    weight DECIMAL(10, 3),
    weight_unit TEXT,
    option1 TEXT,
    option2 TEXT,
    option3 TEXT,
    position INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    
    -- Index for SKU lookups
    INDEX idx_variants_sku (sku) WHERE sku IS NOT NULL
);

-- Create product options table for customization
CREATE TABLE public.product_options (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    position INTEGER DEFAULT 1,
    values TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    
    -- Ensure unique options per product
    UNIQUE(product_id, name)
);

-- Create indexes for vector similarity search
-- HNSW index for fast, high-recall similarity search (best for production)
CREATE INDEX idx_products_description_embedding_hnsw 
    ON products USING hnsw (description_embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_products_combined_embedding_hnsw 
    ON products USING hnsw (combined_embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Traditional indexes for filtering and exact matches
CREATE INDEX idx_products_vendor ON products(vendor);
CREATE INDEX idx_products_product_type ON products(product_type);
CREATE INDEX idx_products_status ON products(status) WHERE status IS NOT NULL;
CREATE INDEX idx_products_published_at ON products(published_at) WHERE published_at IS NOT NULL;
CREATE INDEX idx_products_price_range ON products(price_min, price_max);
CREATE INDEX idx_products_shopify_id ON products(shopify_id);
CREATE INDEX idx_products_handle ON products(handle);

-- GIN index for array search on tags
CREATE INDEX idx_products_tags_gin ON products USING GIN(tags);

-- Full-text search index
CREATE INDEX idx_products_search_text ON products USING GIN(search_text);

-- Indexes for related tables
CREATE INDEX idx_product_images_product_id ON product_images(product_id);
CREATE INDEX idx_product_variants_product_id ON product_variants(product_id);
CREATE INDEX idx_product_variants_available ON product_variants(available);
CREATE INDEX idx_product_options_product_id ON product_options(product_id);

-- Create function to update search_text automatically
CREATE OR REPLACE FUNCTION update_product_search_text()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_text := to_tsvector('english',
        COALESCE(NEW.title, '') || ' ' ||
        COALESCE(NEW.description, '') || ' ' ||
        COALESCE(NEW.vendor, '') || ' ' ||
        COALESCE(NEW.product_type, '') || ' ' ||
        COALESCE(array_to_string(NEW.tags, ' '), '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to maintain search_text
CREATE TRIGGER update_product_search_text_trigger
    BEFORE INSERT OR UPDATE OF title, description, vendor, product_type, tags
    ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_product_search_text();

-- Create function to calculate similarity with multiple strategies
CREATE OR REPLACE FUNCTION search_products_similarity(
    query_embedding vector(1024),
    search_strategy TEXT DEFAULT 'description',
    similarity_threshold FLOAT DEFAULT 0.7,
    max_results INTEGER DEFAULT 50
)
RETURNS TABLE (
    product_id BIGINT,
    title TEXT,
    description TEXT,
    vendor TEXT,
    product_type TEXT,
    tags TEXT[],
    price_min DECIMAL,
    price_max DECIMAL,
    url TEXT,
    similarity_score FLOAT
) AS $$
BEGIN
    IF search_strategy = 'description' THEN
        RETURN QUERY
        SELECT 
            p.id,
            p.title,
            p.description,
            p.vendor,
            p.product_type,
            p.tags,
            p.price_min,
            p.price_max,
            p.url,
            1 - (p.description_embedding <=> query_embedding) as similarity_score
        FROM products p
        WHERE p.description_embedding IS NOT NULL
            AND 1 - (p.description_embedding <=> query_embedding) >= similarity_threshold
        ORDER BY p.description_embedding <=> query_embedding
        LIMIT max_results;
    ELSIF search_strategy = 'combined' THEN
        RETURN QUERY
        SELECT 
            p.id,
            p.title,
            p.description,
            p.vendor,
            p.product_type,
            p.tags,
            p.price_min,
            p.price_max,
            p.url,
            1 - (p.combined_embedding <=> query_embedding) as similarity_score
        FROM products p
        WHERE p.combined_embedding IS NOT NULL
            AND 1 - (p.combined_embedding <=> query_embedding) >= similarity_threshold
        ORDER BY p.combined_embedding <=> query_embedding
        LIMIT max_results;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Create function for hybrid search (vector + keyword)
CREATE OR REPLACE FUNCTION search_products_hybrid(
    query_embedding vector(1024),
    keyword_query TEXT DEFAULT NULL,
    search_strategy TEXT DEFAULT 'description',
    similarity_threshold FLOAT DEFAULT 0.7,
    max_results INTEGER DEFAULT 50
)
RETURNS TABLE (
    product_id BIGINT,
    title TEXT,
    description TEXT,
    vendor TEXT,
    product_type TEXT,
    tags TEXT[],
    price_min DECIMAL,
    price_max DECIMAL,
    url TEXT,
    similarity_score FLOAT,
    text_rank FLOAT,
    combined_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    WITH vector_results AS (
        SELECT * FROM search_products_similarity(
            query_embedding, 
            search_strategy, 
            similarity_threshold, 
            max_results * 2  -- Get more results for hybrid ranking
        )
    ),
    text_results AS (
        SELECT 
            p.id,
            ts_rank(p.search_text, plainto_tsquery('english', keyword_query)) as text_rank
        FROM products p
        WHERE keyword_query IS NOT NULL 
            AND p.search_text @@ plainto_tsquery('english', keyword_query)
    )
    SELECT 
        vr.product_id,
        vr.title,
        vr.description,
        vr.vendor,
        vr.product_type,
        vr.tags,
        vr.price_min,
        vr.price_max,
        vr.url,
        vr.similarity_score,
        COALESCE(tr.text_rank, 0) as text_rank,
        -- Weighted combination: 70% vector similarity, 30% text relevance
        (0.7 * vr.similarity_score + 0.3 * COALESCE(tr.text_rank, 0)) as combined_score
    FROM vector_results vr
    LEFT JOIN text_results tr ON vr.product_id = tr.id
    ORDER BY combined_score DESC
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Enable Row Level Security
ALTER TABLE public.products ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.product_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.product_variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.product_options ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for public read access (products are public)
CREATE POLICY "Products are viewable by everyone" ON public.products
    FOR SELECT USING (true);

CREATE POLICY "Product images are viewable by everyone" ON public.product_images
    FOR SELECT USING (true);

CREATE POLICY "Product variants are viewable by everyone" ON public.product_variants
    FOR SELECT USING (true);

CREATE POLICY "Product options are viewable by everyone" ON public.product_options
    FOR SELECT USING (true);

-- Authenticated users can manage products
CREATE POLICY "Products can be inserted by authenticated users" ON public.products
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Products can be updated by authenticated users" ON public.products
    FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "Products can be deleted by authenticated users" ON public.products
    FOR DELETE USING (auth.role() = 'authenticated');

-- Similar policies for related tables
CREATE POLICY "Product images can be managed by authenticated users" ON public.product_images
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Product variants can be managed by authenticated users" ON public.product_variants
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Product options can be managed by authenticated users" ON public.product_options
    FOR ALL USING (auth.role() = 'authenticated');

-- Add helpful comments
COMMENT ON TABLE products IS 'Main product catalog with Shopify data and vector embeddings for semantic search';
COMMENT ON COLUMN products.description_embedding IS 'Jina v3 embedding (1024 dims) of product title + description for semantic search';
COMMENT ON COLUMN products.combined_embedding IS 'Jina v3 embedding (1024 dims) of title + vendor + type + tags for broader matching';
COMMENT ON INDEX idx_products_description_embedding_hnsw IS 'HNSW index for fast similarity search on product descriptions';
COMMENT ON INDEX idx_products_combined_embedding_hnsw IS 'HNSW index for fast similarity search on combined product metadata';