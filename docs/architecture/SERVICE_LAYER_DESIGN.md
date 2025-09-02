# Service Layer Design for Odoo Integration

## Overview

This document details the service layer design implementing the Clean Architecture pattern for Odoo purchase order synchronization. The design emphasizes testability, maintainability, and separation of concerns.

## Core Service Interfaces

### 1. OdooIntegrationService

The central orchestrator for all Odoo operations, implementing the Facade pattern.

```typescript
interface IOdooIntegrationService {
  // Purchase Order Operations
  syncPurchaseOrderToOdoo(localOrderId: string): Promise<SyncResult>
  syncPurchaseOrderFromOdoo(odooOrderId: number): Promise<SyncResult>
  
  // Batch Operations
  batchSyncPendingOrders(batchSize?: number): Promise<BatchSyncResult>
  batchImportOrders(filters: OrderFilter): Promise<BatchImportResult>
  
  // Real-time Sync
  startRealtimeSync(): Promise<void>
  stopRealtimeSync(): Promise<void>
  
  // Health & Monitoring
  getHealthStatus(): Promise<IntegrationHealthStatus>
  getLastSyncStatus(): Promise<SyncStatus>
  
  // Configuration
  updateSyncSettings(settings: SyncSettings): Promise<void>
  getSyncSettings(): Promise<SyncSettings>
}

// Supporting Types
interface SyncResult {
  success: boolean
  localOrderId: string
  odooOrderId?: number
  operation: 'CREATE' | 'UPDATE' | 'DELETE'
  timestamp: Date
  duration: number
  error?: SyncError
  warnings: string[]
}

interface BatchSyncResult {
  totalProcessed: number
  successful: number
  failed: number
  skipped: number
  results: SyncResult[]
  duration: number
  nextBatchToken?: string
}

interface IntegrationHealthStatus {
  isHealthy: boolean
  lastSuccessfulSync: Date
  consecutiveFailures: number
  odooConnectionStatus: 'CONNECTED' | 'DISCONNECTED' | 'ERROR'
  cacheStatus: 'HEALTHY' | 'DEGRADED' | 'UNAVAILABLE'
  queueStatus: 'HEALTHY' | 'BACKLOGGED' | 'FAILED'
  errorRate: number // percentage in last 24h
}
```

### 2. PurchaseOrderRepository

Data access layer with both local and Odoo operations.

```typescript
interface IPurchaseOrderRepository {
  // Local Operations
  findLocalOrder(id: string): Promise<PurchaseOrder | null>
  findLocalOrdersByStatus(status: OrderStatus[]): Promise<PurchaseOrder[]>
  createLocalOrder(order: CreatePurchaseOrderRequest): Promise<PurchaseOrder>
  updateLocalOrder(id: string, updates: Partial<PurchaseOrder>): Promise<PurchaseOrder>
  deleteLocalOrder(id: string): Promise<void>
  
  // Odoo Operations
  findOdooOrder(id: number): Promise<OdooPurchaseOrder | null>
  createOdooOrder(order: CreateOdooOrderRequest): Promise<number>
  updateOdooOrder(id: number, updates: Partial<OdooPurchaseOrder>): Promise<void>
  findOdooOrdersModifiedSince(timestamp: Date): Promise<OdooPurchaseOrder[]>
  
  // Sync Operations
  markOrderAsSynced(localId: string, odooId: number, syncTimestamp: Date): Promise<void>
  findOrdersRequiringSync(): Promise<PurchaseOrder[]>
  findSyncMapping(localId: string): Promise<OrderSyncMapping | null>
  
  // Conflict Detection
  detectConflicts(localOrder: PurchaseOrder, odooOrder: OdooPurchaseOrder): Promise<ConflictSet>
  findConflictingOrders(): Promise<ConflictingOrder[]>
}

// Domain Entities
interface PurchaseOrder {
  id: string
  orderNumber: string
  supplierId: string
  supplierName: string
  status: OrderStatus
  items: OrderItem[]
  subtotal: number
  taxAmount: number
  totalAmount: number
  notes?: string
  requestedDeliveryDate?: Date
  approvedBy?: string
  approvedAt?: Date
  createdAt: Date
  updatedAt: Date
  syncStatus: SyncStatus
  odooOrderId?: number
  lastSyncedAt?: Date
}

interface OrderItem {
  id: string
  productId: string
  productName: string
  productCode?: string
  quantity: number
  unitPrice: number
  totalPrice: number
  notes?: string
}

enum OrderStatus {
  DRAFT = 'DRAFT',
  PENDING_APPROVAL = 'PENDING_APPROVAL',
  APPROVED = 'APPROVED',
  SENT_TO_SUPPLIER = 'SENT_TO_SUPPLIER',
  CONFIRMED = 'CONFIRMED',
  PARTIALLY_RECEIVED = 'PARTIALLY_RECEIVED',
  RECEIVED = 'RECEIVED',
  CANCELLED = 'CANCELLED'
}

enum SyncStatus {
  NOT_SYNCED = 'NOT_SYNCED',
  PENDING_SYNC = 'PENDING_SYNC',
  SYNCED = 'SYNCED',
  SYNC_FAILED = 'SYNC_FAILED',
  CONFLICT = 'CONFLICT'
}
```

