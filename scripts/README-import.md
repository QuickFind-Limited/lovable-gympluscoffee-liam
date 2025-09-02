# PoundFun Product Import Script

This script imports product data from the PoundFun Shopify export into the Supabase database.

## Prerequisites

1. Ensure the database migrations have been run:
   ```bash
   npm run supabase:migrate
   ```

2. Set up environment variables in `.env`:
   ```env
   VITE_SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
   ```

## Usage

### Dry Run (Preview what will be imported)
```bash
npm run import:products:dry
```

### Live Import
```bash
npm run import:products
```

### Configuration Options

You can customize the import behavior with environment variables:

- `BATCH_SIZE=100` - Number of products to process per batch (default: 100)
- `DRY_RUN=true` - Preview mode without actual database writes
- `SUPABASE_SERVICE_ROLE_KEY` - Required for authentication

Example with custom batch size:
```bash
BATCH_SIZE=50 npm run import:products
```

## What the Script Does

1. **Reads** the JSON export file from `data/poundfun_products_20250723_151901.json`
2. **Validates** the data structure and checks for required fields
3. **Processes** products in batches to avoid overwhelming the database
4. **Imports** data into these tables:
   - `products` - Main product information
   - `product_images` - Product images with positions
   - `product_variants` - Pricing and inventory data
   - `product_options` - Customization options

### Data Processing

- **HTML Cleaning**: Removes HTML tags from descriptions
- **SKU Generation**: Creates SKUs where missing using format: `VENDOR-HANDLE-VARIANTID`
- **Price Parsing**: Extracts numeric values from price strings
- **Error Handling**: Implements retry logic with exponential backoff
- **Progress Tracking**: Shows real-time import progress

### Import Statistics

The script provides detailed statistics:
- Total products processed
- Successful imports
- Failed imports with error details
- Import duration
- Success rate

## Next Steps

After importing products, you'll need to:

1. Generate embeddings for vector search:
   ```bash
   npm run generate:embeddings
   ```

2. Verify the import:
   ```sql
   SELECT COUNT(*) FROM products;
   SELECT COUNT(*) FROM product_images;
   SELECT COUNT(*) FROM product_variants;
   ```

## Troubleshooting

### Common Issues

1. **Authentication Error**: Ensure `SUPABASE_SERVICE_ROLE_KEY` is set correctly
2. **Duplicate Key Error**: The script uses upsert, but if issues persist, check for data conflicts
3. **Memory Issues**: Reduce `BATCH_SIZE` for large imports

### Logs

The script provides detailed logging:
- ✅ Successful imports
- ❌ Failed imports with reasons
- ⚠️ Warnings for partial data
- 📊 Progress updates every 10 products