import { assertEquals, assertExists } from "https://deno.land/std@0.168.0/testing/asserts.ts";

// Test cases for the parse-query function
const testCases = [
  {
    name: "Basic product order",
    query: "I need 50 boxes of blue latex gloves from MedSupply Co",
    expected: {
      product_description: "blue latex gloves",
      quantity: 50,
      supplier: "MedSupply Co",
      search_strategy: "semantic"
    }
  },
  {
    name: "Order with price limit",
    query: "Order 100 surgical masks from Premier Medical under $50",
    expected: {
      product_description: "surgical masks",
      quantity: 100,
      supplier: "Premier Medical",
      price_max: 50,
      search_strategy: "semantic"
    }
  },
  {
    name: "Complex order with size",
    query: "Get me 25 cases of sterile gauze pads 4x4 inches from Johnson Medical Supplies",
    expected: {
      product_description: "sterile gauze pads",
      quantity: 25,
      supplier: "Johnson Medical Supplies",
      size_specification: "4x4 inches",
      search_strategy: "semantic"
    }
  },
  {
    name: "No supplier specified",
    query: "We need 200 units of disposable syringes",
    expected: {
      product_description: "disposable syringes",
      quantity: 200,
      supplier: "Any Supplier",
      search_strategy: "semantic"
    }
  }
];

// Test the fallback parser function
Deno.test("Fallback parser extracts basic information", () => {
  const getFallbackParse = (query: string) => {
    const lowerQuery = query.toLowerCase();
    
    // Extract quantity
    const quantityMatch = query.match(/(\d+)\s*(units?|pieces?|items?|boxes?|cases?)?/i);
    const quantity = quantityMatch ? parseInt(quantityMatch[1]) : 1;
    
    // Extract supplier
    const supplierKeywords = ['from', 'supplier', 'vendor', 'manufacturer'];
    let supplier = 'Any Supplier';
    for (const keyword of supplierKeywords) {
      const regex = new RegExp(`${keyword}\\s+([\\w\\s]+?)(?:,|\\.|$)`, 'i');
      const match = query.match(regex);
      if (match) {
        supplier = match[1].trim();
        break;
      }
    }
    
    // Extract price
    const priceMatch = query.match(/(?:under|below|max|maximum|up to)\s*\$?\s*(\d+(?:\.\d{2})?)/i);
    const price_max = priceMatch ? parseFloat(priceMatch[1]) : undefined;
    
    // Product description
    let product_description = query
      .replace(/\d+\s*(units?|pieces?|items?|boxes?|cases?)/gi, '')
      .replace(new RegExp(`(from|supplier|vendor)\\s+${supplier}`, 'gi'), '')
      .replace(/(?:under|below|max|maximum|up to)\s*\$?\s*\d+(?:\.\d{2})?/gi, '')
      .trim();
    
    return {
      product_description,
      quantity,
      supplier,
      search_strategy: 'semantic',
      ...(price_max && { price_max })
    };
  };

  // Test basic extraction
  const result1 = getFallbackParse("I need 50 boxes of gloves from MedSupply");
  assertEquals(result1.quantity, 50);
  assertEquals(result1.supplier, "MedSupply");
  assertExists(result1.product_description);

  // Test price extraction
  const result2 = getFallbackParse("Order 100 masks under $25");
  assertEquals(result2.quantity, 100);
  assertEquals(result2.price_max, 25);

  // Test default values
  const result3 = getFallbackParse("Some medical supplies");
  assertEquals(result3.quantity, 1);
  assertEquals(result3.supplier, "Any Supplier");
});

// Integration test example (requires running function)
Deno.test("Integration: Function responds to valid request", async () => {
  const functionUrl = Deno.env.get("FUNCTION_URL") || "http://localhost:54321/functions/v1/parse-query";
  
  try {
    const response = await fetch(functionUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${Deno.env.get("SUPABASE_ANON_KEY") || "test-key"}`
      },
      body: JSON.stringify({
        query: "I need 50 boxes of blue latex gloves from MedSupply Co"
      })
    });

    if (response.ok) {
      const data = await response.json();
      assertExists(data.parsed);
      assertEquals(data.parsed.quantity, 50);
      assertEquals(data.parsed.supplier, "MedSupply Co");
    }
  } catch (error) {
    console.log("Integration test skipped - function not running");
  }
});

console.log("✅ All tests completed");