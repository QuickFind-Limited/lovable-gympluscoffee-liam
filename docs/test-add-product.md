# Add Product Feature Test Plan

## Test Steps

1. Navigate to the Order Summary page
2. Click the "+ Add Product" button
3. Verify the search dialog opens
4. Type "sandal" in the search box
5. Verify products with "sandal" in the name appear
6. Adjust quantity using +/- buttons
7. Click "Add to Order" on a product
8. Verify the product is added to the order
9. Verify the order total updates
10. Verify the dialog stays open for adding more products

## Expected Results

- Search dialog opens when clicking "+ Add Product"
- Search results appear after typing (with 300ms debounce)
- Products display with images, names, prices, and suppliers
- Quantity selector works correctly
- Products are added to the order when clicking "Add to Order"
- Order totals update automatically
- Toast notification shows when product is added
- Dialog can be closed with ESC key or clicking outside

## Implementation Complete

All components have been created and integrated:
- ✅ useProductSearch hook for database search
- ✅ AddProductDialog component
- ✅ ProductSearchCard component
- ✅ Integration with OrderSummary page