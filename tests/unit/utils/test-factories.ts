/**
 * Test Data Factories
 * 
 * This file contains factory functions for creating test data objects
 * used across unit tests. Following TDD best practices, these factories
 * provide consistent, valid test data while allowing for easy customization.
 */

import type {
  PurchaseOrder,
  OdooPurchaseOrder,
  OrderItem,
  CreatePurchaseOrderRequest,
  CreateOdooOrderRequest,
  UpdateOdooOrderRequest,
  OrderSyncMapping,
  SyncState,
  SyncConflict,
  SyncResult,
  BatchSyncResult,
  IntegrationHealthStatus,
  OrderStatus,
  SyncStatus,
  EntityType,
  ConflictType,
  ConflictResolution
} from '../../../src/types/odoo-integration'

/**
 * Creates a test OrderItem with sensible defaults
 */
export const createTestOrderItem = (overrides?: Partial<OrderItem>): OrderItem => ({
  id: 'item-1',
  productId: 'product-1',
  productName: 'Test Product',
  productCode: 'TP001',
  quantity: 10,
  unitPrice: 25.50,
  totalPrice: 255.00,
  notes: 'Test item notes',
  ...overrides
})

/**
 * Creates a test PurchaseOrder with sensible defaults
 */
export const createTestPurchaseOrder = (overrides?: Partial<PurchaseOrder>): PurchaseOrder => ({
  id: 'order-123',
  orderNumber: 'PO-2025-001',
  supplierId: 'supplier-456',
  supplierName: 'Test Supplier',
  status: OrderStatus.DRAFT,
  items: [createTestOrderItem()],
  subtotal: 255.00,
  taxAmount: 25.50,
  totalAmount: 280.50,
  notes: 'Test order notes',
  requestedDeliveryDate: new Date('2025-08-15'),
  approvedBy: undefined,
  approvedAt: undefined,
  createdAt: new Date('2025-08-03'),
  updatedAt: new Date('2025-08-03'),
  syncStatus: SyncStatus.NOT_SYNCED,
  odooOrderId: undefined,
  lastSyncedAt: undefined,
  ...overrides
})

/**
 * Creates a test OdooPurchaseOrder with sensible defaults
 */
export const createTestOdooPurchaseOrder = (overrides?: Partial<OdooPurchaseOrder>): OdooPurchaseOrder => ({
  id: 123,
  name: 'PO00001',
  partner_id: [456, 'Test Supplier'],
  date_order: '2025-08-03 00:00:00',
  state: 'draft',
  amount_total: 280.50,
  amount_untaxed: 255.00,
  amount_tax: 25.50,
  order_line: [
    [1, 'product-1', {
      product_id: [1, 'Test Product'],
      product_qty: 10,
      price_unit: 25.50,
      price_subtotal: 255.00,
      name: 'Test Product'
    }]
  ],
  notes: 'Test order notes',
  create_date: '2025-08-03 00:00:00',
  write_date: '2025-08-03 00:00:00',
  ...overrides
})

/**
 * Creates a test CreatePurchaseOrderRequest
 */
export const createTestCreatePurchaseOrderRequest = (
  overrides?: Partial<CreatePurchaseOrderRequest>
): CreatePurchaseOrderRequest => ({
  orderNumber: 'PO-2025-002',
  supplierId: 'supplier-789',
  supplierName: 'New Test Supplier',
  items: [
    {
      productId: 'product-1',
      productName: 'New Product',
      productCode: 'NP001',
      quantity: 5,
      unitPrice: 30.00,
      notes: 'New item notes'
    }
  ],
  notes: 'New order notes',
  requestedDeliveryDate: new Date('2025-08-20'),
  ...overrides
})

/**
 * Creates a test CreateOdooOrderRequest
 */
export const createTestCreateOdooOrderRequest = (
  overrides?: Partial<CreateOdooOrderRequest>
): CreateOdooOrderRequest => ({
  partner_id: 'supplier-456',
  date_order: '2025-08-03T00:00:00Z',
  order_line: [
    {
      product_id: 'product-1',
      product_qty: 10,
      price_unit: 25.50,
      name: 'Test Product'
    }
  ],
  notes: 'Test order notes',
  ...overrides
})

/**
 * Creates a test UpdateOdooOrderRequest
 */
export const createTestUpdateOdooOrderRequest = (
  overrides?: Partial<UpdateOdooOrderRequest>
): UpdateOdooOrderRequest => ({
  order_line: [
    {
      product_id: 'product-1',
      product_qty: 15, // Updated quantity
      price_unit: 25.50,
      name: 'Updated Product Name'
    }
  ],
  notes: 'Updated order notes',
  ...overrides
})

