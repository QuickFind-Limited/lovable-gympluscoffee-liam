-- Create products table with UUID support and vector capabilities
-- Compatible with the imported Kukoon Rugs data

-- Create comprehensive products table with all Shopify fields
CREATE TABLE public.products (
    -- Primary identifiers (UUID for compatibility)
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shopify_id BIGINT UNIQUE,
    
    -- Core product fields (matching import structure)
    name TEXT NOT NULL,
    handle TEXT UNIQUE,
    body_html TEXT,
    image TEXT,
    supplier TEXT,
    vendor TEXT,
    product_type TEXT,
    tags TEXT[] DEFAULT '{}',
    category TEXT,
    size_options TEXT[],
    min_quantity INTEGER DEFAULT 1,
    unit_price TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    published_at TIMESTAMPTZ,
    shopify_created_at TIMESTAMPTZ,
    shopify_updated_at TIMESTAMPTZ,
    
    -- Vector embeddings for semantic search (1024 dimensions for Jina v3)
    embedding vector(1024),
    embedding_combined vector(1024),
    
    -- Search optimization fields
    search_text TSVECTOR,
    last_indexed_at TIMESTAMPTZ
);

-- Create product images table
CREATE TABLE public.product_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    shopify_image_id BIGINT UNIQUE,
    src TEXT NOT NULL,
    alt TEXT,
    position INTEGER DEFAULT 1,
    width INTEGER,
    height INTEGER,
    shopify_created_at TIMESTAMPTZ,
    shopify_updated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create product variants table
CREATE TABLE public.product_variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    shopify_variant_id BIGINT UNIQUE,
    title TEXT,
    option1 TEXT,
    option2 TEXT,
    option3 TEXT,
    sku TEXT,
    requires_shipping BOOLEAN DEFAULT true,
    taxable BOOLEAN DEFAULT true,
    available BOOLEAN DEFAULT false,
    price DECIMAL(10,2),
    compare_at_price DECIMAL(10,2),
    grams INTEGER,
    position INTEGER,
    shopify_created_at TIMESTAMPTZ,
    shopify_updated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create product collections table
CREATE TABLE public.product_collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    collection_handle TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(product_id, collection_handle)
);

-- Create indexes for vector similarity search
CREATE INDEX idx_products_embedding 
    ON products USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100)
    WHERE embedding IS NOT NULL;

CREATE INDEX idx_products_embedding_combined 
    ON products USING ivfflat (embedding_combined vector_cosine_ops)
    WITH (lists = 100)
    WHERE embedding_combined IS NOT NULL;

-- Traditional indexes
CREATE INDEX idx_products_shopify_id ON products(shopify_id);
CREATE INDEX idx_products_handle ON products(handle);
CREATE INDEX idx_products_vendor ON products(vendor);
CREATE INDEX idx_products_product_type ON products(product_type);
CREATE INDEX idx_products_supplier ON products(supplier);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_tags_gin ON products USING GIN(tags);
CREATE INDEX idx_products_search_text ON products USING GIN(search_text);

-- Indexes for related tables
CREATE INDEX idx_product_images_product_id ON product_images(product_id);
CREATE INDEX idx_product_images_shopify_id ON product_images(shopify_image_id);
CREATE INDEX idx_product_variants_product_id ON product_variants(product_id);
CREATE INDEX idx_product_variants_shopify_id ON product_variants(shopify_variant_id);
CREATE INDEX idx_product_variants_sku ON product_variants(sku);
CREATE INDEX idx_product_collections_product_id ON product_collections(product_id);
CREATE INDEX idx_product_collections_handle ON product_collections(collection_handle);