### 3. SyncStateManager

Manages synchronization state and conflict resolution.

```typescript
interface ISyncStateManager {
  // State Management
  getSyncState(entityId: string, entityType: EntityType): Promise<SyncState>
  updateSyncState(entityId: string, entityType: EntityType, state: SyncState): Promise<void>
  clearSyncState(entityId: string, entityType: EntityType): Promise<void>
  
  // Conflict Management
  recordConflict(conflict: SyncConflict): Promise<void>
  resolveConflict(conflictId: string, resolution: ConflictResolution): Promise<void>
  getPendingConflicts(entityType?: EntityType): Promise<SyncConflict[]>
  getConflictHistory(entityId: string): Promise<SyncConflict[]>
  
  // Monitoring
  getLastSuccessfulSync(entityType: EntityType): Promise<Date | null>
  getFailedSyncCount(entityType: EntityType, timeWindow: TimeWindow): Promise<number>
  getSyncMetrics(timeWindow: TimeWindow): Promise<SyncMetrics>
}

interface SyncState {
  entityId: string
  entityType: EntityType
  status: SyncStatus
  lastSyncAttempt?: Date
  lastSuccessfulSync?: Date
  failureCount: number
  lastError?: SyncError
  version: number // for optimistic locking
}

interface SyncConflict {
  id: string
  entityId: string
  entityType: EntityType
  conflictType: ConflictType
  localVersion: any
  remoteVersion: any
  detectedAt: Date
  resolvedAt?: Date
  resolution?: ConflictResolution
}

enum ConflictType {
  DATA_MISMATCH = 'DATA_MISMATCH',
  VERSION_CONFLICT = 'VERSION_CONFLICT',
  CONCURRENT_MODIFICATION = 'CONCURRENT_MODIFICATION',
  BUSINESS_RULE_VIOLATION = 'BUSINESS_RULE_VIOLATION'
}
```

### 4. CacheService

Multi-level caching for performance optimization.

```typescript
interface ICacheService {
  // Basic Cache Operations
  get<T>(key: string, deserializer?: (data: any) => T): Promise<T | null>
  set(key: string, value: any, ttl?: number): Promise<void>
  delete(key: string): Promise<void>
  exists(key: string): Promise<boolean>
  
  // Batch Operations
  getBatch<T>(keys: string[]): Promise<Map<string, T>>
  setBatch(entries: Map<string, any>, ttl?: number): Promise<void>
  deleteBatch(keys: string[]): Promise<void>
  
  // Cache Invalidation
  invalidatePattern(pattern: string): Promise<void>
  invalidateTag(tag: string): Promise<void>
  
  // Cache Statistics
  getStats(): Promise<CacheStats>
  
  // Cache Hierarchy
  warmupCache(keys: string[]): Promise<void>
  getCacheHitRatio(): Promise<number>
}

interface CacheStats {
  hitCount: number
  missCount: number
  hitRatio: number
  totalSize: number
  evictionCount: number
}

// Cache Key Strategies
class CacheKeyBuilder {
  static supplierProducts(supplierId: string): string {
    return `supplier:${supplierId}:products`
  }
  
  static orderSync(localOrderId: string): string {
    return `sync:order:${localOrderId}`
  }
  
  static odooOrder(odooOrderId: number): string {
    return `odoo:order:${odooOrderId}`
  }
}
```

