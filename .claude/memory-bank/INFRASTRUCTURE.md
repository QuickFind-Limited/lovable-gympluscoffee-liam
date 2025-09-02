# Infrastructure Documentation

## Overview

This document outlines the complete infrastructure setup for the Animal Farmacy application, a modern React-based e-commerce platform with Supabase backend integration, AI-powered search capabilities, and comprehensive product management features.

## Architecture

### Frontend Stack
- **Framework**: React 18.3.1 with TypeScript
- **Build Tool**: Vite 5.4.1 with SWC plugin for fast compilation
- **Styling**: Tailwind CSS with shadcn/ui components
- **State Management**: TanStack React Query for server state
- **Routing**: React Router DOM v6
- **UI Components**: Radix UI primitives with custom styling

### Backend Services
- **Primary Database**: Supabase PostgreSQL with real-time capabilities
- **Authentication**: Supabase Auth with PKCE flow
- **File Storage**: Supabase Storage for product images
- **Edge Functions**: Supabase Deno runtime for serverless functions

### AI & Search Infrastructure
- **Vector Search**: PostgreSQL with pgvector extension
- **AI Provider**: OpenAI GPT-4 for query parsing and product recommendations
- **Search Analytics**: Custom analytics tracking for search performance

## Development Environment

### Port Configuration
- **Development Server**: `localhost:8080` (Vite dev server)
- **Supabase Local API**: `localhost:54321`
- **Supabase Database**: `localhost:54322`
- **Supabase Studio**: `localhost:54323`
- **Email Testing**: `localhost:54324` (Inbucket)

### Required Environment Variables

```bash
# Supabase Configuration
VITE_SUPABASE_URL=https://rumaiumnoobdyzdxuumt.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# OpenAI Integration (for Edge Functions)
OPENAI_API_KEY=sk-...

# Database Connection (for local development)
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Development Tools
- **Package Manager**: npm with package-lock.json
- **TypeScript**: v5.5.3 with strict configuration
- **Linting**: ESLint 9.9.0 with React hooks and TypeScript plugins
- **Testing**: Vitest 3.2.4 with Happy DOM and Testing Library
- **Code Quality**: Prettier integration through Lovable Tagger

## Database Schema

### Core Tables
- **products**: Main product catalog with full-text search support
- **product_variants**: Product variations (size, color, price)
- **product_images**: Product image management with positioning
- **product_options**: Dynamic product option definitions
- **collections**: Product categorization and grouping
- **product_collections**: Many-to-many relationship table

### Vector Search Infrastructure
- **pgvector extension**: Enabled for semantic search capabilities
- **products_with_vectors**: Products table with embedding vectors
- **vector_search_analytics**: Search performance and usage tracking

### Security & Access Control
- **Row Level Security (RLS)**: Enabled on all tables
- **Public Read Access**: Anonymous users can read product data
- **Authenticated Operations**: User-specific data requires authentication

## Supabase Configuration

### Authentication Settings
- **Auth Provider**: Email/password with email confirmation
- **JWT Expiry**: 3600 seconds (1 hour)
- **Refresh Token Rotation**: Enabled
- **Session Storage**: localStorage with PKCE flow
- **Redirect URLs**: 
  - `http://127.0.0.1:8080` (local development)
  - `https://127.0.0.1:8080` (HTTPS local)
  - `http://localhost:8080` (alternate local)

### Edge Functions
1. **openai-search**: AI-powered product search with rate limiting
2. **vector-search**: Semantic search using embeddings
3. **parse-query**: Natural language query parsing
4. **generate-embeddings**: Automatic embedding generation for products

### Storage Configuration
- **File Size Limit**: 50MiB per file
- **Public Bucket**: Product images and assets
- **CDN Integration**: Automatic image optimization and delivery

## Build Process

### Development Build
```bash
npm run dev          # Start development server on port 8080
npm run build:dev    # Development build with source maps
npm run preview      # Preview production build locally
```

### Production Build
```bash
npm run build        # Optimized production build
npm run lint         # Code quality checks
npm run test         # Run test suite
```

### Build Optimizations
- **Code Splitting**: Automatic route-based splitting
- **Tree Shaking**: Unused code elimination
- **Asset Optimization**: Image compression and caching
- **Bundle Analysis**: Built-in bundle size monitoring

## Testing Infrastructure

### Test Configuration
- **Test Runner**: Vitest with Happy DOM environment
- **React Testing**: @testing-library/react for component testing
- **User Interactions**: @testing-library/user-event
- **Coverage Reports**: Built-in coverage with c8

### Test Commands
```bash
npm run test          # Run tests in watch mode
npm run test:ui       # Launch Vitest UI
npm run test:coverage # Generate coverage reports
```

### Test Strategy
- **Unit Tests**: Individual component and utility testing
- **Integration Tests**: API endpoint and database operation testing
- **E2E Tests**: Full user workflow testing
- **Performance Tests**: Load testing for search and database operations

## Deployment Architecture

### GitHub Codespaces Compatibility
- **Devcontainer**: Pre-configured development environment
- **Port Forwarding**: Automatic forwarding of development ports
- **Environment Setup**: Automated installation of dependencies
- **Database Seeding**: Automatic setup of local Supabase instance

### Production Deployment Considerations

#### Hosting Recommendations
- **Frontend**: Vercel, Netlify, or similar JAMstack platform
- **API**: Supabase Edge Functions (Deno runtime)
- **Database**: Supabase managed PostgreSQL
- **CDN**: Automatic through Supabase Storage