-- Create function to update search_text automatically
CREATE OR REPLACE FUNCTION update_product_search_text()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_text := to_tsvector('english',
        COALESCE(NEW.name, '') || ' ' ||
        COALESCE(NEW.body_html, '') || ' ' ||
        COALESCE(NEW.vendor, '') || ' ' ||
        COALESCE(NEW.supplier, '') || ' ' ||
        COALESCE(NEW.product_type, '') || ' ' ||
        COALESCE(array_to_string(NEW.tags, ' '), '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to maintain search_text
CREATE TRIGGER update_product_search_text_trigger
    BEFORE INSERT OR UPDATE OF name, body_html, vendor, supplier, product_type, tags
    ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_product_search_text();

-- Create function for vector similarity search (accepts text embedding)
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
            -- Extract numeric price from unit_price text
            CASE 
                WHEN p.unit_price ~ ''^[0-9.]+'' THEN 
                    CAST(REGEXP_REPLACE(p.unit_price, ''[^0-9.]'', '''', ''g'') AS NUMERIC)
                ELSE NULL 
            END as price_min,
            CASE 
                WHEN p.unit_price ~ ''^[0-9.]+'' THEN 
                    CAST(REGEXP_REPLACE(p.unit_price, ''[^0-9.]'', '''', ''g'') AS NUMERIC)
                ELSE NULL 
            END as price_max,
            NULL::TEXT as url,
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

-- Create function for hybrid search (vector + keyword)
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
    text_rank FLOAT,
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
    
    RETURN QUERY EXECUTE format('
        WITH semantic_results AS (
            SELECT 
                p.id,
                1 - (p.%I <=> $1) as similarity_score
            FROM public.products p
            WHERE p.%I IS NOT NULL
        ),
        text_results AS (
            SELECT 
                p.id,
                ts_rank(p.search_text, websearch_to_tsquery(''english'', $2)) as text_rank
            FROM public.products p
            WHERE p.search_text @@ websearch_to_tsquery(''english'', $2)
        ),
        combined AS (
            SELECT 
                COALESCE(s.id, t.id) as id,
                COALESCE(s.similarity_score, 0) as similarity_score,
                COALESCE(t.text_rank, 0) as text_rank,
                COALESCE(s.similarity_score, 0) * 0.7 + COALESCE(t.text_rank, 0) * 0.3 as combined_score
            FROM semantic_results s
            FULL OUTER JOIN text_results t ON s.id = t.id
        )
        SELECT 
            p.id as product_id,
            p.name as title,
            p.handle,
            p.body_html as description,
            p.vendor,
            p.product_type,
            p.tags,
            -- Extract numeric price
            CASE 
                WHEN p.unit_price ~ ''^[0-9.]+'' THEN 
                    CAST(REGEXP_REPLACE(p.unit_price, ''[^0-9.]'', '''', ''g'') AS NUMERIC)
                ELSE NULL 
            END as price_min,
            CASE 
                WHEN p.unit_price ~ ''^[0-9.]+'' THEN 
                    CAST(REGEXP_REPLACE(p.unit_price, ''[^0-9.]'', '''', ''g'') AS NUMERIC)
                ELSE NULL 
            END as price_max,
            NULL::TEXT as url,
            c.similarity_score,
            c.text_rank,
            c.combined_score
        FROM combined c
        JOIN public.products p ON p.id = c.id
        WHERE c.combined_score > $3
        ORDER BY c.combined_score DESC
        LIMIT $4',
        embedding_column, embedding_column
    )
    USING embedding_vector, keyword_query, similarity_threshold, max_results;
END;
$$;

-- Enable Row Level Security
ALTER TABLE public.products ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.product_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.product_variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.product_collections ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for public read access
CREATE POLICY "Products are viewable by everyone" ON public.products
    FOR SELECT USING (true);

CREATE POLICY "Product images are viewable by everyone" ON public.product_images
    FOR SELECT USING (true);

CREATE POLICY "Product variants are viewable by everyone" ON public.product_variants
    FOR SELECT USING (true);

CREATE POLICY "Product collections are viewable by everyone" ON public.product_collections
    FOR SELECT USING (true);

-- Authenticated users can manage products
CREATE POLICY "Products can be managed by authenticated users" ON public.products
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Product images can be managed by authenticated users" ON public.product_images
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Product variants can be managed by authenticated users" ON public.product_variants
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Product collections can be managed by authenticated users" ON public.product_collections
    FOR ALL USING (auth.role() = 'authenticated');