### 5. EventService

Domain event handling for loose coupling.

```typescript
interface IEventService {
  // Event Publishing
  publish<T extends DomainEvent>(event: T): Promise<void>
  publishBatch(events: DomainEvent[]): Promise<void>
  
  // Event Subscription
  subscribe<T extends DomainEvent>(
    eventType: string, 
    handler: EventHandler<T>,
    options?: SubscriptionOptions
  ): Promise<string> // returns subscription ID
  
  unsubscribe(subscriptionId: string): Promise<void>
  
  // Event History
  getEventHistory(entityId: string, entityType: string): Promise<DomainEvent[]>
  
  // Event Replay
  replayEvents(filter: EventFilter): Promise<void>
}

abstract class DomainEvent {
  readonly id: string = crypto.randomUUID()
  readonly timestamp: Date = new Date()
  readonly version: number = 1
  
  abstract readonly eventType: string
  abstract readonly entityId: string
  abstract readonly entityType: string
}

class OrderCreatedEvent extends DomainEvent {
  readonly eventType = 'ORDER_CREATED'
  readonly entityType = 'PURCHASE_ORDER'
  
  constructor(
    readonly entityId: string,
    readonly orderData: PurchaseOrder
  ) {
    super()
  }
}

class OrderSyncedToOdooEvent extends DomainEvent {
  readonly eventType = 'ORDER_SYNCED_TO_ODOO'
  readonly entityType = 'PURCHASE_ORDER'
  
  constructor(
    readonly entityId: string,
    readonly odooOrderId: number,
    readonly syncDuration: number
  ) {
    super()
  }
}
```

## Implementation Examples

### Service Implementation with Dependency Injection

```typescript
class OdooIntegrationService implements IOdooIntegrationService {
  constructor(
    private readonly purchaseOrderRepo: IPurchaseOrderRepository,
    private readonly syncStateManager: ISyncStateManager,
    private readonly cacheService: ICacheService,
    private readonly eventService: IEventService,
    private readonly conflictResolver: IConflictResolver,
    private readonly logger: ILogger
  ) {}
  
  async syncPurchaseOrderToOdoo(localOrderId: string): Promise<SyncResult> {
    const startTime = Date.now()
    
    try {
      // Get local order
      const localOrder = await this.purchaseOrderRepo.findLocalOrder(localOrderId)
      if (!localOrder) {
        throw new OrderNotFoundError(`Local order ${localOrderId} not found`)
      }
      
      // Check if already synced
      const syncMapping = await this.purchaseOrderRepo.findSyncMapping(localOrderId)
      if (syncMapping?.odooOrderId) {
        return await this.updateExistingOdooOrder(localOrder, syncMapping.odooOrderId, startTime)
      }
      
      // Create new order in Odoo
      const odooOrderId = await this.purchaseOrderRepo.createOdooOrder({
        partner_id: localOrder.supplierId,
        date_order: localOrder.createdAt.toISOString(),
        order_line: localOrder.items.map(item => ({
          product_id: item.productId,
          product_qty: item.quantity,
          price_unit: item.unitPrice,
          name: item.productName
        }))
      })
      
      // Mark as synced
      await this.purchaseOrderRepo.markOrderAsSynced(localOrderId, odooOrderId, new Date())
      
      // Clear cache
      await this.cacheService.delete(CacheKeyBuilder.orderSync(localOrderId))
      
      // Publish event
      await this.eventService.publish(new OrderSyncedToOdooEvent(
        localOrderId,
        odooOrderId,
        Date.now() - startTime
      ))
      
      return {
        success: true,
        localOrderId,
        odooOrderId,
        operation: 'CREATE',
        timestamp: new Date(),
        duration: Date.now() - startTime,
        warnings: []
      }
      
    } catch (error) {
      this.logger.error('Failed to sync order to Odoo', { localOrderId, error })
      
      // Update sync state
      await this.syncStateManager.updateSyncState(localOrderId, EntityType.PURCHASE_ORDER, {
        entityId: localOrderId,
        entityType: EntityType.PURCHASE_ORDER,
        status: SyncStatus.SYNC_FAILED,
        lastSyncAttempt: new Date(),
        failureCount: await this.getFailureCount(localOrderId) + 1,
        lastError: {
          message: error.message,
          type: error.constructor.name,
          timestamp: new Date()
        },
        version: 1
      })
      
      return {
        success: false,
        localOrderId,
        operation: 'CREATE',
        timestamp: new Date(),
        duration: Date.now() - startTime,
        error: {
          message: error.message,
          type: error.constructor.name,
          timestamp: new Date()
        },
        warnings: []
      }
    }
  }
  
  private async updateExistingOdooOrder(
    localOrder: PurchaseOrder, 
    odooOrderId: number, 
    startTime: number
  ): Promise<SyncResult> {
    // Check for conflicts
    const odooOrder = await this.purchaseOrderRepo.findOdooOrder(odooOrderId)
    if (odooOrder) {
      const conflicts = await this.purchaseOrderRepo.detectConflicts(localOrder, odooOrder)
      if (conflicts.hasConflicts) {
        await this.syncStateManager.recordConflict({
          id: crypto.randomUUID(),
          entityId: localOrder.id,
          entityType: EntityType.PURCHASE_ORDER,
          conflictType: ConflictType.CONCURRENT_MODIFICATION,
          localVersion: localOrder,
          remoteVersion: odooOrder,
          detectedAt: new Date()
        })
        
        return {
          success: false,
          localOrderId: localOrder.id,
          odooOrderId,
          operation: 'UPDATE',
          timestamp: new Date(),
          duration: Date.now() - startTime,
          error: {
            message: 'Conflict detected - manual resolution required',
            type: 'ConflictError',
            timestamp: new Date()
          },
          warnings: conflicts.warnings
        }
      }
    }
    
    // Update Odoo order
    await this.purchaseOrderRepo.updateOdooOrder(odooOrderId, {
      order_line: localOrder.items.map(item => ({
        product_id: item.productId,
        product_qty: item.quantity,
        price_unit: item.unitPrice,
        name: item.productName
      }))
    })
    
    return {
      success: true,
      localOrderId: localOrder.id,
      odooOrderId,
      operation: 'UPDATE',
      timestamp: new Date(),
      duration: Date.now() - startTime,
      warnings: []
    }
  }
}
```

