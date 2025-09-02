# Odoo Purchase Order Integration

This document describes the Odoo purchase order synchronization feature implemented for Animal Farmacy.

## Overview

The integration allows bidirectional synchronization between the Animal Farmacy application and Odoo's purchase order system:

1. **Display Odoo Purchase Orders**: The orders tab fetches and displays purchase orders from Odoo
2. **Create Orders in Odoo**: When generating a purchase order in the app, it creates a corresponding order in Odoo

## Architecture

### Components

1. **OdooService** (`src/services/OdooService.ts`)
   - Frontend service that communicates with the Odoo edge function
   - Handles purchase order CRUD operations
   - Manages supplier and product data fetching

2. **Odoo Edge Function** (`supabase/functions/odoo/index.ts`)
   - Serverless function that communicates with Odoo's XML-RPC API
   - Uses environment variables for Odoo credentials
   - Handles authentication and API calls

3. **Orders UI** (`src/pages/Orders.tsx`)
   - Updated to fetch orders from Odoo
   - "Sync with Odoo" button for manual refresh
   - Automatic order creation in Odoo when new orders are submitted

## Configuration

### Environment Variables

The following environment variables need to be set in Supabase:

```bash
ODOO_URL=https://your-odoo-instance.com
ODOO_DATABASE=your-database-name
ODOO_USERNAME=your-username
ODOO_PASSWORD=your-password
```

### Deploy the Edge Function

```bash
supabase functions deploy odoo
```

## API Operations

### Fetch Purchase Orders
```typescript
const odooService = new OdooService();
const orders = await odooService.fetchPurchaseOrders();
```

### Create Purchase Order
```typescript
const newOrder = {
  partner_id: 1, // Supplier ID
  order_line: [{
    product_id: 1,
    name: 'Product Name',
    product_qty: 10,
    price_unit: 25.00
  }]
};
const orderId = await odooService.createPurchaseOrder(newOrder);
```

### Get Suppliers
```typescript
const suppliers = await odooService.getSuppliers();
```

### Get Products
```typescript
const products = await odooService.getProducts();
```

## Testing

The integration uses TDD methodology with comprehensive test coverage:

1. Unit tests for OdooService
2. Integration tests for edge function
3. UI tests for Orders component

Run tests with:
```bash
npm test
```

## Error Handling

The integration includes comprehensive error handling:

- Network failures with retry logic
- Authentication errors
- Data validation
- Graceful fallback to local data when Odoo is unavailable

## Security

- Odoo credentials are stored as environment variables
- All API calls go through the edge function
- No direct exposure of Odoo credentials to the frontend
- RLS policies ensure only authenticated users can access the API