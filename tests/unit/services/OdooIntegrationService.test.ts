import { describe, it, expect, beforeEach, vi, type Mock } from 'vitest'
import { OdooIntegrationService } from '../../../src/services/OdooIntegrationService'
import type { 
  IPurchaseOrderRepository,
  ISyncStateManager,
  ICacheService,
  IEventService,
  IConflictResolver,
  ILogger,
  PurchaseOrder,
  SyncResult,
  BatchSyncResult,
  IntegrationHealthStatus,
  OrderStatus,
  SyncStatus,
  EntityType,
  ConflictType
} from '../../../src/types/odoo-integration'

// Mock implementations
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

const createMockConflictResolver = (): jest.Mocked<IConflictResolver> => ({
  resolveConflict: vi.fn(),
  suggestResolution: vi.fn(),
  canAutoResolve: vi.fn()
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
    },
    {
      id: 'item-2',
      productId: 'product-2',
      productName: 'Test Product 2',
      productCode: 'TP002',  
      quantity: 5,
      unitPrice: 50.00,
      totalPrice: 250.00
    }
  ],
  subtotal: 505.00,
  taxAmount: 50.50,
  totalAmount: 555.50,
  notes: 'Test order notes',
  requestedDeliveryDate: new Date('2025-08-15'),
  createdAt: new Date('2025-08-03'),
  updatedAt: new Date('2025-08-03'),
  syncStatus: SyncStatus.NOT_SYNCED,
  ...overrides
})

