# Repository Cleanup TODO List

## ✅ Completed Tasks

### 1. Repository Structure Analysis
- Analyzed 150+ files in the repository
- Identified 10 markdown files in root requiring organization
- Found 11 test .mjs files that needed relocation
- Discovered test files mixed with production code in src/

### 2. Folder Structure Creation
- Created `docs/` hierarchy with implementation, architecture, deployment, api, and assets subdirectories
- Created `tests/` structure with odoo-integration and frontend subdirectories
- Created `scripts/` structure with database, odoo, and utilities subdirectories
- Created `logs/` structure for application, deployment, performance, and archived logs
- Created `.github/` structure for workflows and issue templates

### 3. File Organization
- Moved documentation images (odoo_po.png, product_type.png) to `docs/assets/`
- Moved database scripts to `scripts/database/`
- Moved log files to `logs/application/`
- Moved frontend test files to `tests/frontend/`

## 🔄 In Progress Tasks

### 1. Remove Debug Files from src/
- **Issue**: Test files incorrectly placed in production source
- **Files to move/remove**:
  - `src/test-moq-integration.ts` → `tests/integration/moq-integration.test.ts`
  - `src/test-product-display.js` → `tests/unit/product-display.test.js`

### 2. Playwright Testing
- Currently testing application functionality after each change
- Application confirmed working at http://localhost:8080
- Login functionality verified

## 📋 Pending Tasks

### 1. Code Quality Improvements (High Priority)

#### Remove Console.log Statements (77 occurrences)
**Critical Files**:
- `src/integrations/supabase/auth.ts` - 5 occurrences
- `src/services/OdooService.ts` - 15 occurrences
- `src/contexts/AuthContext.tsx` - 2 occurrences
- `src/hooks/useVectorSearch.ts` - 6 occurrences
- `src/hooks/useInfiniteOdooProducts.ts` - 6 occurrences

**Action**: Replace with proper logging service that respects environment

#### TypeScript Improvements
- Replace `any` types with proper interfaces
- Add missing type definitions
- Enable strict mode compliance

#### Security Fixes
- Remove debug information exposure in `src/utils/supabase-debug.ts`
- Add environment checks to prevent production logging

### 2. Performance Optimizations

#### Large Base64 Images
- **File**: `src/data/product-images/index.ts`
- **Issue**: Contains large base64 encoded images
- **Solution**: Move to public directory or CDN

#### Search Implementation
- Remove console.log statements from search hooks
- Implement proper logging service

### 3. Update Import Paths
- Check all import statements after file moves
- Update any broken references
- Ensure build process still works

### 4. Best Practices Implementation

#### ESLint Configuration
- Add rule to prevent console.log in production
- Configure no-unused-vars rule
- Add TypeScript strict checks

#### Pre-commit Hooks
- Install husky for git hooks
- Add lint-staged for file checking
- Prevent console.log commits

#### Logging Service
```typescript
// Suggested implementation
class Logger {
  static debug(message: string, data?: any) {
    if (process.env.NODE_ENV === 'development') {
      console.log(message, data);
    }
  }
  
  static error(message: string, error?: any) {
    // Send to error tracking service in production
    console.error(message, error);
  }
}
```

### 5. Documentation Updates
- Update README.md with new folder structure
- Create CONTRIBUTING.md guidelines
- Add development setup instructions
- Document logging strategy

### 6. Final Validation
- Run full test suite
- Verify all imports work
- Check production build
- Test deployment process

## 🎯 Priority Order

1. **Immediate (Next 2 hours)**
   - Remove test files from src/
   - Clean console.log from auth and core services
   - Add environment checks to debug functions

2. **Short-term (Next 1-2 days)**
   - Replace `any` types with interfaces
   - Implement centralized logging
   - Move base64 images to external resources

3. **Medium-term (Next week)**
   - Standardize import patterns
   - Improve file naming consistency
   - Add TypeScript strict mode

## 📊 Impact Summary

### Before Cleanup
- 10+ markdown files cluttering root directory
- Test files mixed with production code
- 77 console.log statements in production
- Unorganized scripts and documentation
- Security concerns with debug logging

### After Cleanup
- Organized folder structure following best practices
- Clear separation of concerns
- Production-ready code without debug statements
- Improved security and performance
- Better developer experience

## 🚀 Next Steps

1. Complete removal of test files from src/
2. Implement logging service
3. Run comprehensive tests
4. Create pre-commit hooks
5. Update documentation

This cleanup will significantly improve code quality, security, and maintainability while making the repository more professional and easier to navigate for new developers.