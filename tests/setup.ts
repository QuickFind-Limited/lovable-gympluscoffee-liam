/**
 * Vitest Test Setup
 * 
 * This file is executed before all tests and sets up the testing environment
 * for TDD with comprehensive mocking and utilities.
 */

import { beforeAll, afterAll, beforeEach, afterEach, vi } from 'vitest'
import '@testing-library/jest-dom'

// ============================================================================
// Global Test Configuration
// ============================================================================

// Global test configuration is handled in vitest.config.ts

// ============================================================================
// Mock Environment Variables
// ============================================================================

beforeAll(() => {
  // Mock environment variables for tests
  process.env.NODE_ENV = 'test'
  process.env.VITE_SUPABASE_URL = 'https://test.supabase.co'
  process.env.VITE_SUPABASE_ANON_KEY = 'test-anon-key'
  process.env.ODOO_URL = 'https://test.odoo.com'
  process.env.ODOO_DB = 'test-db'
  process.env.ODOO_USERNAME = 'test-user'
  process.env.ODOO_PASSWORD = 'test-password'
})

// ============================================================================
// Global Mocks
// ============================================================================

// Mock crypto.randomUUID for consistent test results
Object.defineProperty(global, 'crypto', {
  value: {
    randomUUID: vi.fn(() => 'test-uuid-123')
  }
})

// Mock console methods to reduce noise in tests
beforeAll(() => {
  vi.spyOn(console, 'log').mockImplementation(() => {})
  vi.spyOn(console, 'warn').mockImplementation(() => {})
  vi.spyOn(console, 'error').mockImplementation(() => {})
})

// ============================================================================
// Test Database Setup
// ============================================================================

// Mock Supabase client for all tests
vi.mock('@supabase/supabase-js', () => ({
  createClient: vi.fn(() => ({
    from: vi.fn().mockReturnValue({
      select: vi.fn().mockReturnThis(),
      insert: vi.fn().mockReturnThis(),
      update: vi.fn().mockReturnThis(),
      delete: vi.fn().mockReturnThis(),
      eq: vi.fn().mockReturnThis(),
      neq: vi.fn().mockReturnThis(),
      gt: vi.fn().mockReturnThis(),
      gte: vi.fn().mockReturnThis(),
      lt: vi.fn().mockReturnThis(),
      lte: vi.fn().mockReturnThis(),
      like: vi.fn().mockReturnThis(),
      ilike: vi.fn().mockReturnThis(),
      in: vi.fn().mockReturnThis(),
      is: vi.fn().mockReturnThis(),
      order: vi.fn().mockReturnThis(),
      limit: vi.fn().mockReturnThis(),
      range: vi.fn().mockReturnThis(),
      single: vi.fn(),
      maybeSingle: vi.fn()
    }),
    auth: {
      getUser: vi.fn().mockResolvedValue({ data: { user: null }, error: null }),
      signInWithPassword: vi.fn().mockResolvedValue({ data: { user: {} }, error: null }),
      signOut: vi.fn().mockResolvedValue({ error: null })
    }
  }))
}))

// ============================================================================
// Network Mocks
// ============================================================================

// Mock fetch for HTTP requests
global.fetch = vi.fn()

// Reset fetch mock before each test
beforeEach(() => {
  vi.mocked(fetch).mockClear()
})

// ============================================================================
// Timer Mocks
// ============================================================================

// Mock timers for testing time-dependent code
beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

// ============================================================================
// Test Cleanup
// ============================================================================

// Clear all mocks after each test
afterEach(() => {
  vi.clearAllMocks()
  vi.clearAllTimers()
})

// ============================================================================
// Test Utilities
// ============================================================================

/**
 * Wait for a specified number of milliseconds in tests
 */
export const waitFor = (ms: number): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * Advance timers by specified milliseconds
 */
export const advanceTimers = (ms: number): void => {
  vi.advanceTimersByTime(ms)
}

/**
 * Mock implementation helper for promises
 */
export const mockResolvedValue = <T>(value: T): Promise<T> => {
  return Promise.resolve(value)
}

/**
 * Mock implementation helper for rejected promises
 */
export const mockRejectedValue = (error: Error): Promise<never> => {
  return Promise.reject(error)
}

