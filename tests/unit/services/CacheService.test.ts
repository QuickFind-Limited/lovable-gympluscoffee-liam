import { describe, it, expect, beforeEach, vi, type Mock } from 'vitest'
import { CacheService } from '../../../src/services/CacheService'
import type {
  IMemoryCache,
  IRedisCache,
  IDatabaseCache,
  CacheStats,
  ILogger
} from '../../../src/types/odoo-integration'

// Mock implementations
const createMockMemoryCache = (): jest.Mocked<IMemoryCache<string, any>> => ({
  get: vi.fn(),
  set: vi.fn(),
  delete: vi.fn(),
  clear: vi.fn(),
  has: vi.fn(),
  size: vi.fn(),
  keys: vi.fn(),
  values: vi.fn(),
  entries: vi.fn()
})

const createMockRedisCache = (): jest.Mocked<IRedisCache> => ({
  get: vi.fn(),
  set: vi.fn(),
  delete: vi.fn(),
  exists: vi.fn(),
  expire: vi.fn(),
  ttl: vi.fn(),
  keys: vi.fn(),
  flushdb: vi.fn(),
  ping: vi.fn(),
  info: vi.fn()
})

const createMockDatabaseCache = (): jest.Mocked<IDatabaseCache> => ({
  get: vi.fn(),
  set: vi.fn(),
  delete: vi.fn(),
  exists: vi.fn(),
  cleanup: vi.fn(),
  getStats: vi.fn()
})

const createMockLogger = (): jest.Mocked<ILogger> => ({
  debug: vi.fn(),
  info: vi.fn(),
  warn: vi.fn(),
  error: vi.fn()
})

// Test data
const createTestCacheData = () => ({
  suppliers: [
    { id: 'supplier-1', name: 'Supplier One' },
    { id: 'supplier-2', name: 'Supplier Two' }
  ],
  products: [
    { id: 'product-1', name: 'Product One', price: 25.50 },
    { id: 'product-2', name: 'Product Two', price: 45.00 }
  ]
})

