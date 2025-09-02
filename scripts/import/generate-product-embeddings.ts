#!/usr/bin/env npx tsx

import { createClient } from '@supabase/supabase-js'
import * as dotenv from 'dotenv'
import { fileURLToPath } from 'url'
import path from 'path'

// Load environment variables
dotenv.config()

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// Configuration
interface Config {
  supabaseUrl: string
  supabaseServiceKey: string
  jinaApiKey: string
  batchSize: number
  strategy: 'description' | 'combined' | 'both'
  dryRun: boolean
  retryFailed: boolean
  maxRetries: number
  delayBetweenBatches: number
}

const CONFIG: Config = {
  supabaseUrl: process.env.VITE_SUPABASE_URL || process.env.SUPABASE_URL || '',
  supabaseServiceKey: process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SERVICE_KEY || '',
  jinaApiKey: process.env.JINA_API_KEY || '',
  batchSize: parseInt(process.env.EMBEDDING_BATCH_SIZE || '50'),
  strategy: (process.env.EMBEDDING_STRATEGY as any) || 'both',
  dryRun: process.env.DRY_RUN === 'true',
  retryFailed: process.env.RETRY_FAILED === 'true',
  maxRetries: parseInt(process.env.MAX_RETRIES || '3'),
  delayBetweenBatches: parseInt(process.env.DELAY_BETWEEN_BATCHES || '2000'),
}

interface EmbeddingStats {
  totalProducts: number
  processed: number
  successful: number
  failed: number
  skipped: number
  errors: Array<{ product: string; error: string }>
}

// Validate configuration
function validateConfig(): void {
  const missing: string[] = []
  
  if (!CONFIG.supabaseUrl) missing.push('VITE_SUPABASE_URL or SUPABASE_URL')
  if (!CONFIG.supabaseServiceKey) missing.push('SUPABASE_SERVICE_ROLE_KEY')
  if (!CONFIG.jinaApiKey) missing.push('JINA_API_KEY')
  
  if (missing.length > 0) {
    console.error('❌ Missing required environment variables:')
    missing.forEach(env => console.error(`   - ${env}`))
    console.error('\nPlease set these environment variables and try again.')
    process.exit(1)
  }
  
  if (!['description', 'combined', 'both'].includes(CONFIG.strategy)) {
    console.error('❌ Invalid EMBEDDING_STRATEGY. Must be: description, combined, or both')
    process.exit(1)
  }
}

// Initialize Supabase client
function createSupabaseClient() {
  return createClient(CONFIG.supabaseUrl, CONFIG.supabaseServiceKey, {
    auth: {
      autoRefreshToken: false,
      persistSession: false
    }
  })
}

// Call the generate-embeddings edge function
async function generateEmbeddingsBatch(
  supabase: any,
  productIds: number[],
  retryAttempt: number = 1
): Promise<any> {
  try {
    console.log(`🔄 Calling generate-embeddings function for ${productIds.length} products (attempt ${retryAttempt}/${CONFIG.maxRetries})`)
    
    const { data, error } = await supabase.functions.invoke('generate-embeddings', {
      body: {
        productIds,
        batchSize: productIds.length,
        strategy: CONFIG.strategy,
        retryFailed: CONFIG.retryFailed
      }
    })
    
    if (error) {
      throw new Error(`Edge function error: ${error.message}`)
    }
    
    return data
    
  } catch (error) {
    console.error(`❌ Batch generation failed (attempt ${retryAttempt}):`, error.message)
    
    if (retryAttempt >= CONFIG.maxRetries) {
      throw error
    }
    
    const delay = 1000 * Math.pow(2, retryAttempt - 1) // Exponential backoff
    console.log(`⏳ Retrying in ${delay}ms...`)
    await sleep(delay)
    
    return generateEmbeddingsBatch(supabase, productIds, retryAttempt + 1)
  }
}

// Get products that need embeddings
async function getProductsToProcess(supabase: any): Promise<{ id: number; title: string }[]> {
  let query = supabase
    .from('products')
    .select('id, title')
    .order('id')
  
  if (!CONFIG.retryFailed) {
    // Only process products without embeddings
    if (CONFIG.strategy === 'description') {
      query = query.is('description_embedding', null)
    } else if (CONFIG.strategy === 'combined') {
      query = query.is('combined_embedding', null)
    } else if (CONFIG.strategy === 'both') {
      query = query.or('description_embedding.is.null,combined_embedding.is.null')
    }
  } else {
    // Retry failed embeddings (both fields null)
    query = query
      .is('description_embedding', null)
      .is('combined_embedding', null)
  }
  
  const { data, error } = await query
  
  if (error) {
    throw new Error(`Failed to fetch products: ${error.message}`)
  }
  
  return data || []
}

