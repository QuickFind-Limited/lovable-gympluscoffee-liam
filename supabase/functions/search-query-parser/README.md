# Parse Query Edge Function

This Supabase edge function uses OpenAI GPT-4 to parse natural language product order queries into structured JSON data.

## Features

- **Structured Output**: Uses OpenAI's JSON schema mode for guaranteed type-safe outputs
- **Comprehensive Parsing**: Extracts product description, quantity, supplier, size, type, and price
- **Error Handling**: Graceful fallbacks for rate limits, timeouts, and API failures
- **Schema Validation**: Uses Zod for runtime type validation
- **CORS Support**: Ready for browser-based applications

## Setup

1. Deploy the function to Supabase:
```bash
supabase functions deploy parse-query
```

2. Set the OpenAI API key:
```bash
supabase secrets set OPENAI_API_KEY=your_api_key_here
```

## API Usage

### Request
```bash
curl -X POST https://your-project.supabase.co/functions/v1/parse-query \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "I need 50 boxes of blue latex gloves from MedSupply Co"}'
```

### Response
```json
{
  "success": true,
  "parsed": {
    "product_description": "blue latex gloves",
    "quantity": 50,
    "supplier": "MedSupply Co",
    "size_specification": null,
    "product_type": "medical supplies",
    "price_max": null,
    "search_strategy": "semantic"
  },
  "original_query": "I need 50 boxes of blue latex gloves from MedSupply Co"
}
```

## Schema

The function returns parsed data with the following structure:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| product_description | string | Yes | Natural language description for vector search |
| quantity | number | Yes | Number of units needed (positive integer) |
| supplier | string | Yes | Preferred supplier name |
| size_specification | string | No | Specific size requirements |
| product_type | string | No | Category or type of product |
| price_max | number | No | Maximum price per unit |
| search_strategy | enum | Yes | One of: 'semantic', 'combined', 'hybrid' |

## Error Handling

The function handles various error scenarios:

- **Rate Limiting (429)**: Returns retry-after header
- **Service Unavailable (503)**: Provides fallback parsing
- **Validation Errors (422)**: Returns detailed validation errors
- **Timeout (408)**: Falls back to basic parsing

## Fallback Mode

When OpenAI API is unavailable, the function uses regex-based fallback parsing to extract:
- Basic quantity detection
- Supplier name extraction
- Price limit detection
- Cleaned product description

## Development

To run locally:
```bash
supabase functions serve parse-query --env-file=.env.local
```

Test with:
```bash
curl -X POST http://localhost:54321/functions/v1/parse-query \
  -H "Content-Type: application/json" \
  -d '{"query": "Order 100 surgical masks from Premier Medical under $50"}'
```