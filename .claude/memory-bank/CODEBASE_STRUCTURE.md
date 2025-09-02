# Codebase Structure Documentation

## Project Overview

**Project Name:** Animal Farmacy - E-commerce Platform  
**Framework:** React 18 + TypeScript + Vite  
**UI Framework:** shadcn/ui + Radix UI + Tailwind CSS  
**Backend:** Supabase (PostgreSQL + Auth + Edge Functions)  
**State Management:** React Query + Context API  
**Routing:** React Router v6  

## Technology Stack

### Core Technologies
- **Frontend:** React 18.3.1, TypeScript 5.5.3, Vite 5.4.1
- **Backend:** Supabase (PostgreSQL with pgvector for AI search)
- **Authentication:** Supabase Auth with OAuth integrations
- **Styling:** Tailwind CSS 3.4.11, shadcn/ui components
- **State Management:** @tanstack/react-query 5.56.2
- **Form Handling:** React Hook Form + Zod validation
- **Icons:** Lucide React 0.462.0
- **Charts:** Recharts 2.12.7

### Development Tools
- **Build Tool:** Vite with SWC plugin
- **Testing:** Vitest with @testing-library
- **Linting:** ESLint 9.9.0 with TypeScript support
- **Package Manager:** npm (with bun.lockb indicating Bun usage)

## Directory Structure

```
/
├── 📁 src/                           # Main source directory (176 files)
│   ├── 📁 components/                # React components (125+ files)
│   │   ├── 📁 ui/                    # shadcn/ui component library (51 components)
│   │   ├── 📁 admin/                 # Admin dashboard components
│   │   ├── 📁 auth/                  # Authentication components
│   │   ├── 📁 dashboard/             # Dashboard-specific components
│   │   ├── 📁 orders/                # Order management components
│   │   ├── 📁 payment/               # Payment processing components
│   │   ├── 📁 products/              # Product catalog components
│   │   ├── 📁 search/                # AI-powered search components
│   │   └── 📁 erp/                   # ERP integration components
│   ├── 📁 pages/                     # Route-level page components (17 pages)
│   ├── 📁 contexts/                  # React Context providers
│   ├── 📁 hooks/                     # Custom React hooks (8 hooks)
│   ├── 📁 integrations/              # External service integrations
│   │   └── 📁 supabase/              # Supabase client and types
│   ├── 📁 types/                     # TypeScript type definitions
│   ├── 📁 utils/                     # Utility functions
│   ├── 📁 lib/                       # Library configurations
│   ├── App.tsx                       # Main application component
│   ├── main.tsx                      # Application entry point
│   └── index.css                     # Global styles
├── 📁 supabase/                      # Supabase configuration
│   ├── 📁 functions/                 # Edge functions for AI search
│   ├── 📁 migrations/                # Database migrations
│   └── config.toml                   # Supabase configuration
├── 📁 public/                        # Static assets
├── 📁 scripts/                       # Data import and setup scripts
├── 📁 docs/                          # Documentation
├── 📁 data/                          # Sample data files
└── 📁 coordination/                  # AI development coordination
```

## Component Architecture

### UI Component Library (`/src/components/ui/`)
Complete shadcn/ui implementation with 51+ components:

**Core Components:**
- `button.tsx`, `input.tsx`, `label.tsx`, `textarea.tsx`
- `card.tsx`, `dialog.tsx`, `sheet.tsx`, `popover.tsx`
- `form.tsx`, `select.tsx`, `checkbox.tsx`, `radio-group.tsx`

**Navigation Components:**
- `navigation-menu.tsx`, `breadcrumb.tsx`, `sidebar.tsx`
- `dropdown-menu.tsx`, `context-menu.tsx`, `menubar.tsx`

**Data Display:**
- `table.tsx`, `chart.tsx`, `progress.tsx`, `badge.tsx`
- `avatar.tsx`, `skeleton.tsx`, `separator.tsx`

**Feedback Components:**
- `toast.tsx`, `toaster.tsx`, `sonner.tsx`, `alert.tsx`
- `alert-dialog.tsx`, `hover-card.tsx`, `tooltip.tsx`

**Interactive Components:**
- `accordion.tsx`, `collapsible.tsx`, `tabs.tsx`
- `carousel.tsx`, `slider.tsx`, `switch.tsx`, `toggle.tsx`

**Utility Components:**
- `scroll-area.tsx`, `resizable.tsx`, `aspect-ratio.tsx`
- `calendar.tsx`, `command.tsx`, `input-otp.tsx`

### Feature Components

