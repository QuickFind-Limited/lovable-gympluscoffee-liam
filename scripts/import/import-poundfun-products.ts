#!/usr/bin/env npx tsx

import { createClient } from '@supabase/supabase-js';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import * as dotenv from 'dotenv';

// Load environment variables
dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Supabase configuration
const supabaseUrl = process.env.VITE_SUPABASE_URL || process.env.SUPABASE_URL;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SERVICE_KEY;

if (!supabaseUrl || !supabaseServiceKey) {
  console.error('❌ Missing Supabase credentials. Please set VITE_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables.');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseServiceKey, {
  auth: {
    autoRefreshToken: false,
    persistSession: false
  }
});

// Configuration
const CONFIG = {
  batchSize: parseInt(process.env.BATCH_SIZE || '100'),
  dryRun: process.env.DRY_RUN === 'true',
  dataFile: path.join(__dirname, '..', 'data', 'poundfun_products_20250723_151901.json'),
  importBatch: `import_${new Date().toISOString().slice(0, 10)}_${Date.now()}`,
  retryAttempts: 3,
  retryDelay: 1000, // ms
};

// Types
interface PoundFunProduct {
  id: number;
  title: string;
  handle: string;
  description: string | null;
  vendor: string;
  product_type: string | null;
  tags: string[];
  status: string | null;
  created_at: string;
  updated_at: string;
  published_at: string | null;
  url: string;
  images: Array<{
    id: number;
    src: string;
    alt: string | null;
    position: number;
    width: number;
    height: number;
  }>;
  variants: Array<{
    id: number;
    title: string;
    price: string;
    compare_at_price: string | null;
    sku: string | null;
    barcode: string | null;
    inventory_quantity: number | null;
    available: boolean;
    weight: number | null;
    weight_unit: string | null;
    option1: string | null;
    option2: string | null;
    option3: string | null;
  }>;
  options: Array<{
    name: string;
    position: number;
    values: string[];
  }>;
}

interface ImportStats {
  total: number;
  processed: number;
  successful: number;
  failed: number;
  skipped: number;
  errors: Array<{ product: string; error: string }>;
}

// Utility functions
function cleanHtml(html: string | null): string {
  if (!html) return '';
  // Remove HTML tags and decode entities
  return html
    .replace(/<[^>]*>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\s+/g, ' ')
    .trim();
}

function generateSku(product: PoundFunProduct, variant: any): string {
  // Generate SKU if missing: VENDOR-HANDLE-VARIANTID
  if (variant.sku) return variant.sku;
  
  const vendor = product.vendor.toUpperCase().replace(/\s+/g, '').slice(0, 3);
  const handle = product.handle.slice(0, 10).toUpperCase();
  return `${vendor}-${handle}-${variant.id}`;
}

function parsePrice(priceStr: string | null): number | null {
  if (!priceStr) return null;
  // Remove currency symbols and parse
  const cleaned = priceStr.replace(/[^0-9.-]/g, '');
  const parsed = parseFloat(cleaned);
  return isNaN(parsed) ? null : parsed;
}

async function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function retryOperation<T>(
  operation: () => Promise<T>,
  operationName: string,
  attempts: number = CONFIG.retryAttempts
): Promise<T> {
  for (let attempt = 1; attempt <= attempts; attempt++) {
    try {
      return await operation();
    } catch (error) {
      console.error(`❌ ${operationName} failed (attempt ${attempt}/${attempts}):`, error);
      if (attempt < attempts) {
        const delay = CONFIG.retryDelay * attempt;
        console.log(`⏳ Retrying in ${delay}ms...`);
        await sleep(delay);
      } else {
        throw error;
      }
    }
  }
  throw new Error(`${operationName} failed after ${attempts} attempts`);
}

