import { serve } from 'https://deno.land/std@0.190.0/http/server.ts';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE',
};

serve(async (req: Request) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    // All 7 suppliers from Odoo
    const testSuppliers = [
      {
        id: 23,
        name: "European Pet Distributors",
        email: "sales@europeanpetdistributors.com",
        phone: "+79 898 445 3771",
        city: "Amsterdam",
        supplier_rank: 5,
        product_count: 35,
        products: []
      },
      {
        id: 25,
        name: "FastPet Logistics",
        email: "sales@fastpetlogistics.com",
        phone: "+82 659 221 2278",
        city: "Belfast",
        supplier_rank: 5,
        product_count: 0,
        products: []
      },
      {
        id: 21,
        name: "Global Pet Supplies",
        email: "sales@globalpetsupplies.com",
        phone: "+87 601 182 3522",
        city: "Cork",
        supplier_rank: 5,
        product_count: 0,
        products: []
      },
      {
        id: 26,
        name: "Natural Pet Solutions",
        email: "sales@naturalpetsolutions.com",
        phone: "+93 619 831 6514",
        city: "Waterford",
        supplier_rank: 5,
        product_count: 0,
        products: []
      },
      {
        id: 20,
        name: "PetMeds Direct",
        email: "sales@petmedsdirect.com",
        phone: "+48 185 814 7738",
        city: "Dublin",
        supplier_rank: 5,
        product_count: 0,
        products: []
      },
      {
        id: 24,
        name: "Premium Pet Products Co",
        email: "sales@premiumpetproductsco.com",
        phone: "+81 777 283 2608",
        city: "London",
        supplier_rank: 5,
        product_count: 0,
        products: []
      },
      {
        id: 22,
        name: "Veterinary Wholesale Inc",
        email: "sales@veterinarywholesaleinc.com",
        phone: "+88 703 973 4067",
        city: "Galway",
        supplier_rank: 5,
        product_count: 0,
        products: []
      }
    ];

    const url = new URL(req.url);
    const withProducts = url.searchParams.get('withProducts') === 'true';

    console.log('Test function called with withProducts:', withProducts);

    // Add products for European Pet Distributors
    if (withProducts) {
      testSuppliers[0].products = [
        {
          id: 284,
          product_id: [143, '[ANF-00102] Deluxe Cotton Lead Ropes 12Mm'],
          product_name: 'Deluxe Cotton Lead Ropes 12Mm (European Pet Distributors)',
          product_code: 'EUR-ANF-00102',
          price: 6.79,
          min_qty: 4.0,
          delay: 16,
          product_details: {
            id: 143,
            name: 'Deluxe Cotton Lead Ropes 12Mm',
            default_code: 'ANF-00102',
            list_price: 10.0,
            qty_available: 0.0
          }
        },
        {
          id: 285,
          product_id: [144, '[ANF-00103] Deluxe White Cotton Show Halters'],
          product_name: 'Deluxe White Cotton Show Halters (European Pet Distributors)',
          product_code: 'EUR-ANF-00103',
          price: 8.07,
          min_qty: 4.0,
          delay: 16,
          product_details: {
            id: 144,
            name: 'Deluxe White Cotton Show Halters',
            default_code: 'ANF-00103',
            list_price: 12.0,
            qty_available: 0.0
          }
        },
        {
          id: 552,
          product_id: [323, '[ANF-00282] Pink Cotton Deluxe Lead Rope'],
          product_name: 'Pink Cotton Deluxe Lead Rope (European Pet Distributors)',
          product_code: 'EUR-ANF-00282',
          price: 8.65,
          min_qty: 4.0,
          delay: 16,
          product_details: {
            id: 323,
            name: 'Pink Cotton Deluxe Lead Rope',
            default_code: 'ANF-00282',
            list_price: 13.0,
            qty_available: 0.0
          }
        },
        {
          id: 236,
          product_id: [108, '[ANF-00067] Calcium Action Natural Stockcare'],
          product_name: 'Calcium Action Natural Stockcare (European Pet Distributors)',
          product_code: 'EUR-ANF-00067',
          price: 8.72,
          min_qty: 4.0,
          delay: 14,
          product_details: {
            id: 108,
            name: 'Calcium Action Natural Stockcare',
            default_code: 'ANF-00067',
            list_price: 14.0,
            qty_available: 0.0
          }
        },
        {
          id: 499,
          product_id: [289, '[ANF-00248] Natural Stockcare Aqua Lamb 100Ml'],
          product_name: 'Natural Stockcare Aqua Lamb 100Ml (European Pet Distributors)',
          product_code: 'EUR-ANF-00248',
          price: 11.25,
          min_qty: 4.0,
          delay: 14,
          product_details: {
            id: 289,
            name: 'Natural Stockcare Aqua Lamb 100Ml',
            default_code: 'ANF-00248',
            list_price: 18.0,
            qty_available: 0.0
          }
        }
      ];
    }

    return new Response(
      JSON.stringify({
        suppliers: testSuppliers,
        pagination: {
          offset: 0,
          limit: 10,
          total: 7,
          hasMore: false
        }
      }),
      {
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
        },
      }
    );
  } catch (error) {
    console.error('Error:', error);
    return new Response(
      JSON.stringify({ 
        error: error.message || 'Test function error'
      }),
      {
        status: 500,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
        },
      }
    );
  }
});