#### Admin Dashboard (`/src/components/admin/`)
```
admin/
├── communication/          # Email communication management
│   ├── AddAccountForm.tsx
│   ├── EmailAccountCard.tsx
│   ├── EmailAccountList.tsx
│   ├── ProviderContent.tsx
│   ├── StatusIndicators.tsx
│   ├── emailUtils.ts
│   └── types.ts
├── inventory/              # Inventory management
│   ├── InventoryStats.tsx
│   ├── InventoryToolbar.tsx
│   ├── ProductDialog.tsx
│   ├── ProductTable.tsx
│   ├── types.ts
│   └── utils.ts
├── supplier/               # Supplier management
│   ├── EmptySupplierState.tsx
│   ├── SupplierDetail.tsx
│   ├── SupplierForm.tsx
│   ├── SupplierHeader.tsx
│   ├── SupplierList.tsx
│   ├── types.ts
│   └── utils.ts
├── historical/             # Historical data storage
│   ├── AddStorageForm.tsx
│   ├── StatusIndicators.tsx
│   ├── StorageAccountCard.tsx
│   ├── StorageAccountList.tsx
│   ├── StorageContent.tsx
│   ├── storageUtils.ts
│   └── types.ts
├── referenceData/
│   └── hooks/
│       └── useStorageData.tsx
├── erp/
│   └── ERPContent.tsx
└── excel/
    └── ExcelContent.tsx
```

#### Authentication (`/src/components/auth/`)
- `GoogleOAuthFlow.tsx` - Google OAuth integration
- `MicrosoftOAuthFlow.tsx` - Microsoft OAuth integration

#### Dashboard (`/src/components/dashboard/`)
- `AppSidebar.tsx` - Main navigation sidebar
- `Header.tsx` - Dashboard header with search
- `SearchBar.tsx`, `SearchDialog.tsx` - Search functionality
- `UserNavigation.tsx` - User menu and profile
- `QuickActions.tsx` - Quick action buttons
- `ProductCard.tsx` - Product display card
- `SalesDataPopover.tsx` - Sales analytics popover
- `analytics/` - Analytics dashboard components

#### Search System (`/src/components/search/`)
- `SearchPerformanceMonitor.tsx` - Search performance tracking
- `SearchSuggestions.tsx` - AI-powered search suggestions
- `SimilarProducts.tsx` - Similar product recommendations

#### Payment Processing (`/src/components/payment/`)
- `MainCheckoutView.tsx` - Main checkout interface
- `PaymentFormSection.tsx` - Payment form handling
- `PaymentProcessingView.tsx` - Processing state
- `PaymentSuccessView.tsx` - Success confirmation
- `InvoicePreviewView.tsx` - Invoice preview
- `DetailedPDFView.tsx` - PDF generation

#### Orders Management (`/src/components/orders/`)
- `AddProductDialog.tsx` - Add products to orders
- `ProductSearchCard.tsx` - Product search in orders

#### ERP Integration (`/src/components/erp/`)
- `NetSuiteConnectionFlow.tsx` - NetSuite integration

## Page Structure (`/src/pages/`)

### Authentication Pages
- `Auth.tsx` - Login/signup page
- `AuthConfirm.tsx` - Email confirmation
- `VerifyEmail.tsx` - Email verification

### Core Application Pages
- `Dashboard.tsx` - Main dashboard with AI search
- `ProductsCatalog.tsx` - Product catalog with filters
- `ProductDetails.tsx` - Individual product details
- `Orders.tsx` - Order management
- `OrderSummary.tsx` - Order summary and checkout
- `OrderConfirmation.tsx` - Order confirmation
- `Suppliers.tsx` - Supplier management
- `DataSources.tsx` - Data source configuration
- `AIInsights.tsx` - AI-powered insights
- `Invoices.tsx` - Invoice management
- `PurchaseOrderEditor.tsx` - Purchase order creation
- `NotFound.tsx` - 404 error page

## Context Providers (`/src/contexts/`)

### Authentication Context (`AuthContext.tsx`)
- Supabase authentication management
- User session handling
- Protected route logic

### User Context (`UserContext.tsx`)
- User profile management
- User preferences

### Financial Data Context (`FinancialDataContext.tsx`)
- Financial data state management
- Order and invoice tracking

## Custom Hooks (`/src/hooks/`)

### Search and Product Hooks
- `useProductSearch.ts` - Product search functionality
- `useVectorSearch.ts` - AI-powered vector search
- `useOpenAISearch.ts` - OpenAI integration for search
- `useOpenAIQueryParser.ts` - Natural language query parsing
- `useInfiniteProducts.ts` - Infinite scrolling for products

### Data Management Hooks
- `useDataSources.ts` - Data source management
- `use-mobile.tsx` - Mobile device detection
- `use-toast.ts` - Toast notification management

## Supabase Integration (`/src/integrations/supabase/`)

### Client Configuration
- `client.ts` - Supabase client initialization
- `auth.ts` - Authentication utilities
- `types.ts` - Database type definitions
- `index.ts` - Integration exports

### Database Schema
- User profiles and authentication
- Product catalog with vector embeddings
- Order and invoice management
- Supplier relationships
- Search analytics

