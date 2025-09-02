// Test the full search flow with images
const SUPABASE_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testFullSearchFlow() {
  try {
    console.log('=== TESTING FULL SEARCH FLOW WITH IMAGES ===\n');
    
    const searchQuery = 'acralube';
    
    // Simulate what the frontend does in useVectorSearch
    console.log(`1. Searching for "${searchQuery}"...`);
    const searchResponse = await fetch(`${SUPABASE_URL}/functions/v1/odoo-search-working`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${ANON_KEY}`,
      },
      body: JSON.stringify({
        query: searchQuery,
        search_type: 'single'
      })
    });
    
    console.log('Search response status:', searchResponse.status);
    if (!searchResponse.ok) {
      throw new Error(`Search failed: ${searchResponse.statusText}`);
    }
    
    const data = await searchResponse.json();
    console.log('Search found', data.products?.length || 0, 'products');
    
    // If images are available separately, fetch them
    if (data.images_available && data.products?.length > 0) {
      const productIds = data.products.map(p => p.id).filter(Boolean);
      
      console.log('\n2. Fetching images for product IDs:', productIds);
      
      const imageResponse = await fetch(`${SUPABASE_URL}/functions/v1/${data.image_endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${ANON_KEY}`,
        },
        body: JSON.stringify({
          product_ids: productIds,
          image_size: 'image_256'
        })
      });
      
      console.log('Image response status:', imageResponse.status);
      if (imageResponse.ok) {
        const imageData = await imageResponse.json();
        
        // Merge images into products
        if (imageData.images) {
          data.products = data.products.map(product => ({
            ...product,
            image_256: imageData.images[product.id] || null
          }));
          console.log('✅ Successfully merged images into products');
        }
      } else {
        console.warn('❌ Failed to fetch product images:', imageResponse.statusText);
      }
    }
    
    // Display final results
    console.log('\n3. Final search results with images:');
    data.products?.forEach(product => {
      console.log(`\n  Product: ${product.display_name || product.name}`);
      console.log(`  - ID: ${product.id}`);
      console.log(`  - Price: $${product.list_price || 0}`);
      console.log(`  - Stock: ${product.qty_available || 0}`);
      console.log(`  - Has Image: ${product.image_256 ? 'Yes' : 'No'}`);
      if (product.image_256) {
        console.log(`  - Image Size: ${Math.round(product.image_256.length / 1024)}KB`);
      }
    });
    
  } catch (error) {
    console.error('Error in full search flow:', error);
  }
}

testFullSearchFlow();