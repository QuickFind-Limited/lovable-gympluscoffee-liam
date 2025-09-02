# Task: Odoo Migration Phase 4 - Testing & Demo Preparation

## Objective
Test the Odoo integration thoroughly and prepare for a smooth demo experience.

## Context
- All integration through Supabase Edge Functions
- Minimal frontend changes
- Demo environment focus
- Quick setup and teardown

## Testing Requirements

### 1. Edge Function Testing
Test each function locally before deployment:

```bash
# Test locally with Supabase CLI
supabase start
supabase functions serve odoo-products --env-file .env.local

# Test with curl
curl -X GET 'http://localhost:54321/functions/v1/odoo-products' \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -H "Content-Type: application/json"

# Test search
curl -X GET 'http://localhost:54321/functions/v1/odoo-products?search=dog' \
  -H "Authorization: Bearer YOUR_ANON_KEY"

# Test order creation
curl -X POST 'http://localhost:54321/functions/v1/odoo-orders' \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{"items": [{"product_id": 42, "quantity": 2, "price": 70}]}'
```

### 2. End-to-End Test Scenarios

#### Scenario 1: Browse and Search
1. Load product catalog
2. Search "dog shampoo"
3. Filter by category
4. View product details
5. Verify images display

#### Scenario 2: Multi-Product Search
1. Search "I need 5 collars and 3 leashes for my dogs"
2. Verify AI parsing works
3. Check both product types returned
4. Verify quantities preserved

#### Scenario 3: Complete Purchase
1. Add products to cart
2. Go to checkout
3. Complete order
4. Verify order in Odoo
5. Check order history

### 3. Demo Environment Setup

#### Pre-Demo Checklist
```bash
# 1. Deploy all edge functions
supabase functions deploy odoo-products --no-verify-jwt
supabase functions deploy odoo-categories --no-verify-jwt
supabase functions deploy odoo-orders --no-verify-jwt
supabase functions deploy odoo-product-search --no-verify-jwt
supabase functions deploy odoo-search-suggestions --no-verify-jwt

# 2. Set secrets in Supabase dashboard
# ODOO_URL, ODOO_DATABASE, ODOO_USERNAME, ODOO_PASSWORD

# 3. Test auth flow
# Ensure Supabase auth is working

# 4. Verify Odoo access
# Check credentials work from edge functions
```

#### Demo Data Preparation
1. Ensure Odoo has good demo products
2. Clear any test orders before demo
3. Create a demo user account
4. Pre-load some cart items if needed

### 4. Performance Validation

#### Expected Response Times
- Product list: < 300ms
- Search: < 500ms
- Product details: < 200ms
- Order creation: < 1s

#### Monitor During Demo
```javascript
// Add timing logs to edge functions
console.time('odoo-search');
const results = await searchProducts(odoo, query);
console.timeEnd('odoo-search');
```

### 5. Fallback Strategies

#### If Odoo Connection Fails
```typescript
// In edge functions, add fallback
try {
  const odoo = new OdooClient();
  await odoo.connect();
} catch (error) {
  console.error('Odoo connection failed:', error);
  // Return mock data for demo
  return new Response(JSON.stringify({
    products: [
      { id: 1, name: 'Demo Product', price: 99.99 }
    ]
  }), { headers: corsHeaders });
}
```

#### Quick Fixes During Demo
1. Have Odoo admin panel open
2. Keep edge function logs visible
3. Have backup demo video ready
4. Know how to quickly restart services

### 6. Demo Script

#### Opening
"This is our animal pharmacy e-commerce platform, now fully integrated with Odoo ERP..."

#### Key Points to Show
1. **Search**: "Let me search for dog grooming supplies..."
2. **AI Understanding**: "I can even ask for '5 blue collars and 3 red leashes'..."
3. **Seamless Integration**: "All products come directly from Odoo..."
4. **Order Flow**: "When I complete this order, it's created instantly in Odoo..."
5. **Real-time Sync**: "Let me show you the order in Odoo..."

#### Impressive Features
- Natural language search
- Multi-product understanding
- Real-time Odoo sync
- Secure architecture (edge functions)
- Fast performance

### 7. Troubleshooting Guide

#### Common Issues
1. **Auth errors**: Check Supabase session
2. **Odoo timeout**: Verify credentials and URL
3. **No products**: Check search terms and Odoo data
4. **Slow response**: Check Odoo server load

#### Quick Debug Commands
```bash
# Check edge function logs
supabase functions logs odoo-products

# Test Odoo connection directly
curl -X POST https://source-animalfarmacy.odoo.com/xmlrpc/2/common \
  -H "Content-Type: text/xml" \
  -d '<?xml version="1.0"?><methodCall>...'

# Verify environment variables
supabase secrets list
```

## Demo Success Criteria

### Must Work
- ✅ Product browsing
- ✅ Search functionality  
- ✅ Order creation
- ✅ Odoo sync visible

### Nice to Have
- ✅ Fast response times
- ✅ No console errors
- ✅ Smooth transitions

### Acceptable Limitations
- ⚠️ Limited to existing Odoo products
- ⚠️ Basic search (no fuzzy matching)
- ⚠️ Simple order flow

## Post-Demo
1. Document any issues found
2. Gather feedback on search quality
3. Note performance bottlenecks
4. Plan production improvements

## Notes
- Keep demo focused on integration success
- Emphasize security (secrets in edge functions)
- Show real Odoo data syncing
- Highlight maintained UX despite backend change