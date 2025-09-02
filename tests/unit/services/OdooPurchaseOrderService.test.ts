import { describe, it, expect, beforeEach, vi, type Mock } from 'vitest'
import { OdooPurchaseOrderService } from '../../../src/services/OdooPurchaseOrderService'
import type {
  IOdooClient,
  IPurchaseOrderRepository,
  ICacheService,
  IEventService,
  ILogger,
  PurchaseOrder,
  OdooPurchaseOrder,
  CreateOdooOrderRequest,
  UpdateOdooOrderRequest,
  OrderStatus,
  SyncStatus
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
  order_line: [
    [1, 'product-1', {
      product_id: [1, 'Test Product 1'],
      product_qty: 10,
      price_unit: 25.50,
      price_subtotal: 255.00,
      name: 'Test Product 1'
    }]
  ],
  notes: 'Test order notes',
  create_date: '2025-08-03 00:00:00',
  write_date: '2025-08-03 00:00:00',
  ...overrides
})

describe('OdooPurchaseOrderService', () => {
  let service: OdooPurchaseOrderService
  let mockOdooClient: jest.Mocked<IOdooClient>
  let mockRepository: jest.Mocked<IPurchaseOrderRepository>
  let mockCacheService: jest.Mocked<ICacheService>
  let mockEventService: jest.Mocked<IEventService>
  let mockLogger: jest.Mocked<ILogger>

  beforeEach(() => {
    mockOdooClient = createMockOdooClient()
    mockRepository = createMockPurchaseOrderRepository()
    mockCacheService = createMockCacheService()
    mockEventService = createMockEventService()
    mockLogger = createMockLogger()

    service = new OdooPurchaseOrderService(
      mockOdooClient,
      mockRepository,
      mockCacheService,
      mockEventService,
      mockLogger
    )
  })

  describe('createPurchaseOrder', () => {
    it('should create a new purchase order in Odoo successfully', async () => {
      // Arrange
      const localOrder = createTestPurchaseOrder()
      const expectedOdooId = 123
      const createRequest: CreateOdooOrderRequest = {
        partner_id: localOrder.supplierId,
        date_order: localOrder.createdAt.toISOString(),
        order_line: localOrder.items.map(item => ({
          product_id: item.productId,
          product_qty: item.quantity,
          price_unit: item.unitPrice,
          name: item.productName
        })),
        notes: localOrder.notes
      }

      mockOdooClient.create.mockResolvedValue(expectedOdooId)
      mockEventService.publish.mockResolvedValue()

      // Act
      const result = await service.createPurchaseOrder(createRequest)

      // Assert
      expect(result).toBe(expectedOdooId)
      expect(mockOdooClient.create).toHaveBeenCalledWith('purchase.order', {
        partner_id: parseInt(localOrder.supplierId),
        date_order: localOrder.createdAt.toISOString(),
        order_line: [
          [0, 0, {
            product_id: parseInt(localOrder.items[0].productId),
            product_qty: localOrder.items[0].quantity,
            price_unit: localOrder.items[0].unitPrice,
            name: localOrder.items[0].productName
          }]
        ],
        notes: localOrder.notes
      })
      expect(mockEventService.publish).toHaveBeenCalledWith(
        expect.objectContaining({
          eventType: 'PURCHASE_ORDER_CREATED_IN_ODOO',
          odooOrderId: expectedOdooId
        })
      )
    })

    it('should handle validation errors when creating purchase order', async () => {
      // Arrange
      const invalidRequest: CreateOdooOrderRequest = {
        partner_id: '', // Invalid empty partner
        date_order: 'invalid-date',
        order_line: []
      }

      mockOdooClient.create.mockRejectedValue(new Error('Invalid partner_id'))

      // Act & Assert
      await expect(service.createPurchaseOrder(invalidRequest))
        .rejects
        .toThrow('Invalid partner_id')

      expect(mockLogger.error).toHaveBeenCalledWith(
        'Failed to create purchase order in Odoo',
        expect.any(Object)
      )
    })

    it('should handle network errors gracefully', async () => {
      // Arrange
      const request = {
        partner_id: 'supplier-123',
        date_order: '2025-08-03T00:00:00Z',
        order_line: []
      }
      const networkError = new Error('Connection timeout')

      mockOdooClient.create.mockRejectedValue(networkError)

      // Act & Assert
      await expect(service.createPurchaseOrder(request))
        .rejects
        .toThrow('Connection timeout')

      expect(mockLogger.error).toHaveBeenCalledWith(
        'Failed to create purchase order in Odoo',
        { request, error: networkError }
      )
    })
  })

  describe('getPurchaseOrder', () => {
    it('should retrieve purchase order from cache if available', async () => {
      // Arrange
      const odooOrderId = 123
      const cachedOrder = createTestOdooPurchaseOrder({ id: odooOrderId })
      const cacheKey = `odoo:order:${odooOrderId}`

      mockCacheService.get.mockResolvedValue(cachedOrder)

      // Act
      const result = await service.getPurchaseOrder(odooOrderId)

      // Assert
      expect(result).toEqual(cachedOrder)
      expect(mockCacheService.get).toHaveBeenCalledWith(cacheKey, expect.any(Function))
      expect(mockOdooClient.read).not.toHaveBeenCalled()
    })

    it('should fetch from Odoo and cache when not in cache', async () => {
      // Arrange
      const odooOrderId = 123
      const odooOrder = createTestOdooPurchaseOrder({ id: odooOrderId })
      const cacheKey = `odoo:order:${odooOrderId}`

      mockCacheService.get.mockResolvedValue(null)
      mockOdooClient.read.mockResolvedValue([odooOrder])
      mockCacheService.set.mockResolvedValue()

      // Act
      const result = await service.getPurchaseOrder(odooOrderId)

      // Assert
      expect(result).toEqual(odooOrder)
      expect(mockOdooClient.read).toHaveBeenCalledWith(
        'purchase.order',
        [odooOrderId],
        expect.arrayContaining(['id', 'name', 'partner_id', 'date_order', 'state', 'amount_total'])
      )
      expect(mockCacheService.set).toHaveBeenCalledWith(
        cacheKey,
        odooOrder,
        expect.any(Number) // TTL
      )
    })

    it('should return null when order not found in Odoo', async () => {
      // Arrange
      const odooOrderId = 999
      
      mockCacheService.get.mockResolvedValue(null)
      mockOdooClient.read.mockResolvedValue([])

      // Act
      const result = await service.getPurchaseOrder(odooOrderId)

      // Assert
      expect(result).toBeNull()
      expect(mockOdooClient.read).toHaveBeenCalledWith(
        'purchase.order',
        [odooOrderId],
        expect.any(Array)
      )
    })

    it('should handle authentication errors', async () => {
      // Arrange
      const odooOrderId = 123
      const authError = new Error('Authentication failed')

      mockCacheService.get.mockResolvedValue(null)
      mockOdooClient.read.mockRejectedValue(authError)

      // Act & Assert
      await expect(service.getPurchaseOrder(odooOrderId))
        .rejects
        .toThrow('Authentication failed')

      expect(mockLogger.error).toHaveBeenCalledWith(
        'Failed to retrieve purchase order from Odoo',
        { odooOrderId, error: authError }
      )
    })
  })

  describe('updatePurchaseOrder', () => {
    it('should update purchase order in Odoo successfully', async () => {
      // Arrange
      const odooOrderId = 123
      const updates: UpdateOdooOrderRequest = {
        order_line: [
          {
            product_id: 'product-1',
            product_qty: 15, // Updated quantity
            price_unit: 25.50,
            name: 'Test Product 1'
          }
        ],
        notes: 'Updated notes'
      }
      const cacheKey = `odoo:order:${odooOrderId}`

      mockOdooClient.write.mockResolvedValue(true)
      mockCacheService.delete.mockResolvedValue()
      mockEventService.publish.mockResolvedValue()

      // Act
      const result = await service.updatePurchaseOrder(odooOrderId, updates)

      // Assert
      expect(result).toBe(true)
      expect(mockOdooClient.write).toHaveBeenCalledWith(
        'purchase.order',
        [odooOrderId],
        {
          order_line: [
            [0, 0, {
              product_id: parseInt(updates.order_line![0].product_id),
              product_qty: updates.order_line![0].product_qty,
              price_unit: updates.order_line![0].price_unit,
              name: updates.order_line![0].name
            }]
          ],
          notes: updates.notes
        }
      )
      expect(mockCacheService.delete).toHaveBeenCalledWith(cacheKey)
      expect(mockEventService.publish).toHaveBeenCalledWith(
        expect.objectContaining({
          eventType: 'PURCHASE_ORDER_UPDATED_IN_ODOO',
          odooOrderId
        })
      )
    })

    it('should handle update failures gracefully', async () => {
      // Arrange
      const odooOrderId = 123
      const updates = { notes: 'Updated notes' }
      const updateError = new Error('Update failed - record locked')

      mockOdooClient.write.mockRejectedValue(updateError)

      // Act & Assert
      await expect(service.updatePurchaseOrder(odooOrderId, updates))
        .rejects
        .toThrow('Update failed - record locked')

      expect(mockLogger.error).toHaveBeenCalledWith(
        'Failed to update purchase order in Odoo',
        { odooOrderId, updates, error: updateError }
      )
    })
  })

  describe('searchPurchaseOrders', () => {
    it('should search purchase orders with filters', async () => {
      // Arrange
      const filters = [['state', '=', 'draft'], ['partner_id', '=', 456]]
      const searchResults = [
        createTestOdooPurchaseOrder({ id: 123 }),
        createTestOdooPurchaseOrder({ id: 124 })
      ]

      mockOdooClient.searchRead.mockResolvedValue(searchResults)

      // Act
      const result = await service.searchPurchaseOrders(filters, 50, 0)

      // Assert
      expect(result).toEqual(searchResults)
      expect(mockOdooClient.searchRead).toHaveBeenCalledWith(
        'purchase.order',
        filters,
        expect.arrayContaining(['id', 'name', 'partner_id', 'state']),
        50,
        0,
        'date_order desc'
      )
    })

    it('should handle empty search results', async () => {
      // Arrange  
      const filters = [['state', '=', 'cancelled']]

      mockOdooClient.searchRead.mockResolvedValue([])

      // Act
      const result = await service.searchPurchaseOrders(filters)

      // Assert
      expect(result).toEqual([])
      expect(result).toHaveLength(0)
    })

    it('should apply default limit when not specified', async () => {
      // Arrange
      const filters = []

      mockOdooClient.searchRead.mockResolvedValue([])

      // Act
      await service.searchPurchaseOrders(filters)

      // Assert
      expect(mockOdooClient.searchRead).toHaveBeenCalledWith(
        'purchase.order',
        filters,
        expect.any(Array),
        80, // Default limit
        0,
        expect.any(String)
      )
    })
  })

  describe('getOrdersModifiedSince', () => {
    it('should retrieve orders modified after specified timestamp', async () => {
      // Arrange
      const timestamp = new Date('2025-08-01T00:00:00Z')
      const modifiedOrders = [
        createTestOdooPurchaseOrder({ 
          id: 123, 
          write_date: '2025-08-02 10:00:00' 
        }),
        createTestOdooPurchaseOrder({ 
          id: 124, 
          write_date: '2025-08-03 15:30:00' 
        })
      ]

      mockOdooClient.searchRead.mockResolvedValue(modifiedOrders)

      // Act
      const result = await service.getOrdersModifiedSince(timestamp)

      // Assert
      expect(result).toEqual(modifiedOrders)
      expect(mockOdooClient.searchRead).toHaveBeenCalledWith(
        'purchase.order',
        [['write_date', '>', timestamp.toISOString()]],
        expect.any(Array),
        expect.any(Number),
        0,
        'write_date desc'
      )
    })

    it('should return empty array when no orders modified since timestamp', async () => {
      // Arrange
      const timestamp = new Date('2025-08-10T00:00:00Z') // Future date

      mockOdooClient.searchRead.mockResolvedValue([])

      // Act
      const result = await service.getOrdersModifiedSince(timestamp)

      // Assert
      expect(result).toEqual([])
      expect(result).toHaveLength(0)
    })
  })

  describe('confirmPurchaseOrder', () => {
    it('should confirm draft purchase order successfully', async () => {
      // Arrange
      const odooOrderId = 123
      const cacheKey = `odoo:order:${odooOrderId}`

      mockOdooClient.write.mockResolvedValue(true)
      mockCacheService.delete.mockResolvedValue()
      mockEventService.publish.mockResolvedValue()

      // Act
      const result = await service.confirmPurchaseOrder(odooOrderId)

      // Assert
      expect(result).toBe(true)
      expect(mockOdooClient.write).toHaveBeenCalledWith(
        'purchase.order',
        [odooOrderId],
        { state: 'purchase' }
      )
      expect(mockCacheService.delete).toHaveBeenCalledWith(cacheKey)
      expect(mockEventService.publish).toHaveBeenCalledWith(
        expect.objectContaining({
          eventType: 'PURCHASE_ORDER_CONFIRMED_IN_ODOO',
          odooOrderId
        })
      )
    })

    it('should handle confirmation failures', async () => {
      // Arrange
      const odooOrderId = 123
      const confirmError = new Error('Cannot confirm - missing required fields')

      mockOdooClient.write.mockRejectedValue(confirmError)

      // Act & Assert
      await expect(service.confirmPurchaseOrder(odooOrderId))
        .rejects
        .toThrow('Cannot confirm - missing required fields')

      expect(mockLogger.error).toHaveBeenCalledWith(
        'Failed to confirm purchase order in Odoo',
        { odooOrderId, error: confirmError }
      )
    })
  })

  describe('cancelPurchaseOrder', () => {
    it('should cancel purchase order successfully', async () => {
      // Arrange
      const odooOrderId = 123
      const cacheKey = `odoo:order:${odooOrderId}`

      mockOdooClient.write.mockResolvedValue(true)
      mockCacheService.delete.mockResolvedValue()
      mockEventService.publish.mockResolvedValue()

      // Act
      const result = await service.cancelPurchaseOrder(odooOrderId)

      // Assert
      expect(result).toBe(true)
      expect(mockOdooClient.write).toHaveBeenCalledWith(
        'purchase.order',
        [odooOrderId],
        { state: 'cancel' }
      )
      expect(mockCacheService.delete).toHaveBeenCalledWith(cacheKey)
      expect(mockEventService.publish).toHaveBeenCalledWith(
        expect.objectContaining({
          eventType: 'PURCHASE_ORDER_CANCELLED_IN_ODOO',
          odooOrderId
        })
      )
    })
  })

  describe('Error handling and resilience', () => {
    it('should retry failed operations with exponential backoff', async () => {
      // Arrange
      const odooOrderId = 123
      const transientError = new Error('Temporary network error')
      
      // Mock to fail twice then succeed
      mockOdooClient.read
        .mockRejectedValueOnce(transientError)
        .mockRejectedValueOnce(transientError)
        .mockResolvedValue([createTestOdooPurchaseOrder()])

      mockCacheService.get.mockResolvedValue(null)

      // Act
      const result = await service.getPurchaseOrder(odooOrderId)

      // Assert
      expect(result).toBeDefined()
      expect(mockOdooClient.read).toHaveBeenCalledTimes(3)
      expect(mockLogger.warn).toHaveBeenCalledWith(
        expect.stringContaining('Retrying operation'),
        expect.any(Object)
      )
    })

    it('should fail after maximum retry attempts', async () => {
      // Arrange
      const odooOrderId = 123
      const persistentError = new Error('Persistent connection error')
      
      mockOdooClient.read.mockRejectedValue(persistentError)
      mockCacheService.get.mockResolvedValue(null)

      // Act & Assert
      await expect(service.getPurchaseOrder(odooOrderId))
        .rejects
        .toThrow('Persistent connection error')

      expect(mockOdooClient.read).toHaveBeenCalledTimes(3) // Initial + 2 retries
      expect(mockLogger.error).toHaveBeenCalledWith(
        expect.stringContaining('Failed after maximum retry attempts'),
        expect.any(Object)
      )
    })
  })
})