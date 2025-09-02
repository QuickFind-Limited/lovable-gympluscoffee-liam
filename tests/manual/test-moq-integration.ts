/**
 * Test MOQ Integration
 * This script tests the MOQ service with sample data
 */

import { MOQService } from './services/moqService';

const testProducts = [
  {
    id: 1,
    name: "Floral Back Tie Tiered Mini Dress",
    quantity: 2,
    supplier: "Impala"
  },
  {
    id: 2,
    name: "2021 Pinot Noir Reserve",
    quantity: 12,
    supplier: "Impala"
  },
  {
    id: 3,
    name: "Organic Solid Hazelnut Oil Cream",
    quantity: 5,
    supplier: "Impala"
  },
  {
    id: 4,
    name: "Round Mirror in Gilded Brass",
    quantity: 1,
    supplier: "Comme Avant"
  }
];

async function testMOQIntegration() {
  console.log('🧪 Testing MOQ Integration...\n');
  
  try {
    console.log('📋 Test Products:');
    testProducts.forEach(product => {
      console.log(`  - ${product.name}: ${product.quantity} units (${product.supplier})`);
    });
    console.log('');

    console.log('⚡ Applying MOQ logic...');
    const result = await MOQService.applyMOQLogic(testProducts);
    
    console.log('\n📊 MOQ Processing Results:');
    console.log(`  Success: ${result.success}`);
    console.log(`  Processing Time: ${result.processingInfo.processingTime}ms`);
    console.log(`  MOQ Data Fetched: ${result.processingInfo.moqDataFetched}`);
    console.log(`  Adjustments Made: ${result.processingInfo.moqAdjustmentsMade}`);
    console.log(`  Fallback Used: ${result.processingInfo.fallbackUsed}`);
    
    if (result.error) {
      console.log(`  Error: ${result.error}`);
    }
    
    if (result.data) {
      console.log('\n📦 Product Details:');
      result.data.forEach(product => {
        console.log(`  ${product.productId}:`);
        console.log(`    Original Quantity: ${product.originalQuantity}`);
        console.log(`    Adjusted Quantity: ${product.adjustedQuantity}`);
        console.log(`    MOQ: ${product.moq}`);
        console.log(`    MOQ Applied: ${product.moqApplied ? 'Yes' : 'No'}`);
        console.log(`    Source: ${product.source}`);
        console.log('');
      });
    }
    
    console.log('✅ MOQ Integration test completed successfully!');
    
  } catch (error) {
    console.error('❌ MOQ Integration test failed:', error);
  }
}

// Run the test
testMOQIntegration();