// Utility function for sleep
async function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

// Process a batch of products
async function processBatch(
  supabase: any,
  products: { id: number; title: string }[],
  batchNumber: number,
  totalBatches: number,
  stats: EmbeddingStats
): Promise<void> {
  console.log(`\n📦 Processing batch ${batchNumber}/${totalBatches} (${products.length} products)`)
  
  if (CONFIG.dryRun) {
    console.log('🔍 [DRY RUN] Would process products:')
    products.forEach(p => console.log(`   - ${p.id}: ${p.title}`))
    stats.successful += products.length
    stats.processed += products.length
    return
  }
  
  try {
    const productIds = products.map(p => p.id)
    const result = await generateEmbeddingsBatch(supabase, productIds)
    
    console.log('📊 Batch result:', result.results)
    
    // Update stats
    stats.processed += result.results.processed || products.length
    stats.successful += result.results.successful || 0
    stats.failed += result.results.failed || 0
    
    // Add any errors
    if (result.errors && Array.isArray(result.errors)) {
      result.errors.forEach((error: string) => {
        stats.errors.push({ product: 'batch', error })
      })
    }
    
    console.log(`✅ Batch ${batchNumber} completed: ${result.results.successful}/${products.length} successful`)
    
  } catch (error) {
    console.error(`❌ Batch ${batchNumber} failed:`, error.message)
    
    // Mark all products in batch as failed
    stats.failed += products.length
    stats.processed += products.length
    
    products.forEach(product => {
      stats.errors.push({ 
        product: `${product.id}: ${product.title}`, 
        error: error.message 
      })
    })
  }
}

// Display progress
function displayProgress(stats: EmbeddingStats): void {
  const progressPercent = stats.totalProducts > 0 
    ? ((stats.processed / stats.totalProducts) * 100).toFixed(1)
    : '0.0'
  
  console.log(`\n📊 Progress: ${stats.processed}/${stats.totalProducts} (${progressPercent}%)`)
  console.log(`   ✅ Successful: ${stats.successful}`)
  console.log(`   ❌ Failed: ${stats.failed}`)
  console.log(`   ⏭️ Skipped: ${stats.skipped}`)
}

// Main execution function
async function main(): Promise<void> {
  console.log('🚀 PoundFun Product Embeddings Generation')
  console.log('==========================================')
  console.log(`🔧 Configuration:`)
  console.log(`   📦 Batch size: ${CONFIG.batchSize}`)
  console.log(`   🎯 Strategy: ${CONFIG.strategy}`)
  console.log(`   🔄 Max retries: ${CONFIG.maxRetries}`)
  console.log(`   ⏱️ Delay between batches: ${CONFIG.delayBetweenBatches}ms`)
  console.log(`   🔍 Dry run: ${CONFIG.dryRun ? 'Yes' : 'No'}`)
  console.log(`   🔄 Retry failed: ${CONFIG.retryFailed ? 'Yes' : 'No'}`)
  console.log('')
  
  validateConfig()
  
  const supabase = createSupabaseClient()
  
  const stats: EmbeddingStats = {
    totalProducts: 0,
    processed: 0,
    successful: 0,
    failed: 0,
    skipped: 0,
    errors: []
  }
  
  try {
    // Get products to process
    console.log('📋 Fetching products to process...')
    const products = await getProductsToProcess(supabase)
    
    if (products.length === 0) {
      console.log('✅ No products found that need embedding generation.')
      console.log('   This could mean:')
      console.log('   - All products already have embeddings')
      console.log('   - No products in the database')
      console.log('   - Configuration filters exclude all products')
      return
    }
    
    stats.totalProducts = products.length
    console.log(`✅ Found ${products.length} products to process\n`)
    
    // Process in batches
    const startTime = Date.now()
    const totalBatches = Math.ceil(products.length / CONFIG.batchSize)
    
    for (let i = 0; i < products.length; i += CONFIG.batchSize) {
      const batch = products.slice(i, i + CONFIG.batchSize)
      const batchNumber = Math.floor(i / CONFIG.batchSize) + 1
      
      await processBatch(supabase, batch, batchNumber, totalBatches, stats)
      
      // Display progress
      displayProgress(stats)
      
      // Delay between batches (except for the last batch)
      if (i + CONFIG.batchSize < products.length && CONFIG.delayBetweenBatches > 0) {
        console.log(`⏳ Waiting ${CONFIG.delayBetweenBatches}ms before next batch...`)
        await sleep(CONFIG.delayBetweenBatches)
      }
    }
    
    // Final summary
    const duration = ((Date.now() - startTime) / 1000).toFixed(1)
    const successRate = stats.totalProducts > 0 
      ? ((stats.successful / stats.totalProducts) * 100).toFixed(1)
      : '0.0'
    
    console.log('\n🎉 Embedding Generation Complete!')
    console.log('=================================')
    console.log(`⏱️ Duration: ${duration}s`)
    console.log(`📊 Total products: ${stats.totalProducts}`)
    console.log(`✅ Successfully processed: ${stats.successful}`)
    console.log(`❌ Failed: ${stats.failed}`)
    console.log(`⏭️ Skipped: ${stats.skipped}`)
    console.log(`📈 Success rate: ${successRate}%`)
    
    if (stats.errors.length > 0) {
      console.log('\n❌ Errors encountered:')
      stats.errors.slice(0, 10).forEach(({ product, error }, index) => {
        console.log(`   ${index + 1}. ${product}: ${error}`)
      })
      if (stats.errors.length > 10) {
        console.log(`   ... and ${stats.errors.length - 10} more errors`)
      }
    }
    
    if (CONFIG.dryRun) {
      console.log('\n🔍 This was a DRY RUN. No actual embeddings were generated.')
      console.log('   Set DRY_RUN=false to perform actual embedding generation.')
    } else {
      console.log('\n✅ Embedding generation completed successfully!')
      console.log('   Products now have vector embeddings for semantic search.')
    }
    
    // Exit with appropriate code
    process.exit(stats.failed > 0 ? 1 : 0)
    
  } catch (error) {
    console.error('\n💥 Fatal error:', error.message)
    console.error('Stack trace:', error.stack)
    process.exit(1)
  }
}

