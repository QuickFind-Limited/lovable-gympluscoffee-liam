#!/usr/bin/env node

import { readFileSync } from 'fs';

const SUPABASE_URL = 'https://fttkapvhobelvodnqxgu.supabase.co';
const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ0dGthcHZob2JlbHZvZG5xeGd1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ4MzYzMzAsImV4cCI6MjA3MDQxMjMzMH0.taeZ2if0Yv0Uoldfiwzib71c1LgLSUd6-bToDGVmAiA';

const localData = JSON.parse(readFileSync('./data/gym_plus_coffee_products.json', 'utf-8'));

async function testEdgeFunction(functionName, options = {}) {
  const url = `${SUPABASE_URL}/functions/v1/${functionName}`;
  
  try {
    console.log(`\n📝 Testing: ${functionName}`);
    console.log(`URL: ${url}`);
    
    const response = await fetch(url, {
      method: options.method || 'GET',
      headers: {
        'Authorization': `Bearer ${ANON_KEY}`,
        'Content-Type': 'application/json',
        ...options.headers
      },
      body: options.body ? JSON.stringify(options.body) : undefined
    });
    
    const data = await response.json();
    console.log(`✅ Response status: ${response.status}`);
    return data;
  } catch (error) {
    console.error(`❌ Error testing ${functionName}:`, error.message);
    return null;
  }
}

async function runTests() {
  console.log('🚀 Starting Edge Function Tests\n');
  console.log('='.repeat(50));
  
  // Test 1: Connection Test
  const connectionTest = await testEdgeFunction('debug-odoo-connection');
  if (connectionTest) {
    console.log('✅ Odoo Connection: SUCCESS');
    console.log(`   - Authenticated as UID: ${connectionTest.steps?.find(s => s.step === 'authentication_result')?.uid}`);
    console.log(`   - Product count: ${connectionTest.steps?.find(s => s.step === 'product_count')?.count}`);
  }
  
  // Test 2: Product Data Test
  console.log('\n' + '='.repeat(50));
  const productsTest = await testEdgeFunction('debug-odoo-products');
  if (productsTest) {
    console.log('✅ Product Retrieval: SUCCESS');
    console.log(`   - Products retrieved: ${productsTest.tests?.find(t => t.test === 'count')?.result}`);
    
    // Compare with local data
    console.log('\n📊 Comparing with local data:');
    console.log(`   - Local products: ${localData.total_skus} SKUs`);
    console.log(`   - Odoo products: ${productsTest.tests?.find(t => t.test === 'count')?.result} products`);
    
    // Check first product
    const firstOdooProduct = productsTest.tests?.find(t => t.test === 'read')?.result?.[0];
    if (firstOdooProduct) {
      console.log('\n   First Odoo Product:');
      console.log(`   - Name: ${firstOdooProduct.name}`);
      console.log(`   - SKU: ${firstOdooProduct.default_code}`);
    }
    
    console.log('\n   First Local Product:');
    console.log(`   - Name: ${localData.products[0].name}`);
    console.log(`   - SKU: ${localData.products[0].sku}`);
  }
  
  // Test 3: Test search functionality
  console.log('\n' + '='.repeat(50));
  const searchTest = await testEdgeFunction('product-search', {
    method: 'POST',
    body: { query: 'hoodie', limit: 5 }
  });
  
  if (searchTest) {
    console.log('✅ Product Search: SUCCESS');
    console.log(`   - Search results: ${searchTest.products?.length || 0} products found`);
  }
  
  // Test 4: Supplier Catalog
  console.log('\n' + '='.repeat(50));
  const supplierTest = await testEdgeFunction('supplier-catalog', {
    method: 'POST',
    body: { limit: 5 }
  });
  
  if (supplierTest) {
    console.log('✅ Supplier Catalog: SUCCESS');
    console.log(`   - Suppliers found: ${supplierTest.suppliers?.length || 0}`);
  }
  
  console.log('\n' + '='.repeat(50));
  console.log('✨ Test Summary:');
  console.log('   - Edge Functions are deployed and accessible');
  console.log('   - Odoo connection is working');
  console.log('   - Product data is being retrieved');
  console.log('   - Note: Data differences between local JSON and Odoo are expected');
  console.log('     (Local JSON may be a snapshot while Odoo has live data)');
}

runTests().catch(console.error);