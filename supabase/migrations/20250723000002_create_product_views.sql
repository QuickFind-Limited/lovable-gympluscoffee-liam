-- Create a view for easy product retrieval with supplier information
CREATE OR REPLACE VIEW public.products_with_suppliers AS
SELECT 
    p.id,
    p.name,
    p.image,
    p.supplier,
    p.min_quantity,
    p.unit_price,
    p.category,
    p.size_options,
    p.created_at,
    s.id as supplier_id,
    s.description as supplier_description
FROM public.products p
LEFT JOIN public.suppliers s ON p.supplier = s.name;

-- Grant permissions on the view
GRANT SELECT ON public.products_with_suppliers TO authenticated;

-- Create a function to search products
CREATE OR REPLACE FUNCTION public.search_products(search_term TEXT)
RETURNS TABLE (
    id UUID,
    name TEXT,
    image TEXT,
    supplier TEXT,
    min_quantity INTEGER,
    unit_price TEXT,
    category TEXT,
    size_options TEXT[],
    created_at TIMESTAMP WITH TIME ZONE,
    rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.name,
        p.image,
        p.supplier,
        p.min_quantity,
        p.unit_price,
        p.category,
        p.size_options,
        p.created_at,
        ts_rank(to_tsvector('english', p.name), plainto_tsquery('english', search_term)) as rank
    FROM public.products p
    WHERE to_tsvector('english', p.name) @@ plainto_tsquery('english', search_term)
    ORDER BY rank DESC;
END;
$$ LANGUAGE plpgsql;

-- Create a function to get products by supplier
CREATE OR REPLACE FUNCTION public.get_products_by_supplier(supplier_name TEXT)
RETURNS SETOF public.products AS $$
BEGIN
    RETURN QUERY
    SELECT * FROM public.products
    WHERE supplier = supplier_name
    ORDER BY name;
END;
$$ LANGUAGE plpgsql;

-- Create a function to get products by category
CREATE OR REPLACE FUNCTION public.get_products_by_category(category_name TEXT)
RETURNS SETOF public.products AS $$
BEGIN
    RETURN QUERY
    SELECT * FROM public.products
    WHERE category = category_name
    ORDER BY name;
END;
$$ LANGUAGE plpgsql;

-- Create a function to calculate order total
CREATE OR REPLACE FUNCTION public.calculate_order_total(
    product_items JSONB
) RETURNS TABLE (
    subtotal NUMERIC,
    sales_tax NUMERIC,
    grand_total NUMERIC
) AS $$
DECLARE
    item JSONB;
    unit_price NUMERIC;
    quantity INTEGER;
    subtotal_amount NUMERIC := 0;
    tax_rate NUMERIC := 0.10; -- 10% sales tax
BEGIN
    -- Calculate subtotal
    FOR item IN SELECT * FROM jsonb_array_elements(product_items)
    LOOP
        -- Extract price (remove $ sign and convert to numeric)
        unit_price := REPLACE(item->>'unit_price', '$', '')::NUMERIC;
        quantity := (item->>'quantity')::INTEGER;
        subtotal_amount := subtotal_amount + (unit_price * quantity);
    END LOOP;
    
    -- Calculate tax and total
    subtotal := subtotal_amount;
    sales_tax := subtotal_amount * tax_rate;
    grand_total := subtotal_amount + sales_tax;
    
    RETURN QUERY SELECT subtotal, sales_tax, grand_total;
END;
$$ LANGUAGE plpgsql;