// Import functions
async function importProduct(product: PoundFunProduct, stats: ImportStats): Promise<void> {
  try {
    if (CONFIG.dryRun) {
      console.log(`🔍 [DRY RUN] Would import: ${product.title} (${product.id})`);
      stats.successful++;
      return;
    }

    // Calculate min and max prices from variants
    const prices = product.variants
      .map(v => parsePrice(v.price))
      .filter(p => p !== null) as number[];
    
    const priceMin = prices.length > 0 ? Math.min(...prices) : null;
    const priceMax = prices.length > 0 ? Math.max(...prices) : null;

    // Prepare product data
    const productData = {
      shopify_id: product.id,
      title: product.title,
      handle: product.handle,
      description: cleanHtml(product.description),
      vendor: product.vendor,
      product_type: product.product_type,
      tags: product.tags || [],
      status: product.status,
      url: product.url,
      price_min: priceMin,
      price_max: priceMax,
      shopify_created_at: product.created_at,
      shopify_updated_at: product.updated_at,
      published_at: product.published_at,
      import_batch: CONFIG.importBatch,
    };

    // Insert product
    const { data: insertedProduct, error: productError } = await supabase
      .from('products')
      .upsert(productData, { onConflict: 'shopify_id' })
      .select('id')
      .single();

    if (productError) {
      throw new Error(`Product insert failed: ${productError.message}`);
    }

    const productId = insertedProduct.id;

    // Insert images
    if (product.images && product.images.length > 0) {
      const imageData = product.images.map(img => ({
        product_id: productId,
        shopify_image_id: img.id,
        src: img.src,
        alt: img.alt,
        position: img.position,
        width: img.width,
        height: img.height,
      }));

      const { error: imageError } = await supabase
        .from('product_images')
        .upsert(imageData, { onConflict: 'shopify_image_id' });

      if (imageError) {
        console.warn(`⚠️ Image insert warning for ${product.title}:`, imageError.message);
      }
    }

    // Insert variants
    if (product.variants && product.variants.length > 0) {
      const variantData = product.variants.map((variant, index) => ({
        product_id: productId,
        shopify_variant_id: variant.id,
        title: variant.title,
        price: parsePrice(variant.price) || 0,
        compare_at_price: parsePrice(variant.compare_at_price),
        sku: generateSku(product, variant),
        barcode: variant.barcode,
        inventory_quantity: variant.inventory_quantity,
        available: variant.available,
        weight: variant.weight,
        weight_unit: variant.weight_unit,
        option1: variant.option1,
        option2: variant.option2,
        option3: variant.option3,
        position: index + 1,
      }));

      const { error: variantError } = await supabase
        .from('product_variants')
        .upsert(variantData, { onConflict: 'shopify_variant_id' });

      if (variantError) {
        console.warn(`⚠️ Variant insert warning for ${product.title}:`, variantError.message);
      }
    }

    // Insert options
    if (product.options && product.options.length > 0) {
      const optionData = product.options.map(opt => ({
        product_id: productId,
        name: opt.name,
        position: opt.position,
        values: opt.values || [],
      }));

      // Delete existing options first to avoid conflicts
      await supabase
        .from('product_options')
        .delete()
        .eq('product_id', productId);

      const { error: optionError } = await supabase
        .from('product_options')
        .insert(optionData);

      if (optionError) {
        console.warn(`⚠️ Option insert warning for ${product.title}:`, optionError.message);
      }
    }

    console.log(`✅ Imported: ${product.title}`);
    stats.successful++;
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error(`❌ Failed to import ${product.title}:`, errorMessage);
    stats.failed++;
    stats.errors.push({ product: product.title, error: errorMessage });
  }
}

async function importBatch(products: PoundFunProduct[], stats: ImportStats, batchNumber: number): Promise<void> {
  console.log(`\n📦 Processing batch ${batchNumber} (${products.length} products)...`);
  
  for (const product of products) {
    await importProduct(product, stats);
    stats.processed++;
    
    // Progress update every 10 products
    if (stats.processed % 10 === 0) {
      const progress = ((stats.processed / stats.total) * 100).toFixed(1);
      console.log(`\n📊 Progress: ${stats.processed}/${stats.total} (${progress}%)`);
      console.log(`   ✅ Successful: ${stats.successful}`);
      console.log(`   ❌ Failed: ${stats.failed}`);
      console.log(`   ⏭️ Skipped: ${stats.skipped}\n`);
    }
  }
}

async function main() {
  console.log('🚀 PoundFun Product Import Script');
  console.log('=================================');
  console.log(`📁 Data file: ${CONFIG.dataFile}`);
  console.log(`📦 Batch size: ${CONFIG.batchSize}`);
  console.log(`🔄 Retry attempts: ${CONFIG.retryAttempts}`);
  console.log(`🏷️ Import batch: ${CONFIG.importBatch}`);
  console.log(`${CONFIG.dryRun ? '🔍 DRY RUN MODE' : '✅ LIVE MODE'}\n`);

  const stats: ImportStats = {
    total: 0,
    processed: 0,
    successful: 0,
    failed: 0,
    skipped: 0,
    errors: [],
  };

  try {
    // Load product data
    console.log('📖 Loading product data...');
    const rawData = await fs.readFile(CONFIG.dataFile, 'utf-8');
    const data = JSON.parse(rawData);
    
    if (!data.products || !Array.isArray(data.products)) {
      throw new Error('Invalid data format: expected products array');
    }

    stats.total = data.products.length;
    console.log(`✅ Loaded ${stats.total} products from ${data.extraction_date}\n`);

    // Process in batches
    const startTime = Date.now();
    for (let i = 0; i < data.products.length; i += CONFIG.batchSize) {
      const batch = data.products.slice(i, i + CONFIG.batchSize);
      const batchNumber = Math.floor(i / CONFIG.batchSize) + 1;
      await importBatch(batch, stats, batchNumber);
      
      // Small delay between batches to avoid overwhelming the database
      if (i + CONFIG.batchSize < data.products.length) {
        await sleep(500);
      }
    }

    // Final summary
    const duration = ((Date.now() - startTime) / 1000).toFixed(1);
    console.log('\n📊 Import Summary');
    console.log('=================');
    console.log(`⏱️ Duration: ${duration}s`);
    console.log(`📦 Total products: ${stats.total}`);
    console.log(`✅ Successfully imported: ${stats.successful}`);
    console.log(`❌ Failed: ${stats.failed}`);
    console.log(`⏭️ Skipped: ${stats.skipped}`);
    console.log(`📈 Success rate: ${((stats.successful / stats.total) * 100).toFixed(1)}%`);

    if (stats.errors.length > 0) {
      console.log('\n❌ Errors:');
      stats.errors.slice(0, 10).forEach(({ product, error }) => {
        console.log(`   - ${product}: ${error}`);
      });
      if (stats.errors.length > 10) {
        console.log(`   ... and ${stats.errors.length - 10} more errors`);
      }
    }

    if (CONFIG.dryRun) {
      console.log('\n🔍 This was a DRY RUN. No data was actually imported.');
      console.log('   Remove DRY_RUN=true to perform actual import.');
    }

    process.exit(stats.failed > 0 ? 1 : 0);
  } catch (error) {
    console.error('\n💥 Fatal error:', error);
    process.exit(1);
  }
}

// Run the import
main().catch(console.error);