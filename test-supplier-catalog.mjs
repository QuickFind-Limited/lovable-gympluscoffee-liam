import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

const supabaseUrl = process.env.VITE_SUPABASE_URL;
const supabaseAnonKey = process.env.VITE_SUPABASE_ANON_KEY;

const supabase = createClient(supabaseUrl, supabaseAnonKey);

async function testSupplierCatalog() {
  try {
    // Get session
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      console.log('No active session. Please login first.');
      return;
    }

    console.log('Testing supplier catalog endpoint...\n');

    // Test 1: Get suppliers list
    console.log('1. Fetching suppliers list...');
    const suppliersResponse = await fetch(
      `${supabaseUrl}/functions/v1/supplier-catalog?offset=0&limit=5&withProducts=true`,
      {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      }
    );

    if (!suppliersResponse.ok) {
      console.error('Failed to fetch suppliers:', await suppliersResponse.text());
      return;
    }

    const suppliersData = await suppliersResponse.json();
    console.log('Suppliers response:', JSON.stringify(suppliersData, null, 2));

    // Test 2: Get products for a specific supplier
    if (suppliersData.suppliers && suppliersData.suppliers.length > 0) {
      const firstSupplierId = suppliersData.suppliers[0].id;
      console.log(`\n2. Fetching products for supplier ${firstSupplierId}...`);
      
      const productsResponse = await fetch(
        `${supabaseUrl}/functions/v1/supplier-catalog?supplierId=${firstSupplierId}&offset=0&limit=10`,
        {
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!productsResponse.ok) {
        console.error('Failed to fetch products:', await productsResponse.text());
        return;
      }

      const productsData = await productsResponse.json();
      console.log('Products response:', JSON.stringify(productsData, null, 2));
    }

  } catch (error) {
    console.error('Error:', error);
  }
}

testSupplierCatalog();