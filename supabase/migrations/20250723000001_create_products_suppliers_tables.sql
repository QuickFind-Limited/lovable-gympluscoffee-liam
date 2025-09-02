-- Create suppliers table
CREATE TABLE IF NOT EXISTS public.suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create products table
CREATE TABLE IF NOT EXISTS public.products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    image TEXT NOT NULL,
    supplier TEXT NOT NULL,
    min_quantity INTEGER NOT NULL,
    unit_price TEXT NOT NULL,
    category TEXT,
    size_options TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create indexes for better search performance
CREATE INDEX idx_products_name ON public.products USING GIN (to_tsvector('english', name));
CREATE INDEX idx_products_supplier ON public.products(supplier);
CREATE INDEX idx_products_category ON public.products(category);
CREATE INDEX idx_suppliers_name ON public.suppliers(name);

-- Enable Row Level Security
ALTER TABLE public.suppliers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.products ENABLE ROW LEVEL SECURITY;

-- Create policies for suppliers table
CREATE POLICY "Suppliers are viewable by authenticated users" ON public.suppliers
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Suppliers can be inserted by authenticated users" ON public.suppliers
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Suppliers can be updated by authenticated users" ON public.suppliers
    FOR UPDATE USING (auth.role() = 'authenticated');

-- Create policies for products table
CREATE POLICY "Products are viewable by authenticated users" ON public.products
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Products can be inserted by authenticated users" ON public.products
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Products can be updated by authenticated users" ON public.products
    FOR UPDATE USING (auth.role() = 'authenticated');

-- Insert suppliers data
INSERT INTO public.suppliers (name, description) VALUES
    ('Impala', 'Premium fashion and lifestyle products supplier'),
    ('Comme Avant', 'Home decor and luxury goods supplier'),
    ('Nova Brands', 'Electronics and lifestyle accessories supplier'),
    ('Echo Supply', 'Office furniture and equipment supplier')
ON CONFLICT (name) DO NOTHING;

-- Insert products data
-- Impala products (formerly independent suppliers)
INSERT INTO public.products (name, image, supplier, min_quantity, unit_price, category, size_options) VALUES
    ('Floral Back Tie Tiered Mini Dress', '/lovable-uploads/eae07338-87ef-485f-948b-9baac3389dba.png', 'Impala', 36, '$11.20', 'Clothing', ARRAY['XS', 'S', 'M', 'L', 'XL']),
    ('2021 Pinot Noir Reserve', '/lovable-uploads/ece5d739-6092-4e95-a923-e4372626177e.png', 'Impala', 24, '$8.50', 'Wine', NULL),
    ('Organic Solid Hazelnut Oil Cream', '/lovable-uploads/04e1c43b-f6da-4eae-bb7d-fd5581abaa50.png', 'Impala', 25, '$7.95', 'Beauty', NULL),
    ('Pearl Circle Pendant Jewelry Set', '/lovable-uploads/7c27528a-b2dd-4f35-90c2-b1aace1200ea.png', 'Impala', 20, '$22.50', 'Jewelry', NULL);

-- Comme Avant products
INSERT INTO public.products (name, image, supplier, min_quantity, unit_price, category, size_options) VALUES
    ('Round Mirror in Gilded Brass', '/lovable-uploads/183882eb-50f4-4541-924c-22cbf9aa291e.png', 'Comme Avant', 10, '$26.95', 'Home Decor', NULL),
    ('Crossover Hemp Chelsea Boot', '/lovable-uploads/180d7dec-c110-4413-8c0d-580b73dffedb.png', 'Comme Avant', 15, '$67.95', 'Footwear', ARRAY['7', '8', '9', '10', '11', '12']),
    ('Premium Cotton Throw Blanket', '/lovable-uploads/9745aadc-804e-4ef1-8ab1-0baa0df9289e.png', 'Comme Avant', 12, '$34.50', 'Home Textiles', NULL),
    ('Ceramic Coffee Mug Set', '/lovable-uploads/75c231a2-97f5-4a0b-b9af-8cab19800c51.png', 'Comme Avant', 20, '$18.75', 'Kitchen', NULL),
    ('Bamboo Kitchen Utensil Set', '/lovable-uploads/253f7914-95dc-4817-a80e-b1ece852d561.png', 'Comme Avant', 15, '$12.95', 'Kitchen', NULL),
    ('Scented Candle Collection', '/lovable-uploads/269b1c3e-0693-4bd7-843e-e853d37b3e0a.png', 'Comme Avant', 24, '$8.25', 'Home Fragrance', NULL);

-- Nova Brands products
INSERT INTO public.products (name, image, supplier, min_quantity, unit_price, category, size_options) VALUES
    ('Wireless Bluetooth Speaker', '/lovable-uploads/dec66015-9254-41bc-8143-43811c7f4806.png', 'Nova Brands', 10, '$45.99', 'Electronics', NULL),
    ('Leather Wallet Collection', '/lovable-uploads/d514022c-2770-4ec5-abcc-137320c83376.png', 'Nova Brands', 18, '$29.50', 'Accessories', NULL),
    ('Stainless Steel Water Bottle', '/lovable-uploads/1b305c23-bc7d-4fb1-94d3-1732379b25dd.png', 'Nova Brands', 25, '$16.75', 'Lifestyle', ARRAY['500ml', '750ml', '1L']),
    ('Fitness Tracker Band', '/lovable-uploads/130a08b3-97c2-4602-becd-6a3e6d3b9187.png', 'Nova Brands', 12, '$52.80', 'Fitness', NULL);

-- Echo Supply products
INSERT INTO public.products (name, image, supplier, min_quantity, unit_price, category, size_options) VALUES
    ('Ergonomic Office Chair', '/lovable-uploads/d24004d6-3d5f-4eda-8981-c91f8e91904b.png', 'Echo Supply', 5, '$149.99', 'Furniture', NULL),
    ('Standing Desk Converter', '/lovable-uploads/9796497f-60a9-4ae2-9c4a-4788a233e6aa.png', 'Echo Supply', 8, '$89.50', 'Furniture', NULL);