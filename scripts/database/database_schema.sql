-- Kukoon Rugs Database Schema

-- Products table
CREATE TABLE products (
  id BIGINT PRIMARY KEY,
  title TEXT NOT NULL,
  handle TEXT UNIQUE NOT NULL,
  body_html TEXT,
  vendor TEXT,
  product_type TEXT,
  tags TEXT[],
  published_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  created_at_db TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX idx_products_handle ON products(handle);
CREATE INDEX idx_products_product_type ON products(product_type);
CREATE INDEX idx_products_vendor ON products(vendor);
CREATE INDEX idx_products_tags ON products USING gin(tags);

-- Product variants table
CREATE TABLE product_variants (
  id BIGINT PRIMARY KEY,
  product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
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
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  created_at_db TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for variants
CREATE INDEX idx_variants_product_id ON product_variants(product_id);
CREATE INDEX idx_variants_sku ON product_variants(sku);
CREATE INDEX idx_variants_available ON product_variants(available);

-- Product images table
CREATE TABLE product_images (
  id BIGINT PRIMARY KEY,
  product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  position INTEGER,
  src TEXT NOT NULL,
  width INTEGER,
  height INTEGER,
  variant_ids BIGINT[],
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  created_at_db TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for images
CREATE INDEX idx_images_product_id ON product_images(product_id);
CREATE INDEX idx_images_position ON product_images(position);

-- Product options table
CREATE TABLE product_options (
  id SERIAL PRIMARY KEY,
  product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  position INTEGER,
  values TEXT[],
  created_at_db TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for options
CREATE INDEX idx_options_product_id ON product_options(product_id);

-- Collections table
CREATE TABLE collections (
  id SERIAL PRIMARY KEY,
  handle TEXT UNIQUE NOT NULL,
  title TEXT,
  description TEXT,
  created_at_db TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for collections
CREATE INDEX idx_collections_handle ON collections(handle);

-- Product-Collection junction table
CREATE TABLE product_collections (
  product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  collection_handle TEXT NOT NULL,
  created_at_db TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (product_id, collection_handle)
);

-- Create indexes for junction table
CREATE INDEX idx_product_collections_product ON product_collections(product_id);
CREATE INDEX idx_product_collections_collection ON product_collections(collection_handle);

-- Create a view for easy product querying with variant count
CREATE VIEW products_with_stats AS
SELECT 
  p.*,
  COUNT(DISTINCT v.id) as variant_count,
  COUNT(DISTINCT i.id) as image_count,
  MIN(v.price) as min_price,
  MAX(v.price) as max_price,
  BOOL_OR(v.available) as has_available_variants
FROM products p
LEFT JOIN product_variants v ON p.id = v.product_id
LEFT JOIN product_images i ON p.id = i.product_id
GROUP BY p.id;

-- Create a materialized view for product search
CREATE MATERIALIZED VIEW product_search AS
SELECT 
  p.id,
  p.handle,
  p.title,
  p.product_type,
  p.vendor,
  p.tags,
  to_tsvector('english', 
    COALESCE(p.title, '') || ' ' || 
    COALESCE(p.product_type, '') || ' ' || 
    COALESCE(p.vendor, '') || ' ' ||
    COALESCE(array_to_string(p.tags, ' '), '')
  ) as search_vector
FROM products p;

-- Create index for full-text search
CREATE INDEX idx_product_search_vector ON product_search USING gin(search_vector);

-- Function to refresh search index
CREATE OR REPLACE FUNCTION refresh_product_search()
RETURNS void AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY product_search;
END;
$$ LANGUAGE plpgsql;

-- Enable Row Level Security (RLS) for all tables
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_options ENABLE ROW LEVEL SECURITY;
ALTER TABLE collections ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_collections ENABLE ROW LEVEL SECURITY;

-- Create policy for public read access
CREATE POLICY "Enable read access for all users" ON products
  FOR SELECT USING (true);

CREATE POLICY "Enable read access for all users" ON product_variants
  FOR SELECT USING (true);

CREATE POLICY "Enable read access for all users" ON product_images
  FOR SELECT USING (true);

CREATE POLICY "Enable read access for all users" ON product_options
  FOR SELECT USING (true);

CREATE POLICY "Enable read access for all users" ON collections
  FOR SELECT USING (true);

CREATE POLICY "Enable read access for all users" ON product_collections
  FOR SELECT USING (true);