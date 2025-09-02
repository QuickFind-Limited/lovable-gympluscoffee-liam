// Script to get the actual image URLs for hardcoding
const SUPABASE_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function getAllProductImageUrls() {
  try {
    console.log('=== Getting all product image URLs for hardcoding ===');
    
    // All product IDs from the catalog
    const productIds = [45, 76, 54, 53, 73, 75, 51, 57, 55, 60, 48];
    
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
      console.log('=== HARDCODED IMAGE URLS ===');
      productIds.forEach(id => {
        const imageUrl = data.images[id];
        if (imageUrl) {
          console.log(`Product ID ${id}: "${imageUrl}",`);
        } else {
          console.log(`Product ID ${id}: "https://via.placeholder.com/256/4B5563/FFFFFF?text=Product", // No image available`);
        }
      });
    } else {
      console.log('No images data in response');
    }
    
  } catch (error) {
    console.error('Error fetching product images:', error);
  }
}

getAllProductImageUrls();