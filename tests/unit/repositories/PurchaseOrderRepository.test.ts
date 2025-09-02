import { describe, it, expect, beforeEach, vi, type Mock } from 'vitest'
import { PurchaseOrderRepository } from '../../../src/repositories/PurchaseOrderRepository'
import type {
  SupabaseClient,
  IOdooClient,
  ILogger,
  PurchaseOrder,
  OdooPurchaseOrder,
  CreatePurchaseOrderRequest,
  CreateOdooOrderRequest,
  UpdateOdooOrderRequest,
  OrderSyncMapping,
  ConflictSet,
  ConflictingOrder,
  OrderStatus,
  SyncStatus,
  ConflictType
} from '../../../src/types/odoo-integration'

// Mock implementations
const createMockSupabaseClient = (): jest.Mocked<SupabaseClient> => ({
  from: vi.fn().mockReturnThis(),
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
  maybeSingle: vi.fn(),
  // Add other methods as needed
} as any)

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

const createTestSupabaseOrderData = (overrides?: any) => ({
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
  created_at: '2025-08-03T00:00:00Z',
  updated_at: '2025-08-03T00:00:00Z',
  sync_status: 'not_synced',
  odoo_order_id: null,
  last_synced_at: null,
  order_items: [
    {
      id: 'item-1',
      product_id: 'product-1',
      product_name: 'Test Product 1',
      product_code: 'TP001',
      quantity: 10,
      unit_price: '25.50',
      total_price: '255.00',
      notes: 'Test item 1'
    }
  ],
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

describe('PurchaseOrderRepository', () => {
  let repository: PurchaseOrderRepository
  let mockSupabaseClient: jest.Mocked<SupabaseClient>
  let mockOdooClient: jest.Mocked<IOdooClient>
  let mockLogger: jest.Mocked<ILogger>

  beforeEach(() => {
    mockSupabaseClient = createMockSupabaseClient()
    mockOdooClient = createMockOdooClient()
    mockLogger = createMockLogger()

    repository = new PurchaseOrderRepository(
      mockSupabaseClient,
      mockOdooClient,
      mockLogger
    )
  })

  describe('findLocalOrder', () => {
    it('should return purchase order when found', async () => {
      // Arrange
      const orderId = 'order-123'
      const orderData = createTestSupabaseOrderData()
      
      mockSupabaseClient.single.mockResolvedValue({
        data: orderData,
        error: null
      })

      // Act
      const result = await repository.findLocalOrder(orderId)

      // Assert
      expect(result).toBeDefined()
      expect(result?.id).toBe(orderId)
      expect(result?.orderNumber).toBe('PO-2025-001')
      expect(result?.totalAmount).toBe(280.50)
      expect(result?.items).toHaveLength(1)
      
      expect(mockSupabaseClient.from).toHaveBeenCalledWith('orders')
      expect(mockSupabaseClient.select).toHaveBeenCalledWith(
        expect.stringContaining('order_items')
      )
      expect(mockSupabaseClient.eq).toHaveBeenCalledWith('id', orderId)
    })

    it('should return null when order not found', async () => {
      // Arrange
      const orderId = 'non-existent-order'
      
      mockSupabaseClient.single.mockResolvedValue({
        data: null,
        error: new Error('Not found')
      })

      // Act
      const result = await repository.findLocalOrder(orderId)

      // Assert
      expect(result).toBeNull()
    })

    it('should handle database errors gracefully', async () => {
      // Arrange
      const orderId = 'order-123'
      const dbError = new Error('Database connection failed')
      
      mockSupabaseClient.single.mockResolvedValue({
        data: null,
        error: dbError
      })

      // Act
      const result = await repository.findLocalOrder(orderId)

      // Assert
      expect(result).toBeNull()
      expect(mockLogger.error).toHaveBeenCalledWith(
        'Failed to find local order',
        { orderId, error: dbError }
      )
    })
  })

  describe('findLocalOrdersByStatus', () => {
    it('should return orders filtered by status', async () => {
      // Arrange
      const statuses = [OrderStatus.DRAFT, OrderStatus.APPROVED]
      const ordersData = [
        createTestSupabaseOrderData({ id: 'order-1', status: 'draft' }),
        createTestSupabaseOrderData({ id: 'order-2', status: 'approved' })
      ]
      
      mockSupabaseClient.from.mockReturnValue({
        select: vi.fn().mockReturnThis(),
        in: vi.fn().mockReturnThis(),
        order: vi.fn().mockResolvedValue({
          data: ordersData,
          error: null
        })
      } as any)

      // Act
      const result = await repository.findLocalOrdersByStatus(statuses)

      // Assert
      expect(result).toHaveLength(2)
      expect(result[0].status).toBe(OrderStatus.DRAFT)
      expect(result[1].status).toBe(OrderStatus.APPROVED)
      
      expect(mockSupabaseClient.from).toHaveBeenCalledWith('orders')
      expect(mockSupabaseClient.in).toHaveBeenCalledWith('status', ['draft', 'approved'])
    })

    it('should return empty array when no orders match status', async () => {
      // Arrange
      const statuses = [OrderStatus.CANCELLED]
      
      mockSupabaseClient.from.mockReturnValue({
        select: vi.fn().mockReturnThis(),
        in: vi.fn().mockReturnThis(),
        order: vi.fn().mockResolvedValue({
          data: [],
          error: null
        })
      } as any)

      // Act
      const result = await repository.findLocalOrdersByStatus(statuses)

      // Assert
      expect(result).toEqual([])
      expect(result).toHaveLength(0)
    })
  })

  describe('createLocalOrder', () => {
    it('should create new local order successfully', async () => {
      // Arrange
      const createRequest: CreatePurchaseOrderRequest = {
        orderNumber: 'PO-2025-002',
        supplierId: 'supplier-789',
        supplierName: 'New Supplier',
        items: [
          {
            productId: 'product-2',
            productName: 'New Product',
            quantity: 5,
            unitPrice: 15.00
          }
        ],
        notes: 'New order notes'
      }
      const createdOrderData = createTestSupabaseOrderData({
        id: 'new-order-456',
        order_number: 'PO-2025-002',
        supplier_id: 'supplier-789'
      })
      
      mockSupabaseClient.from.mockReturnValue({
        insert: vi.fn().mockReturnThis(),
        select: vi.fn().mockReturnThis(),
        single: vi.fn().mockResolvedValue({
          data: createdOrderData,
          error: null
        })
      } as any)

      // Act
      const result = await repository.createLocalOrder(createRequest)

      // Assert
      expect(result).toBeDefined()
      expect(result.orderNumber).toBe('PO-2025-002')
      expect(result.supplierId).toBe('supplier-789')
      expect(result.syncStatus).toBe(SyncStatus.NOT_SYNCED)
      
      expect(mockSupabaseClient.insert).toHaveBeenCalledWith(
        expect.objectContaining({
          order_number: 'PO-2025-002',
          supplier_id: 'supplier-789',
          supplier_name: 'New Supplier',
          sync_status: 'not_synced'
        })
      )
    })

    it('should handle creation errors', async () => {
      // Arrange
      const createRequest: CreatePurchaseOrderRequest = {
        orderNumber: 'PO-2025-002',
        supplierId: 'supplier-789',
        supplierName: 'New Supplier',
        items: []
      }
      const dbError = new Error('Unique constraint violation')
      
      mockSupabaseClient.from.mockReturnValue({
        insert: vi.fn().mockReturnThis(),
        select: vi.fn().mockReturnThis(),
        single: vi.fn().mockResolvedValue({
          data: null,
          error: dbError
        })
      } as any)

      // Act & Assert
      await expect(repository.createLocalOrder(createRequest))
        .rejects
        .toThrow('Failed to create local order')

      expect(mockLogger.error).toHaveBeenCalledWith(
        'Failed to create local order',
        { createRequest, error: dbError }
      )
    })
  })

  describe('updateLocalOrder', () => {
    it('should update existing local order successfully', async () => {
      // Arrange
      const orderId = 'order-123'
      const updates = {
        status: OrderStatus.APPROVED,
        notes: 'Updated notes',
        approvedBy: 'user-456',
        approvedAt: new Date()
      }
      const updatedOrderData = createTestSupabaseOrderData({
        ...updates,
        status: 'approved'
      })
      
      mockSupabaseClient.from.mockReturnValue({
        update: vi.fn().mockReturnThis(),
        eq: vi.fn().mockReturnThis(),
        select: vi.fn().mockReturnThis(),
        single: vi.fn().mockResolvedValue({
          data: updatedOrderData,
          error: null
        })
      } as any)

      // Act
      const result = await repository.updateLocalOrder(orderId, updates)

      // Assert
      expect(result).toBeDefined()
      expect(result.status).toBe(OrderStatus.APPROVED)
      expect(result.notes).toBe('Updated notes')
      
      expect(mockSupabaseClient.update).toHaveBeenCalledWith(
        expect.objectContaining({
          status: 'approved',
          notes: 'Updated notes'
        })
      )
      expect(mockSupabaseClient.eq).toHaveBeenCalledWith('id', orderId)
    })

    it('should handle update errors', async () => {
      // Arrange
      const orderId = 'order-123'
      const updates = { status: OrderStatus.APPROVED }
      const dbError = new Error('Record not found')
      
      mockSupabaseClient.from.mockReturnValue({
        update: vi.fn().mockReturnThis(),
        eq: vi.fn().mockReturnThis(),
        select: vi.fn().mockReturnThis(),
        single: vi.fn().mockResolvedValue({
          data: null,
          error: dbError
        })
      } as any)

      // Act & Assert
      await expect(repository.updateLocalOrder(orderId, updates))
        .rejects
        .toThrow('Failed to update local order')
    })
  })

  describe('Odoo operations', () => {
    describe('findOdooOrder', () => {
      it('should return Odoo order when found', async () => {
        // Arrange
        const odooOrderId = 123
        const odooOrder = createTestOdooPurchaseOrder({ id: odooOrderId })
        
        mockOdooClient.read.mockResolvedValue([odooOrder])

        // Act
        const result = await repository.findOdooOrder(odooOrderId)

        // Assert
        expect(result).toEqual(odooOrder)
        expect(mockOdooClient.read).toHaveBeenCalledWith(
          'purchase.order',
          [odooOrderId],
          expect.arrayContaining(['id', 'name', 'partner_id', 'state'])
        )
      })

      it('should return null when Odoo order not found', async () => {
        // Arrange
        const odooOrderId = 999
        
        mockOdooClient.read.mockResolvedValue([])

        // Act
        const result = await repository.findOdooOrder(odooOrderId)

        // Assert
        expect(result).toBeNull()
      })
    })

    describe('createOdooOrder', () => {
      it('should create new order in Odoo successfully', async () => {
        // Arrange
        const createRequest: CreateOdooOrderRequest = {
          partner_id: 'supplier-456',
          date_order: '2025-08-03T00:00:00Z',
          order_line: [
            {
              product_id: 'product-1',
              product_qty: 10,
              price_unit: 25.50,
              name: 'Test Product 1'
            }
          ],
          notes: 'Test order'
        }
        const expectedOdooId = 123

        mockOdooClient.create.mockResolvedValue(expectedOdooId)

        // Act
        const result = await repository.createOdooOrder(createRequest)

        // Assert
        expect(result).toBe(expectedOdooId)
        expect(mockOdooClient.create).toHaveBeenCalledWith(
          'purchase.order',
          expect.objectContaining({
            partner_id: parseInt(createRequest.partner_id),
            date_order: createRequest.date_order,
            order_line: [
              [0, 0, expect.objectContaining({
                product_id: parseInt(createRequest.order_line[0].product_id),
                product_qty: createRequest.order_line[0].product_qty,
                price_unit: createRequest.order_line[0].price_unit
              })]
            ]
          })
        )
      })

      it('should handle Odoo creation errors', async () => {
        // Arrange
        const createRequest: CreateOdooOrderRequest = {
          partner_id: 'invalid-supplier',
          date_order: 'invalid-date',
          order_line: []
        }
        const odooError = new Error('Invalid partner_id')

        mockOdooClient.create.mockRejectedValue(odooError)

        // Act & Assert
        await expect(repository.createOdooOrder(createRequest))
          .rejects
          .toThrow('Failed to create Odoo order')

        expect(mockLogger.error).toHaveBeenCalledWith(
          'Failed to create order in Odoo',
          { createRequest, error: odooError }
        )
      })
    })

    describe('updateOdooOrder', () => {
      it('should update existing Odoo order successfully', async () => {
        // Arrange
        const odooOrderId = 123
        const updates: UpdateOdooOrderRequest = {
          order_line: [
            {
              product_id: 'product-1',
              product_qty: 15,
              price_unit: 25.50,
              name: 'Updated Product'
            }
          ],
          notes: 'Updated notes'
        }

        mockOdooClient.write.mockResolvedValue(true)

        // Act
        await repository.updateOdooOrder(odooOrderId, updates)

        // Assert
        expect(mockOdooClient.write).toHaveBeenCalledWith(
          'purchase.order',
          [odooOrderId],
          expect.objectContaining({
            order_line: [
              [0, 0, expect.objectContaining({
                product_id: parseInt(updates.order_line![0].product_id),
                product_qty: updates.order_line![0].product_qty
              })]
            ],
            notes: updates.notes
          })
        )
      })
    })

    describe('findOdooOrdersModifiedSince', () => {
      it('should return orders modified after timestamp', async () => {
        // Arrange
        const timestamp = new Date('2025-08-01T00:00:00Z')
        const modifiedOrders = [
          createTestOdooPurchaseOrder({ id: 123, write_date: '2025-08-02 10:00:00' }),
          createTestOdooPurchaseOrder({ id: 124, write_date: '2025-08-03 15:30:00' })
        ]

        mockOdooClient.searchRead.mockResolvedValue(modifiedOrders)

        // Act
        const result = await repository.findOdooOrdersModifiedSince(timestamp)

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
    })
  })

  describe('Sync operations', () => {
    describe('markOrderAsSynced', () => {
      it('should mark order as synced successfully', async () => {
        // Arrange
        const localOrderId = 'order-123'
        const odooOrderId = 123
        const syncTimestamp = new Date()
        
        mockSupabaseClient.from.mockReturnValue({
          update: vi.fn().mockReturnThis(),
          eq: vi.fn().mockResolvedValue({
            data: null,
            error: null
          })
        } as any)

        // Act
        await repository.markOrderAsSynced(localOrderId, odooOrderId, syncTimestamp)

        // Assert
        expect(mockSupabaseClient.update).toHaveBeenCalledWith({
          sync_status: 'synced',
          odoo_order_id: odooOrderId,
          last_synced_at: syncTimestamp.toISOString()
        })
        expect(mockSupabaseClient.eq).toHaveBeenCalledWith('id', localOrderId)
      })
    })

    describe('findOrdersRequiringSync', () => {
      it('should return orders that need synchronization', async () => {
        // Arrange
        const unsyncedOrders = [
          createTestSupabaseOrderData({ id: 'order-1', sync_status: 'not_synced' }),
          createTestSupabaseOrderData({ id: 'order-2', sync_status: 'sync_failed' }),
          createTestSupabaseOrderData({ id: 'order-3', sync_status: 'pending_sync' })
        ]
        
        mockSupabaseClient.from.mockReturnValue({
          select: vi.fn().mockReturnThis(),
          in: vi.fn().mockReturnThis(),
          order: vi.fn().mockResolvedValue({
            data: unsyncedOrders,
            error: null
          })
        } as any)

        // Act
        const result = await repository.findOrdersRequiringSync()

        // Assert
        expect(result).toHaveLength(3)
        expect(result.every(order => 
          [SyncStatus.NOT_SYNCED, SyncStatus.SYNC_FAILED, SyncStatus.PENDING_SYNC]
            .includes(order.syncStatus)
        )).toBe(true)
        
        expect(mockSupabaseClient.in).toHaveBeenCalledWith(
          'sync_status',
          ['not_synced', 'sync_failed', 'pending_sync']
        )
      })
    })

    describe('findSyncMapping', () => {
      it('should return sync mapping when found', async () => {
        // Arrange
        const localOrderId = 'order-123'
        const mappingData = {
          local_order_id: localOrderId,
          odoo_order_id: 123,
          last_synced_at: '2025-08-03T10:00:00Z'
        }
        
        mockSupabaseClient.from.mockReturnValue({
          select: vi.fn().mockReturnThis(),
          eq: vi.fn().mockReturnThis(),
          single: vi.fn().mockResolvedValue({
            data: mappingData,
            error: null
          })
        } as any)

        // Act
        const result = await repository.findSyncMapping(localOrderId)

        // Assert
        expect(result).toEqual({
          localOrderId: localOrderId,
          odooOrderId: 123,
          lastSyncedAt: new Date('2025-08-03T10:00:00Z')
        })
      })

      it('should return null when mapping not found', async () => {
        // Arrange
        const localOrderId = 'non-existent-order'
        
        mockSupabaseClient.from.mockReturnValue({
          select: vi.fn().mockReturnThis(),
          eq: vi.fn().mockReturnThis(),
          single: vi.fn().mockResolvedValue({
            data: null,
            error: new Error('Not found')
          })
        } as any)

        // Act
        const result = await repository.findSyncMapping(localOrderId)

        // Assert
        expect(result).toBeNull()
      })
    })
  })

  describe('Conflict detection', () => {
    describe('detectConflicts', () => {
      it('should detect total amount mismatch', async () => {
        // Arrange
        const localOrder = createTestPurchaseOrder({ totalAmount: 280.50 })
        const odooOrder = createTestOdooPurchaseOrder({ amount_total: 350.00 })

        // Act
        const result = await repository.detectConflicts(localOrder, odooOrder)

        // Assert
        expect(result.hasConflicts).toBe(true)
        expect(result.conflicts).toHaveLength(1)
        expect(result.conflicts[0]).toMatchObject({
          field: 'totalAmount',
          localValue: 280.50,
          remoteValue: 350.00,
          type: ConflictType.DATA_MISMATCH
        })
      })

      it('should detect item count mismatch', async () => {
        // Arrange
        const localOrder = createTestPurchaseOrder({
          items: [
            { id: '1', productId: 'p1', productName: 'P1', quantity: 10, unitPrice: 10, totalPrice: 100 },
            { id: '2', productId: 'p2', productName: 'P2', quantity: 5, unitPrice: 20, totalPrice: 100 }
          ]
        })
        const odooOrder = createTestOdooPurchaseOrder({
          order_line: [
            [1, 'p1', { product_qty: 10, price_unit: 10 }]
          ]
        })

        // Act
        const result = await repository.detectConflicts(localOrder, odooOrder)

        // Assert
        expect(result.hasConflicts).toBe(true)
        const itemCountConflict = result.conflicts.find(c => c.field === 'itemCount')
        expect(itemCountConflict).toBeDefined()
        expect(itemCountConflict?.localValue).toBe(2)
        expect(itemCountConflict?.remoteValue).toBe(1)
      })

      it('should return no conflicts when orders match', async () => {
        // Arrange
        const localOrder = createTestPurchaseOrder({ 
          totalAmount: 280.50,
          items: [{ id: '1', productId: 'p1', productName: 'P1', quantity: 10, unitPrice: 28.05, totalPrice: 280.50 }]
        })
        const odooOrder = createTestOdooPurchaseOrder({ 
          amount_total: 280.50,
          order_line: [
            [1, 'p1', { product_qty: 10, price_unit: 28.05 }]
          ]
        })

        // Act
        const result = await repository.detectConflicts(localOrder, odooOrder)

        // Assert
        expect(result.hasConflicts).toBe(false)
        expect(result.conflicts).toHaveLength(0)
      })

      it('should generate warnings for timestamp differences', async () => {
        // Arrange
        const localOrder = createTestPurchaseOrder({ 
          updatedAt: new Date('2025-08-03T12:00:00Z')
        })
        const odooOrder = createTestOdooPurchaseOrder({ 
          write_date: '2025-08-03 10:00:00' // 2 hours earlier
        })

        // Act
        const result = await repository.detectConflicts(localOrder, odooOrder)

        // Assert
        expect(result.warnings).toContain('Local order is newer than Odoo order')
      })
    })

    describe('findConflictingOrders', () => {
      it('should return orders with conflict status', async () => {
        // Arrange
        const conflictingOrders = [
          createTestSupabaseOrderData({ 
            id: 'order-1', 
            sync_status: 'conflict',
            odoo_order_id: 123
          }),
          createTestSupabaseOrderData({ 
            id: 'order-2', 
            sync_status: 'conflict',
            odoo_order_id: 124
          })
        ]
        
        mockSupabaseClient.from.mockReturnValue({
          select: vi.fn().mockReturnThis(),
          eq: vi.fn().mockReturnThis(),
          is: vi.fn().mockReturnThis(),
          order: vi.fn().mockResolvedValue({
            data: conflictingOrders,
            error: null
          })
        } as any)

        // Act
        const result = await repository.findConflictingOrders()

        // Assert
        expect(result).toHaveLength(2)
        expect(result.every(order => order.syncStatus === SyncStatus.CONFLICT)).toBe(true)
        expect(result.every(order => order.odooOrderId !== null)).toBe(true)
      })
    })
  })

  describe('Error handling', () => {
    it('should handle Supabase connection errors', async () => {
      // Arrange
      const orderId = 'order-123'
      const connectionError = new Error('Connection refused')
      
      mockSupabaseClient.single.mockRejectedValue(connectionError)

      // Act
      const result = await repository.findLocalOrder(orderId)

      // Assert
      expect(result).toBeNull()
      expect(mockLogger.error).toHaveBeenCalledWith(
        expect.stringContaining('Failed to find local order'),
        expect.objectContaining({ error: connectionError })
      )
    })

    it('should handle Odoo authentication errors', async () => {
      // Arrange
      const odooOrderId = 123
      const authError = new Error('Authentication failed')
      
      mockOdooClient.read.mockRejectedValue(authError)

      // Act & Assert
      await expect(repository.findOdooOrder(odooOrderId))
        .rejects
        .toThrow('Failed to find Odoo order')

      expect(mockLogger.error).toHaveBeenCalledWith(
        expect.stringContaining('Failed to find Odoo order'),
        expect.objectContaining({ error: authError })
      )
    })
  })
})