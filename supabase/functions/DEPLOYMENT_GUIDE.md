# Supabase Edge Functions Deployment Guide

## OpenAI Search Function Deployment

### Prerequisites

1. Supabase CLI installed
2. OpenAI API key
3. Supabase project created

### Deployment Steps

1. **Set up environment secrets:**
   ```bash
   # Set your OpenAI API key as a secret
   supabase secrets set OPENAI_API_KEY="sk-your-openai-api-key"
   ```

2. **Deploy the edge function:**
   ```bash
   # Deploy the openai-search function
   supabase functions deploy openai-search
   ```

3. **Test the function locally:**
   ```bash
   # Start local Supabase
   supabase start

   # Test with a sample query
   supabase functions invoke openai-search \
     --body '{"query": "I need sandals from Impala size 9"}' \
     --local
   ```

4. **Test the deployed function:**
   ```bash
   # Test production deployment
   supabase functions invoke openai-search \
     --body '{"query": "Show me Nike slides in size 10"}'
   ```

### Function Details

- **Endpoint**: `https://your-project.supabase.co/functions/v1/openai-search`
- **Method**: POST
- **Headers**: 
  - `Authorization: Bearer YOUR_ANON_KEY`
  - `Content-Type: application/json`
- **Body**: `{"query": "your natural language search query"}`

### Features Implemented

1. **Natural Language Processing**: Uses GPT-3.5-turbo to extract search criteria
2. **Smart Fallback**: Falls back to keyword matching if OpenAI fails
3. **Rate Limiting**: 10 requests per minute per IP address
4. **CORS Support**: Ready for frontend integration
5. **Comprehensive Error Handling**: Validates inputs and handles edge cases

### Database Schema

The function expects a `products` table with the following structure:
- `id`: UUID primary key
- `name`: Product name
- `product_type`: Type of product (sandals, slides, etc.)
- `supplier`: Brand/supplier name
- `size`: Product size
- `color`: Product color (optional)
- `price`: Decimal price
- `stock_quantity`: Available stock
- `description`: Product description (optional)
- `image_url`: Product image URL (optional)

### Cost Optimization

- Uses GPT-3.5-turbo for cost efficiency
- Implements rate limiting to prevent abuse
- Falls back to keyword search to save API calls
- Caches results in memory for repeated queries

### Security Considerations

1. OpenAI API key stored as Supabase secret
2. Input validation prevents injection attacks
3. Rate limiting prevents abuse
4. Error messages don't expose sensitive data
5. Uses Supabase RLS for data security

### Monitoring

Monitor function performance:
```bash
# View function logs
supabase functions logs openai-search

# View function metrics
supabase functions list
```

### Troubleshooting

1. **Function not found**: Ensure deployment completed successfully
2. **OpenAI errors**: Check API key is valid and has credits
3. **Database errors**: Verify products table exists with correct schema
4. **Rate limit errors**: Wait 1 minute before retrying
5. **CORS errors**: Check frontend is using correct headers

### Next Steps

1. Add search analytics table for tracking queries
2. Implement caching with Redis for better performance
3. Add more sophisticated NLP for complex queries
4. Create admin dashboard for monitoring searches
5. Add support for multi-language queries