### Edge Functions (`/supabase/functions/`)
- `vector-search/` - AI-powered product search
- `openai-search/` - OpenAI integration
- `parse-query/` - Natural language processing
- `generate-embeddings/` - Product embedding generation

## Type Definitions (`/src/types/`)

### Core Types
- `search.types.ts` - Search functionality types
- `queryParser.types.ts` - Query parsing types

## Utilities (`/src/utils/`)

### Core Utilities
- `searchClient.ts` - Search client configuration
- `pdfGenerator.ts` - PDF generation utilities

### Library Configuration (`/src/lib/`)
- `utils.ts` - Utility functions and className helpers

## Configuration Files

### Build Configuration
- `vite.config.ts` - Vite build configuration
- `tsconfig.json` - TypeScript configuration
- `tsconfig.app.json` - App-specific TypeScript config
- `tsconfig.node.json` - Node.js TypeScript config

### Code Quality
- `eslint.config.js` - ESLint configuration
- `postcss.config.js` - PostCSS configuration
- `tailwind.config.ts` - Tailwind CSS configuration

### Component Library
- `components.json` - shadcn/ui configuration

## Key Features

### AI-Powered Search
- Vector similarity search using pgvector
- Natural language query processing with OpenAI
- Semantic product matching
- Search performance monitoring
- Real-time search suggestions

### Authentication System
- Supabase Auth integration
- OAuth providers (Google, Microsoft)
- Email verification workflow
- Protected routes with loading states

### E-commerce Functionality
- Product catalog with advanced filtering
- Shopping cart and checkout flow
- Order management system
- Invoice generation and PDF export
- Supplier relationship management

### Admin Dashboard
- Inventory management
- Supplier management
- Communication tools
- Historical data access
- ERP integrations (NetSuite)

### Data Management
- Multiple data source integration
- Real-time data synchronization
- Comprehensive analytics
- Performance monitoring

## Development Patterns

### Component Organization
- Atomic design principles
- Feature-based component grouping
- Shared UI component library
- Type-safe props and interfaces

### State Management
- React Query for server state
- Context API for application state
- Local state for component-specific data
- Optimistic updates for better UX

### Code Standards
- TypeScript strict mode disabled for flexibility
- Consistent file naming conventions
- Barrel exports for clean imports
- ESLint with TypeScript rules

### Performance Optimizations
- Code splitting with React.lazy
- Image optimization and lazy loading
- Memoization for expensive computations
- Efficient re-rendering patterns

## Import Strategies

### Path Aliases
```typescript
// Configured in tsconfig.json and vite.config.ts
"@/*": ["./src/*"]

// Usage examples:
import { Button } from "@/components/ui/button"
import { useAuth } from "@/contexts/AuthContext"
import { searchClient } from "@/utils/searchClient"
```

### Component Imports
```typescript
// UI Components (barrel exports)
import { Button, Input, Card } from "@/components/ui"

// Feature Components (direct imports)
import { ProductCard } from "@/components/products/ProductCard"
import { SearchBar } from "@/components/dashboard/SearchBar"

// Page Components
import Dashboard from "@/pages/Dashboard"
```

## Database Schema

### Core Tables
- `profiles` - User profiles and settings
- `products` - Product catalog with embeddings
- `suppliers` - Supplier information
- `orders` - Order management
- `order_items` - Order line items
- `invoices` - Invoice tracking

### AI/Search Tables
- `product_embeddings` - Vector embeddings for search
- `search_analytics` - Search performance metrics
- `query_logs` - Search query logging

## Development Workflow

### Local Development
```bash
npm run dev          # Start development server
npm run build        # Production build
npm run preview      # Preview production build
npm run lint         # Run ESLint
npm run test         # Run tests
```

### Data Import
```bash
npm run import:products      # Import product data
npm run import:products:dry  # Dry run import
```

### Supabase Development
- Local Supabase instance with Docker
- Migration-based schema management
- Edge function development and testing
- Real-time database subscriptions

## Security Considerations

### Authentication
- JWT token management
- Secure cookie handling
- OAuth integration security
- Session timeout management

### Data Protection
- Row Level Security (RLS) in Supabase
- Input validation with Zod
- CORS configuration
- API rate limiting

### Frontend Security
- XSS prevention
- CSRF protection
- Secure API communication
- Environment variable protection

## Performance Metrics

### Bundle Size
- Optimized with Vite and tree shaking
- Code splitting for route-based chunks
- Dynamic imports for heavy components

### Database Performance
- Vector similarity search optimization
- Efficient indexing strategies
- Query performance monitoring
- Connection pooling

### User Experience
- Loading states for all async operations
- Optimistic updates
- Error boundary implementations
- Responsive design patterns

This documentation provides a comprehensive overview of the codebase structure, reflecting the current state of the Animal Farmacy e-commerce platform with its advanced AI search capabilities, comprehensive admin features, and modern React architecture.