import { describe, it, expect, beforeEach, vi, type Mock } from 'vitest'
import { OdooSyncService } from '../../../src/services/OdooSyncService'
import type {
  IOdooClient,
  IPurchaseOrderRepository,
  ISyncStateManager,
  ICacheService,
  IEventService,
  ILogger,
  PurchaseOrder,
  OdooPurchaseOrder,
  SyncState,
  SyncConflict,
  SyncResult,
  BatchSyncResult,
  ConflictResolution,
  OrderStatus,
  SyncStatus,
  EntityType,
  ConflictType
} from '../../../src/types/odoo-integration'

// Mock implementations
const createMockOdooClient = (): jest.Mocked<IOdooClient> => ({
  create: vi.fn(),
  read: vi.fn(),
  write: vi.fn(),
  unlink: vi.fn(),
  search: vi.fn(),
  searchRead: vi.fn(),
  searchCount: vi.fn(),
  fieldsGet: vi.fn(),
  getConnectionStatus: vi.fn(),
  authenticate: vi.fn(),
  logout: vi.fn()
})

const createMockPurchaseOrderRepository = (): jest.Mocked<IPurchaseOrderRepository> => ({
  findLocalOrder: vi.fn(),
  findLocalOrdersByStatus: vi.fn(),
  createLocalOrder: vi.fn(),
  updateLocalOrder: vi.fn(),
  deleteLocalOrder: vi.fn(),
  findOdooOrder: vi.fn(),
  createOdooOrder: vi.fn(),
  updateOdooOrder: vi.fn(),
  findOdooOrdersModifiedSince: vi.fn(),
  markOrderAsSynced: vi.fn(),
  findOrdersRequiringSync: vi.fn(),
  findSyncMapping: vi.fn(),
  detectConflicts: vi.fn(),
  findConflictingOrders: vi.fn()
})

const createMockSyncStateManager = (): jest.Mocked<ISyncStateManager> => ({
  getSyncState: vi.fn(),
  updateSyncState: vi.fn(),
  clearSyncState: vi.fn(),
  recordConflict: vi.fn(),
  resolveConflict: vi.fn(),
  getPendingConflicts: vi.fn(),
  getConflictHistory: vi.fn(),
  getLastSuccessfulSync: vi.fn(),
  getFailedSyncCount: vi.fn(),
  getSyncMetrics: vi.fn()
})

const createMockCacheService = (): jest.Mocked<ICacheService> => ({
  get: vi.fn(),
  set: vi.fn(),
  delete: vi.fn(),
  exists: vi.fn(),
  getBatch: vi.fn(),
  setBatch: vi.fn(),
  deleteBatch: vi.fn(),
  invalidatePattern: vi.fn(),
  invalidateTag: vi.fn(),
  getStats: vi.fn(),
  warmupCache: vi.fn(),
  getCacheHitRatio: vi.fn()
})

const createMockEventService = (): jest.Mocked<IEventService> => ({
  publish: vi.fn(),
  publishBatch: vi.fn(),
  subscribe: vi.fn(),
  unsubscribe: vi.fn(),
  getEventHistory: vi.fn(),
  replayEvents: vi.fn()
})

const createMockLogger = (): jest.Mocked<ILogger> => ({
  debug: vi.fn(),
  info: vi.fn(),
  warn: vi.fn(),
  error: vi.fn()
})

// Test data factories
const createTestPurchaseOrder = (overrides?: Partial<PurchaseOrder>): PurchaseOrder => ({
  id: 'order-123',
  orderNumber: 'PO-2025-001',
  supplierId: 'supplier-456',
  supplierName: 'Test Supplier',
  status: OrderStatus.DRAFT,
  items: [
    {
      id: 'item-1',
      productId: 'product-1',
      productName: 'Test Product 1',
      productCode: 'TP001',
      quantity: 10,
      unitPrice: 25.50,
      totalPrice: 255.00,
      notes: 'Test item 1'
    }
  ],
  subtotal: 255.00,
  taxAmount: 25.50,
  totalAmount: 280.50,
  notes: 'Test order notes',
  requestedDeliveryDate: new Date('2025-08-15'),
  createdAt: new Date('2025-08-03'),
  updatedAt: new Date('2025-08-03'),
  syncStatus: SyncStatus.NOT_SYNCED,
  ...overrides
})

