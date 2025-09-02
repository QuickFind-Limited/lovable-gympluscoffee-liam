// Test to trace the exact differences between working and failing functions
const SUPABASE_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function traceFunction(functionName, requestBody) {
  try {
    console.log(`=== TRACING ${functionName.toUpperCase()} ===`);
    console.log('Request body:', JSON.stringify(requestBody, null, 2));
    
    const response = await fetch(`${SUPABASE_URL}/functions/v1/${functionName}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${ANON_KEY}`,
      },
      body: JSON.stringify(requestBody)
    });
    
    console.log('Response status:', response.status);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.log('Error response:', errorText);
      return null;
    }
    
    const data = await response.json();
    console.log('Response structure keys:', Object.keys(data));
    
    if (data.results) {
      console.log('Found results array with length:', data.results.length);
      if (data.results.length > 0) {
        console.log('First result has products:', data.results[0].products ? data.results[0].products.length : 'no products field');
      }
    } else if (data.products) {
      console.log('Found products array with length:', data.products.length);
      if (data.products.length > 0) {
        console.log('First product:', data.products[0].name);
      }
    } else {
      console.log('No products or results field found');
      console.log('Available fields:', Object.keys(data));
    }
    
    return data;
    
  } catch (error) {
    console.error(`Error tracing ${functionName}:`, error);
    return null;
  }
}

async function compareFunctions() {
  console.log('COMPARING FUNCTION BEHAVIOR\\n');
  
  // Test the working function (test-simple-odoo)
  const workingResult = await traceFunction('test-simple-odoo', {});
  
  console.log('\\n' + '='.repeat(50) + '\\n');
  
  // Test the main function with single search
  const mainResult = await traceFunction('odoo-product-search', {
    query: 'acra',
    search_type: 'single'
  });
  
  console.log('\\n' + '='.repeat(50) + '\\n');
  
  // Test the main function with multi search
  const multiResult = await traceFunction('odoo-product-search', {
    parsed_query: {
      products: [{
        product_description: 'acra',
        quantity: 1
      }]
    },
    search_type: 'multi'
  });
  
  console.log('\\n=== SUMMARY ===');
  console.log('Working function found products:', workingResult?.count || 0);
  console.log('Main single search found products:', mainResult?.products ? mainResult.products.length : 0);
  console.log('Main multi search found products:', multiResult?.results?.[0]?.products ? multiResult.results[0].products.length : 0);
}

compareFunctions();