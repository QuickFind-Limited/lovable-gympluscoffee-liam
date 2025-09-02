# MOQ (Minimum Order Quantity) Implementation

## Overview

The MOQ implementation ensures that all product orders meet supplier minimum quantity requirements by integrating with Odoo's `product.supplierinfo` model to fetch real-time MOQ data and automatically adjusting quantities during the search process.

## Architecture

### Components

1. **MOQ Service** (`src/services/moqService.ts`)
   - Fetches MOQ data from Odoo via edge function
   - Applies MOQ logic: `max(MOQ, requested_quantity)`
   - Provides fallback behavior for API failures

2. **MOQ Edge Function** (`supabase/functions/fetch-moq/index.ts`)
   - XML-RPC integration with Odoo
   - Fetches `min_qty` from `product.supplierinfo` model
   - Returns structured MOQ data

3. **MOQ Hook** (`src/hooks/useMOQLogic.ts`)
   - React hook for MOQ processing
   - Handles loading states and error recovery
   - Provides user feedback via toasts

4. **UI Integration**
   - SearchBar: Automatically applies MOQ during search
   - OrderSummary: Displays MOQ info and adjustments

## Data Flow

```
Search Query → Parse → Vector Search → MOQ Processing → Display Results
                                            ↓
                              Odoo (product.supplierinfo.min_qty)
```

### MOQ Processing Steps

1. **Search Results**: Products found with requested quantities
2. **MOQ Lookup**: Fetch minimum quantities from Odoo
3. **Logic Application**: Apply `max(MOQ, requested_quantity)` rule
4. **UI Update**: Show adjusted quantities with badges

## API Integration

### Odoo Fields Used
- `product.supplierinfo.min_qty` - Minimum order quantity
- `product.supplierinfo.product_name` - Product name for matching
- `product.supplierinfo.partner_id` - Supplier information
- `product.supplierinfo.price` - Unit price
- `product.supplierinfo.delay` - Lead time

### Edge Function Endpoint
```
POST /functions/v1/fetch-moq
{
  "products": [
    {
      "productName": "Product Name",
      "supplierName": "Supplier Name",
      "productCode": "SKU123"
    }
  ]
}
```

## Error Handling

### Fallback Strategy
1. **Network Errors**: Use default MOQ of 1
2. **Authentication Failures**: Continue with fallback
3. **Timeout (15s)**: Graceful degradation
4. **Odoo Unavailable**: Default minimum quantities

### User Experience
- Non-blocking: Search continues even if MOQ fails
- Informative: Toast notifications for important events
- Transparent: Clear indication of MOQ source (Odoo/fallback)

## UI Features

### Order Summary Display
- **MOQ Badge**: Shows actual MOQ when > 1
- **Adjustment Badge**: Indicates when quantity was increased
- **Info Banner**: Summary of MOQ processing results
- **Source Indicator**: Shows data source (Odoo/fallback)

### Visual Indicators
- 🔵 Blue badges for MOQ information
- ✅ Green for successful Odoo data
- ⚠️ Yellow for fallback data
- 📊 Processing time display

## Configuration

### Service Configuration
```typescript
// Default settings in useMOQLogic
{
  enabled: true,
  staleTime: 10 * 60 * 1000,  // 10 minutes
  cacheTime: 30 * 60 * 1000,  // 30 minutes
  retryCount: 2,
  timeout: 15000              // 15 seconds
}
```

### Odoo Connection
- URL: `https://source-animalfarmacy.odoo.com`
- Database: `source-animalfarmacy`
- Authentication: Via environment variables

## Testing

### Test Script
Run `npx tsx src/test-moq-integration.ts` to verify:
- MOQ data fetching
- Logic application
- Error handling
- Edge cases

### Test Cases
1. **Valid Products**: Products with MOQ data in Odoo
2. **Unknown Products**: Products not in supplier info
3. **Network Failures**: Offline/timeout scenarios
4. **Empty Requests**: No products provided
5. **Authentication**: Invalid/expired tokens

## Performance

### Optimization Features
- **Parallel Processing**: MOQ lookup doesn't block search
- **Caching**: React Query caches MOQ data (10 min)
- **Batching**: Multiple products in single API call
- **Timeout**: 15s limit prevents hanging
- **Fallback**: Immediate response on failures

### Metrics Tracked
- MOQ data fetch success rate
- Processing time (typically <2s)
- Adjustment count per search
- Fallback usage frequency

## Future Enhancements

1. **Caching**: Redis cache for MOQ data
2. **Webhooks**: Real-time MOQ updates from Odoo
3. **Bulk Operations**: MOQ for entire catalogs
4. **Analytics**: MOQ impact reporting
5. **Admin Panel**: MOQ override capabilities

## Support

For issues or questions:
- Check browser console for detailed error logs
- Verify Odoo connectivity via direct API calls
- Review MOQ test script results
- Monitor edge function logs in Supabase dashboard