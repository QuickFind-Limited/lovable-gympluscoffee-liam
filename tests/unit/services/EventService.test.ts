import { describe, it, expect, beforeEach, vi, type Mock } from 'vitest'
import { EventService } from '../../../src/services/EventService'
import type {
  DomainEvent,
  EventHandler,
  SubscriptionOptions,
  EventFilter,
  IEventStore,
  ILogger
} from '../../../src/types/odoo-integration'

// Mock domain events for testing
class OrderCreatedEvent extends DomainEvent {
  readonly eventType = 'ORDER_CREATED'
  readonly entityType = 'PURCHASE_ORDER'
  
  constructor(
    readonly entityId: string,
    readonly orderData: any
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

class OrderUpdatedEvent extends DomainEvent {
  readonly eventType = 'ORDER_UPDATED'
  readonly entityType = 'PURCHASE_ORDER'
  
  constructor(
    readonly entityId: string,
    readonly changes: any
  ) {
    super()
  }
}

// Mock implementations
const createMockEventStore = (): jest.Mocked<IEventStore> => ({
  save: vi.fn(),
  getByEntityId: vi.fn(),
  getByEventType: vi.fn(),
  getByDateRange: vi.fn(),
  deleteOlderThan: vi.fn(),
  count: vi.fn()
})

const createMockLogger = (): jest.Mocked<ILogger> => ({
  debug: vi.fn(),
  info: vi.fn(),
  warn: vi.fn(),
  error: vi.fn()
})

describe('EventService', () => {
  let eventService: EventService
  let mockEventStore: jest.Mocked<IEventStore>
  let mockLogger: jest.Mocked<ILogger>

  beforeEach(() => {
    mockEventStore = createMockEventStore()
    mockLogger = createMockLogger()

    eventService = new EventService(mockEventStore, mockLogger)
  })

  describe('Event publishing', () => {
    it('should publish single event successfully', async () => {
      // Arrange
      const event = new OrderCreatedEvent('order-123', {
        orderNumber: 'PO-2025-001',
        total: 280.50
      })

      mockEventStore.save.mockResolvedValue()

      // Act
      await eventService.publish(event)

      // Assert
      expect(mockEventStore.save).toHaveBeenCalledWith(event)
      expect(mockLogger.debug).toHaveBeenCalledWith(
        'Published event',
        {
          eventType: 'ORDER_CREATED',
          entityId: 'order-123',
          eventId: event.id
        }
      )
    })

    it('should publish event and notify all matching subscribers', async () => {
      // Arrange
      const event = new OrderCreatedEvent('order-123', { total: 280.50 })
      const handler1 = vi.fn().mockResolvedValue(undefined)
      const handler2 = vi.fn().mockResolvedValue(undefined)
      const handler3 = vi.fn().mockResolvedValue(undefined) // Different event type

      mockEventStore.save.mockResolvedValue()

      // Subscribe handlers
      await eventService.subscribe('ORDER_CREATED', handler1)
      await eventService.subscribe('ORDER_CREATED', handler2)
      await eventService.subscribe('ORDER_UPDATED', handler3) // Should not be called

      // Act
      await eventService.publish(event)

      // Assert
      expect(handler1).toHaveBeenCalledWith(event)
      expect(handler2).toHaveBeenCalledWith(event)
      expect(handler3).not.toHaveBeenCalled()
    })

    it('should handle handler failures gracefully and continue processing', async () => {
      // Arrange
      const event = new OrderCreatedEvent('order-123', { total: 280.50 })
      const failingHandler = vi.fn().mockRejectedValue(new Error('Handler failed'))
      const successHandler = vi.fn().mockResolvedValue(undefined)

      mockEventStore.save.mockResolvedValue()

      await eventService.subscribe('ORDER_CREATED', failingHandler)
      await eventService.subscribe('ORDER_CREATED', successHandler)

      // Act
      await eventService.publish(event)

      // Assert
      expect(failingHandler).toHaveBeenCalledWith(event)
      expect(successHandler).toHaveBeenCalledWith(event)
      expect(mockLogger.error).toHaveBeenCalledWith(
        'Event handler failed',
        {
          eventType: 'ORDER_CREATED',
          eventId: event.id,
          error: expect.any(Error)
        }
      )
    })

    it('should publish batch of events efficiently', async () => {
      // Arrange
      const events = [
        new OrderCreatedEvent('order-123', { total: 280.50 }),
        new OrderUpdatedEvent('order-123', { status: 'approved' }),
        new OrderSyncedToOdooEvent('order-123', 456, 2500)
      ]

      mockEventStore.save.mockResolvedValue()

      // Act
      await eventService.publishBatch(events)

      // Assert
      expect(mockEventStore.save).toHaveBeenCalledTimes(3)
      events.forEach(event => {
        expect(mockEventStore.save).toHaveBeenCalledWith(event)
      })
    })

    it('should handle event store failures', async () => {
      // Arrange
      const event = new OrderCreatedEvent('order-123', { total: 280.50 })
      const storeError = new Error('Event store unavailable')

      mockEventStore.save.mockRejectedValue(storeError)

      // Act & Assert
      await expect(eventService.publish(event))
        .rejects
        .toThrow('Failed to publish event')

      expect(mockLogger.error).toHaveBeenCalledWith(
        'Failed to save event to store',
        {
          eventType: 'ORDER_CREATED',
          eventId: event.id,
          error: storeError
        }
      )
    })
  })

  describe('Event subscription', () => {
    it('should register event handler and return subscription ID', async () => {
      // Arrange
      const handler = vi.fn()
      const eventType = 'ORDER_CREATED'

      // Act
      const subscriptionId = await eventService.subscribe(eventType, handler)

      // Assert
      expect(subscriptionId).toBeDefined()
      expect(typeof subscriptionId).toBe('string')
      expect(subscriptionId).toMatch(/^sub-[a-f0-9-]+$/)
    })

    it('should support subscription options', async () => {
      // Arrange
      const handler = vi.fn()
      const eventType = 'ORDER_CREATED'
      const options: SubscriptionOptions = {
        filter: (event) => event.entityId.startsWith('order-vip'),
        retry: true,
        maxRetries: 3,
        retryDelay: 1000
      }

      // Act
      const subscriptionId = await eventService.subscribe(eventType, handler, options)

      // Assert
      expect(subscriptionId).toBeDefined()
      
      // Test filter functionality
      const regularEvent = new OrderCreatedEvent('order-123', {})
      const vipEvent = new OrderCreatedEvent('order-vip-456', {})
      
      mockEventStore.save.mockResolvedValue()
      
      await eventService.publish(regularEvent)
      await eventService.publish(vipEvent)
      
      expect(handler).not.toHaveBeenCalledWith(regularEvent)
      expect(handler).toHaveBeenCalledWith(vipEvent)
    })

    it('should support wildcard subscriptions', async () => {
      // Arrange
      const handler = vi.fn()
      const wildcardType = 'ORDER_*'

      await eventService.subscribe(wildcardType, handler)
      mockEventStore.save.mockResolvedValue()

      // Act
      const createdEvent = new OrderCreatedEvent('order-123', {})
      const updatedEvent = new OrderUpdatedEvent('order-123', {})
      const syncedEvent = new OrderSyncedToOdooEvent('order-123', 456, 1000)

      await eventService.publish(createdEvent)
      await eventService.publish(updatedEvent)
      await eventService.publish(syncedEvent)

      // Assert
      expect(handler).toHaveBeenCalledWith(createdEvent)
      expect(handler).toHaveBeenCalledWith(updatedEvent)
      expect(handler).not.toHaveBeenCalledWith(syncedEvent) // ORDER_SYNCED_TO_ODOO doesn't match ORDER_*
    })

    it('should unsubscribe handler successfully', async () => {
      // Arrange
      const handler = vi.fn()
      const eventType = 'ORDER_CREATED'

      const subscriptionId = await eventService.subscribe(eventType, handler)
      mockEventStore.save.mockResolvedValue()

      // Act
      await eventService.unsubscribe(subscriptionId)

      // Verify unsubscription
      const event = new OrderCreatedEvent('order-123', {})
      await eventService.publish(event)

      // Assert
      expect(handler).not.toHaveBeenCalled()
    })

    it('should handle unsubscribing non-existent subscription gracefully', async () => {
      // Arrange
      const nonExistentId = 'sub-non-existent'

      // Act & Assert
      await expect(eventService.unsubscribe(nonExistentId))
        .resolves
        .not.toThrow()

      expect(mockLogger.warn).toHaveBeenCalledWith(
        'Attempted to unsubscribe non-existent subscription',
        { subscriptionId: nonExistentId }
      )
    })
  })

  describe('Event history and querying', () => {
    it('should retrieve event history for specific entity', async () => {
      // Arrange
      const entityId = 'order-123'
      const entityType = 'PURCHASE_ORDER'
      const historicalEvents = [
        new OrderCreatedEvent(entityId, { total: 280.50 }),
        new OrderUpdatedEvent(entityId, { status: 'approved' }),
        new OrderSyncedToOdooEvent(entityId, 456, 2500)
      ]

      mockEventStore.getByEntityId.mockResolvedValue(historicalEvents)

      // Act
      const result = await eventService.getEventHistory(entityId, entityType)

      // Assert
      expect(result).toEqual(historicalEvents)
      expect(mockEventStore.getByEntityId).toHaveBeenCalledWith(entityId, entityType)
    })

    it('should return empty array when no events exist for entity', async () => {
      // Arrange
      const entityId = 'non-existent-order'
      const entityType = 'PURCHASE_ORDER'

      mockEventStore.getByEntityId.mockResolvedValue([])

      // Act
      const result = await eventService.getEventHistory(entityId, entityType)

      // Assert
      expect(result).toEqual([])
      expect(result).toHaveLength(0)
    })

    it('should handle event store query failures', async () => {
      // Arrange
      const entityId = 'order-123'
      const entityType = 'PURCHASE_ORDER'
      const queryError = new Error('Database connection failed')

      mockEventStore.getByEntityId.mockRejectedValue(queryError)

      // Act & Assert
      await expect(eventService.getEventHistory(entityId, entityType))
        .rejects
        .toThrow('Failed to retrieve event history')

      expect(mockLogger.error).toHaveBeenCalledWith(
        'Failed to query event history',
        { entityId, entityType, error: queryError }
      )
    })
  })

  describe('Event replay', () => {
    it('should replay events matching filter criteria', async () => {
      // Arrange
      const filter: EventFilter = {
        eventTypes: ['ORDER_CREATED', 'ORDER_UPDATED'],
        entityIds: ['order-123', 'order-456'],
        fromDate: new Date('2025-08-01'),
        toDate: new Date('2025-08-03')
      }

      const eventsToReplay = [
        new OrderCreatedEvent('order-123', { total: 280.50 }),
        new OrderUpdatedEvent('order-456', { status: 'approved' })
      ]

      const replayHandler = vi.fn()
      await eventService.subscribe('ORDER_CREATED', replayHandler)
      await eventService.subscribe('ORDER_UPDATED', replayHandler)

      mockEventStore.getByDateRange.mockResolvedValue(eventsToReplay)

      // Act
      await eventService.replayEvents(filter)

      // Assert
      expect(mockEventStore.getByDateRange).toHaveBeenCalledWith(
        filter.fromDate!,
        filter.toDate!,
        filter.eventTypes,
        filter.entityIds
      )
      expect(replayHandler).toHaveBeenCalledTimes(2)
      expect(replayHandler).toHaveBeenCalledWith(eventsToReplay[0])
      expect(replayHandler).toHaveBeenCalledWith(eventsToReplay[1])
    })

    it('should replay events in chronological order', async () => {
      // Arrange
      const filter: EventFilter = {
        eventTypes: ['ORDER_CREATED', 'ORDER_UPDATED'],
        entityIds: ['order-123']
      }

      const event1 = new OrderCreatedEvent('order-123', {})
      event1.timestamp = new Date('2025-08-01T10:00:00Z')
      
      const event2 = new OrderUpdatedEvent('order-123', {})
      event2.timestamp = new Date('2025-08-01T11:00:00Z')
      
      const event3 = new OrderUpdatedEvent('order-123', {})
      event3.timestamp = new Date('2025-08-01T12:00:00Z')

      const eventsToReplay = [event3, event1, event2] // Out of order from store

      const replayHandler = vi.fn()
      const callOrder: Date[] = []
      
      replayHandler.mockImplementation((event: DomainEvent) => {
        callOrder.push(event.timestamp)
      })

      await eventService.subscribe('ORDER_CREATED', replayHandler)
      await eventService.subscribe('ORDER_UPDATED', replayHandler)

      mockEventStore.getByDateRange.mockResolvedValue(eventsToReplay)

      // Act
      await eventService.replayEvents(filter)

      // Assert
      expect(callOrder).toEqual([
        new Date('2025-08-01T10:00:00Z'),
        new Date('2025-08-01T11:00:00Z'),
        new Date('2025-08-01T12:00:00Z')
      ])
    })

    it('should handle empty replay result set', async () => {
      // Arrange
      const filter: EventFilter = {
        eventTypes: ['ORDER_CREATED'],
        fromDate: new Date('2025-12-01'), // Future date
        toDate: new Date('2025-12-31')
      }

      mockEventStore.getByDateRange.mockResolvedValue([])

      // Act
      await eventService.replayEvents(filter)

      // Assert
      expect(mockEventStore.getByDateRange).toHaveBeenCalled()
      expect(mockLogger.info).toHaveBeenCalledWith(
        'Event replay completed',
        { eventsReplayed: 0, filter }
      )
    })
  })

  describe('Event retry mechanism', () => {
    it('should retry failing handlers with exponential backoff', async () => {
      // Arrange
      const event = new OrderCreatedEvent('order-123', {})
      const failingHandler = vi.fn()
        .mockRejectedValueOnce(new Error('Temporary failure'))
        .mockRejectedValueOnce(new Error('Still failing'))
        .mockResolvedValue(undefined) // Succeeds on third attempt

      const options: SubscriptionOptions = {
        retry: true,
        maxRetries: 3,
        retryDelay: 100
      }

      await eventService.subscribe('ORDER_CREATED', failingHandler, options)
      mockEventStore.save.mockResolvedValue()

      // Act
      await eventService.publish(event)

      // Give time for retries
      await new Promise(resolve => setTimeout(resolve, 500))

      // Assert
      expect(failingHandler).toHaveBeenCalledTimes(3)
      expect(mockLogger.warn).toHaveBeenCalledWith(
        expect.stringContaining('Retrying event handler'),
        expect.any(Object)
      )
    })

    it('should stop retrying after max attempts', async () => {
      // Arrange
      const event = new OrderCreatedEvent('order-123', {})
      const persistentlyFailingHandler = vi.fn()
        .mockRejectedValue(new Error('Persistent failure'))

      const options: SubscriptionOptions = {
        retry: true,
        maxRetries: 2,
        retryDelay: 50
      }

      await eventService.subscribe('ORDER_CREATED', persistentlyFailingHandler, options)
      mockEventStore.save.mockResolvedValue()

      // Act
      await eventService.publish(event)

      // Give time for retries
      await new Promise(resolve => setTimeout(resolve, 300))

      // Assert
      expect(persistentlyFailingHandler).toHaveBeenCalledTimes(3) // Initial + 2 retries
      expect(mockLogger.error).toHaveBeenCalledWith(
        expect.stringContaining('Event handler failed after maximum retries'),
        expect.any(Object)
      )
    })
  })

  describe('Performance and scalability', () => {
    it('should handle high volume of events efficiently', async () => {
      // Arrange
      const eventCount = 1000
      const events = Array.from({ length: eventCount }, (_, i) => 
        new OrderCreatedEvent(`order-${i}`, { total: 100 + i })
      )

      const handler = vi.fn().mockResolvedValue(undefined)
      await eventService.subscribe('ORDER_CREATED', handler)
      mockEventStore.save.mockResolvedValue()

      const startTime = Date.now()

      // Act
      await eventService.publishBatch(events)

      const duration = Date.now() - startTime

      // Assert
      expect(handler).toHaveBeenCalledTimes(eventCount)
      expect(mockEventStore.save).toHaveBeenCalledTimes(eventCount)
      expect(duration).toBeLessThan(5000) // Should complete within 5 seconds
    })

    it('should handle many concurrent subscriptions', async () => {
      // Arrange
      const subscriberCount = 100
      const handlers = Array.from({ length: subscriberCount }, () => vi.fn())
      
      // Subscribe all handlers
      for (const handler of handlers) {
        await eventService.subscribe('ORDER_CREATED', handler)
      }

      const event = new OrderCreatedEvent('order-123', {})
      mockEventStore.save.mockResolvedValue()

      // Act
      await eventService.publish(event)

      // Assert
      handlers.forEach(handler => {
        expect(handler).toHaveBeenCalledWith(event)
      })
    })
  })

  describe('Event serialization and persistence', () => {
    it('should properly serialize complex event data', async () => {
      // Arrange
      const complexOrderData = {
        orderNumber: 'PO-2025-001',
        items: [
          { id: 1, name: 'Product A', price: 25.50, metadata: { supplier: 'Acme Inc' } },
          { id: 2, name: 'Product B', price: 45.00, metadata: { supplier: 'Beta Corp' } }
        ],
        dates: {
          created: new Date('2025-08-03T10:00:00Z'),
          requested: new Date('2025-08-15T00:00:00Z')
        }
      }

      const event = new OrderCreatedEvent('order-123', complexOrderData)
      mockEventStore.save.mockResolvedValue()

      // Act
      await eventService.publish(event)

      // Assert
      expect(mockEventStore.save).toHaveBeenCalledWith(
        expect.objectContaining({
          entityId: 'order-123',
          eventType: 'ORDER_CREATED',
          orderData: complexOrderData
        })
      )
    })
  })
})