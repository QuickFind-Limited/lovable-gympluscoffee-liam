// Test script for parse-query edge function
// Run with: deno run --allow-net test-parse-query.ts

const EDGE_FUNCTION_URL = 'http://localhost:54321/functions/v1/parse-query';

interface TestCase {
  name: string;
  query: string;
  expectedFields: string[];
  validateResponse?: (response: any) => void;
}

const testCases: TestCase[] = [
  {
    name: "Basic product query",
    query: "I need 5 boxes of printer paper",
    expectedFields: ["product_description", "quantity"],
    validateResponse: (response) => {
      console.assert(response.quantity === 5, "Should extract quantity as 5");
      console.assert(response.product_description.includes("printer paper"), 
        "Should extract product description");
    }
  },
  {
    name: "Query with supplier",
    query: "Get me 10 reams of A4 paper from 3M",
    expectedFields: ["product_description", "quantity", "supplier"],
    validateResponse: (response) => {
      console.assert(response.quantity === 10, "Should extract quantity as 10");
      console.assert(response.supplier === "3M", "Should extract supplier as 3M");
      console.assert(response.product_description.includes("A4 paper"), 
        "Should extract product with size");
    }
  },
  {
    name: "Query with size specification",
    query: "I want 2 large whiteboards, at least 6 feet wide",
    expectedFields: ["product_description", "quantity", "size_specification"],
    validateResponse: (response) => {
      console.assert(response.quantity === 2, "Should extract quantity as 2");
      console.assert(response.size_specification?.includes("6 feet") || 
        response.size_specification?.includes("large"), 
        "Should extract size specification");
    }
  },
  {
    name: "Query with price limit",
    query: "Need 50 pens under $2 each",
    expectedFields: ["product_description", "quantity", "price_max"],
    validateResponse: (response) => {
      console.assert(response.quantity === 50, "Should extract quantity as 50");
      console.assert(response.price_max === 2, "Should extract max price as 2");
    }
  },
  {
    name: "Complex query with multiple attributes",
    query: "Order 3 dozen blue ballpoint pens from Bic, preferably under $1 each",
    expectedFields: ["product_description", "quantity", "supplier", "price_max"],
    validateResponse: (response) => {
      console.assert(response.quantity === 36, "Should convert 3 dozen to 36");
      console.assert(response.supplier?.toLowerCase() === "bic", "Should extract Bic as supplier");
      console.assert(response.price_max === 1, "Should extract price limit");
      console.assert(response.product_description.includes("blue") && 
        response.product_description.includes("ballpoint"), 
        "Should include color and type in description");
    }
  },
  {
    name: "Ambiguous quantity (should default to 1)",
    query: "I need some paper clips",
    expectedFields: ["product_description", "quantity"],
    validateResponse: (response) => {
      console.assert(response.quantity === 1, "Should default to 1 for 'some'");
    }
  },
  {
    name: "Product type extraction",
    query: "Get me 100 units of office furniture, specifically ergonomic chairs",
    expectedFields: ["product_description", "quantity", "product_type"],
    validateResponse: (response) => {
      console.assert(response.quantity === 100, "Should extract quantity");
      console.assert(response.product_type === "office furniture" || 
        response.product_type === "furniture", "Should extract product type");
      console.assert(response.product_description.includes("ergonomic chairs"), 
        "Should specify the exact product");
    }
  }
];

async function runTest(testCase: TestCase) {
  console.log(`\n🧪 Running test: ${testCase.name}`);
  console.log(`  Query: "${testCase.query}"`);
  
  try {
    const response = await fetch(EDGE_FUNCTION_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0'
      },
      body: JSON.stringify({ query: testCase.query })
    });

    if (response.ok) {
      const data = await response.json();
      console.log(`  Status: ${response.status} ✅`);
      
      // Check if expected fields are present
      const missingFields = testCase.expectedFields.filter(field => !(field in data));
      if (missingFields.length === 0) {
        console.log(`  Fields: ✅ All expected fields present`);
      } else {
        console.log(`  Fields: ❌ Missing: ${missingFields.join(', ')}`);
      }

      // Run custom validation
      if (testCase.validateResponse) {
        try {
          testCase.validateResponse(data);
          console.log(`  Validation: ✅ Passed`);
        } catch (error) {
          console.log(`  Validation: ❌ Failed - ${error.message}`);
        }
      }

      // Log parsed result
      console.log(`  Parsed result:`);
      console.log(`    - Product: ${data.product_description}`);
      console.log(`    - Quantity: ${data.quantity}`);
      if (data.supplier) console.log(`    - Supplier: ${data.supplier}`);
      if (data.size_specification) console.log(`    - Size: ${data.size_specification}`);
      if (data.product_type) console.log(`    - Type: ${data.product_type}`);
      if (data.price_max) console.log(`    - Max price: $${data.price_max}`);

    } else {
      const errorData = await response.json();
      console.log(`  Status: ${response.status} ❌`);
      console.log(`  Error: ${errorData.error || errorData.message}`);
    }

  } catch (error) {
    console.log(`  ❌ Test failed with error: ${error.message}`);
  }
}

async function runAllTests() {
  console.log("🚀 Starting Parse Query Edge Function Tests");
  console.log("=" .repeat(50));

  for (const testCase of testCases) {
    await runTest(testCase);
    // Small delay between tests to avoid rate limiting
    await new Promise(resolve => setTimeout(resolve, 500));
  }

  console.log("\n✅ All tests completed!");
}

// Run tests
if (import.meta.main) {
  runAllTests();
}