import { serve } from "https://deno.land/std@0.208.0/http/server.ts";
import { z } from "https://deno.land/x/zod@v3.22.4/mod.ts";
// CORS headers
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE'
};
// Environment configuration
const OPENAI_API_KEY = Deno.env.get('OPENAI_API_KEY');
const OPENAI_API_URL = 'https://api.openai.com/v1/chat/completions';
// Zod schema for a single product
const ProductSchema = z.object({
  product_description: z.string().min(1).describe('Product description for vector search'),
  quantity: z.number().int().positive().describe('Requested quantity')
});

// Zod schema for parsed query output - now supports multiple products
const ParsedQuerySchema = z.object({
  products: z.array(ProductSchema).min(1).max(10).describe('Array of products to order')
});
// Request schema
const RequestSchema = z.object({
  query: z.string().min(1).max(500)
});
// JSON Schema for OpenAI structured output - now supports multiple products
const openAIJsonSchema = {
  name: "multi_product_query_parser",
  schema: {
    type: "object",
    required: ["products"],
    properties: {
      products: {
        type: "array",
        minItems: 1,
        maxItems: 10,
        items: {
          type: "object",
          required: ["product_description", "quantity"],
          properties: {
            product_description: {
              type: "string",
              description: "Product description for vector search (e.g., 'blue shirt', 'sandals size 9')"
            },
            quantity: {
              type: "integer",
              minimum: 1,
              description: "Number of units for this specific product"
            }
          },
          additionalProperties: false
        }
      }
    },
    additionalProperties: false
  },
  strict: true
};
serve(async (req)=>{
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response(null, {
      headers: corsHeaders
    });
  }
  let body: any = null;
  try {
    // Validate request
    body = await req.json();
    const validatedRequest = RequestSchema.parse(body);
    if (!OPENAI_API_KEY) {
      console.error('OpenAI API key not configured');
      // Fallback to basic parsing
      const fallbackResult = fallbackParser(validatedRequest.query);
      return new Response(JSON.stringify({
        success: true,
        data: fallbackResult,
        fallback: true
      }), {
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }
    // Call OpenAI API with structured output
    const openAIResponse = await fetch(OPENAI_API_URL, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${OPENAI_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'gpt-4.1',
        messages: [
          {
            role: 'system',
            content: `You are a product order parser. Extract structured information from natural language queries about product orders.
            
            Key instructions:
            1. Identify ALL products mentioned in the query
            2. Each product gets its own entry in the products array
            3. Extract specific quantities for each product
            4. If a quantity applies to multiple items (e.g., "3 shirts and pants"), apply it to each item
            5. Default to quantity 1 if not specified
            6. Parse quantities like "a dozen" (12), "a pair" (2), "half dozen" (6)
            
            Examples:
            - "5 blue shirts and 3 red pants" → [{product_description: "blue shirts", quantity: 5}, {product_description: "red pants", quantity: 3}]
            - "I need sandals and a hat" → [{product_description: "sandals", quantity: 1}, {product_description: "hat", quantity: 1}]
            - "A dozen white t-shirts" → [{product_description: "white t-shirts", quantity: 12}]
            `
          },
          {
            role: 'user',
            content: validatedRequest.query
          }
        ],
        response_format: {
          type: "json_schema",
          json_schema: openAIJsonSchema
        },
        temperature: 0.1
      })
    });
    if (!openAIResponse.ok) {
      const error = await openAIResponse.json().catch(()=>({}));
      console.error('OpenAI API error:', error);
      // Handle rate limiting
      if (openAIResponse.status === 429) {
        return new Response(JSON.stringify({
          success: false,
          error: 'Rate limit exceeded. Please try again later.',
          code: 'RATE_LIMIT'
        }), {
          status: 429,
          headers: {
            ...corsHeaders,
            'Content-Type': 'application/json',
            'Retry-After': '60'
          }
        });
      }
      // Fallback for other errors
      const fallbackResult = fallbackParser(validatedRequest.query);
      return new Response(JSON.stringify({
        success: true,
        data: fallbackResult,
        fallback: true
      }), {
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }
    const openAIData = await openAIResponse.json();
    const parsedContent = JSON.parse(openAIData.choices[0].message.content);
    // Validate the parsed output
    const validatedOutput = ParsedQuerySchema.parse(parsedContent);
    return new Response(JSON.stringify({
      success: true,
      data: validatedOutput,
      usage: openAIData.usage
    }), {
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  } catch (error) {
    console.error('Parse query error:', error);
    if (error instanceof z.ZodError) {
      return new Response(JSON.stringify({
        success: false,
        error: 'Invalid request format',
        details: error.errors
      }), {
        status: 422,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }
    // For any other error, try fallback parser
    if (body?.query) {
      const fallbackResult = fallbackParser(body.query);
      return new Response(JSON.stringify({
        success: true,
        data: fallbackResult,
        fallback: true
      }), {
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }
    return new Response(JSON.stringify({
      success: false,
      error: 'Failed to parse query',
      message: error instanceof Error ? error.message : 'Unknown error'
    }), {
      status: 500,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  }
});
// Fallback parser for when OpenAI is unavailable - now supports multiple products
function fallbackParser(query: string) {
  const lowerQuery = query.toLowerCase();
  
  // Try to split by common separators
  const parts = lowerQuery.split(/\s+and\s+|,\s*|\s+&\s+/);
  
  const products = parts.map(part => {
    const trimmedPart = part.trim();
    if (!trimmedPart) return null;
    
    // Extract quantity from this part
    const quantityMatch = trimmedPart.match(/(\d+)\s*(boxes?|units?|pieces?|items?|pairs?|dozen)?/);
    let quantity = 1;
    
    if (quantityMatch) {
      quantity = parseInt(quantityMatch[1]);
      // Handle special words
      if (quantityMatch[2] && quantityMatch[2].includes('dozen')) {
        quantity = quantity * 12;
      } else if (quantityMatch[2] && quantityMatch[2].includes('pair')) {
        quantity = quantity * 2;
      }
    }
    
    // Build product description by removing quantity
    let product_description = trimmedPart
      .replace(/\b(a\s+)?(dozen|pair|half\s+dozen)\s+/gi, '')
      .replace(/\b\d+\s*(boxes?|units?|pieces?|items?|pairs?)?\s*/gi, '')
      .replace(/\s+/g, ' ')
      .trim();
    
    if (!product_description) {
      product_description = trimmedPart;
    }
    
    return {
      product_description,
      quantity
    };
  }).filter(p => p !== null);
  
  // If no products found, return the whole query as one product
  if (products.length === 0) {
    return {
      products: [{
        product_description: query,
        quantity: 1
      }]
    };
  }
  
  return { products };
}
