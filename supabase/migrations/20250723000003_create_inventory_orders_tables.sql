-- Create inventory table for tracking stock levels
CREATE TABLE IF NOT EXISTS public.inventory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES public.products(id) ON DELETE CASCADE,
    current_stock INTEGER NOT NULL DEFAULT 0,
    reserved_stock INTEGER NOT NULL DEFAULT 0,
    reorder_point INTEGER NOT NULL DEFAULT 10,
    last_restocked_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create orders table
CREATE TABLE IF NOT EXISTS public.orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number TEXT NOT NULL UNIQUE,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    supplier_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    subtotal NUMERIC(10, 2) NOT NULL,
    sales_tax NUMERIC(10, 2) NOT NULL,
    grand_total NUMERIC(10, 2) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create order_items table
CREATE TABLE IF NOT EXISTS public.order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES public.orders(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES public.products(id),
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,
    total_price NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create indexes
CREATE INDEX idx_inventory_product_id ON public.inventory(product_id);
CREATE INDEX idx_orders_user_id ON public.orders(user_id);
CREATE INDEX idx_orders_supplier_name ON public.orders(supplier_name);
CREATE INDEX idx_orders_status ON public.orders(status);
CREATE INDEX idx_order_items_order_id ON public.order_items(order_id);
CREATE INDEX idx_order_items_product_id ON public.order_items(product_id);

-- Enable RLS
ALTER TABLE public.inventory ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.order_items ENABLE ROW LEVEL SECURITY;

-- Create policies for inventory
CREATE POLICY "Inventory is viewable by authenticated users" ON public.inventory
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Inventory can be updated by authenticated users" ON public.inventory
    FOR UPDATE USING (auth.role() = 'authenticated');

-- Create policies for orders
CREATE POLICY "Users can view their own orders" ON public.orders
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create orders" ON public.orders
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own orders" ON public.orders
    FOR UPDATE USING (auth.uid() = user_id);

-- Create policies for order_items
CREATE POLICY "Users can view their own order items" ON public.order_items
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.orders o
            WHERE o.id = order_items.order_id
            AND o.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can create order items for their orders" ON public.order_items
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.orders o
            WHERE o.id = order_items.order_id
            AND o.user_id = auth.uid()
        )
    );

-- Create trigger to update inventory on order creation
CREATE OR REPLACE FUNCTION public.update_inventory_on_order()
RETURNS TRIGGER AS $$
BEGIN
    -- Reserve stock when order is created
    IF TG_OP = 'INSERT' THEN
        UPDATE public.inventory
        SET reserved_stock = reserved_stock + NEW.quantity,
            updated_at = timezone('utc'::text, now())
        WHERE product_id = NEW.product_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_inventory_trigger
    AFTER INSERT ON public.order_items
    FOR EACH ROW
    EXECUTE FUNCTION public.update_inventory_on_order();

-- Create function to check if minimum order value is met
CREATE OR REPLACE FUNCTION public.check_minimum_order_value(
    supplier_name TEXT,
    order_total NUMERIC
) RETURNS BOOLEAN AS $$
DECLARE
    mov_target NUMERIC;
BEGIN
    -- Define MOV targets for each supplier
    CASE supplier_name
        WHEN 'Impala' THEN mov_target := 3250;
        WHEN 'Comme Avant' THEN mov_target := 3000;
        WHEN 'Nova Brands' THEN mov_target := 1800;
        WHEN 'Echo Supply' THEN mov_target := 1200;
        ELSE mov_target := 0;
    END CASE;
    
    RETURN order_total >= mov_target;
END;
$$ LANGUAGE plpgsql;

-- Initialize inventory for all products with default stock
INSERT INTO public.inventory (product_id, current_stock, reorder_point)
SELECT id, 100, 20 FROM public.products
ON CONFLICT DO NOTHING;