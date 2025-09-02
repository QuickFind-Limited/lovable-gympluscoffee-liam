#!/usr/bin/env tsx
/**
 * Import Kukoon Rugs products from scraped JSON data
 */

import { createClient } from '@supabase/supabase-js'
import fs from 'fs'
import path from 'path'

// Read the scraped data
const dataPath = path.join(process.cwd(), 'kukoon_products.json')
const rawData = fs.readFileSync(dataPath, 'utf-8')
const kukoonData = JSON.parse(rawData)

// Initialize Supabase client
const supabaseUrl = process.env.SUPABASE_URL || 'https://rumaiumnoobdyzdxuumt.supabase.co'
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || ''

if (!supabaseKey) {
  console.error('Please set SUPABASE_SERVICE_ROLE_KEY environment variable')
  process.exit(1)
}

const supabase = createClient(supabaseUrl, supabaseKey)

async function importProducts() {
  console.log(`Starting import of ${kukoonData.products.length} products...`)
  
  let successCount = 0
  let errorCount = 0
  
  // First, ensure we have a Kukoon Rugs supplier
  const { error: supplierError } = await supabase
    .from('suppliers')
    .upsert([
      {
        name: 'Kukoon Rugs',
        description: 'Premium rugs and home decor from kukoonrugs.com'
      }
    ], { onConflict: 'name' })
  
  if (supplierError) {
    console.error('Error creating supplier:', supplierError)
    return
  }
  
  // Process products in batches
  const batchSize = 50
  for (let i = 0; i < kukoonData.products.length; i += batchSize) {
    const batch = kukoonData.products.slice(i, i + batchSize)
    
    console.log(`Processing batch ${Math.floor(i/batchSize) + 1}/${Math.ceil(kukoonData.products.length/batchSize)}...`)
    
    for (const product of batch) {
      try {
        // Get the first image URL (or use placeholder)
        const imageUrl = product.images?.[0]?.src || '/placeholder.svg'
        
        // Get the lowest price from variants
        const prices = product.variants
          .map(v => parseFloat(v.price))
          .filter(p => !isNaN(p))
        const minPrice = prices.length > 0 ? Math.min(...prices) : 0
        
        // Extract size options from variants
        const sizeOptions = [...new Set(
          product.variants
            .map(v => v.option1 || v.title)
            .filter(Boolean)
        )]
        
        // Insert or update product
        const { data: productData, error: productError } = await supabase
          .from('products')
          .upsert([{
            shopify_id: product.id,
            name: product.title,
            handle: product.handle,
            body_html: product.body_html,
            image: imageUrl,
            supplier: 'Kukoon Rugs',
            min_quantity: 1,
            unit_price: `$${minPrice.toFixed(2)}`,
            category: product.product_type || 'Rugs',
            size_options: sizeOptions.length > 0 ? sizeOptions : null,
            product_type: product.product_type,
            tags: product.tags,
            vendor: product.vendor,
            published_at: product.published_at,
            shopify_created_at: product.created_at,
            shopify_updated_at: product.updated_at
          }], { 
            onConflict: 'shopify_id',
            ignoreDuplicates: false 
          })
          .select()
          .single()
        
        if (productError) {
          console.error(`Error inserting product ${product.title}:`, productError)
          errorCount++
          continue
        }
        
        if (!productData) {
          console.error(`No data returned for product ${product.title}`)
          errorCount++
          continue
        }
        
        // Insert variants
        const variantsToInsert = product.variants.map(variant => ({
          product_id: productData.id,
          shopify_variant_id: variant.id,
          title: variant.title,
          option1: variant.option1,
          option2: variant.option2,
          option3: variant.option3,
          sku: variant.sku,
          requires_shipping: variant.requires_shipping,
          taxable: variant.taxable,
          available: variant.available,
          price: parseFloat(variant.price) || 0,
          compare_at_price: variant.compare_at_price ? parseFloat(variant.compare_at_price) : null,
          grams: variant.grams,
          position: variant.position,
          shopify_created_at: variant.created_at,
          shopify_updated_at: variant.updated_at
        }))
        
        if (variantsToInsert.length > 0) {
          const { error: variantError } = await supabase
            .from('product_variants')
            .upsert(variantsToInsert, { 
              onConflict: 'shopify_variant_id',
              ignoreDuplicates: false 
            })
          
          if (variantError) {
            console.error(`Error inserting variants for ${product.title}:`, variantError)
          }
        }
        
        // Insert images
        const imagesToInsert = product.images.map(image => ({
          product_id: productData.id,
          shopify_image_id: image.id,
          position: image.position,
          src: image.src,
          width: image.width,
          height: image.height,
          shopify_created_at: image.created_at,
          shopify_updated_at: image.updated_at
        }))
        
        if (imagesToInsert.length > 0) {
          const { error: imageError } = await supabase
            .from('product_images')
            .upsert(imagesToInsert, { 
              onConflict: 'shopify_image_id',
              ignoreDuplicates: false 
            })
          
          if (imageError) {
            console.error(`Error inserting images for ${product.title}:`, imageError)
          }
        }
        
        // Insert collections
        if (product.collections && product.collections.length > 0) {
          const collectionsToInsert = product.collections.map(collection => ({
            product_id: productData.id,
            collection_handle: collection
          }))
          
          const { error: collectionError } = await supabase
            .from('product_collections')
            .upsert(collectionsToInsert, { 
              onConflict: 'product_id,collection_handle',
              ignoreDuplicates: true 
            })
          
          if (collectionError) {
            console.error(`Error inserting collections for ${product.title}:`, collectionError)
          }
        }
        
        successCount++
        
      } catch (error) {
        console.error(`Error processing product ${product.title}:`, error)
        errorCount++
      }
    }
    
    // Small delay between batches
    await new Promise(resolve => setTimeout(resolve, 100))
  }
  
  console.log('\nImport complete!')
  console.log(`Successfully imported: ${successCount} products`)
  console.log(`Errors: ${errorCount} products`)
}

// Run the import
importProducts().catch(console.error)