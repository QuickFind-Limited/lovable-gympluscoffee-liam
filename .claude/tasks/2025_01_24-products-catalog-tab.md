# Instruction: Add Products Catalog Tab with Infinite Scrolling

## Goal

Create a new Products Catalog tab in the application where users can browse all their product data with infinite scrolling functionality.

## Existing files

- src/components/dashboard/AppSidebar.tsx
- src/App.tsx
- src/hooks/useProductSearch.ts
- src/integrations/supabase/client.ts
- src/types/search.types.ts

### New file to create

- src/pages/ProductsCatalog.tsx
- src/components/products/ProductCard.tsx
- src/components/products/ProductFilters.tsx
- src/hooks/useInfiniteProducts.ts

## Grouped tasks

### Navigation Setup

> Add Products Catalog to the main navigation

- Add new route in App.tsx for /products-catalog path
- Add Products Catalog menu item to AppSidebar.tsx with Package icon
- Ensure proper navigation flow from sidebar to new page

### Products Catalog Page

> Create the main products catalog page with layout

- Create ProductsCatalog.tsx page component with header and layout
- Implement search bar for filtering products by name
- Add filter options sidebar for vendor, price range, and product type
- Set up grid layout for product cards display

### Infinite Scroll Implementation

> Implement infinite scrolling for products list

- Create useInfiniteProducts hook using React Query's useInfiniteQuery
- Fetch products in batches of 20 items per page
- Implement scroll detection to trigger next page load
- Add loading spinner at bottom when fetching more products

### Product Display Components

> Create reusable components for product display

- Create ProductCard component showing product image, title, vendor, price
- Add hover effects and click handler for product details
- Implement ProductFilters component with vendor dropdown, price range inputs
- Add sort options (name, price, vendor, date added)

### Data Integration

> Connect to Supabase for product data

- Query products table with pagination support
- Join with product_images table for primary image
- Implement filter queries based on selected filters
- Add proper error handling and loading states

## Validation checkpoints

- Products Catalog tab appears in sidebar navigation
- Page loads and displays products in grid layout
- Infinite scroll loads more products when reaching bottom
- Search filters products in real-time
- Filters update product display correctly
- Product cards show image, title, vendor, and price
- Responsive design works on mobile and desktop

## Estimations

- Confidence: High
- Time to implement: 3-4 hours

## Guidance
- Use perplexity as much as you can when you have any doubt, bug or anything, it's there to help you be the best so don't hesitate to use it.