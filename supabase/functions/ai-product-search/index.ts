import { serve } from "https://deno.land/std@0.208.0/http/server.ts"
import { z } from "https://deno.land/x/zod@v3.22.4/mod.ts"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE',
}

// Zod schemas for validation
const SearchRequestSchema = z.object({
  query: z.string().min(1).max(500)
})

// Updated response schema to match Odoo products
const OdooProductSchema = z.object({
  id: z.number(),
  name: z.string(),
  display_name: z.string().optional(),
  description_sale: z.string().nullable().optional(),
  list_price: z.number(),
  categ_id: z.union([z.array(z.union([z.number(), z.string()])), z.boolean()]).optional(),
  image_1920: z.string().nullable().optional(),
  default_code: z.string().nullable().optional(),
  qty_available: z.number().optional(),
  barcode: z.string().nullable().optional(),
  relevance_score: z.number().optional(),
  requested_quantity: z.number().optional()
})

const SearchResponseSchema = z.object({
  query: z.string(),
  totalResults: z.number(),
  products: z.array(OdooProductSchema),
  suggestions: z.array(z.string()),
  debug: z.object({
    parsedUsed: z.boolean(),
    parseError: z.string().optional(),
    searchType: z.string()
  }).optional()
})

// Types inferred from Zod schemas
type SearchRequest = z.infer<typeof SearchRequestSchema>
type SearchResponse = z.infer<typeof SearchResponseSchema>

// Rate limiting
const rateLimitStore = new Map<string, { count: number; resetTime: number }>()
const RATE_LIMIT_WINDOW = 60000 // 1 minute
const RATE_LIMIT_MAX_REQUESTS = 10

function checkRateLimit(clientIp: string): boolean {
  const now = Date.now()
  const clientData = rateLimitStore.get(clientIp)
  
  if (!clientData || now > clientData.resetTime) {
    rateLimitStore.set(clientIp, {
      count: 1,
      resetTime: now + RATE_LIMIT_WINDOW
    })
    return true
  }
  
  if (clientData.count >= RATE_LIMIT_MAX_REQUESTS) {
    return false
  }
  
  clientData.count++
  return true
}

async function callParseQuery(query: string, supabaseUrl: string, authToken: string) {
  const response = await fetch(`${supabaseUrl}/functions/v1/parse-query`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ query })
  })

  if (!response.ok) {
    throw new Error(`Parse query failed: ${response.status}`)
  }

  const data = await response.json()
  if (!data.success) {
    throw new Error(data.error || 'Parse query failed')
  }

  return data.data
}

async function callOdooProductSearch(
  parsedQuery: any, 
  supabaseUrl: string, 
  authToken: string,
  searchType: 'single' | 'multi' = 'multi'
) {
  // For now, we'll use odoo-catalog-v2 for single searches which has proper parsing
  // Multi-search functionality will need to be implemented later
  if (searchType === 'single') {
    const response = await fetch(`${supabaseUrl}/functions/v1/odoo-catalog-v2`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        search: parsedQuery,
        offset: 0,
        limit: 20,
        category: null
      })
    })

    if (!response.ok) {
      throw new Error(`Odoo product search failed: ${response.status}`)
    }

    return await response.json()
  } else {
    // For multi searches, we need to handle parsed queries
    // This would require implementing multiple searches based on the parsed query
    // For now, we'll throw an error to fall back to single search
    throw new Error('Multi-search not yet implemented')
  }
}

serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  const clientIp = req.headers.get('x-forwarded-for') || 'unknown'

  try {
    // Rate limiting
    if (!checkRateLimit(clientIp)) {
      return new Response(
        JSON.stringify({ error: 'Rate limit exceeded. Please try again later.' }),
        { status: 429, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Method validation
    if (req.method !== 'POST') {
      return new Response(
        JSON.stringify({ error: 'Method not allowed' }),
        { status: 405, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Parse and validate request
    const body = await req.json()
    const searchRequest = SearchRequestSchema.parse(body)

    // Get environment variables
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    
    const authHeader = req.headers.get('authorization')
    const authToken = authHeader || `Bearer ${supabaseServiceKey}`

    let products: any[] = []
    let totalResults = 0
    let parsedUsed = false
    let parseError: string | undefined
    let searchType = 'single'

    try {
      // First try to parse the query using the parse-query function
      const parsedQuery = await callParseQuery(searchRequest.query, supabaseUrl, authToken)
      parsedUsed = true
      searchType = 'multi'

      // Use multi-product search with parsed query
      const searchResults = await callOdooProductSearch(parsedQuery, supabaseUrl, authToken, 'multi')
      
      if (searchResults.results && Array.isArray(searchResults.results)) {
        // Flatten results from multiple product searches
        products = searchResults.results.flatMap((result: any) => result.products || [])
        totalResults = products.length
      }
    } catch (error) {
      console.error('Parse query failed, falling back to simple search:', error)
      parseError = error instanceof Error ? error.message : 'Unknown error'
      parsedUsed = false
      searchType = 'single'

      // Fallback to simple keyword search
      const searchResults = await callOdooProductSearch(searchRequest.query, supabaseUrl, authToken, 'single')
      products = searchResults.products || []
      totalResults = products.length
    }

    // Generate suggestions if no results
    const suggestions: string[] = []
    if (totalResults === 0) {
      suggestions.push('Try using more general terms')
      suggestions.push('Try different product names or categories')
      suggestions.push('Check your spelling')
    } else if (totalResults < 3) {
      suggestions.push('Try using broader search terms for more results')
    }

    // Prepare response
    const response: SearchResponse = {
      query: searchRequest.query,
      totalResults,
      products: products.slice(0, 20), // Limit to 20 results
      suggestions,
      debug: {
        parsedUsed,
        parseError,
        searchType
      }
    }

    // Validate response
    const validatedResponse = SearchResponseSchema.parse(response)

    return new Response(
      JSON.stringify(validatedResponse),
      {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )

  } catch (error) {
    console.error('Request error:', error)
    
    // Zod validation error
    if (error instanceof z.ZodError) {
      return new Response(
        JSON.stringify({ 
          error: 'Validation error',
          details: error.errors 
        }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Generic error
    return new Response(
      JSON.stringify({ 
        error: 'Internal server error',
        message: error instanceof Error ? error.message : 'Unknown error'
      }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})