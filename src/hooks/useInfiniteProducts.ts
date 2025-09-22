import { useInfiniteQuery } from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';

interface Product {
  id: string;
  name: string;
  vendor: string;
  price_min: number | null;
  price_max: number | null;
  product_type: string | null;
  body_html: string | null;
  handle: string | null;
  created_at: string;
  image: string | null;
  product_images?: {
    src: string;
    alt: string | null;
    position: number;
  }[];
}

interface UseInfiniteProductsParams {
  searchQuery?: string;
  vendor?: string | null;
  priceMin?: number;
  priceMax?: number;
  productType?: string | null;
  sortBy?: 'name' | 'price' | 'vendor' | 'created_at';
  pageSize?: number;
}

interface ProductsPage {
  products: Product[];
  nextPage: number | null;
  totalCount: number;
}

const fetchProducts = async ({
  pageParam = 0,
  searchQuery = '',
  vendor = null,
  priceMin = 0,
  priceMax = 1000000,
  productType = null,
  sortBy = 'name',
  pageSize = 20
}: UseInfiniteProductsParams & { pageParam?: number }): Promise<ProductsPage> => {
  // TODO: Enable when products table is created - returning mock data for now
  return {
    products: [],
    nextPage: null,
    totalCount: 0
  };
};

export const useInfiniteProducts = (params: UseInfiniteProductsParams) => {
  return useInfiniteQuery({
    queryKey: ['products', 'infinite', params],
    queryFn: ({ pageParam }) => fetchProducts({ ...params, pageParam }),
    initialPageParam: 0,
    getNextPageParam: (lastPage) => lastPage.nextPage,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 10, // 10 minutes
  });
};