// Integration test for parse-query -> vector-search flow
// Run with: deno run --allow-net test-integration.ts

const PARSE_QUERY_URL = 'http://localhost:54321/functions/v1/parse-query';
const VECTOR_SEARCH_URL = 'http://localhost:54321/functions/v1/vector-search';

interface IntegrationTestCase {
  name: string;
  naturalQuery: string;
  validateParsedQuery?: (parsed: any) => void;
  validateSearchResults?: (results: any) => void;
}

const testCases: IntegrationTestCase[] = [
  {
    name: "End-to-end: Simple product search",
    naturalQuery: "I need 10 boxes of printer paper",
    validateParsedQuery: (parsed) => {
      console.assert(parsed.quantity === 10, "Should parse quantity as 10");
      console.assert(parsed.product_description.includes("printer paper"), 
        "Should extract printer paper");
    },
    validateSearchResults: (results) => {
      console.assert(results.total_results > 0, "Should find some products");
      console.assert(results.products.some((p: any) => 
        p.title.toLowerCase().includes("paper") || 
        p.description?.toLowerCase().includes("paper")), 
        "Results should contain paper products");
    }
  },
  {
    name: "End-to-end: Filtered search with supplier",
    naturalQuery: "Get me 5 packs of sticky notes from 3M",
    validateParsedQuery: (parsed) => {
      console.assert(parsed.quantity === 5, "Should parse quantity");
      console.assert(parsed.supplier === "3M", "Should extract 3M as supplier");
      console.assert(parsed.product_description.includes("sticky notes"), 
        "Should extract product");
    },
    validateSearchResults: (results) => {
      console.assert(results.filters?.vendor === "3M", "Should apply vendor filter");
      console.assert(results.products.every((p: any) => p.vendor === "3M"), 
        "All results should be from 3M");
    }
  },
  {
    name: "End-to-end: Price-filtered search",
    naturalQuery: "I want 20 notebooks under $5 each",
    validateParsedQuery: (parsed) => {
      console.assert(parsed.quantity === 20, "Should parse quantity");
      console.assert(parsed.price_max === 5, "Should extract price limit");
    },
    validateSearchResults: (results) => {
      console.assert(results.filters?.price_max === 5, "Should apply price filter");
      console.assert(results.products.every((p: any) => 
        p.price_min == null || p.price_min <= 5), 
        "All products should be under $5");
    }
  },
  {
    name: "End-to-end: Complex query with multiple filters",
    naturalQuery: "Order 3 dozen blue ballpoint pens from Bic under $2 each",
    validateParsedQuery: (parsed) => {
      console.assert(parsed.quantity === 36, "Should convert dozen to 36");
      console.assert(parsed.supplier?.toLowerCase() === "bic", "Should extract Bic");
      console.assert(parsed.price_max === 2, "Should extract price limit");
      console.assert(parsed.product_description.includes("blue") && 
        parsed.product_description.includes("ballpoint"), 
        "Should include attributes in description");
    },
    validateSearchResults: (results) => {
      console.assert(results.filters?.vendor?.toLowerCase() === "bic", 
        "Should filter by Bic");
      console.assert(results.filters?.price_max === 2, "Should filter by price");
    }
  }
];

async function runIntegrationTest(testCase: IntegrationTestCase) {
  console.log(`\n🔗 Running integration test: ${testCase.name}`);
  console.log(`  Natural query: "${testCase.naturalQuery}"`);
  
  try {
    // Step 1: Parse the natural language query
    console.log("\n  📝 Step 1: Parsing query...");
    const parseResponse = await fetch(PARSE_QUERY_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0'
      },
      body: JSON.stringify({ query: testCase.naturalQuery })
    });

    if (!parseResponse.ok) {
      throw new Error(`Parse query failed: ${parseResponse.status}`);
    }

    const parsedQuery = await parseResponse.json();
    console.log(`  ✅ Query parsed successfully`);
    console.log(`     Product: ${parsedQuery.product_description}`);
    console.log(`     Quantity: ${parsedQuery.quantity}`);
    
    if (testCase.validateParsedQuery) {
      try {
        testCase.validateParsedQuery(parsedQuery);
        console.log(`  ✅ Parse validation passed`);
      } catch (error) {
        console.log(`  ❌ Parse validation failed: ${error.message}`);
      }
    }

    // Step 2: Use parsed query for vector search
    console.log("\n  🔍 Step 2: Performing vector search...");
    
    // Build search request from parsed query
    const searchRequest: any = {
      query: parsedQuery.product_description,
      strategy: "hybrid",
      max_results: 10,
      filters: {}
    };

    // Add filters based on parsed query
    if (parsedQuery.supplier) {
      searchRequest.filters.vendor = parsedQuery.supplier;
    }
    if (parsedQuery.price_max) {
      searchRequest.filters.price_max = parsedQuery.price_max;
    }

    const searchResponse = await fetch(VECTOR_SEARCH_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0'
      },
      body: JSON.stringify(searchRequest)
    });

    if (!searchResponse.ok) {
      throw new Error(`Vector search failed: ${searchResponse.status}`);
    }

    const searchResults = await searchResponse.json();
    console.log(`  ✅ Search completed successfully`);
    console.log(`     Found: ${searchResults.total_results} products`);
    console.log(`     Time: ${searchResults.performance.total_time_ms}ms`);
    
    if (searchResults.products.length > 0) {
      console.log(`     Top result: ${searchResults.products[0].title}`);
      console.log(`     Score: ${searchResults.products[0].similarity_score}`);
    }

    if (testCase.validateSearchResults) {
      try {
        testCase.validateSearchResults(searchResults);
        console.log(`  ✅ Search validation passed`);
      } catch (error) {
        console.log(`  ❌ Search validation failed: ${error.message}`);
      }
    }

    // Step 3: Simulate purchase order population
    console.log("\n  📦 Step 3: Simulating purchase order...");
    if (searchResults.products.length > 0) {
      const selectedProduct = searchResults.products[0];
      console.log(`  Selected product: ${selectedProduct.title}`);
      console.log(`  Vendor: ${selectedProduct.vendor}`);
      console.log(`  Price range: $${selectedProduct.price_min || 'N/A'} - $${selectedProduct.price_max || 'N/A'}`);
      console.log(`  Quantity needed: ${parsedQuery.quantity}`);
      
      if (selectedProduct.variants?.length > 0) {
        const availableVariant = selectedProduct.variants.find((v: any) => v.available);
        if (availableVariant) {
          console.log(`  Available variant: ${availableVariant.title} @ $${availableVariant.price}`);
          console.log(`  Total cost: $${(availableVariant.price * parsedQuery.quantity).toFixed(2)}`);
        }
      }
    }

  } catch (error) {
    console.log(`  ❌ Integration test failed: ${error.message}`);
  }
}

async function runAllTests() {
  console.log("🚀 Starting Integration Tests (Parse Query → Vector Search)");
  console.log("=" .repeat(60));

  for (const testCase of testCases) {
    await runIntegrationTest(testCase);
    // Delay between tests
    await new Promise(resolve => setTimeout(resolve, 1500));
  }

  console.log("\n✅ All integration tests completed!");
}

// Run tests
if (import.meta.main) {
  runAllTests();
}