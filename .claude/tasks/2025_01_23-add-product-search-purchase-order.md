# Instruction: Add Product Search Functionality in Purchase Order

## Goal

Enable users to search and add products to their purchase order by clicking the "Add Product" button, which opens a search dialog with simple text-based product name search.

## Existing files

- src/pages/OrderSummary.tsx
- src/integrations/supabase/client.ts
- src/components/ui/dialog.tsx
- src/components/ui/button.tsx
- src/components/ui/input.tsx
- src/components/ui/card.tsx

### New file to create

- src/components/orders/AddProductDialog.tsx
- src/components/orders/ProductSearchCard.tsx
- src/hooks/useProductSearch.ts

## Grouped tasks

### Create Product Search Hook

> Build a custom hook for simple database product search

- Create useProductSearch hook that queries Supabase products table
- Implement search using ilike pattern matching on product title field
- Add debounced search with 300ms delay to reduce database queries
- Return products array, loading state, and error state

### Create Add Product Dialog Component

> Build a modal dialog that opens when "Add Product" is clicked and provides search functionality

- Create AddProductDialog component with Dialog, search Input, and loading states
- Connect to useProductSearch hook for product queries
- Display search results as user types (with debouncing)
- Show loading spinner while searching

### Build Product Search Results Display

> Display search results as interactive product cards within the dialog

- Create ProductSearchCard component showing product image, name, supplier, price
- Add quantity selector (input or +/- buttons) with default value of 1
- Implement "Add to Order" button on each product card
- Handle loading skeletons and empty state messages
- Fetch product images from product_images table

### Integrate with Order State Management

> Connect the search dialog to the existing purchase order state

- Add dialog open/close state management in OrderSummary component
- Implement handleAddProduct function to append products to orderProducts array
- Update order totals (subtotal, tax, total) when products are added
- Show success toast notification after adding product
- Keep dialog open after adding to allow multiple product additions

### Implement User Experience Enhancements

> Polish the search experience with proper feedback and keyboard support

- Add keyboard shortcuts (ESC to close dialog, Enter to focus search)
- Implement error handling with user-friendly error messages
- Add smooth open/close animations for the dialog
- Ensure responsive design works on mobile devices
- Handle edge cases like duplicate products (combine quantities)

## Validation checkpoints

- Clicking "Add Product" button opens the search dialog
- Typing "sandal" returns products with "sandal" in the name
- Product cards display with correct images, prices, and supplier information
- Quantity can be adjusted before adding product to order
- Products are successfully added to the purchase order
- Order totals update correctly after adding products
- Dialog remains open after adding a product
- Search works with debouncing (no excessive database queries)
- Error states display appropriate messages
- Dialog closes with ESC key or clicking outside

## Estimations

- Confidence: High (98%) - Simple database search implementation
- Time to implement: 3-4 hours