/**
 * Create a mock function with specified implementation
 */
export const mockFunction = <T extends (...args: any[]) => any>(
  implementation?: T
): vi.MockedFunction<T> => {
  return vi.fn(implementation) as vi.MockedFunction<T>
}

/**
 * Create a spy on an object method
 */
export const spyOn = <T, K extends keyof T>(
  object: T,
  method: K
): vi.SpyInstance => {
  return vi.spyOn(object, method)
}

// ============================================================================
// Custom Test Matchers
// ============================================================================

declare global {
  namespace Vi {
    interface JestAssertion<T = any> {
      toBeValidUUID(): T
      toBeWithinRange(floor: number, ceiling: number): T
      toHaveBeenCalledOnceWith(...args: any[]): T
    }
  }
}

// Custom matcher for UUID validation
expect.extend({
  toBeValidUUID(received: string) {
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
    const pass = uuidRegex.test(received)
    
    return {
      pass,
      message: () => 
        pass 
          ? `Expected ${received} not to be a valid UUID`
          : `Expected ${received} to be a valid UUID`
    }
  },
  
  toBeWithinRange(received: number, floor: number, ceiling: number) {
    const pass = received >= floor && received <= ceiling
    
    return {
      pass,
      message: () =>
        pass
          ? `Expected ${received} not to be within range ${floor} - ${ceiling}`
          : `Expected ${received} to be within range ${floor} - ${ceiling}`
    }
  },
  
  toHaveBeenCalledOnceWith(received: vi.MockedFunction<any>, ...args: any[]) {
    const pass = received.mock.calls.length === 1 && 
                  received.mock.calls[0].every((arg, index) => 
                    expect(arg).toEqual(args[index])
                  )
    
    return {
      pass,
      message: () =>
        pass
          ? `Expected function not to have been called once with ${args}`
          : `Expected function to have been called once with ${args}, but was called ${received.mock.calls.length} times`
    }
  }
})

// ============================================================================
// Global Test Constants
// ============================================================================

export const TEST_CONSTANTS = {
  DEFAULT_TIMEOUT: 5000,
  LONG_TIMEOUT: 30000,
  SHORT_TIMEOUT: 1000,
  
  // Test data constants
  TEST_ORDER_ID: 'test-order-123',
  TEST_SUPPLIER_ID: 'test-supplier-456',
  TEST_PRODUCT_ID: 'test-product-789',
  TEST_USER_ID: 'test-user-101',
  
  // Mock dates for consistent testing
  MOCK_DATE_NOW: new Date('2025-08-03T12:00:00Z'),
  MOCK_DATE_PAST: new Date('2025-08-01T10:00:00Z'),
  MOCK_DATE_FUTURE: new Date('2025-08-15T14:00:00Z'),
  
  // Error messages
  NETWORK_ERROR: 'Network request failed',
  VALIDATION_ERROR: 'Validation failed',
  NOT_FOUND_ERROR: 'Resource not found',
  CONFLICT_ERROR: 'Resource conflict detected'
}

// ============================================================================
// Test Performance Monitoring
// ============================================================================

let testStartTime: number
let slowTests: Array<{ name: string; duration: number }> = []

beforeEach(() => {
  testStartTime = Date.now()
})

afterEach((context) => {
  const duration = Date.now() - testStartTime
  
  // Track slow tests (> 1 second)
  if (duration > 1000) {
    slowTests.push({
      name: context?.meta?.name || 'Unknown test',
      duration
    })
  }
})

afterAll(() => {
  // Report slow tests
  if (slowTests.length > 0) {
    console.log('\n⚠️  Slow tests detected:')
    slowTests.forEach(test => {
      console.log(`  - ${test.name}: ${test.duration}ms`)
    })
    console.log('\nConsider optimizing these tests for better performance.\n')
  }
})

// ============================================================================
// Export test setup completion
// ============================================================================

console.log('✅ Test environment setup completed')
console.log(`   Node environment: ${process.env.NODE_ENV}`)
console.log(`   Test timeout: 30000ms`)
console.log(`   Fake timers: enabled`)
console.log(`   Global mocks: enabled`)
console.log(`   Custom matchers: loaded`)
console.log('')