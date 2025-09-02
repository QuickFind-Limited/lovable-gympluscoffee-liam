import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE',
}

interface EmbeddingRequest {
  productIds?: number[]
  batchSize?: number
  strategy?: 'description' | 'combined' | 'both'
  retryFailed?: boolean
}

interface JinaEmbeddingResponse {
  model: string
  object: string
  usage: {
    total_tokens: number
    prompt_tokens: number
  }
  data: Array<{
    object: string
    index: number
    embedding: number[]
  }>
}

interface Product {
  id: string
  name: string
  body_html: string
  vendor: string
  product_type: string
  tags: string[]
}

// Configuration
const CONFIG = {
  JINA_API_URL: 'https://api.jina.ai/v1/embeddings',
  MODEL_NAME: 'jina-embeddings-v3',
  MAX_TOKENS_PER_TEXT: 8192,
  MAX_TEXTS_PER_REQUEST: 100, // Conservative batch size for edge function
  EMBEDDING_DIMENSION: 1024,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY_MS: 1000,
  REQUEST_TIMEOUT_MS: 30000,
}

// Utility functions
function cleanHtml(html: string | null): string {
  if (!html) return ''
  
  return html
    .replace(/<[^>]*>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\s+/g, ' ')
    .trim()
}

function truncateText(text: string, maxTokens: number = CONFIG.MAX_TOKENS_PER_TEXT): string {
  // Rough token estimation: 1 token ≈ 4 characters for English text
  const maxChars = maxTokens * 3.5
  
  if (text.length <= maxChars) {
    return text
  }
  
  // Truncate at word boundary near the limit
  const truncated = text.substring(0, maxChars)
  const lastSpaceIndex = truncated.lastIndexOf(' ')
  
  return lastSpaceIndex > maxChars * 0.8 
    ? truncated.substring(0, lastSpaceIndex) + '...'
    : truncated + '...'
}

function prepareDescriptionText(product: Product): string {
  const name = product.name || ''
  const description = cleanHtml(product.body_html) || ''
  
  const combinedText = `${name}${description ? '. ' + description : ''}`
  return truncateText(combinedText)
}

function prepareCombinedText(product: Product): string {
  const name = product.name || ''
  const vendor = product.vendor || ''
  const productType = product.product_type || ''
  const tags = Array.isArray(product.tags) ? product.tags.join(', ') : ''
  const description = cleanHtml(product.body_html) || ''
  
  // Prioritize different fields for rich semantic understanding
  const parts = [
    name,
    vendor ? `by ${vendor}` : '',
    productType ? `(${productType})` : '',
    tags ? `Tags: ${tags}` : '',
    description ? `Description: ${description}` : ''
  ].filter(Boolean)
  
  const combinedText = parts.join('. ')
  return truncateText(combinedText)
}

async function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

async function callJinaAPI(texts: string[], apiKey: string): Promise<number[][]> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), CONFIG.REQUEST_TIMEOUT_MS)
  
  try {
    console.log(`🔄 Calling Jina API with ${texts.length} texts`)
    
    const response = await fetch(CONFIG.JINA_API_URL, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({
        model: CONFIG.MODEL_NAME,
        input: texts,
        task: 'retrieval.passage', // Optimize for retrieval tasks
      }),
      signal: controller.signal,
    })
    
    clearTimeout(timeoutId)
    
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`Jina API error (${response.status}): ${errorText}`)
    }
    
    const data: JinaEmbeddingResponse = await response.json()
    
    if (!data.data || !Array.isArray(data.data)) {
      throw new Error('Invalid Jina API response format')
    }
    
    // Sort by index to ensure correct order
    const sortedEmbeddings = data.data
      .sort((a, b) => a.index - b.index)
      .map(item => item.embedding)
    
    console.log(`✅ Jina API returned ${sortedEmbeddings.length} embeddings`)
    console.log(`📊 Token usage: ${data.usage?.total_tokens || 'unknown'}`)
    
    return sortedEmbeddings
    
  } catch (error) {
    clearTimeout(timeoutId)
    if (error.name === 'AbortError') {
      throw new Error(`Jina API request timed out after ${CONFIG.REQUEST_TIMEOUT_MS}ms`)
    }
    throw error
  }
}

async function generateEmbeddingsWithRetry(
  texts: string[], 
  apiKey: string, 
  attempt: number = 1
): Promise<number[][]> {
  try {
    return await callJinaAPI(texts, apiKey)
  } catch (error) {
    console.error(`❌ Jina API attempt ${attempt} failed:`, error.message)
    
    if (attempt >= CONFIG.RETRY_ATTEMPTS) {
      throw error
    }
    
    const delay = CONFIG.RETRY_DELAY_MS * Math.pow(2, attempt - 1) // Exponential backoff
    console.log(`⏳ Retrying in ${delay}ms... (${attempt}/${CONFIG.RETRY_ATTEMPTS})`)
    await sleep(delay)
    
    return generateEmbeddingsWithRetry(texts, apiKey, attempt + 1)
  }
}