// Handle CLI arguments
function parseCliArgs(): void {
  const args = process.argv.slice(2)
  
  args.forEach(arg => {
    if (arg === '--dry-run') {
      CONFIG.dryRun = true
    } else if (arg === '--retry-failed') {
      CONFIG.retryFailed = true
    } else if (arg.startsWith('--batch-size=')) {
      CONFIG.batchSize = parseInt(arg.split('=')[1]) || CONFIG.batchSize
    } else if (arg.startsWith('--strategy=')) {
      const strategy = arg.split('=')[1]
      if (['description', 'combined', 'both'].includes(strategy)) {
        CONFIG.strategy = strategy as any
      }
    } else if (arg === '--help' || arg === '-h') {
      console.log(`
🚀 PoundFun Product Embeddings Generation Script

Usage: npx tsx scripts/generate-product-embeddings.ts [options]

Options:
  --dry-run                    Preview what would be processed without making changes
  --retry-failed              Retry products that previously failed embedding generation
  --batch-size=N              Number of products to process per batch (default: 50)
  --strategy=STRATEGY         Embedding strategy: description, combined, or both (default: both)
  --help, -h                  Show this help message

Environment Variables:
  VITE_SUPABASE_URL          Supabase project URL (required)
  SUPABASE_SERVICE_ROLE_KEY  Supabase service role key (required)
  JINA_API_KEY               Jina AI API key (required)
  EMBEDDING_BATCH_SIZE       Default batch size (default: 50)
  EMBEDDING_STRATEGY         Default embedding strategy (default: both)
  DRY_RUN                    Enable dry run mode (true/false)
  RETRY_FAILED               Retry failed embeddings (true/false)
  MAX_RETRIES                Maximum retry attempts (default: 3)
  DELAY_BETWEEN_BATCHES      Delay between batches in ms (default: 2000)

Examples:
  # Generate embeddings for all products
  npx tsx scripts/generate-product-embeddings.ts

  # Dry run to see what would be processed
  npx tsx scripts/generate-product-embeddings.ts --dry-run

  # Retry failed embeddings with smaller batch size
  npx tsx scripts/generate-product-embeddings.ts --retry-failed --batch-size=25

  # Generate only description embeddings
  npx tsx scripts/generate-product-embeddings.ts --strategy=description
`)
      process.exit(0)
    }
  })
}

// Run the script
if (import.meta.url === `file://${process.argv[1]}`) {
  parseCliArgs()
  main().catch(console.error)
}

export { main, CONFIG }