#### Environment Configuration
```bash
# Production Environment Variables
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
OPENAI_API_KEY=your-openai-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

#### Performance Optimizations
- **Static Asset Caching**: 1 year cache headers for immutable assets
- **API Response Caching**: Redis layer for frequently accessed data
- **Image Optimization**: WebP conversion and responsive sizing
- **Database Indexing**: Optimized indexes for search and filtering

## External Service Dependencies

### Required Services
1. **Supabase**: Primary backend infrastructure
   - Database hosting and management
   - Authentication and authorization
   - Real-time subscriptions
   - File storage and CDN

2. **OpenAI**: AI-powered features
   - Natural language query parsing
   - Product recommendation engine
   - Search result enhancement

### Optional Services
1. **Email Provider**: Transactional email delivery
2. **Analytics**: Application performance monitoring
3. **Error Tracking**: Production error monitoring and alerting

## Monitoring & Logging

### Application Monitoring
- **Performance Metrics**: Core Web Vitals tracking
- **User Analytics**: Search behavior and conversion tracking
- **Error Tracking**: Client-side error reporting
- **API Monitoring**: Edge function performance and errors

### Database Monitoring
- **Query Performance**: Slow query identification and optimization
- **Connection Pooling**: Efficient database connection management
- **Storage Usage**: Database size and growth monitoring
- **Backup Strategy**: Automated daily backups with point-in-time recovery

### Log Management
- **Frontend Logs**: Browser console and error boundary capture
- **Backend Logs**: Supabase Edge Function logs
- **Database Logs**: PostgreSQL query logs and performance insights
- **Security Logs**: Authentication attempts and security events

## Security Considerations

### Data Protection
- **Encryption at Rest**: Supabase provides automatic encryption
- **Encryption in Transit**: HTTPS everywhere with TLS 1.3
- **API Security**: Row Level Security and JWT validation
- **Input Validation**: Zod schemas for all API endpoints

### Authentication Security
- **Password Requirements**: Configurable strength requirements
- **Session Management**: Secure token storage and rotation
- **Rate Limiting**: API endpoint protection against abuse
- **CORS Configuration**: Strict origin validation

### Code Security
- **Dependency Scanning**: Automated vulnerability detection
- **Secret Management**: Environment variable protection
- **Code Analysis**: ESLint security rules and static analysis
- **Access Control**: GitHub repository protection rules

## Scalability Considerations

### Database Scaling
- **Read Replicas**: Automatic read scaling with Supabase
- **Connection Pooling**: PgBouncer for efficient connection management
- **Query Optimization**: Materialized views for complex queries
- **Partitioning**: Table partitioning for large datasets

### Application Scaling
- **Edge Functions**: Automatic scaling with Deno runtime
- **CDN Distribution**: Global content delivery
- **Caching Strategy**: Multi-layer caching (browser, CDN, database)
- **Load Balancing**: Automatic with Supabase infrastructure

### Cost Optimization
- **Resource Monitoring**: Usage tracking and alerts
- **Query Optimization**: Efficient database operations
- **Asset Optimization**: Compressed and optimized static assets
- **Serverless Functions**: Pay-per-use pricing model

## Disaster Recovery

### Backup Strategy
- **Database Backups**: Daily automated backups with 30-day retention
- **Code Repository**: Distributed Git history across multiple locations
- **Configuration Backup**: Environment and deployment configuration versioning
- **Asset Backup**: Media files stored with redundancy

### Recovery Procedures
- **Database Recovery**: Point-in-time restore capabilities
- **Application Recovery**: Automated deployment from Git repository
- **Configuration Recovery**: Infrastructure as code for rapid rebuilding
- **Rollback Strategy**: Blue-green deployment for safe rollbacks

## Development Workflow

### Local Development Setup
1. **Clone Repository**: `git clone <repository-url>`
2. **Install Dependencies**: `npm install`
3. **Environment Setup**: Copy `.env.example` to `.env.local`
4. **Database Setup**: `supabase start` for local development
5. **Start Development**: `npm run dev`

### Continuous Integration
- **Automated Testing**: Test suite runs on every commit
- **Code Quality**: Linting and formatting checks
- **Security Scanning**: Dependency vulnerability detection
- **Build Verification**: Successful build confirmation

### Deployment Pipeline
- **Development**: Automatic deployment to staging environment
- **Testing**: Comprehensive test suite execution
- **Review**: Manual review and approval process
- **Production**: Automated deployment with rollback capability

## Support & Maintenance

### Regular Maintenance Tasks
- **Dependency Updates**: Monthly security and feature updates
- **Database Maintenance**: Query optimization and index management
- **Performance Monitoring**: Regular performance audit and optimization
- **Security Audits**: Quarterly security review and penetration testing

### Documentation Maintenance
- **API Documentation**: Automated generation from code comments
- **User Documentation**: Regular updates with feature releases
- **Infrastructure Documentation**: This document updated with changes
- **Deployment Guides**: Step-by-step deployment instructions

### Contact Information
- **Technical Lead**: [Contact Information]
- **DevOps Team**: [Contact Information]
- **Security Team**: [Contact Information]
- **Support Team**: [Contact Information]

---

**Last Updated**: 2025-01-31
**Document Version**: 1.0
**Next Review Date**: 2025-04-30