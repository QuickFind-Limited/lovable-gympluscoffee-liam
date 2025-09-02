# TDD Test Execution Guide

## Running the Odoo Service Layer Tests

This guide explains how to run the comprehensive unit tests created for the Odoo integration service layer following TDD methodology.

## Test Structure

The tests are organized following the Red-Green-Refactor TDD cycle:

```
tests/
├── unit/
│   ├── services/
│   │   ├── OdooIntegrationService.test.ts    # Main orchestrator tests
│   │   ├── OdooPurchaseOrderService.test.ts  # Purchase order service tests
│   │   ├── OdooSyncService.test.ts           # Sync service tests
│   │   ├── CacheService.test.ts              # Cache service tests
│   │   └── EventService.test.ts              # Event service tests
│   ├── repositories/
│   │   └── PurchaseOrderRepository.test.ts   # Repository layer tests
│   └── utils/
│       └── test-factories.ts                 # Test data factories
├── setup.ts                                  # Test environment setup
└── run-tests.md                              # This guide
```

## Test Commands

### Run All Unit Tests
```bash
npm test
```

### Run Tests with Coverage
```bash
npm run test:coverage
```

### Run Tests in Watch Mode
```bash
npm test -- --watch
```

### Run Specific Test File
```bash
npm test -- tests/unit/services/OdooIntegrationService.test.ts
```

### Run Tests with UI
```bash
npm run test:ui
```

## Test Categories

### 1. Service Layer Tests (Red Phase - Currently Failing)

These tests define the expected behavior for services that haven't been implemented yet:

- **OdooIntegrationService**: Central orchestrator for all Odoo operations
- **OdooPurchaseOrderService**: CRUD operations for purchase orders
- **OdooSyncService**: Bidirectional synchronization logic
- **CacheService**: Multi-level caching implementation
- **EventService**: Domain event publishing and handling

### 2. Repository Layer Tests (Red Phase - Currently Failing)

Tests for data access layer:

- **PurchaseOrderRepository**: Local and Odoo data operations
- Conflict detection and resolution
- Sync state management

### 3. Error Handling Tests

Comprehensive error scenarios including:

- Network failures
- Authentication errors
- Data validation failures
- Conflict resolution
- Circuit breaker patterns
- Retry mechanisms

## TDD Implementation Workflow

### Current Status: RED PHASE ✅
All tests are written and currently failing (as expected in TDD):

```bash
# Expected output - all tests should fail
npm test

❌ OdooIntegrationService tests: 12 failing
❌ OdooPurchaseOrderService tests: 8 failing  
❌ OdooSyncService tests: 10 failing
❌ CacheService tests: 15 failing
❌ EventService tests: 12 failing
❌ PurchaseOrderRepository tests: 18 failing

Total: 75 tests failing (Expected in RED phase)
```

### Next Phase: GREEN PHASE 🔄
Implement minimal code to make tests pass:

1. Create service implementations in `src/services/`
2. Create repository implementations in `src/repositories/`
3. Run tests after each implementation
4. Ensure all tests pass with minimal code

### Final Phase: REFACTOR PHASE 🔄
Improve code quality while keeping tests passing:

1. Extract common patterns
2. Improve error handling
3. Optimize performance
4. Enhance maintainability

## Test Features

### Comprehensive Mocking
- Supabase client mocking
- Odoo client mocking
- Cache service mocking
- Event service mocking
- Logger mocking

### Test Data Factories
Consistent test data creation with:
```typescript
import { createTestPurchaseOrder } from '@tests/utils/test-factories'

const order = createTestPurchaseOrder({
  status: OrderStatus.APPROVED,
  totalAmount: 500.00
})
```

### Custom Matchers
```typescript
expect(uuid).toBeValidUUID()
expect(duration).toBeWithinRange(1000, 5000)
expect(mockFn).toHaveBeenCalledOnceWith(expectedArgs)
```

### Performance Monitoring
Tests track slow operations and report performance issues.

## Coverage Goals

Target coverage thresholds:
- **Branches**: 80%
- **Functions**: 80%
- **Lines**: 80%
- **Statements**: 80%

## Test Environment

### Setup Features
- Fake timers for testing time-dependent code
- Global mocks for external dependencies
- Environment variable mocking
- Automatic cleanup between tests

### Testing Tools
- **Vitest**: Fast test runner with TypeScript support
- **Happy DOM**: Lightweight DOM implementation
- **@testing-library**: Testing utilities
- **Vi**: Mocking and spying utilities

## Running Specific Test Scenarios

### Sync Operation Tests
```bash
npm test -- --grep "sync"
```

### Error Handling Tests
```bash
npm test -- --grep "error|failure|timeout"
```

### Cache Tests
```bash
npm test -- --grep "cache"
```

### Conflict Resolution Tests
```bash
npm test -- --grep "conflict"
```

## Debugging Tests

### Enable Verbose Output
```bash
npm test -- --reporter=verbose
```

### Debug Specific Test
```bash
npm test -- --grep "should create new order" --reporter=verbose
```

### Check Test Coverage
```bash
npm run test:coverage
open coverage/index.html
```

## Expected Test Results (RED Phase)

Since we're in the RED phase of TDD, all tests should currently fail with "Method not implemented" errors. This is expected and correct behavior.

Example expected output:
```
FAIL tests/unit/services/OdooIntegrationService.test.ts
  OdooIntegrationService
    syncPurchaseOrderToOdoo
      ✗ should successfully create new order in Odoo when no existing sync mapping exists
        Error: Method not implemented.
      ✗ should update existing order when sync mapping exists  
        Error: Method not implemented.
```

## Next Steps

1. **GREEN PHASE**: Implement services to make tests pass
2. **REFACTOR PHASE**: Improve code quality
3. **Integration Tests**: Add integration test layer
4. **E2E Tests**: Add end-to-end test scenarios

## Test Maintenance

- Keep tests updated as requirements change
- Add new tests for new features
- Remove obsolete tests
- Maintain test data factories
- Monitor test performance

## Troubleshooting

### Common Issues

1. **Import Errors**: Check path aliases in `vitest.config.ts`
2. **Type Errors**: Ensure all types are exported from `src/types/odoo-integration.ts`
3. **Mock Issues**: Check mock implementations in test setup
4. **Timeout Issues**: Increase timeout for slow operations

### Getting Help

1. Check test output for specific error messages
2. Review test setup in `tests/setup.ts`
3. Verify vitest configuration
4. Check TypeScript compilation errors

---

**Remember**: In TDD, failing tests in the RED phase are SUCCESS! They define the behavior we want to implement.