# Vendor Auto-Update Functionality

## Overview
When creating an order from the search bar on the dashboard page, the system **automatically sets the vendor/supplier based on the vendor of the first product** in the search results.

## How It Works

### 1. Search Flow
- User enters a search query in the dashboard search bar
- `SearchBar` component (`src/components/dashboard/SearchBar.tsx`) processes the query
- Search results include products with their vendor/supplier information
- Results are passed to `OrderSummary` page

### 2. Vendor Selection
In `OrderSummary.tsx` (line 808):
```typescript
const currentSupplier = fashionForwardProducts[0]?.supplier || 'Unknown Supplier';
```

### 3. Purchase Order Generation
When user clicks "Generate Purchase Order" (lines 940-944):
```typescript
// Get current supplier from the first product
const currentSupplier = fashionForwardProducts[0]?.supplier || 'Unknown Supplier';

// Prepare data for PO editor
const orderDataToPass = {
  supplier: currentSupplier,  // <-- Vendor is set from first product
  orderNumber: `PO-${Date.now().toString().slice(-6)}`,
  products: fashionForwardProducts.map(product => ({...}))
};
```

### 4. Order Creation
In `PurchaseOrderEditor.tsx`, when sending to supplier (line 401):
```typescript
const newOrder = {
  id: editableData.orderNumber,
  supplier: editableData.supplier,  // <-- Vendor preserved from first product
  // ... other order details
};
```

## Edge Cases Handled

1. **No Vendor Information**: If the first product has no vendor, defaults to "Unknown Supplier"
2. **Mixed Vendors**: When products from different vendors are in the search results, only the first product's vendor is used for the order
3. **Empty Results**: If no products are found, the system uses default products

## Important Notes

- This functionality works specifically for orders created from the **dashboard search bar**
- The vendor is determined by the **first product** in the search results
- If you need to create orders with products from multiple vendors, you would need to create separate purchase orders for each vendor

## Testing

A unit test has been created at `tests/unit/vendor-from-first-product.test.tsx` to verify this functionality.

## Future Considerations

If you need to handle products from multiple vendors in a single search:
1. Group products by vendor
2. Create separate purchase orders for each vendor group
3. Or prompt the user to select which vendor's products to order

Currently, the system simplifies this by using the first product's vendor for the entire order.