const createTestOdooPurchaseOrder = (overrides?: Partial<OdooPurchaseOrder>): OdooPurchaseOrder => ({
  id: 123,
  name: 'PO00001',
  partner_id: [456, 'Test Supplier'],
  date_order: '2025-08-03 00:00:00',
  state: 'draft',
  amount_total: 280.50,
  amount_untaxed: 255.00,
  amount_tax: 25.50,
  order_line: [],
  notes: 'Test order notes',
  create_date: '2025-08-03 00:00:00',
  write_date: '2025-08-03 00:00:00',
  ...overrides
})

const createTestSyncState = (overrides?: Partial<SyncState>): SyncState => ({
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

describe('OdooSyncService', () => {
  let service: OdooSyncService
  let mockOdooClient: jest.Mocked<IOdooClient>
  let mockRepository: jest.Mocked<IPurchaseOrderRepository>
  let mockSyncStateManager: jest.Mocked<ISyncStateManager>
  let mockCacheService: jest.Mocked<ICacheService>
  let mockEventService: jest.Mocked<IEventService>
  let mockLogger: jest.Mocked<ILogger>

  beforeEach(() => {
    mockOdooClient = createMockOdooClient()
    mockRepository = createMockPurchaseOrderRepository()
    mockSyncStateManager = createMockSyncStateManager()
    mockCacheService = createMockCacheService()
    mockEventService = createMockEventService()
    mockLogger = createMockLogger()

    service = new OdooSyncService(
      mockOdooClient,
      mockRepository,
      mockSyncStateManager,
      mockCacheService,
      mockEventService,
      mockLogger
    )
  })

  describe('syncOrderToOdoo', () => {
    it('should successfully sync a new order to Odoo', async () => {
      // Arrange 
      const localOrder = createTestPurchaseOrder()
      const expectedOdooId = 123
      const syncState = createTestSyncState({ entityId: localOrder.id })

      mockRepository.findLocalOrder.mockResolvedValue(localOrder)
      mockSyncStateManager.getSyncState.mockResolvedValue(syncState)
      mockRepository.findSyncMapping.mockResolvedValue(null)
      mockRepository.createOdooOrder.mockResolvedValue(expectedOdooId)
      mockRepository.markOrderAsSynced.mockResolvedValue()
      mockSyncStateManager.updateSyncState.mockResolvedValue()
      mockEventService.publish.mockResolvedValue()

      // Act
      const result = await service.syncOrderToOdoo(localOrder.id)

      // Assert
      expect(result).toMatchObject({
        success: true,
        localOrderId: localOrder.id,
        odooOrderId: expectedOdooId,
        operation: 'CREATE',
        timestamp: expect.any(Date),
        duration: expect.any(Number)
      })

      expect(mockRepository.createOdooOrder).toHaveBeenCalledWith(
        expect.objectContaining({
          partner_id: localOrder.supplierId,
          date_order: localOrder.createdAt.toISOString()
        })
      )
      expect(mockRepository.markOrderAsSynced).toHaveBeenCalledWith(
        localOrder.id,
        expectedOdooId,
        expect.any(Date)
      )
      expect(mockSyncStateManager.updateSyncState).toHaveBeenCalledWith(
        localOrder.id,
        EntityType.PURCHASE_ORDER,
        expect.objectContaining({
          status: SyncStatus.SYNCED,
          lastSuccessfulSync: expect.any(Date)
        })
      )
    })

    it('should update existing order when sync mapping exists', async () => {
      // Arrange
      const localOrder = createTestPurchaseOrder({
        syncStatus: SyncStatus.SYNCED,
        odooOrderId: 123
      })
      const odooOrder = createTestOdooPurchaseOrder({ id: 123 })
      const syncMapping = {
        localOrderId: localOrder.id,
        odooOrderId: 123,
        lastSyncedAt: new Date('2025-08-01')
      }

      mockRepository.findLocalOrder.mockResolvedValue(localOrder)
      mockRepository.findSyncMapping.mockResolvedValue(syncMapping)
      mockRepository.findOdooOrder.mockResolvedValue(odooOrder)
      mockRepository.detectConflicts.mockResolvedValue({
        hasConflicts: false,
        conflicts: [],
        warnings: []
      })
      mockRepository.updateOdooOrder.mockResolvedValue()
      mockSyncStateManager.updateSyncState.mockResolvedValue()

      // Act
      const result = await service.syncOrderToOdoo(localOrder.id)

      // Assert
      expect(result).toMatchObject({
        success: true,
        localOrderId: localOrder.id,
        odooOrderId: 123,
        operation: 'UPDATE'
      })

      expect(mockRepository.detectConflicts).toHaveBeenCalledWith(localOrder, odooOrder)
      expect(mockRepository.updateOdooOrder).toHaveBeenCalledWith(123, expect.any(Object))
    })

    it('should handle conflicts and record them for manual resolution', async () => {
      // Arrange
      const localOrder = createTestPurchaseOrder({
        syncStatus: SyncStatus.SYNCED,
        odooOrderId: 123,
        totalAmount: 280.50
      })
      const conflictingOdooOrder = createTestOdooPurchaseOrder({
        id: 123,
        amount_total: 500.00 // Different total
      })
      const conflicts = {
        hasConflicts: true,
        conflicts: [{
          field: 'totalAmount',
          localValue: 280.50,
          remoteValue: 500.00,
          type: ConflictType.DATA_MISMATCH
        }],
        warnings: ['Total amount mismatch detected']
      }

      mockRepository.findLocalOrder.mockResolvedValue(localOrder)
      mockRepository.findSyncMapping.mockResolvedValue({
        localOrderId: localOrder.id,
        odooOrderId: 123,
        lastSyncedAt: new Date()
      })
      mockRepository.findOdooOrder.mockResolvedValue(conflictingOdooOrder)
      mockRepository.detectConflicts.mockResolvedValue(conflicts)
      mockSyncStateManager.recordConflict.mockResolvedValue()
      mockSyncStateManager.updateSyncState.mockResolvedValue()

      // Act
      const result = await service.syncOrderToOdoo(localOrder.id)

      // Assert
      expect(result).toMatchObject({
        success: false,
        localOrderId: localOrder.id,
        odooOrderId: 123,
        operation: 'UPDATE',
        error: expect.objectContaining({
          message: expect.stringContaining('Conflict detected'),
          type: 'ConflictError'
        }),
        warnings: conflicts.warnings
      })

      expect(mockSyncStateManager.recordConflict).toHaveBeenCalledWith(
        expect.objectContaining({
          entityId: localOrder.id,
          entityType: EntityType.PURCHASE_ORDER,
          conflictType: ConflictType.CONCURRENT_MODIFICATION,
          localVersion: localOrder,
          remoteVersion: conflictingOdooOrder
        })
      )
      expect(mockSyncStateManager.updateSyncState).toHaveBeenCalledWith(
        localOrder.id,
        EntityType.PURCHASE_ORDER,
        expect.objectContaining({
          status: SyncStatus.CONFLICT
        })
      )
    })

    it('should handle network errors and update sync state', async () => {
      // Arrange
      const localOrder = createTestPurchaseOrder()
      const networkError = new Error('Connection timeout')

      mockRepository.findLocalOrder.mockResolvedValue(localOrder)
      mockSyncStateManager.getSyncState.mockResolvedValue(createTestSyncState())
      mockRepository.findSyncMapping.mockResolvedValue(null)
      mockRepository.createOdooOrder.mockRejectedValue(networkError)
      mockSyncStateManager.updateSyncState.mockResolvedValue()

      // Act
      const result = await service.syncOrderToOdoo(localOrder.id)

      // Assert
      expect(result).toMatchObject({
        success: false,
        localOrderId: localOrder.id,
        operation: 'CREATE',
        error: expect.objectContaining({
          message: 'Connection timeout',
          type: 'Error'
        })
      })

      expect(mockSyncStateManager.updateSyncState).toHaveBeenCalledWith(
        localOrder.id,
        EntityType.PURCHASE_ORDER,
        expect.objectContaining({
          status: SyncStatus.SYNC_FAILED,
          failureCount: 1,
          lastError: expect.objectContaining({
            message: 'Connection timeout'
          })
        })
      )
    })

    it('should throw error when local order not found', async () => {
      // Arrange
      const orderId = 'non-existent-order'
      mockRepository.findLocalOrder.mockResolvedValue(null)

      // Act & Assert
      await expect(service.syncOrderToOdoo(orderId))
        .rejects
        .toThrow(`Local order ${orderId} not found`)
    })
  })

  describe('syncOrderFromOdoo', () => {
    it('should successfully sync order from Odoo to local database', async () => {
      // Arrange
      const odooOrderId = 123
      const odooOrder = createTestOdooPurchaseOrder({ id: odooOrderId })
      const localOrder = createTestPurchaseOrder({
        id: 'order-123',
        syncStatus: SyncStatus.SYNCED,
        odooOrderId
      })

      mockRepository.findOdooOrder.mockResolvedValue(odooOrder)
      mockRepository.findSyncMapping.mockResolvedValue({
        localOrderId: 'order-123',
        odooOrderId,
        lastSyncedAt: new Date('2025-08-01')
      })
      mockRepository.findLocalOrder.mockResolvedValue(localOrder)
      mockRepository.detectConflicts.mockResolvedValue({
        hasConflicts: false,
        conflicts: [],
        warnings: []
      })
      mockRepository.updateLocalOrder.mockResolvedValue(localOrder)
      mockSyncStateManager.updateSyncState.mockResolvedValue()

      // Act
      const result = await service.syncOrderFromOdoo(odooOrderId)

      // Assert
      expect(result).toMatchObject({
        success: true,
        localOrderId: 'order-123',
        odooOrderId,
        operation: 'UPDATE'
      })

      expect(mockRepository.updateLocalOrder).toHaveBeenCalledWith(
        'order-123',
        expect.objectContaining({
          status: expect.any(String),
          totalAmount: odooOrder.amount_total
        })
      )
    })

    it('should create new local order when no sync mapping exists', async () => {
      // Arrange
      const odooOrderId = 123
      const odooOrder = createTestOdooPurchaseOrder({ id: odooOrderId })
      const newLocalOrder = createTestPurchaseOrder({
        id: 'new-order-456',
        syncStatus: SyncStatus.SYNCED,
        odooOrderId
      })

      mockRepository.findOdooOrder.mockResolvedValue(odooOrder)
      mockRepository.findSyncMapping.mockResolvedValue(null)
      mockRepository.createLocalOrder.mockResolvedValue(newLocalOrder)
      mockRepository.markOrderAsSynced.mockResolvedValue()
      mockSyncStateManager.updateSyncState.mockResolvedValue()

      // Act
      const result = await service.syncOrderFromOdoo(odooOrderId)

      // Assert
      expect(result).toMatchObject({
        success: true,
        localOrderId: newLocalOrder.id,
        odooOrderId,
        operation: 'CREATE'
      })

      expect(mockRepository.createLocalOrder).toHaveBeenCalledWith(
        expect.objectContaining({
          supplierId: odooOrder.partner_id[0].toString(),
          supplierName: odooOrder.partner_id[1],
          totalAmount: odooOrder.amount_total,
          syncStatus: SyncStatus.SYNCED,
          odooOrderId
        })
      )
    })

    it('should throw error when Odoo order not found', async () => {
      // Arrange
      const odooOrderId = 999
      mockRepository.findOdooOrder.mockResolvedValue(null)

      // Act & Assert
      await expect(service.syncOrderFromOdoo(odooOrderId))
        .rejects
        .toThrow(`Odoo order ${odooOrderId} not found`)
    })
  })

  describe('batchSyncPendingOrders', () => {
    it('should process multiple pending orders successfully', async () => {
      // Arrange
      const pendingOrders = [
        createTestPurchaseOrder({ id: 'order-1' }),
        createTestPurchaseOrder({ id: 'order-2' }),
        createTestPurchaseOrder({ id: 'order-3' })
      ]

      mockRepository.findOrdersRequiringSync.mockResolvedValue(pendingOrders)
      
      // Mock successful sync for all orders
      pendingOrders.forEach((order, index) => {
        mockRepository.findLocalOrder.mockResolvedValueOnce(order)
        mockSyncStateManager.getSyncState.mockResolvedValueOnce(createTestSyncState({ entityId: order.id }))
        mockRepository.findSyncMapping.mockResolvedValueOnce(null)
        mockRepository.createOdooOrder.mockResolvedValueOnce(100 + index + 1)
        mockRepository.markOrderAsSynced.mockResolvedValueOnce()
        mockSyncStateManager.updateSyncState.mockResolvedValueOnce()
        mockEventService.publish.mockResolvedValueOnce()
      })

      // Act
      const result = await service.batchSyncPendingOrders(10)

      // Assert
      expect(result).toMatchObject({
        totalProcessed: 3,
        successful: 3,
        failed: 0,
        skipped: 0,
        duration: expect.any(Number)
      })

      expect(result.results).toHaveLength(3)
      expect(result.results.every(r => r.success)).toBe(true)
      expect(mockRepository.createOdooOrder).toHaveBeenCalledTimes(3)
    })

    it('should handle partial failures in batch processing', async () => {
      // Arrange
      const pendingOrders = [
        createTestPurchaseOrder({ id: 'order-success' }),
        createTestPurchaseOrder({ id: 'order-failure' })
      ]

      mockRepository.findOrdersRequiringSync.mockResolvedValue(pendingOrders)
      
      // First order succeeds
      mockRepository.findLocalOrder.mockResolvedValueOnce(pendingOrders[0])
      mockSyncStateManager.getSyncState.mockResolvedValueOnce(createTestSyncState())
      mockRepository.findSyncMapping.mockResolvedValueOnce(null)
      mockRepository.createOdooOrder.mockResolvedValueOnce(101)
      
      // Second order fails
      mockRepository.findLocalOrder.mockResolvedValueOnce(pendingOrders[1])
      mockSyncStateManager.getSyncState.mockResolvedValueOnce(createTestSyncState())
      mockRepository.findSyncMapping.mockResolvedValueOnce(null)
      mockRepository.createOdooOrder.mockRejectedValueOnce(new Error('Network error'))

      // Act
      const result = await service.batchSyncPendingOrders()

      // Assert
      expect(result).toMatchObject({
        totalProcessed: 2,
        successful: 1,
        failed: 1,
        skipped: 0
      })

      expect(result.results[0]).toMatchObject({ success: true })
      expect(result.results[1]).toMatchObject({ success: false })
    })

    it('should respect batch size limit', async () => {
      // Arrange
      const pendingOrders = Array.from({ length: 50 }, (_, i) => 
        createTestPurchaseOrder({ id: `order-${i + 1}` })
      )
      const batchSize = 10

      mockRepository.findOrdersRequiringSync.mockResolvedValue(pendingOrders.slice(0, batchSize))

      // Act
      const result = await service.batchSyncPendingOrders(batchSize)

      // Assert
      expect(result.totalProcessed).toBe(batchSize)
      expect(mockRepository.findOrdersRequiringSync).toHaveBeenCalledWith(batchSize)
    })
  })

  describe('resolveConflict', () => {
    it('should resolve conflict by accepting local version', async () => {
      // Arrange
      const conflictId = 'conflict-123'
      const conflict: SyncConflict = {
        id: conflictId,
        entityId: 'order-123',
        entityType: EntityType.PURCHASE_ORDER,
        conflictType: ConflictType.DATA_MISMATCH,
        localVersion: createTestPurchaseOrder({ totalAmount: 280.50 }),
        remoteVersion: createTestOdooPurchaseOrder({ amount_total: 500.00 }),
        detectedAt: new Date()
      }
      const resolution: ConflictResolution = {
        strategy: 'ACCEPT_LOCAL',
        resolvedBy: 'user-123',
        notes: 'Local version is more accurate'
      }

      mockSyncStateManager.resolveConflict.mockResolvedValue()
      mockRepository.updateOdooOrder.mockResolvedValue()
      mockSyncStateManager.updateSyncState.mockResolvedValue()
      mockEventService.publish.mockResolvedValue()

      // Act
      await service.resolveConflict(conflictId, conflict, resolution)

      // Assert
      expect(mockSyncStateManager.resolveConflict).toHaveBeenCalledWith(conflictId, resolution)
      expect(mockRepository.updateOdooOrder).toHaveBeenCalledWith(
        (conflict.remoteVersion as OdooPurchaseOrder).id,
        expect.objectContaining({
          amount_total: (conflict.localVersion as PurchaseOrder).totalAmount
        })
      )
      expect(mockSyncStateManager.updateSyncState).toHaveBeenCalledWith(
        conflict.entityId,
        EntityType.PURCHASE_ORDER,
        expect.objectContaining({
          status: SyncStatus.SYNCED
        })
      )
    })

    it('should resolve conflict by accepting remote version', async () => {
      // Arrange
      const conflictId = 'conflict-123'
      const conflict: SyncConflict = {
        id: conflictId,
        entityId: 'order-123',
        entityType: EntityType.PURCHASE_ORDER,
        conflictType: ConflictType.DATA_MISMATCH,
        localVersion: createTestPurchaseOrder({ totalAmount: 280.50 }),
        remoteVersion: createTestOdooPurchaseOrder({ amount_total: 500.00 }),
        detectedAt: new Date()
      }
      const resolution: ConflictResolution = {
        strategy: 'ACCEPT_REMOTE',
        resolvedBy: 'user-123',
        notes: 'Remote version has latest pricing'
      }

      mockSyncStateManager.resolveConflict.mockResolvedValue()
      mockRepository.updateLocalOrder.mockResolvedValue(
        createTestPurchaseOrder({ totalAmount: 500.00 })
      )
      mockSyncStateManager.updateSyncState.mockResolvedValue()
      mockEventService.publish.mockResolvedValue()

      // Act
      await service.resolveConflict(conflictId, conflict, resolution)

      // Assert
      expect(mockRepository.updateLocalOrder).toHaveBeenCalledWith(
        conflict.entityId,
        expect.objectContaining({
          totalAmount: (conflict.remoteVersion as OdooPurchaseOrder).amount_total
        })
      )
    })
  })

  describe('getPendingConflicts', () => {
    it('should retrieve all pending conflicts', async () => {
      // Arrange
      const pendingConflicts: SyncConflict[] = [
        {
          id: 'conflict-1',
          entityId: 'order-1',
          entityType: EntityType.PURCHASE_ORDER,
          conflictType: ConflictType.DATA_MISMATCH,
          localVersion: createTestPurchaseOrder(),
          remoteVersion: createTestOdooPurchaseOrder(),
          detectedAt: new Date()
        },
        {
          id: 'conflict-2',
          entityId: 'order-2',
          entityType: EntityType.PURCHASE_ORDER,
          conflictType: ConflictType.VERSION_CONFLICT,
          localVersion: createTestPurchaseOrder(),
          remoteVersion: createTestOdooPurchaseOrder(),
          detectedAt: new Date()
        }
      ]

      mockSyncStateManager.getPendingConflicts.mockResolvedValue(pendingConflicts)

      // Act
      const result = await service.getPendingConflicts()

      // Assert
      expect(result).toEqual(pendingConflicts)
      expect(result).toHaveLength(2)
      expect(mockSyncStateManager.getPendingConflicts).toHaveBeenCalledWith(EntityType.PURCHASE_ORDER)
    })

    it('should return empty array when no conflicts exist', async () => {
      // Arrange
      mockSyncStateManager.getPendingConflicts.mockResolvedValue([])

      // Act
      const result = await service.getPendingConflicts()

      // Assert
      expect(result).toEqual([])
      expect(result).toHaveLength(0)
    })
  })

  describe('getSyncMetrics', () => {
    it('should return comprehensive sync metrics', async () => {
      // Arrange
      const mockMetrics = {
        totalSyncs: 100,
        successfulSyncs: 85,
        failedSyncs: 10,
        conflictingSyncs: 5,
        successRate: 0.85,
        averageSyncDuration: 2500,
        lastSyncTimestamp: new Date(),
        syncsByStatus: {
          [SyncStatus.SYNCED]: 85,
          [SyncStatus.SYNC_FAILED]: 10,
          [SyncStatus.CONFLICT]: 5
        }
      }

      mockSyncStateManager.getSyncMetrics.mockResolvedValue(mockMetrics)

      // Act
      const result = await service.getSyncMetrics()

      // Assert
      expect(result).toEqual(mockMetrics)
      expect(result.successRate).toBe(0.85)
      expect(result.totalSyncs).toBe(100)
    })
  })

  describe('Error handling and resilience', () => {
    it('should implement circuit breaker pattern for persistent failures', async () => {
      // Arrange
      const localOrder = createTestPurchaseOrder()
      const persistentError = new Error('Service unavailable')
      
      // Mock repeated failures
      mockRepository.findLocalOrder.mockResolvedValue(localOrder)
      mockSyncStateManager.getSyncState.mockResolvedValue(createTestSyncState())
      mockRepository.findSyncMapping.mockResolvedValue(null)
      mockRepository.createOdooOrder.mockRejectedValue(persistentError)

      // Act - Multiple attempts should trigger circuit breaker
      const results = await Promise.all([
        service.syncOrderToOdoo(localOrder.id).catch(e => ({ error: e.message })),
        service.syncOrderToOdoo(localOrder.id).catch(e => ({ error: e.message })),
        service.syncOrderToOdoo(localOrder.id).catch(e => ({ error: e.message }))
      ])

      // Assert
      expect(results.every(r => 'error' in r)).toBe(true)
      expect(mockLogger.error).toHaveBeenCalledWith(
        expect.stringContaining('Circuit breaker'),
        expect.any(Object)
      )
    })

    it('should implement retry logic with exponential backoff', async () => {
      // Arrange
      const localOrder = createTestPurchaseOrder()
      const transientError = new Error('Temporary network error')
      
      mockRepository.findLocalOrder.mockResolvedValue(localOrder)
      mockSyncStateManager.getSyncState.mockResolvedValue(createTestSyncState())
      mockRepository.findSyncMapping.mockResolvedValue(null)
      
      // Fail twice, then succeed
      mockRepository.createOdooOrder
        .mockRejectedValueOnce(transientError)
        .mockRejectedValueOnce(transientError)
        .mockResolvedValue(123)

      // Act
      const result = await service.syncOrderToOdoo(localOrder.id)

      // Assert
      expect(result.success).toBe(true)
      expect(mockRepository.createOdooOrder).toHaveBeenCalledTimes(3)
      expect(mockLogger.warn).toHaveBeenCalledWith(
        expect.stringContaining('Retrying sync operation'),
        expect.any(Object)
      )
    })
  })
})