/**
 * Creates a test OrderSyncMapping
 */
export const createTestOrderSyncMapping = (
  overrides?: Partial<OrderSyncMapping>
): OrderSyncMapping => ({
  localOrderId: 'order-123',
  odooOrderId: 123,
  lastSyncedAt: new Date('2025-08-03T10:00:00Z'),
  ...overrides
})

/**
 * Creates a test SyncState
 */
export const createTestSyncState = (overrides?: Partial<SyncState>): SyncState => ({
  entityId: 'order-123',
  entityType: EntityType.PURCHASE_ORDER,
  status: SyncStatus.NOT_SYNCED,
  lastSyncAttempt: undefined,
  lastSuccessfulSync: undefined,
  failureCount: 0,
  lastError: undefined,
  version: 1,
  ...overrides
})

/**
 * Creates a test SyncConflict
 */
export const createTestSyncConflict = (overrides?: Partial<SyncConflict>): SyncConflict => ({
  id: 'conflict-123',
  entityId: 'order-123',
  entityType: EntityType.PURCHASE_ORDER,
  conflictType: ConflictType.DATA_MISMATCH,
  localVersion: createTestPurchaseOrder(),
  remoteVersion: createTestOdooPurchaseOrder(),
  detectedAt: new Date('2025-08-03T12:00:00Z'),
  resolvedAt: undefined,
  resolution: undefined,
  ...overrides
})

/**
 * Creates a test ConflictResolution
 */
export const createTestConflictResolution = (
  overrides?: Partial<ConflictResolution>
): ConflictResolution => ({
  strategy: 'ACCEPT_LOCAL',
  resolvedBy: 'user-123',
  resolvedAt: new Date(),
  notes: 'Resolved in favor of local version',
  ...overrides
})

/**
 * Creates a test SyncResult
 */
export const createTestSyncResult = (overrides?: Partial<SyncResult>): SyncResult => ({
  success: true,
  localOrderId: 'order-123',
  odooOrderId: 123,
  operation: 'CREATE',
  timestamp: new Date(),
  duration: 1500,
  error: undefined,
  warnings: [],
  ...overrides
})

/**
 * Creates a test BatchSyncResult
 */
export const createTestBatchSyncResult = (overrides?: Partial<BatchSyncResult>): BatchSyncResult => ({
  totalProcessed: 5,
  successful: 4,
  failed: 1,
  skipped: 0,
  results: [
    createTestSyncResult({ localOrderId: 'order-1', success: true }),
    createTestSyncResult({ localOrderId: 'order-2', success: true }),
    createTestSyncResult({ localOrderId: 'order-3', success: true }),
    createTestSyncResult({ localOrderId: 'order-4', success: true }),
    createTestSyncResult({ 
      localOrderId: 'order-5', 
      success: false,
      error: {
        message: 'Network timeout',
        type: 'NetworkError',
        timestamp: new Date()
      }
    })
  ],
  duration: 12000,
  nextBatchToken: undefined,
  ...overrides
})

/**
 * Creates a test IntegrationHealthStatus
 */
export const createTestIntegrationHealthStatus = (
  overrides?: Partial<IntegrationHealthStatus>
): IntegrationHealthStatus => ({
  isHealthy: true,
  lastSuccessfulSync: new Date('2025-08-03T10:00:00Z'),
  consecutiveFailures: 0,
  odooConnectionStatus: 'CONNECTED',
  cacheStatus: 'HEALTHY',
  queueStatus: 'HEALTHY',
  errorRate: 0.05, // 5% error rate
  ...overrides
})

/**
 * Creates a test Supabase order data object (database format)
 */
export const createTestSupabaseOrderData = (overrides?: any) => ({
  id: 'order-123',
  order_number: 'PO-2025-001',
  supplier_id: 'supplier-456',
  supplier_name: 'Test Supplier',
  status: 'draft',
  subtotal: '255.00',
  sales_tax: '25.50',
  grand_total: '280.50',
  notes: 'Test order notes',
  requested_delivery_date: '2025-08-15T00:00:00Z',
  approved_by: null,
  approved_at: null,
  created_at: '2025-08-03T00:00:00Z',
  updated_at: '2025-08-03T00:00:00Z',
  sync_status: 'not_synced',
  odoo_order_id: null,
  last_synced_at: null,
  order_items: [
    {
      id: 'item-1',
      product_id: 'product-1',
      product_name: 'Test Product',
      product_code: 'TP001',
      quantity: 10,
      unit_price: '25.50',
      total_price: '255.00',
      notes: 'Test item notes'
    }
  ],
  ...overrides
})