### Repository Implementation

```typescript
class PurchaseOrderRepository implements IPurchaseOrderRepository {
  constructor(
    private readonly supabaseClient: SupabaseClient,
    private readonly odooClient: IOdooClient,
    private readonly logger: ILogger
  ) {}
  
  async findLocalOrder(id: string): Promise<PurchaseOrder | null> {
    const { data, error } = await this.supabaseClient
      .from('orders')
      .select(`
        *,
        order_items (*)
      `)
      .eq('id', id)
      .single()
    
    if (error || !data) {
      return null
    }
    
    return this.mapToPurchaseOrder(data)
  }
  
  async createOdooOrder(order: CreateOdooOrderRequest): Promise<number> {
    return await this.odooClient.create('purchase.order', {
      partner_id: parseInt(order.partner_id),
      date_order: order.date_order,
      order_line: order.order_line.map(line => [0, 0, {
        product_id: parseInt(line.product_id),
        product_qty: line.product_qty,
        price_unit: line.price_unit,
        name: line.name
      }])
    })
  }
  
  async detectConflicts(
    localOrder: PurchaseOrder, 
    odooOrder: OdooPurchaseOrder
  ): Promise<ConflictSet> {
    const conflicts: Conflict[] = []
    const warnings: string[] = []
    
    // Check total amount
    if (Math.abs(localOrder.totalAmount - odooOrder.amount_total) > 0.01) {
      conflicts.push({
        field: 'totalAmount',
        localValue: localOrder.totalAmount,
        remoteValue: odooOrder.amount_total,
        type: ConflictType.DATA_MISMATCH
      })
    }
    
    // Check item count
    if (localOrder.items.length !== odooOrder.order_line.length) {
      conflicts.push({
        field: 'itemCount',
        localValue: localOrder.items.length,
        remoteValue: odooOrder.order_line.length,
        type: ConflictType.DATA_MISMATCH
      })
    }
    
    // Check modification times
    if (localOrder.updatedAt > new Date(odooOrder.write_date)) {
      warnings.push('Local order is newer than Odoo order')
    }
    
    return {
      hasConflicts: conflicts.length > 0,
      conflicts,
      warnings
    }
  }
  
  private mapToPurchaseOrder(data: any): PurchaseOrder {
    return {
      id: data.id,
      orderNumber: data.order_number,
      supplierId: data.supplier_id,
      supplierName: data.supplier_name,
      status: data.status as OrderStatus,
      items: data.order_items.map(this.mapToOrderItem),
      subtotal: parseFloat(data.subtotal),
      taxAmount: parseFloat(data.sales_tax),
      totalAmount: parseFloat(data.grand_total),
      notes: data.notes,
      createdAt: new Date(data.created_at),
      updatedAt: new Date(data.updated_at),
      syncStatus: data.sync_status as SyncStatus,
      odooOrderId: data.odoo_order_id,
      lastSyncedAt: data.last_synced_at ? new Date(data.last_synced_at) : undefined
    }
  }
  
  private mapToOrderItem(data: any): OrderItem {
    return {
      id: data.id,
      productId: data.product_id,
      productName: data.product_name,
      productCode: data.product_code,
      quantity: data.quantity,
      unitPrice: parseFloat(data.unit_price),
      totalPrice: parseFloat(data.total_price),
      notes: data.notes
    }
  }
}
```

