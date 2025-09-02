// Test script for vector-search edge function
// Run with: deno run --allow-net test-vector-search.ts

const EDGE_FUNCTION_URL = 'http://localhost:54321/functions/v1/vector-search';

interface TestCase {
  name: string;
  request: any;
  expectedStatus: number;
  validateResponse?: (response: any) => void;
}

const testCases: TestCase[] = [
  {
    name: "Basic search without similarity threshold",
    request: {
      query: "office supplies",
      strategy: "hybrid",
      max_results: 10
    },
    expectedStatus: 200,
    validateResponse: (response) => {
      console.assert(response.query === "office supplies", "Query should match");
      console.assert(response.strategy === "hybrid", "Strategy should match");
      console.assert(Array.isArray(response.products), "Products should be an array");
      console.assert(response.performance, "Should include performance metrics");
    }
  },
  {
    name: "Search with similarity threshold = 0.8",
    request: {
      query: "office supplies",
      strategy: "semantic",
      similarity_threshold: 0.8,
      max_results: 10
    },
    expectedStatus: 200,
    validateResponse: (response) => {
      console.assert(response.products.every((p: any) => p.similarity_score >= 0.8), 
        "All products should have similarity >= 0.8");
    }
  },
  {
    name: "Search with filters",
    request: {
      query: "office supplies",
      strategy: "combined",
      filters: {
        vendor: "3M",
        price_max: 50
      },
      max_results: 10
    },
    expectedStatus: 200,
    validateResponse: (response) => {
      console.assert(response.filters?.vendor === "3M", "Should include filters in response");
    }
  },
  {
    name: "Pagination test",
    request: {
      query: "paper",
      strategy: "hybrid",
      max_results: 5,
      page: 2
    },
    expectedStatus: 200,
    validateResponse: (response) => {
      console.assert(response.page === 2, "Should be on page 2");
      console.assert(response.per_page === 5, "Should have 5 results per page");
    }
  },
  {
    name: "Invalid request - empty query",
    request: {
      query: "",
      strategy: "hybrid"
    },
    expectedStatus: 400
  },
  {
    name: "Invalid request - invalid strategy",
    request: {
      query: "test",
      strategy: "invalid_strategy"
    },
    expectedStatus: 400
  }
];

async function runTest(testCase: TestCase) {
  console.log(`\n🧪 Running test: ${testCase.name}`);
  
  try {
    const response = await fetch(EDGE_FUNCTION_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0'
      },
      body: JSON.stringify(testCase.request)
    });

    const statusMatch = response.status === testCase.expectedStatus;
    console.log(`  Status: ${response.status} ${statusMatch ? '✅' : '❌'} (expected: ${testCase.expectedStatus})`);

    if (response.ok) {
      const data = await response.json();
      
      if (testCase.validateResponse) {
        try {
          testCase.validateResponse(data);
          console.log(`  Validation: ✅ Passed`);
        } catch (error) {
          console.log(`  Validation: ❌ Failed - ${error.message}`);
        }
      }

      // Log some response details
      console.log(`  Results: ${data.total_results} products found`);
      console.log(`  Performance: ${data.performance?.total_time_ms}ms total`);
      console.log(`  Cache hit: ${data.performance?.cache_hit ? 'Yes' : 'No'}`);
      
      if (data.products?.length > 0) {
        console.log(`  Sample product: ${data.products[0].title} (score: ${data.products[0].similarity_score})`);
      }
    } else {
      const errorData = await response.json();
      console.log(`  Error: ${errorData.error || errorData.message}`);
    }

  } catch (error) {
    console.log(`  ❌ Test failed with error: ${error.message}`);
  }
}

async function runAllTests() {
  console.log("🚀 Starting Vector Search Edge Function Tests");
  console.log("=" .repeat(50));

  for (const testCase of testCases) {
    await runTest(testCase);
    // Small delay between tests to avoid rate limiting
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  console.log("\n✅ All tests completed!");
}

// Run tests
if (import.meta.main) {
  runAllTests();
}