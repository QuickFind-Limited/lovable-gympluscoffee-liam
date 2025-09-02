// Test the image fetching functionality
const SUPABASE_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testImageFetching() {
  try {
    console.log('=== TESTING IMAGE FETCHING ===\n');
    
    // First, search for products
    console.log('1. Searching for "acra"...');
    const searchResponse = await fetch(`${SUPABASE_URL}/functions/v1/odoo-search-working`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${ANON_KEY}`,
      },
      body: JSON.stringify({
        query: 'acra',
        search_type: 'single'
      })
    });
    
    const searchData = await searchResponse.json();
    console.log('Search response:', searchData);
    
    if (searchData.products && searchData.products.length > 0) {
      console.log(`\nFound ${searchData.products.length} products`);
      
      // Extract product IDs
      const productIds = searchData.products.map(p => p.id);
      console.log('Product IDs:', productIds);
      
      // Test fetching images
      console.log('\n2. Fetching images for products...');
      const imageResponse = await fetch(`${SUPABASE_URL}/functions/v1/odoo-product-images`, {
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
      const imageData = await imageResponse.json();
      console.log('Image data:', imageData);
      
      if (imageData.images) {
        console.log('\n✅ SUCCESS! Fetched images for products:');
        Object.entries(imageData.images).forEach(([productId, imageData]) => {
          const hasImage = imageData && imageData.startsWith('data:image');
          console.log(`  - Product ${productId}: ${hasImage ? 'Has image' : 'No image'}`);
          if (hasImage) {
            console.log(`    Image size: ${Math.round(imageData.length / 1024)}KB`);
          }
        });
      }
    } else {
      console.log('\n❌ No products found in search');
    }
    
  } catch (error) {
    console.error('Error testing image fetching:', error);
  }
}

testImageFetching();