/**
 * Creates multiple test orders for batch testing
 */
export const createTestOrderBatch = (count: number, overrides?: Partial<PurchaseOrder>): PurchaseOrder[] => {
  return Array.from({ length: count }, (_, index) => 
    createTestPurchaseOrder({
      id: `order-${index + 1}`,
      orderNumber: `PO-2025-${(index + 1).toString().padStart(3, '0')}`,
      ...overrides
    })
  )
}

/**
 * Creates test error objects
 */
export const createTestError = (message: string, type: string = 'Error') => ({
  message,
  type,
  timestamp: new Date()
})

/**
 * Creates test cache statistics
 */
export const createTestCacheStats = () => ({
  hitCount: 850,
  missCount: 150,
  hitRatio: 0.85,
  totalSize: 1024,
  evictionCount: 25
})

/**
 * Helper function to create mock promises for testing async operations
 */
export const createMockPromise = <T>(value: T, delay: number = 0): Promise<T> => {
  return new Promise((resolve) => {
    setTimeout(() => resolve(value), delay)
  })
}

/**
 * Helper function to create mock rejected promises for error testing
 */
export const createMockRejectedPromise = (error: Error, delay: number = 0): Promise<never> => {
  return new Promise((_, reject) => {
    setTimeout(() => reject(error), delay)
  })
}

/**
 * Test data sets for comprehensive testing scenarios
 */
export const TestDataSets = {
  /**
   * Orders with different statuses for status-based testing
   */
  ordersByStatus: {
    draft: createTestPurchaseOrder({ status: OrderStatus.DRAFT }),
    pendingApproval: createTestPurchaseOrder({ 
      status: OrderStatus.PENDING_APPROVAL,
      id: 'order-pending'
    }),
    approved: createTestPurchaseOrder({ 
      status: OrderStatus.APPROVED,
      id: 'order-approved',
      approvedBy: 'user-123',
      approvedAt: new Date()
    }),
    sent: createTestPurchaseOrder({ 
      status: OrderStatus.SENT_TO_SUPPLIER,
      id: 'order-sent'
    }),
    confirmed: createTestPurchaseOrder({ 
      status: OrderStatus.CONFIRMED,
      id: 'order-confirmed'
    }),
    received: createTestPurchaseOrder({ 
      status: OrderStatus.RECEIVED,
      id: 'order-received'
    }),
    cancelled: createTestPurchaseOrder({ 
      status: OrderStatus.CANCELLED,
      id: 'order-cancelled'
    })
  },

  /**
   * Orders with different sync statuses for sync testing
   */
  ordersBySyncStatus: {
    notSynced: createTestPurchaseOrder({ syncStatus: SyncStatus.NOT_SYNCED }),
    pendingSync: createTestPurchaseOrder({ 
      syncStatus: SyncStatus.PENDING_SYNC,
      id: 'order-pending-sync'
    }),
    synced: createTestPurchaseOrder({ 
      syncStatus: SyncStatus.SYNCED,
      id: 'order-synced',
      odooOrderId: 123,
      lastSyncedAt: new Date()
    }),
    syncFailed: createTestPurchaseOrder({ 
      syncStatus: SyncStatus.SYNC_FAILED,
      id: 'order-sync-failed'
    }),
    conflict: createTestPurchaseOrder({ 
      syncStatus: SyncStatus.CONFLICT,
      id: 'order-conflict',
      odooOrderId: 456
    })
  },

  /**
   * Complex orders for edge case testing
   */
  complexOrders: {
    multipleItems: createTestPurchaseOrder({
      items: [
        createTestOrderItem({ id: 'item-1', productName: 'Product A', quantity: 10, unitPrice: 25.50 }),
        createTestOrderItem({ id: 'item-2', productName: 'Product B', quantity: 5, unitPrice: 45.00 }),
        createTestOrderItem({ id: 'item-3', productName: 'Product C', quantity: 15, unitPrice: 12.75 })
      ]
    }),
    
    highValue: createTestPurchaseOrder({
      items: [
        createTestOrderItem({ quantity: 100, unitPrice: 1000.00, totalPrice: 100000.00 })
      ],
      subtotal: 100000.00,
      taxAmount: 10000.00,
      totalAmount: 110000.00
    }),
    
    zeroValue: createTestPurchaseOrder({
      items: [
        createTestOrderItem({ quantity: 1, unitPrice: 0.00, totalPrice: 0.00 })
      ],
      subtotal: 0.00,
      taxAmount: 0.00,
      totalAmount: 0.00
    })
  }
}