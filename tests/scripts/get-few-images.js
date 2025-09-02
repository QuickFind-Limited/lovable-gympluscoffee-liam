// Script to get just a few product image URLs for testing
const SUPABASE_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function getFirstThreeImages() {
  try {
    console.log('=== Getting first 3 product image URLs ===');
    
    // First 3 product IDs from the catalog
    const productIds = [45, 76, 54];
    
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
    
    if (!response.ok) {
      const errorText = await response.text();
      console.log('Error response:', errorText);
      return;
    }
    
    const data = await response.json();
    
    if (data.images) {
      console.log('=== First 3 Product Images ===');
      productIds.forEach(id => {
        const imageUrl = data.images[id];
        if (imageUrl) {
          console.log(`\nProduct ID ${id}:`);
          console.log(`"${imageUrl}"`);
          console.log('---');
        } else {
          console.log(`Product ID ${id}: No image available`);
        }
      });
    } else {
      console.log('No images data in response');
    }
    
  } catch (error) {
    console.error('Error fetching product images:', error);
  }
}

getFirstThreeImages();