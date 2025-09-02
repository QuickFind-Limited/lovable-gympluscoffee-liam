// Test script to fetch product images from Odoo
const SUPABASE_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testProductImages() {
  try {
    console.log('=== Testing product images ===');
    
    // Test with our suggested product IDs
    const productIds = [45, 76, 54, 53, 73, 75, 51, 57, 59, 60, 48];
    
    const response = await fetch(`${SUPABASE_URL}/functions/v1/odoo-product-images`, {
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
    
    console.log('Response status:', response.status);
    const data = await response.json();
    
    if (data.images) {
      console.log('Image results:');
      productIds.forEach(id => {
        const imageUrl = data.images[id];
        console.log(`Product ID ${id}: ${imageUrl ? 'Has image' : 'No image'}`);
        if (imageUrl) {
          console.log(`  URL: data:image/png;base64,${imageUrl.substring(0, 50)}...`);
        }
      });
    } else {
      console.log('No images data:', JSON.stringify(data, null, 2));
    }
    
  } catch (error) {
    console.error('Error fetching product images:', error);
  }
}

testProductImages();