// Test the product display logic with different values

const testCases = [
  { product_name: false, product_id: [464, '[ANF-00423] Wahl Aloe Soothe Shampoo'], expected: 'Should show product ID' },
  { product_name: 'False', product_id: [464, '[ANF-00423] Wahl Aloe Soothe Shampoo'], expected: 'Should show product ID' },
  { product_name: 'false', product_id: [464, '[ANF-00423] Wahl Aloe Soothe Shampoo'], expected: 'Should show product ID' },
  { product_name: '', product_id: [464, '[ANF-00423] Wahl Aloe Soothe Shampoo'], expected: 'Should show product ID' },
  { product_name: '  ', product_id: [464, '[ANF-00423] Wahl Aloe Soothe Shampoo'], expected: 'Should show product ID' },
  { product_name: null, product_id: [464, '[ANF-00423] Wahl Aloe Soothe Shampoo'], expected: 'Should show product ID' },
  { product_name: undefined, product_id: [464, '[ANF-00423] Wahl Aloe Soothe Shampoo'], expected: 'Should show product ID' },
  { product_name: 'Valid Product Name', product_id: [464, '[ANF-00423] Wahl Aloe Soothe Shampoo'], expected: 'Should show product_name' },
  { product_name: false, product_id: null, expected: 'Should show Unnamed Product' },
  { product_name: false, product_id: [], expected: 'Should show Unnamed Product' },
];

function testProductDisplay(product) {
  // Current logic from Suppliers.tsx
  if (product.product_name && 
      typeof product.product_name === 'string' && 
      product.product_name !== 'False' && 
      product.product_name !== 'false' &&
      product.product_name.trim() !== '') {
    return product.product_name;
  } else if (product.product_id && Array.isArray(product.product_id) && product.product_id[1]) {
    return product.product_id[1];
  } else {
    return 'Unnamed Product';
  }
}

console.log('Testing product display logic:\n');

testCases.forEach((testCase, index) => {
  const result = testProductDisplay(testCase);
  const passed = (testCase.expected.includes('product_name') && result === testCase.product_name) ||
                 (testCase.expected.includes('product ID') && result === testCase.product_id[1]) ||
                 (testCase.expected.includes('Unnamed Product') && result === 'Unnamed Product');
  
  console.log(`Test ${index + 1}: ${passed ? '✅' : '❌'}`);
  console.log(`  Input: product_name = ${JSON.stringify(testCase.product_name)}, product_id = ${JSON.stringify(testCase.product_id)}`);
  console.log(`  Expected: ${testCase.expected}`);
  console.log(`  Got: "${result}"`);
  console.log('');
});

// Test the specific EUR-ANF-00423 case
console.log('\nTesting EUR-ANF-00423 specific case:');
const eurAnf00423 = {
  product_name: false,  // Boolean false as shown in Python test
  product_id: [464, '[ANF-00423] Wahl Aloe Soothe Shampoo 5Litre']
};
console.log('Result:', testProductDisplay(eurAnf00423));