# Generate Embeddings Edge Function

This Supabase Edge Function generates vector embeddings for PoundFun products using Jina AI's `jina-embeddings-v3` model. It supports dual embedding strategies for comprehensive semantic search capabilities.

## Features

- **Jina AI Integration**: Uses `jina-embeddings-v3` model with 1024-dimensional embeddings
- **Dual Embedding Strategy**:
  - `description_embedding`: Title + description for focused product search
  - `combined_embedding`: Title + vendor + product_type + tags for broader matching
- **Batch Processing**: Handles up to 100 products per request with intelligent batching
- **Rate Limiting**: Built-in retry logic with exponential backoff
- **Token Management**: Handles Jina's 8192 token limit with intelligent text truncation
- **Error Handling**: Comprehensive error recovery and reporting
- **HTML Cleaning**: Sanitizes product descriptions by removing HTML tags

## API Endpoint

```
POST /functions/v1/generate-embeddings
```

## Request Body

```json
{
  "productIds": [1, 2, 3],        // Optional: Specific product IDs to process
  "batchSize": 50,                // Optional: Number of products per batch (default: 50)
  "strategy": "both",             // Optional: "description", "combined", or "both" (default: "both")
  "retryFailed": false            // Optional: Retry products with failed embeddings (default: false)
}
```

## Environment Variables

The following environment variables must be set in Supabase Edge Functions:

- `JINA_API_KEY`: Your Jina AI API key (required)
- `SUPABASE_URL`: Supabase project URL (automatically available)
- `SUPABASE_SERVICE_ROLE_KEY`: Service role key (automatically available)

## Response Format

```json
{
  "message": "Embedding generation completed",
  "results": {
    "processed": 50,
    "successful": 48,
    "failed": 2,
    "success_rate": "96.0%"
  },
  "errors": [
    "Product 123: API timeout",
    "Product 456: Invalid text format"
  ],
  "truncated_errors": false
}
```

## Embedding Strategies

### Description Strategy (`description`)
Combines product title and description for focused semantic search:
```
"${title}. ${cleanDescription}"
```

### Combined Strategy (`combined`)  
Combines multiple product fields for broader matching:
```
"${title}. by ${vendor}. (${productType}). Tags: ${tags}. Description: ${cleanDescription}"
```

### Both Strategy (`both`)
Generates both embedding types for maximum search flexibility.

## Text Processing

1. **HTML Cleaning**: Removes HTML tags and decodes entities
2. **Token Limiting**: Truncates text to stay within 8192 token limit
3. **Smart Truncation**: Cuts at word boundaries when possible
4. **Field Prioritization**: Orders fields by importance for combined embeddings

## Error Handling

- **Retry Logic**: Up to 3 attempts with exponential backoff
- **Timeout Protection**: 30-second request timeout
- **Batch Failure Recovery**: Individual product failures don't stop the batch
- **Detailed Error Reporting**: Specific error messages for debugging

## Usage Examples

### Generate embeddings for all products without embeddings
```bash
curl -X POST "https://your-project.supabase.co/functions/v1/generate-embeddings" \
  -H "Authorization: Bearer $SUPABASE_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Generate embeddings for specific products
```bash
curl -X POST "https://your-project.supabase.co/functions/v1/generate-embeddings" \
  -H "Authorization: Bearer $SUPABASE_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "productIds": [1, 2, 3, 4, 5],
    "strategy": "both",
    "batchSize": 10
  }'
```

### Retry failed embeddings
```bash
curl -X POST "https://your-project.supabase.co/functions/v1/generate-embeddings" \
  -H "Authorization: Bearer $SUPABASE_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "retryFailed": true,
    "batchSize": 25
  }'
```

## Deployment

1. **Set Environment Variables**:
   ```bash
   supabase secrets set JINA_API_KEY=your_jina_api_key_here
   ```

2. **Deploy Function**:
   ```bash
   supabase functions deploy generate-embeddings
   ```

3. **Test Deployment**:
   ```bash
   supabase functions invoke generate-embeddings \
     --data '{"productIds": [1], "strategy": "description"}'
   ```

## Performance Considerations

- **Batch Size**: Optimal batch size is 50-100 products per request
- **Rate Limits**: Jina API supports up to 100 texts per request
- **Memory Usage**: Large batches may consume significant memory
- **Timeout**: Individual API calls timeout after 30 seconds
- **Token Usage**: Each product uses ~100-500 tokens depending on content length

## Monitoring

The function logs detailed information about:
- Processing progress
- API response times
- Token usage
- Error rates
- Success metrics

Monitor logs using:
```bash
supabase functions logs generate-embeddings
```

## Database Integration

The function directly updates the `products` table with:
- `description_embedding`: vector(1024) field
- `combined_embedding`: vector(1024) field  
- `last_indexed_at`: timestamp of last embedding generation

These embeddings are used by the vector search functions for semantic product discovery.

## Troubleshooting

### Common Issues

1. **Missing API Key**: Ensure `JINA_API_KEY` is set in Supabase secrets
2. **Timeout Errors**: Reduce batch size or check network connectivity
3. **Token Limit Exceeded**: Function automatically truncates long descriptions
4. **Rate Limiting**: Built-in retry logic handles temporary rate limits

### Debug Mode

Add debug logging by setting `console.log` statements or checking the function logs for detailed execution information.

## Integration with Batch Script

This function is designed to work with the `scripts/generate-product-embeddings.ts` batch processing script, which provides:
- CLI interface for bulk processing
- Progress tracking
- Retry mechanisms
- Configuration management

See the batch script documentation for bulk embedding generation workflows.