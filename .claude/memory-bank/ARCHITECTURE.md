# ARCHITECTURE.md

## Frontend

- **Framework**: React 18.3.1 with TypeScript 5.5.3 → @package.json
- **State Management**: Multi-layered approach:
  - **Supabase Auth Context** - `AuthContext` for authentication state management with real-time session handling
  - **React Query (TanStack Query 5.56.2)** - Server state management, caching, and data fetching
  - **React Context API** - Client state management (UserContext, FinancialDataContext)
- **Build Tool**: Vite 5.4.1 - Modern build tool with React SWC plugin for fast HMR and builds
- **UI Framework**: shadcn/ui with Radix UI primitives and Tailwind CSS 3.4.11
- **Form Management**: React Hook Form 7.53.0 with Zod 3.23.8 for validation

## Backend

- **Service**: Supabase (PostgreSQL + Auth + Edge Functions)
- **Authentication**: Supabase Auth with JWT tokens, email confirmation, and session management
- **Database**: PostgreSQL via Supabase with type-safe TypeScript integration
- **Real-time**: Supabase Realtime for live data updates
- **API Style**: RESTful via Supabase client + Edge Functions for complex operations
- **File Structure**: Feature-based monolith with clear separation of concerns

## Mobile (if applicable)

- **Framework**: Responsive web application only - Mobile-first design with Tailwind CSS
- **State Management**: Same as frontend (shared contexts and React Query)
- **Platform**: PWA-ready architecture (not currently implemented)

## Database

- **Type**: Supabase PostgreSQL with automated migrations and type generation
- **Schema**: Comprehensive product catalog schema with:
  - `profiles` - User profile management linked to Supabase Auth
  - `products` - Product catalog with vector search capabilities
  - `product_images` - Normalized product image storage
  - Additional tables for suppliers, orders, etc. (as needed)
- **Key Entities**: [User/Profile, Product, ProductImage, Supplier, Order, Invoice]
- **Search**: Full-text search with PostgreSQL + potential vector embeddings for semantic search

## Authentication & Authorization

- **Authentication**: Supabase Auth with comprehensive security:
  - Email/password authentication with confirmation flow
  - JWT tokens with automatic refresh
  - Session persistence across browser sessions
  - Email verification required for new accounts
  - Password reset functionality
- **Authorization**: User-based access control with extensible role system
- **Session Management**: Automatic session handling via Supabase with localStorage persistence
- **Security Features**:
  - PKCE flow for enhanced security
  - Auto-refresh tokens
  - Rate limiting on auth endpoints
  - Comprehensive error handling with user-friendly messages

## API & Communication

- **Primary API**: Supabase client with real-time subscriptions
- **Data Fetching**: React Query for server state management with:
  - Automatic caching and background updates
  - Optimistic updates
  - Error handling and retry logic
  - Infinite queries for pagination
- **Real-time**: Supabase Realtime for live data synchronization
- **External APIs**: OpenAI integration for search enhancement (via Edge Functions)
- **Edge Functions**: Serverless functions for complex business logic and AI integration

## Core Patterns

- **Component Pattern**: Feature-based organization with domain-driven design:
  - `/components/admin/` - Administrative interfaces
  - `/components/dashboard/` - Dashboard-specific components
  - `/components/auth/` - Authentication flows
  - `/components/payment/` - Payment processing
  - `/components/ui/` - Reusable UI components (shadcn/ui)
- **Routing Pattern**: Protected routes with comprehensive authentication guards
- **Styling Pattern**: Tailwind CSS with shadcn/ui design system:
  - Custom brand colors and design tokens
  - Responsive design patterns
  - Consistent component theming
  - Custom animations and transitions

## Performance & Monitoring

- **Caching Strategy**: Multi-level caching approach:
  - React Query for server state caching
  - Supabase built-in query caching
  - Browser caching for static assets
  - Potential Redis caching for Edge Functions
- **Performance Patterns**: 
  - Code splitting with React.lazy and Vite's automatic chunking
  - Image optimization and lazy loading
  - Debounced search queries (300ms)
  - Optimistic updates for better UX
- **Error Handling**: Comprehensive error boundaries and user feedback
- **Monitoring**: Console-based logging with potential for external monitoring integration

## Data Layer Architecture

### State Management Strategy

1. **Server State (React Query)**:
   - Product searches and catalog data
   - User profiles and settings
   - Order and invoice data
   - Real-time updates from Supabase

2. **Authentication State (Supabase Auth Context)**:
   - User session management
   - Authentication status
   - JWT token handling

3. **Client State (React Context)**:
   - UI state and preferences
   - Form state (React Hook Form)
   - Financial dashboard data (temporary mock data)

### Search Architecture

- **Basic Search**: PostgreSQL full-text search via Supabase
- **Enhanced Search**: AI-powered semantic search using OpenAI embeddings
- **Search Client**: Singleton pattern with retry logic and error handling
- **Vector Search**: Capability for semantic product discovery (infrastructure ready)

## Security Architecture

- **Authentication Security**:
  - Email verification required
  - Secure password requirements
  - JWT tokens with expiration
  - PKCE flow implementation
  - Rate limiting on auth endpoints

- **Data Security**:
  - Row Level Security (RLS) policies in Supabase
  - Type-safe database queries
  - Input validation with Zod schemas
  - XSS protection via React's built-in escaping

- **API Security**:
  - Authenticated API calls only
  - Bearer token authentication
  - CORS configuration
  - Environment variable protection

## Deployment Architecture

- **Frontend**: Static site generation via Vite
- **Backend**: Supabase hosted infrastructure
- **CDN**: Supabase CDN for static assets
- **Environment Management**: Environment-based configuration
- **CI/CD**: Ready for integration with GitHub Actions or similar

## Development Tools & Scripts

- **Import Scripts**: Automated product data import utilities
- **Type Generation**: Automatic TypeScript types from Supabase schema
- **Testing Framework**: Vitest with React Testing Library setup
- **Linting**: ESLint with TypeScript and React rules
- **Development Server**: Vite dev server with hot reload

## Integration Points

- **Supabase Services**:
  - Database (PostgreSQL)
  - Authentication
  - Edge Functions
  - Real-time subscriptions
  - File storage (ready for implementation)

- **Third-party Services**:
  - OpenAI for search enhancement
  - Potential payment processors
  - Email services via Supabase

## Scalability Considerations

- **Database Scaling**: Supabase handles PostgreSQL scaling automatically
- **Frontend Scaling**: Static site deployment with CDN distribution
- **Search Scaling**: Vector embeddings ready for large product catalogs
- **Caching Strategy**: Multi-level caching for optimal performance
- **Code Splitting**: Automatic optimization via Vite build process

## Future Architecture Enhancements

- **PWA Implementation**: Service workers for offline capability
- **Advanced Search**: Full vector search implementation
- **Real-time Features**: Live notifications and updates
- **Analytics Integration**: User behavior tracking
- **Advanced Monitoring**: Error tracking and performance monitoring
- **Multi-tenancy**: Support for multiple organizations
- **API Rate Limiting**: Enhanced rate limiting for public APIs