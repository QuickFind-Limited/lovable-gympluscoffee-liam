// Test to check Odoo supplier search
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const supabaseAnonKey = process.env.SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjI0MzMwODIsImV4cCI6MjAzODAwOTA4Mn0.9O6YEhEUMj-2nBZW1hfgXdFWv1sJlOdS1V5cXE5KJJs';

const supabase = createClient(supabaseUrl, supabaseAnonKey);

async function testSupplierSearch() {
  try {
    console.log('Testing Odoo supplier search...\n');
    
    // Test 1: Get all suppliers
    console.log('1. Fetching all suppliers...');
    const { data: allSuppliers, error: allError } = await supabase.functions.invoke('purchase-orders', {
      body: {
        method: 'search_read',
        model: 'res.partner',
        domain: [['supplier_rank', '>', 0]],
        fields: ['id', 'name'],
        limit: 5
      }
    });
    
    if (allError) {
      console.error('Error fetching all suppliers:', allError);
      return;
    }
    
    console.log('Found suppliers:', allSuppliers?.partners || []);
    
    // Test 2: Search for specific supplier
    console.log('\n2. Searching for "Impala" supplier...');
    const { data: searchResult, error: searchError } = await supabase.functions.invoke('purchase-orders', {
      body: {
        method: 'search_read',
        model: 'res.partner',
        domain: [
          ['supplier_rank', '>', 0],
          ['name', 'ilike', 'Impala']
        ],
        fields: [
          'id', 'name', 'email', 'street', 'street2', 
          'city', 'state_id', 'zip', 'country_id', 
          'phone', 'mobile', 'vat'
        ],
        limit: 1
      }
    });
    
    if (searchError) {
      console.error('Error searching for Impala:', searchError);
      console.error('Full error details:', JSON.stringify(searchError, null, 2));
      return;
    }
    
    console.log('Search result:', searchResult?.partners?.[0] || 'No supplier found');
    
  } catch (error) {
    console.error('Test failed:', error);
  }
}

testSupplierSearch();