async function updateProductEmbeddings(
  supabase: any,
  productId: number,
  descriptionEmbedding?: number[],
  combinedEmbedding?: number[]
): Promise<void> {
  const updates: any = {
    last_indexed_at: new Date().toISOString(),
  }
  
  if (descriptionEmbedding) {
    updates.embedding = `[${descriptionEmbedding.join(',')}]`
  }
  
  if (combinedEmbedding) {
    updates.embedding_combined = `[${combinedEmbedding.join(',')}]`
  }
  
  const { error } = await supabase
    .from('products')
    .update(updates)
    .eq('id', productId)
  
  if (error) {
    throw new Error(`Failed to update product ${productId}: ${error.message}`)
  }
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Validate environment
    const jinaApiKey = Deno.env.get('JINA_API_KEY')
    if (!jinaApiKey) {
      return new Response(
        JSON.stringify({ error: 'JINA_API_KEY environment variable is required' }),
        { 
          status: 500, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    
    const supabase = createClient(supabaseUrl, supabaseServiceKey, {
      auth: {
        autoRefreshToken: false,
        persistSession: false
      }
    })

    // Parse request
    const {
      productIds = [],
      batchSize = 50,
      strategy = 'both',
      retryFailed = false
    }: EmbeddingRequest = await req.json()

    console.log(`🚀 Starting embedding generation for ${productIds.length || 'all'} products`)
    console.log(`📦 Batch size: ${batchSize}, Strategy: ${strategy}`)

    // Build query for products to process
    let query = supabase
      .from('products')
      .select('id, name, body_html, vendor, product_type, tags')

    if (productIds.length > 0) {
      query = query.in('id', productIds)
    } else if (!retryFailed) {
      // Only process products without embeddings
      if (strategy === 'description' || strategy === 'both') {
        query = query.is('embedding', null)
      } else if (strategy === 'combined') {
        query = query.is('embedding_combined', null)
      }
    } else {
      // Retry failed embeddings (both fields null)
      query = query
        .is('embedding', null)
        .is('embedding_combined', null)
    }

    const { data: products, error: fetchError } = await query
      .order('id')
      .limit(batchSize)

    if (fetchError) {
      throw new Error(`Failed to fetch products: ${fetchError.message}`)
    }

    if (!products || products.length === 0) {
      return new Response(
        JSON.stringify({ 
          message: 'No products found to process',
          processed: 0 
        }),
        { 
          status: 200, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    console.log(`📋 Processing ${products.length} products`)

    // Process products in smaller batches for API calls
    const results = {
      processed: 0,
      successful: 0,
      failed: 0,
      errors: [] as string[]
    }

    for (let i = 0; i < products.length; i += CONFIG.MAX_TEXTS_PER_REQUEST) {
      const batch = products.slice(i, i + CONFIG.MAX_TEXTS_PER_REQUEST)
      console.log(`\n🔄 Processing batch ${Math.floor(i / CONFIG.MAX_TEXTS_PER_REQUEST) + 1}/${Math.ceil(products.length / CONFIG.MAX_TEXTS_PER_REQUEST)}`)

      try {
        // Prepare texts for embedding
        const descriptionTexts: string[] = []
        const combinedTexts: string[] = []
        
        for (const product of batch) {
          if (strategy === 'description' || strategy === 'both') {
            descriptionTexts.push(prepareDescriptionText(product))
          }
          if (strategy === 'combined' || strategy === 'both') {
            combinedTexts.push(prepareCombinedText(product))
          }
        }

        // Generate embeddings
        let descriptionEmbeddings: number[][] = []
        let combinedEmbeddings: number[][] = []

        if (descriptionTexts.length > 0) {
          console.log(`🧠 Generating description embeddings for ${descriptionTexts.length} texts`)
          descriptionEmbeddings = await generateEmbeddingsWithRetry(descriptionTexts, jinaApiKey)
        }

        if (combinedTexts.length > 0) {
          console.log(`🧠 Generating combined embeddings for ${combinedTexts.length} texts`)
          combinedEmbeddings = await generateEmbeddingsWithRetry(combinedTexts, jinaApiKey)
        }

        // Update products with embeddings
        for (let j = 0; j < batch.length; j++) {
          const product = batch[j]
          
          try {
            await updateProductEmbeddings(
              supabase,
              product.id,
              descriptionEmbeddings[j],
              combinedEmbeddings[j]
            )
            
            console.log(`✅ Updated embeddings for product ${product.id}: ${product.name}`)
            results.successful++
          } catch (error) {
            console.error(`❌ Failed to update product ${product.id}:`, error.message)
            results.failed++
            results.errors.push(`Product ${product.id}: ${error.message}`)
          }
          
          results.processed++
        }

        // Small delay between batches to avoid rate limiting
        if (i + CONFIG.MAX_TEXTS_PER_REQUEST < products.length) {
          await sleep(1000)
        }

      } catch (error) {
        console.error(`❌ Batch processing failed:`, error.message)
        
        // Mark all products in this batch as failed
        for (const product of batch) {
          results.failed++
          results.processed++
          results.errors.push(`Product ${product.id}: Batch failed - ${error.message}`)
        }
      }
    }

    const response = {
      message: `Embedding generation completed`,
      results: {
        processed: results.processed,
        successful: results.successful,
        failed: results.failed,
        success_rate: results.processed > 0 ? (results.successful / results.processed * 100).toFixed(1) + '%' : '0%'
      },
      errors: results.errors.slice(0, 10), // Return first 10 errors
      truncated_errors: results.errors.length > 10
    }

    console.log('\n📊 Final Results:', response.results)

    return new Response(
      JSON.stringify(response),
      { 
        status: 200, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )

  } catch (error) {
    console.error('💥 Fatal error:', error)
    return new Response(
      JSON.stringify({ 
        error: 'Internal server error', 
        details: error.message 
      }),
      { 
        status: 500, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )
  }
})