describe('OdooIntegrationService', () => {
  let service: OdooIntegrationService
  let mockRepo: jest.Mocked<IPurchaseOrderRepository>
  let mockSyncStateManager: jest.Mocked<ISyncStateManager>
  let mockCacheService: jest.Mocked<ICacheService>
  let mockEventService: jest.Mocked<IEventService>
  let mockConflictResolver: jest.Mocked<IConflictResolver>
  let mockLogger: jest.Mocked<ILogger>

  beforeEach(() => {
    mockRepo = createMockPurchaseOrderRepository()
    mockSyncStateManager = createMockSyncStateManager()
    mockCacheService = createMockCacheService()
    mockEventService = createMockEventService()
    mockConflictResolver = createMockConflictResolver()
    mockLogger = createMockLogger()

    service = new OdooIntegrationService(
      mockRepo,
      mockSyncStateManager,
      mockCacheService,
      mockEventService,
      mockConflictResolver,
      mockLogger
    )
  })

  describe('syncPurchaseOrderToOdoo', () => {
    it('should successfully create new order in Odoo when no existing sync mapping exists', async () => {
      // Arrange
      const localOrder = createTestPurchaseOrder()
      const expectedOdooOrderId = 123
      
      mockRepo.findLocalOrder.mockResolvedValue(localOrder)
      mockRepo.findSyncMapping.mockResolvedValue(null)
      mockRepo.createOdooOrder.mockResolvedValue(expectedOdooOrderId)
      mockRepo.markOrderAsSynced.mockResolvedValue()
      mockCacheService.delete.mockResolvedValue()
      mockEventService.publish.mockResolvedValue()

      // Act
      const result = await service.syncPurchaseOrderToOdoo(localOrder.id)

      // Assert
      expect(result).toMatchObject({
        success: true,
        localOrderId: localOrder.id,
        odooOrderId: expectedOdooOrderId,
        operation: 'CREATE',
        timestamp: expect.any(Date),
        duration: expect.any(Number),
        warnings: []
      })

      expect(mockRepo.findLocalOrder).toHaveBeenCalledWith(localOrder.id)
      expect(mockRepo.findSyncMapping).toHaveBeenCalledWith(localOrder.id)
      expect(mockRepo.createOdooOrder).toHaveBeenCalledWith({
        partner_id: localOrder.supplierId,
        date_order: localOrder.createdAt.toISOString(),
        order_line: [
          {
            product_id: 'product-1',
            product_qty: 10,
            price_unit: 25.50,
            name: 'Test Product 1'
          },
          {
            product_id: 'product-2',
            product_qty: 5,
            price_unit: 50.00,
            name: 'Test Product 2'
          }
        ]
      })
      expect(mockRepo.markOrderAsSynced).toHaveBeenCalledWith(
        localOrder.id,
        expectedOdooOrderId,
        expect.any(Date)
      )
      expect(mockEventService.publish).toHaveBeenCalledWith(
        expect.objectContaining({
          eventType: 'ORDER_SYNCED_TO_ODOO',
          entityId: localOrder.id,
          odooOrderId: expectedOdooOrderId
        })
      )
    })

    it('should update existing Odoo order when sync mapping exists', async () => {
      // Arrange
      const localOrder = createTestPurchaseOrder({
        syncStatus: SyncStatus.SYNCED,
        odooOrderId: 123,
        lastSyncedAt: new Date('2025-08-01')
      })
      const existingOdooOrder = {
        id: 123,
        amount_total: 555.50,
        order_line: [],
        write_date: '2025-08-01T10:00:00Z'
      }
      
      mockRepo.findLocalOrder.mockResolvedValue(localOrder)
      mockRepo.findSyncMapping.mockResolvedValue({
        localOrderId: localOrder.id,
        odooOrderId: 123,
        lastSyncedAt: new Date('2025-08-01')
      })
      mockRepo.findOdooOrder.mockResolvedValue(existingOdooOrder)
      mockRepo.detectConflicts.mockResolvedValue({
        hasConflicts: false,
        conflicts: [],
        warnings: []
      })
      mockRepo.updateOdooOrder.mockResolvedValue()

      // Act
      const result = await service.syncPurchaseOrderToOdoo(localOrder.id)

      // Assert
      expect(result).toMatchObject({
        success: true,
        localOrderId: localOrder.id,
        odooOrderId: 123,
        operation: 'UPDATE',
        warnings: []
      })

      expect(mockRepo.detectConflicts).toHaveBeenCalledWith(localOrder, existingOdooOrder)
      expect(mockRepo.updateOdooOrder).toHaveBeenCalledWith(123, expect.any(Object))
    })

    it('should handle conflict detection and record conflicts appropriately', async () => {
      // Arrange
      const localOrder = createTestPurchaseOrder({
        syncStatus: SyncStatus.SYNCED,
        odooOrderId: 123
      })
      const conflictingOdooOrder = {
        id: 123,
        amount_total: 999.99, // Different total
        order_line: [],
        write_date: '2025-08-03T12:00:00Z'
      }
      const conflicts = {
        hasConflicts: true,
        conflicts: [{
          field: 'totalAmount',
          localValue: 555.50,
          remoteValue: 999.99,
          type: ConflictType.DATA_MISMATCH
        }],
        warnings: ['Data mismatch detected']
      }
      
      mockRepo.findLocalOrder.mockResolvedValue(localOrder)
      mockRepo.findSyncMapping.mockResolvedValue({
        localOrderId: localOrder.id,
        odooOrderId: 123,
        lastSyncedAt: new Date('2025-08-01')
      })
      mockRepo.findOdooOrder.mockResolvedValue(conflictingOdooOrder)
      mockRepo.detectConflicts.mockResolvedValue(conflicts)
      mockSyncStateManager.recordConflict.mockResolvedValue()

      // Act
      const result = await service.syncPurchaseOrderToOdoo(localOrder.id)

      // Assert
      expect(result).toMatchObject({
        success: false,
        localOrderId: localOrder.id,
        odooOrderId: 123,
        operation: 'UPDATE',
        error: expect.objectContaining({
          message: 'Conflict detected - manual resolution required',
          type: 'ConflictError'
        }),
        warnings: conflicts.warnings
      })

      expect(mockSyncStateManager.recordConflict).toHaveBeenCalledWith({
        id: expect.any(String),
        entityId: localOrder.id,
        entityType: EntityType.PURCHASE_ORDER,
        conflictType: ConflictType.CONCURRENT_MODIFICATION,
        localVersion: localOrder,
        remoteVersion: conflictingOdooOrder,
        detectedAt: expect.any(Date)
      })
    })

    it('should handle network errors and update sync state accordingly', async () => {
      // Arrange
      const localOrder = createTestPurchaseOrder()
      const networkError = new Error('Connection timeout')
      
      mockRepo.findLocalOrder.mockResolvedValue(localOrder)
      mockRepo.findSyncMapping.mockResolvedValue(null)
      mockRepo.createOdooOrder.mockRejectedValue(networkError)
      mockSyncStateManager.updateSyncState.mockResolvedValue()

      // Act
      const result = await service.syncPurchaseOrderToOdoo(localOrder.id)

      // Assert
      expect(result).toMatchObject({
        success: false,
        localOrderId: localOrder.id,
        operation: 'CREATE',
        error: {
          message: 'Connection timeout',
          type: 'Error',
          timestamp: expect.any(Date)
        }
      })

      expect(mockSyncStateManager.updateSyncState).toHaveBeenCalledWith(
        localOrder.id,
        EntityType.PURCHASE_ORDER,
        expect.objectContaining({
          status: SyncStatus.SYNC_FAILED,
          lastSyncAttempt: expect.any(Date),
          failureCount: expect.any(Number),
          lastError: expect.objectContaining({
            message: 'Connection timeout',
            type: 'Error'
          })
        })
      )

      expect(mockLogger.error).toHaveBeenCalledWith(
        'Failed to sync order to Odoo',
        { localOrderId: localOrder.id, error: networkError }
      )
    })

    it('should throw error when local order not found', async () => {
      // Arrange
      const nonExistentOrderId = 'non-existent-order'
      mockRepo.findLocalOrder.mockResolvedValue(null)

      // Act & Assert
      await expect(service.syncPurchaseOrderToOdoo(nonExistentOrderId))
        .rejects
        .toThrow('Local order non-existent-order not found')

      expect(mockRepo.findLocalOrder).toHaveBeenCalledWith(nonExistentOrderId)
    })
  })

  describe('batchSyncPendingOrders', () => {
    it('should successfully process multiple pending orders', async () => {
      // Arrange
      const pendingOrders = [
        createTestPurchaseOrder({ id: 'order-1' }),
        createTestPurchaseOrder({ id: 'order-2' }),
        createTestPurchaseOrder({ id: 'order-3' })
      ]
      
      mockRepo.findOrdersRequiringSync.mockResolvedValue(pendingOrders)
      mockRepo.findLocalOrder.mockImplementation(async (id) => 
        pendingOrders.find(order => order.id === id) || null
      )
      mockRepo.findSyncMapping.mockResolvedValue(null)
      mockRepo.createOdooOrder.mockResolvedValueOnce(101)
        .mockResolvedValueOnce(102)
        .mockResolvedValueOnce(103)
      mockRepo.markOrderAsSynced.mockResolvedValue()

      // Act
      const result = await service.batchSyncPendingOrders(10)

      // Assert
      expect(result).toMatchObject({
        totalProcessed: 3,
        successful: 3,
        failed: 0,
        skipped: 0,
        results: expect.arrayContaining([
          expect.objectContaining({ success: true, localOrderId: 'order-1' }),
          expect.objectContaining({ success: true, localOrderId: 'order-2' }),
          expect.objectContaining({ success: true, localOrderId: 'order-3' })
        ])
      })

      expect(mockRepo.findOrdersRequiringSync).toHaveBeenCalled()
      expect(mockRepo.createOdooOrder).toHaveBeenCalledTimes(3)
    })

    it('should handle partial failures in batch sync', async () => {
      // Arrange
      const pendingOrders = [
        createTestPurchaseOrder({ id: 'order-success' }),
        createTestPurchaseOrder({ id: 'order-failure' })
      ]
      
      mockRepo.findOrdersRequiringSync.mockResolvedValue(pendingOrders)
      mockRepo.findLocalOrder.mockImplementation(async (id) => 
        pendingOrders.find(order => order.id === id) || null
      )
      mockRepo.findSyncMapping.mockResolvedValue(null)
      mockRepo.createOdooOrder.mockResolvedValueOnce(101)
        .mockRejectedValueOnce(new Error('Network error'))

      // Act
      const result = await service.batchSyncPendingOrders()

      // Assert
      expect(result).toMatchObject({
        totalProcessed: 2,
        successful: 1,
        failed: 1,
        skipped: 0
      })

      expect(result.results).toHaveLength(2)
      expect(result.results[0]).toMatchObject({ success: true, localOrderId: 'order-success' })
      expect(result.results[1]).toMatchObject({ success: false, localOrderId: 'order-failure' })
    })

    it('should respect batch size limit', async () => {
      // Arrange
      const pendingOrders = Array.from({ length: 20 }, (_, i) => 
        createTestPurchaseOrder({ id: `order-${i + 1}` })
      )
      const batchSize = 5
      
      mockRepo.findOrdersRequiringSync.mockResolvedValue(pendingOrders)

      // Act
      const result = await service.batchSyncPendingOrders(batchSize)

      // Assert
      expect(result.totalProcessed).toBe(batchSize)
      expect(result.nextBatchToken).toBeDefined()
    })
  })

  describe('getHealthStatus', () => {
    it('should return healthy status when all systems are operational', async () => {
      // Arrange
      mockSyncStateManager.getLastSuccessfulSync.mockResolvedValue(new Date())
      mockSyncStateManager.getFailedSyncCount.mockResolvedValue(0)
      mockCacheService.getStats.mockResolvedValue({
        hitCount: 100,
        missCount: 10,
        hitRatio: 0.91,
        totalSize: 1000,
        evictionCount: 5
      })

      // Act
      const health = await service.getHealthStatus()

      // Assert
      expect(health).toMatchObject({
        isHealthy: true,
        lastSuccessfulSync: expect.any(Date),
        consecutiveFailures: 0,
        odooConnectionStatus: 'CONNECTED',
        cacheStatus: 'HEALTHY',
        queueStatus: 'HEALTHY',
        errorRate: expect.any(Number)
      })
    })

    it('should return unhealthy status when errors are detected', async () => {
      // Arrange
      mockSyncStateManager.getLastSuccessfulSync.mockResolvedValue(null)
      mockSyncStateManager.getFailedSyncCount.mockResolvedValue(10)

      // Act
      const health = await service.getHealthStatus()

      // Assert
      expect(health).toMatchObject({
        isHealthy: false,
        consecutiveFailures: expect.any(Number),
        odooConnectionStatus: expect.stringMatching(/DISCONNECTED|ERROR/),
        errorRate: expect.any(Number)
      })
    })
  })

  describe('Real-time sync management', () => {
    it('should start real-time sync successfully', async () => {
      // Act
      await expect(service.startRealtimeSync()).resolves.not.toThrow()
    })

    it('should stop real-time sync successfully', async () => {
      // Act  
      await expect(service.stopRealtimeSync()).resolves.not.toThrow()
    })
  })

  describe('Configuration management', () => {
    it('should update sync settings', async () => {
      // Arrange
      const newSettings = {
        batchSize: 20,
        retryAttempts: 5,
        syncInterval: 300000,
        enableRealtimeSync: true
      }

      // Act
      await expect(service.updateSyncSettings(newSettings)).resolves.not.toThrow()
    })

    it('should retrieve current sync settings', async () => {
      // Act
      const settings = await service.getSyncSettings()

      // Assert
      expect(settings).toBeDefined()
      expect(settings).toHaveProperty('batchSize')
      expect(settings).toHaveProperty('retryAttempts')
      expect(settings).toHaveProperty('syncInterval')
    })
  })
})