describe('CacheService', () => {
  let cacheService: CacheService
  let mockMemoryCache: jest.Mocked<IMemoryCache<string, any>>
  let mockRedisCache: jest.Mocked<IRedisCache>
  let mockDatabaseCache: jest.Mocked<IDatabaseCache>
  let mockLogger: jest.Mocked<ILogger>

  beforeEach(() => {
    mockMemoryCache = createMockMemoryCache()
    mockRedisCache = createMockRedisCache()
    mockDatabaseCache = createMockDatabaseCache()
    mockLogger = createMockLogger()

    cacheService = new CacheService(
      mockMemoryCache,
      mockRedisCache,
      mockDatabaseCache,
      mockLogger
    )
  })

  describe('Hierarchical cache get operations', () => {
    it('should return value from L1 cache (memory) when available', async () => {
      // Arrange
      const key = 'supplier:123:products'
      const cachedData = createTestCacheData().products
      
      mockMemoryCache.get.mockResolvedValue(cachedData)

      // Act
      const result = await cacheService.get(key)

      // Assert
      expect(result).toEqual(cachedData)
      expect(mockMemoryCache.get).toHaveBeenCalledWith(key)
      expect(mockRedisCache.get).not.toHaveBeenCalled()
      expect(mockDatabaseCache.get).not.toHaveBeenCalled()
    })

    it('should fallback to L2 cache (Redis) when L1 miss', async () => {
      // Arrange
      const key = 'supplier:123:products'
      const cachedData = createTestCacheData().products
      
      mockMemoryCache.get.mockResolvedValue(null)
      mockRedisCache.get.mockResolvedValue(JSON.stringify(cachedData))
      mockMemoryCache.set.mockResolvedValue()

      // Act
      const result = await cacheService.get(key)

      // Assert
      expect(result).toEqual(cachedData)
      expect(mockMemoryCache.get).toHaveBeenCalledWith(key)
      expect(mockRedisCache.get).toHaveBeenCalledWith(key)
      expect(mockMemoryCache.set).toHaveBeenCalledWith(key, cachedData, expect.any(Number))
      expect(mockDatabaseCache.get).not.toHaveBeenCalled()
    })

    it('should fallback to L3 cache (Database) when L1 and L2 miss', async () => {
      // Arrange
      const key = 'supplier:123:products'
      const cachedData = createTestCacheData().products
      
      mockMemoryCache.get.mockResolvedValue(null)
      mockRedisCache.get.mockResolvedValue(null)
      mockDatabaseCache.get.mockResolvedValue(cachedData)
      mockRedisCache.set.mockResolvedValue()
      mockMemoryCache.set.mockResolvedValue()

      // Act
      const result = await cacheService.get(key)

      // Assert
      expect(result).toEqual(cachedData)
      expect(mockMemoryCache.get).toHaveBeenCalledWith(key)
      expect(mockRedisCache.get).toHaveBeenCalledWith(key)
      expect(mockDatabaseCache.get).toHaveBeenCalledWith(key)
      
      // Should populate higher cache levels
      expect(mockRedisCache.set).toHaveBeenCalledWith(key, JSON.stringify(cachedData), expect.any(Number))
      expect(mockMemoryCache.set).toHaveBeenCalledWith(key, cachedData, expect.any(Number))
    })

    it('should return null when value not found in any cache level', async () => {
      // Arrange
      const key = 'non-existent-key'
      
      mockMemoryCache.get.mockResolvedValue(null)
      mockRedisCache.get.mockResolvedValue(null)
      mockDatabaseCache.get.mockResolvedValue(null)

      // Act
      const result = await cacheService.get(key)

      // Assert
      expect(result).toBeNull()
      expect(mockMemoryCache.get).toHaveBeenCalledWith(key)
      expect(mockRedisCache.get).toHaveBeenCalledWith(key)
      expect(mockDatabaseCache.get).toHaveBeenCalledWith(key)
    })

    it('should use custom deserializer when provided', async () => {
      // Arrange
      const key = 'custom-data'
      const rawData = '{"date":"2025-08-03T00:00:00Z","amount":100.50}'
      const deserializer = (data: any) => ({
        ...JSON.parse(data),
        date: new Date(JSON.parse(data).date)
      })
      
      mockMemoryCache.get.mockResolvedValue(null)
      mockRedisCache.get.mockResolvedValue(rawData)

      // Act
      const result = await cacheService.get(key, deserializer)

      // Assert
      expect(result).toEqual({
        date: new Date('2025-08-03T00:00:00Z'),
        amount: 100.50
      })
      expect(result.date).toBeInstanceOf(Date)
    })
  })

  describe('Cache set operations', () => {
    it('should set value in all cache levels with write-through strategy', async () => {
      // Arrange
      const key = 'supplier:456:info'
      const value = { id: '456', name: 'New Supplier', active: true }
      const ttl = 3600

      mockMemoryCache.set.mockResolvedValue()
      mockRedisCache.set.mockResolvedValue()
      mockDatabaseCache.set.mockResolvedValue()

      // Act
      await cacheService.set(key, value, ttl)

      // Assert
      expect(mockMemoryCache.set).toHaveBeenCalledWith(key, value, ttl)
      expect(mockRedisCache.set).toHaveBeenCalledWith(key, JSON.stringify(value), ttl)
      expect(mockDatabaseCache.set).toHaveBeenCalledWith(key, value, ttl)
    })

    it('should use default TTL when not specified', async () => {
      // Arrange
      const key = 'default-ttl-key'
      const value = { data: 'test' }

      mockMemoryCache.set.mockResolvedValue()
      mockRedisCache.set.mockResolvedValue()
      mockDatabaseCache.set.mockResolvedValue()

      // Act
      await cacheService.set(key, value)

      // Assert
      expect(mockMemoryCache.set).toHaveBeenCalledWith(key, value, expect.any(Number))
      expect(mockRedisCache.set).toHaveBeenCalledWith(key, JSON.stringify(value), expect.any(Number))
      expect(mockDatabaseCache.set).toHaveBeenCalledWith(key, value, expect.any(Number))
    })

    it('should handle individual cache layer failures gracefully', async () => {
      // Arrange
      const key = 'failure-test-key'
      const value = { data: 'test' }
      const redisError = new Error('Redis connection failed')

      mockMemoryCache.set.mockResolvedValue()
      mockRedisCache.set.mockRejectedValue(redisError)
      mockDatabaseCache.set.mockResolvedValue()

      // Act
      await cacheService.set(key, value)

      // Assert
      expect(mockMemoryCache.set).toHaveBeenCalled()
      expect(mockDatabaseCache.set).toHaveBeenCalled()
      expect(mockLogger.warn).toHaveBeenCalledWith(
        'Failed to set value in Redis cache',
        { key, error: redisError }
      )
    })
  })

  describe('Cache delete operations', () => {
    it('should delete value from all cache levels', async () => {
      // Arrange
      const key = 'delete-test-key'

      mockMemoryCache.delete.mockResolvedValue(true)
      mockRedisCache.delete.mockResolvedValue(1)
      mockDatabaseCache.delete.mockResolvedValue()

      // Act
      await cacheService.delete(key)

      // Assert
      expect(mockMemoryCache.delete).toHaveBeenCalledWith(key)
      expect(mockRedisCache.delete).toHaveBeenCalledWith(key)
      expect(mockDatabaseCache.delete).toHaveBeenCalledWith(key)
    })

    it('should continue deleting from other levels if one fails', async () => {
      // Arrange
      const key = 'delete-failure-key'
      const memoryError = new Error('Memory cache error')

      mockMemoryCache.delete.mockRejectedValue(memoryError)
      mockRedisCache.delete.mockResolvedValue(1)
      mockDatabaseCache.delete.mockResolvedValue()

      // Act
      await cacheService.delete(key)

      // Assert
      expect(mockRedisCache.delete).toHaveBeenCalledWith(key)
      expect(mockDatabaseCache.delete).toHaveBeenCalledWith(key)
      expect(mockLogger.warn).toHaveBeenCalledWith(
        'Failed to delete from memory cache',
        { key, error: memoryError }
      )
    })
  })

  describe('Batch operations', () => {
    it('should perform batch get operations efficiently', async () => {
      // Arrange
      const keys = ['key1', 'key2', 'key3']
      const batchData = new Map([
        ['key1', { id: '1', data: 'data1' }],
        ['key2', { id: '2', data: 'data2' }],
        ['key3', null] // Cache miss
      ])

      // Mock memory cache returns partial results
      mockMemoryCache.get
        .mockResolvedValueOnce(batchData.get('key1'))
        .mockResolvedValueOnce(null) // key2 not in memory
        .mockResolvedValueOnce(null) // key3 not in memory

      // Mock Redis cache returns key2
      mockRedisCache.get
        .mockResolvedValueOnce(JSON.stringify(batchData.get('key2')))
        .mockResolvedValueOnce(null) // key3 not in Redis

      // Mock database cache returns nothing for key3
      mockDatabaseCache.get.mockResolvedValueOnce(null)

      // Act
      const result = await cacheService.getBatch(keys)

      // Assert
      expect(result).toBeInstanceOf(Map)
      expect(result.get('key1')).toEqual(batchData.get('key1'))
      expect(result.get('key2')).toEqual(batchData.get('key2'))
      expect(result.has('key3')).toBe(false) // Not in result due to cache miss
    })

    it('should perform batch set operations', async () => {
      // Arrange
      const entries = new Map([
        ['batch-key1', { data: 'batch-data1' }],
        ['batch-key2', { data: 'batch-data2' }]
      ])
      const ttl = 1800

      mockMemoryCache.set.mockResolvedValue()
      mockRedisCache.set.mockResolvedValue()
      mockDatabaseCache.set.mockResolvedValue()

      // Act
      await cacheService.setBatch(entries, ttl)

      // Assert
      expect(mockMemoryCache.set).toHaveBeenCalledTimes(2)
      expect(mockRedisCache.set).toHaveBeenCalledTimes(2)
      expect(mockDatabaseCache.set).toHaveBeenCalledTimes(2)
      
      for (const [key, value] of entries) {
        expect(mockMemoryCache.set).toHaveBeenCalledWith(key, value, ttl)
        expect(mockRedisCache.set).toHaveBeenCalledWith(key, JSON.stringify(value), ttl)
        expect(mockDatabaseCache.set).toHaveBeenCalledWith(key, value, ttl)
      }
    })

    it('should perform batch delete operations', async () => {
      // Arrange
      const keys = ['batch-del-1', 'batch-del-2', 'batch-del-3']

      mockMemoryCache.delete.mockResolvedValue(true)
      mockRedisCache.delete.mockResolvedValue(1)
      mockDatabaseCache.delete.mockResolvedValue()

      // Act
      await cacheService.deleteBatch(keys)

      // Assert
      expect(mockMemoryCache.delete).toHaveBeenCalledTimes(3)
      expect(mockRedisCache.delete).toHaveBeenCalledTimes(3)
      expect(mockDatabaseCache.delete).toHaveBeenCalledTimes(3)
      
      keys.forEach(key => {
        expect(mockMemoryCache.delete).toHaveBeenCalledWith(key)
        expect(mockRedisCache.delete).toHaveBeenCalledWith(key)
        expect(mockDatabaseCache.delete).toHaveBeenCalledWith(key)
      })
    })
  })

  describe('Cache invalidation', () => {
    it('should invalidate cache entries by pattern', async () => {
      // Arrange
      const pattern = 'supplier:*:products'
      const matchingKeys = ['supplier:123:products', 'supplier:456:products', 'supplier:789:products']

      mockRedisCache.keys.mockResolvedValue(matchingKeys)
      mockMemoryCache.keys.mockReturnValue(matchingKeys)
      mockMemoryCache.delete.mockResolvedValue(true)
      mockRedisCache.delete.mockResolvedValue(1)
      mockDatabaseCache.delete.mockResolvedValue()

      // Act
      await cacheService.invalidatePattern(pattern)

      // Assert
      expect(mockRedisCache.keys).toHaveBeenCalledWith(pattern)
      expect(mockMemoryCache.keys).toHaveBeenCalled()
      
      matchingKeys.forEach(key => {
        expect(mockMemoryCache.delete).toHaveBeenCalledWith(key)
        expect(mockRedisCache.delete).toHaveBeenCalledWith(key)
        expect(mockDatabaseCache.delete).toHaveBeenCalledWith(key)
      })
    })

    it('should invalidate cache entries by tag', async () => {
      // Arrange
      const tag = 'supplier-data'
      const taggedKeys = ['supplier:123:info', 'supplier:123:products', 'supplier:456:info']

      // Mock tag-based key lookup
      mockRedisCache.keys.mockResolvedValue(taggedKeys)
      mockMemoryCache.keys.mockReturnValue(taggedKeys)
      mockMemoryCache.delete.mockResolvedValue(true)
      mockRedisCache.delete.mockResolvedValue(1)
      mockDatabaseCache.delete.mockResolvedValue()

      // Act
      await cacheService.invalidateTag(tag)

      // Assert
      expect(mockRedisCache.keys).toHaveBeenCalledWith(`tag:${tag}:*`)
      
      taggedKeys.forEach(key => {
        expect(mockMemoryCache.delete).toHaveBeenCalledWith(key)
        expect(mockRedisCache.delete).toHaveBeenCalledWith(key)
        expect(mockDatabaseCache.delete).toHaveBeenCalledWith(key)
      })
    })
  })

  describe('Cache statistics and monitoring', () => {
    it('should return comprehensive cache statistics', async () => {
      // Arrange
      const memoryStats = { hitCount: 100, missCount: 20, hitRatio: 0.83 }
      const redisStats = { hitCount: 80, missCount: 40, hitRatio: 0.67 }
      const dbStats = { hitCount: 20, missCount: 60, hitRatio: 0.25 }

      mockMemoryCache.size.mockReturnValue(150)
      mockDatabaseCache.getStats.mockResolvedValue({
        hitCount: 200,
        missCount: 120,
        hitRatio: 0.625,
        totalSize: 500,
        evictionCount: 10
      })

      // Act
      const stats = await cacheService.getStats()

      // Assert
      expect(stats).toMatchObject({
        hitCount: expect.any(Number),
        missCount: expect.any(Number),
        hitRatio: expect.any(Number),
        totalSize: expect.any(Number),
        evictionCount: expect.any(Number)
      })
      expect(stats.hitRatio).toBeGreaterThanOrEqual(0)
      expect(stats.hitRatio).toBeLessThanOrEqual(1)
    })

    it('should calculate cache hit ratio accurately', async () => {
      // Arrange
      const mockStats = {
        hitCount: 850,
        missCount: 150,
        hitRatio: 0.85,
        totalSize: 1000,
        evictionCount: 25
      }
      
      mockDatabaseCache.getStats.mockResolvedValue(mockStats)

      // Act
      const hitRatio = await cacheService.getCacheHitRatio()

      // Assert
      expect(hitRatio).toBe(0.85)
    })
  })

  describe('Cache warming and preloading', () => {
    it('should warmup cache with specified keys', async () => {
      // Arrange
      const keys = ['warmup-key1', 'warmup-key2', 'warmup-key3']
      const warmupData = [
        { key: 'warmup-key1', data: 'data1' },
        { key: 'warmup-key2', data: 'data2' },
        { key: 'warmup-key3', data: 'data3' }
      ]

      // Mock database having the warmup data
      mockDatabaseCache.get
        .mockResolvedValueOnce(warmupData[0])
        .mockResolvedValueOnce(warmupData[1])
        .mockResolvedValueOnce(warmupData[2])

      mockMemoryCache.set.mockResolvedValue()
      mockRedisCache.set.mockResolvedValue()

      // Act
      await cacheService.warmupCache(keys)

      // Assert
      keys.forEach((key, index) => {
        expect(mockDatabaseCache.get).toHaveBeenCalledWith(key)
        expect(mockMemoryCache.set).toHaveBeenCalledWith(key, warmupData[index], expect.any(Number))
        expect(mockRedisCache.set).toHaveBeenCalledWith(key, JSON.stringify(warmupData[index]), expect.any(Number))
      })
    })

    it('should skip warming cache for keys with no data', async () => {
      // Arrange
      const keys = ['existing-key', 'non-existent-key']
      
      mockDatabaseCache.get
        .mockResolvedValueOnce({ data: 'exists' })
        .mockResolvedValueOnce(null) // No data for second key

      mockMemoryCache.set.mockResolvedValue()
      mockRedisCache.set.mockResolvedValue()

      // Act
      await cacheService.warmupCache(keys)

      // Assert
      expect(mockMemoryCache.set).toHaveBeenCalledTimes(1) // Only for existing key
      expect(mockRedisCache.set).toHaveBeenCalledTimes(1)
    })
  })

  describe('Error handling and resilience', () => {
    it('should handle Redis connection failures gracefully', async () => {
      // Arrange
      const key = 'redis-failure-key'
      const value = { data: 'test' }
      const redisError = new Error('Redis server unreachable')

      mockMemoryCache.get.mockResolvedValue(null)
      mockRedisCache.get.mockRejectedValue(redisError)
      mockDatabaseCache.get.mockResolvedValue(value)

      // Act
      const result = await cacheService.get(key)

      // Assert
      expect(result).toEqual(value)
      expect(mockLogger.warn).toHaveBeenCalledWith(
        'Redis cache operation failed, falling back to database',
        { key, error: redisError }
      )
    })

    it('should continue operation when memory cache fails', async () => {
      // Arrange
      const key = 'memory-failure-key'
      const value = { data: 'test' }
      const memoryError = new Error('Memory cache full')

      mockMemoryCache.get.mockRejectedValue(memoryError)
      mockRedisCache.get.mockResolvedValue(JSON.stringify(value))

      // Act
      const result = await cacheService.get(key)

      // Assert
      expect(result).toEqual(value)
      expect(mockLogger.warn).toHaveBeenCalledWith(
        'Memory cache operation failed, checking Redis',
        { key, error: memoryError }
      )
    })

    it('should handle serialization errors gracefully', async () => {
      // Arrange
      const key = 'serialization-error-key'
      const invalidJson = 'invalid-json-string{'
      
      mockMemoryCache.get.mockResolvedValue(null)
      mockRedisCache.get.mockResolvedValue(invalidJson)
      mockDatabaseCache.get.mockResolvedValue(null)

      // Act
      const result = await cacheService.get(key)

      // Assert
      expect(result).toBeNull()
      expect(mockLogger.error).toHaveBeenCalledWith(
        'Failed to deserialize cached value',
        { key, value: invalidJson, error: expect.any(Error) }
      )
    })

    it('should implement circuit breaker pattern for persistent failures', async () => {
      // Arrange
      const key = 'circuit-breaker-test'
      const persistentError = new Error('Service unavailable')

      // Simulate multiple consecutive failures
      mockMemoryCache.get.mockRejectedValue(persistentError)
      mockRedisCache.get.mockRejectedValue(persistentError)
      mockDatabaseCache.get.mockRejectedValue(persistentError)

      // Act - Multiple calls should trigger circuit breaker
      const results = await Promise.all([
        cacheService.get(key).catch(() => null),
        cacheService.get(key).catch(() => null),
        cacheService.get(key).catch(() => null)
      ])

      // Assert
      expect(results.every(r => r === null)).toBe(true)
      expect(mockLogger.error).toHaveBeenCalledWith(
        expect.stringContaining('Circuit breaker opened'),
        expect.any(Object)
      )
    })
  })

  describe('Performance optimization', () => {
    it('should implement cache key optimization for performance', async () => {
      // Arrange
      const longKey = 'very-long-cache-key-that-might-impact-performance-' + 'x'.repeat(100)
      const value = { data: 'performance test' }
      
      mockMemoryCache.set.mockResolvedValue()
      mockRedisCache.set.mockResolvedValue()
      mockDatabaseCache.set.mockResolvedValue()

      // Act
      await cacheService.set(longKey, value)

      // Assert - Should hash long keys for performance
      expect(mockMemoryCache.set).toHaveBeenCalledWith(
        expect.stringMatching(/^[a-f0-9]{32}$/), // MD5 hash pattern
        value,
        expect.any(Number)
      )
    })

    it('should implement TTL-based expiration correctly', async () => {
      // Arrange
      const key = 'ttl-test-key'
      const value = { data: 'ttl test' }
      const ttl = 60 // 60 seconds

      mockMemoryCache.set.mockResolvedValue()
      mockRedisCache.set.mockResolvedValue()
      mockDatabaseCache.set.mockResolvedValue()

      // Act
      await cacheService.set(key, value, ttl)

      // Assert
      expect(mockMemoryCache.set).toHaveBeenCalledWith(key, value, ttl)
      expect(mockRedisCache.set).toHaveBeenCalledWith(key, JSON.stringify(value), ttl)
      expect(mockDatabaseCache.set).toHaveBeenCalledWith(key, value, ttl)
    })
  })
})