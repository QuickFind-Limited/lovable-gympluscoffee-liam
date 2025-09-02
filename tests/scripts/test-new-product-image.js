// Test script to check if the new product ID 55 has an image
const SUPABASE_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testNewProductImage() {
  try {
    console.log('=== Testing image for product ID 55 (Agrimin 24 7 Magnesium Bullets) ===');
    
    // Test with the new product ID
    const productIds = [55];
    
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
    console.log('Response headers:', Object.fromEntries(response.headers.entries()));
    
    if (!response.ok) {
      const errorText = await response.text();
      console.log('Error response:', errorText);
      return;
    }
    
    const data = await response.json();
    console.log('Response data keys:', Object.keys(data));
    
    if (data.images) {
      console.log('Image results:');
      productIds.forEach(id => {
        const imageUrl = data.images[id];
        console.log(`Product ID ${id}: ${imageUrl ? 'Has image' : 'No image'}`);
        if (imageUrl) {
          console.log(`  URL type: ${typeof imageUrl}`);
          console.log(`  URL preview: ${imageUrl.substring(0, 100)}...`);
        }
      });
    } else {
      console.log('No images data in response');
      console.log('Full response:', JSON.stringify(data, null, 2));
    }
    
  } catch (error) {
    console.error('Error fetching product image:', error);
  }
}

testNewProductImage();