## Testing Strategy

### Unit Test Example

```typescript
describe('OdooIntegrationService', () => {
  let service: OdooIntegrationService
  let mockRepo: jest.Mocked<IPurchaseOrderRepository>
  let mockSyncStateManager: jest.Mocked<ISyncStateManager>
  let mockCacheService: jest.Mocked<ICacheService>
  let mockEventService: jest.Mocked<IEventService>
  
  beforeEach(() => {
    mockRepo = {
      findLocalOrder: jest.fn(),
      createOdooOrder: jest.fn(),
      markOrderAsSynced: jest.fn(),
      // ... other methods
    } as any
    
    mockSyncStateManager = {
      updateSyncState: jest.fn(),
      recordConflict: jest.fn(),
      // ... other methods
    } as any
    
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
    it('should create new order in Odoo when no existing sync mapping', async () => {
      // Arrange
      const localOrder = createMockPurchaseOrder()
      mockRepo.findLocalOrder.mockResolvedValue(localOrder)
      mockRepo.findSyncMapping.mockResolvedValue(null)
      mockRepo.createOdooOrder.mockResolvedValue(123)
      
      // Act
      const result = await service.syncPurchaseOrderToOdoo(localOrder.id)
      
      // Assert
      expect(result.success).toBe(true)
      expect(result.odooOrderId).toBe(123)
      expect(result.operation).toBe('CREATE')
      expect(mockRepo.createOdooOrder).toHaveBeenCalledWith(
        expect.objectContaining({
          partner_id: localOrder.supplierId,
          order_line: expect.arrayContaining([
            expect.objectContaining({
              product_id: localOrder.items[0].productId,
              product_qty: localOrder.items[0].quantity
            })
          ])
        })
      )
      expect(mockRepo.markOrderAsSynced).toHaveBeenCalledWith(
        localOrder.id,
        123,
        expect.any(Date)
      )
    })
    
    it('should handle network errors gracefully', async () => {
      // Arrange
      const localOrder = createMockPurchaseOrder()
      mockRepo.findLocalOrder.mockResolvedValue(localOrder)
      mockRepo.findSyncMapping.mockResolvedValue(null)
      mockRepo.createOdooOrder.mockRejectedValue(new Error('Network timeout'))
      
      // Act
      const result = await service.syncPurchaseOrderToOdoo(localOrder.id)
      
      // Assert
      expect(result.success).toBe(false)
      expect(result.error?.message).toBe('Network timeout')
      expect(mockSyncStateManager.updateSyncState).toHaveBeenCalledWith(
        localOrder.id,
        EntityType.PURCHASE_ORDER,
        expect.objectContaining({
          status: SyncStatus.SYNC_FAILED,
          failureCount: expect.any(Number)
        })
      )
    })
  })
})
```

This service layer design provides a clean, testable, and maintainable foundation for Odoo integration while following TDD principles and clean architecture patterns.