# Multi-Product Query Parser Test Plan

## Feature Overview

The multi-product query parser allows users to request multiple products in a single natural language query. Each product is parsed with its own description and quantity, then searched in parallel for optimal performance.

## Test Cases

### Basic Multi-Product Queries

1. **Two products with explicit quantities**
   - Query: "I need 5 blue shirts and 3 red pants"
   - Expected: 2 products parsed, 5 shirts and 3 pants

2. **Three products with mixed quantities**
   - Query: "10 sandals, 5 hats, and 2 bags"
   - Expected: 3 products parsed with correct quantities

3. **Products with shared quantity**
   - Query: "3 shirts and pants"
   - Expected: 2 products, both with quantity 3

4. **Mixed quantity formats**
   - Query: "I want 3 blue shirts, red dress, and 5 hats"
   - Expected: 3 products (3 shirts, 1 dress, 5 hats)

### Special Quantity Words

5. **Dozen parsing**
   - Query: "A dozen white t-shirts and a pair of shoes"
   - Expected: 12 t-shirts and 2 shoes

6. **Half dozen**
   - Query: "Half dozen eggs and 3 bottles of milk"
   - Expected: 6 eggs and 3 milk bottles

### Complex Queries

7. **Long product list**
   - Query: "I need 2 laptops, 5 mice, 5 keyboards, 10 USB cables, and 3 monitors"
   - Expected: 5 products with correct quantities

8. **Natural language flow**
   - Query: "Can you get me some blue jeans, maybe 2 pairs, and also a leather jacket"
   - Expected: 2 pairs of jeans and 1 jacket

## Implementation Details

### What Changed:

1. **Edge Function Schema**
   - Changed from single product to array of products
   - Each product has its own `product_description` and `quantity`
   - Maximum 10 products per query

2. **OpenAI Prompt**
   - Enhanced to identify multiple products
   - Handles shared quantities
   - Parses special words (dozen, pair, etc.)

3. **Parallel Vector Search**
   - Uses `Promise.all()` for simultaneous searches
   - Handles partial failures gracefully
   - Preserves quantity from parsed data

4. **Frontend Integration**
   - SearchBar performs parallel searches
   - Each product gets best match from vector search
   - All matched products display in purchase order

### Performance Benefits:

- **Parallel Execution**: All products searched simultaneously
- **Single API Call**: One OpenAI call parses all products
- **Efficient Processing**: No sequential bottlenecks

## Validation Steps

1. Navigate to Dashboard
2. Enter multi-product query in search bar
3. Verify parsing message shows correct product count
4. Check all products appear in purchase order
5. Verify each product has correct quantity
6. Confirm images and prices display correctly

## Edge Cases Handled

- Empty product descriptions filtered out
- Failed searches for individual products don't break others
- Maximum 10 products enforced
- Fallback parser also supports multiple products