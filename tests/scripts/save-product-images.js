// Script to fetch and save product images to separate files
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SUPABASE_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co';
const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

// Product catalog mapping
const productInfo = {
  45: { name: "Acralube 5Ltr", supplier: "Farm Essentials" },
  76: { name: "Arm Length Examination Gloves", supplier: "Farm Essentials" },
  54: { name: "Agrihealth Lamb Reviver Kit 60Ml", supplier: "Farm Essentials" },
  53: { name: "Agri Lube", supplier: "Farm Essentials" },
  73: { name: "Animec Injection 500Ml", supplier: "Livestock Care" },
  75: { name: "Anyday Coconut Shampoos", supplier: "Livestock Care" },
  51: { name: "Aesculap Hoof Knife", supplier: "Livestock Care" },
  57: { name: "Agvance Footrot Shears", supplier: "Livestock Care" },
  55: { name: "Agrimin 24 7 Magnesium Bullets Cattle 10S", supplier: "Animal Nutrition" },
  60: { name: "Agvance Organic Sheep Mineral Bucket", supplier: "Animal Nutrition" },
  48: { name: "Advance Nutrition Platinum Beef Powder 25Kg Bag", supplier: "Animal Nutrition" }
};

async function saveProductImages() {
  try {
    console.log('=== Fetching and saving product images ===');
    
    // All product IDs from the catalog
    const productIds = Object.keys(productInfo).map(id => parseInt(id));
    
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
      // Create images directory
      const imagesDir = path.join(__dirname, '../../src/data/product-images');
      if (!fs.existsSync(imagesDir)) {
        fs.mkdirSync(imagesDir, { recursive: true });
      }

      // Create TypeScript module with image mappings
      let tsContent = `// Auto-generated product images from Odoo API
// Generated on: ${new Date().toISOString()}

export interface ProductImageMap {
  [productId: number]: string;
}

export const productImages: ProductImageMap = {\n`;

      // Save each image and add to TypeScript mapping
      productIds.forEach(id => {
        const imageUrl = data.images[id];
        const productName = productInfo[id]?.name || `Product ${id}`;
        
        if (imageUrl) {
          console.log(`✅ Product ${id} (${productName}): Image available`);
          
          // Add to TypeScript mapping
          tsContent += `  ${id}: "${imageUrl}",\n`;
        } else {
          console.log(`❌ Product ${id} (${productName}): No image available`);
          
          // Use placeholder for missing images
          tsContent += `  ${id}: "https://via.placeholder.com/256/4B5563/FFFFFF?text=Product",\n`;
        }
      });

      tsContent += '};\n\n';
      
      // Add convenience function
      tsContent += `export const getProductImage = (productId: number): string => {
  return productImages[productId] || "https://via.placeholder.com/256/4B5563/FFFFFF?text=Product";
};\n`;

      // Save TypeScript file
      const tsFilePath = path.join(imagesDir, 'index.ts');
      fs.writeFileSync(tsFilePath, tsContent);
      
      console.log(`\n✅ Saved ${productIds.length} product image mappings to: ${tsFilePath}`);
      console.log('You can now import with: import { productImages, getProductImage } from "@/data/product-images"');
      
    } else {
      console.log('No images data in response');
    }
    
  } catch (error) {
    console.error('Error fetching and saving product images:', error);
  }
}

saveProductImages();