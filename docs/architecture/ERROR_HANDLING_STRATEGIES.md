# Error Handling & Retry Strategies for Odoo Integration

## Overview

This document defines comprehensive error handling and retry strategies for the Odoo integration system. The approach emphasizes graceful degradation, intelligent retries, and comprehensive monitoring for enterprise-grade reliability.

## Error Classification System

### 1. Error Categories

```typescript
enum ErrorCategory {
  // Transient errors - safe to retry automatically
  TRANSIENT = 'TRANSIENT',
  
  // Permanent errors - require manual intervention
  PERMANENT = 'PERMANENT',
  
  // Business errors - require user action
  BUSINESS = 'BUSINESS',
  
  // System errors - require administrator attention
  SYSTEM = 'SYSTEM'
}

enum ErrorType {
  // Transient Errors
  NETWORK_TIMEOUT = 'NETWORK_TIMEOUT',
  CONNECTION_REFUSED = 'CONNECTION_REFUSED',
  RATE_LIMIT_EXCEEDED = 'RATE_LIMIT_EXCEEDED',
  SERVICE_UNAVAILABLE = 'SERVICE_UNAVAILABLE',
  TEMPORARY_SERVER_ERROR = 'TEMPORARY_SERVER_ERROR',
  
  // Permanent Errors
  AUTHENTICATION_FAILED = 'AUTHENTICATION_FAILED',
  INVALID_CREDENTIALS = 'INVALID_CREDENTIALS',
  INSUFFICIENT_PERMISSIONS = 'INSUFFICIENT_PERMISSIONS',
  RESOURCE_NOT_FOUND = 'RESOURCE_NOT_FOUND',
  
  // Business Errors
  DATA_VALIDATION_FAILED = 'DATA_VALIDATION_FAILED',
  BUSINESS_RULE_VIOLATION = 'BUSINESS_RULE_VIOLATION',
  INSUFFICIENT_STOCK = 'INSUFFICIENT_STOCK',
  DUPLICATE_ORDER = 'DUPLICATE_ORDER',
  INVALID_SUPPLIER = 'INVALID_SUPPLIER',
  ORDER_ALREADY_PROCESSED = 'ORDER_ALREADY_PROCESSED',
  
  // System Errors
  DATABASE_CONNECTION_FAILED = 'DATABASE_CONNECTION_FAILED',
  CACHE_UNAVAILABLE = 'CACHE_UNAVAILABLE',
  MESSAGE_QUEUE_FAILED = 'MESSAGE_QUEUE_FAILED',
  CONFIGURATION_ERROR = 'CONFIGURATION_ERROR'
}

interface ErrorClassification {
  category: ErrorCategory
  type: ErrorType
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  retryable: boolean
  requiresUserAction: boolean
  requiresAdminAction: boolean
}
```

### 2. Error Classification Engine

```typescript
class ErrorClassifier {
  private static classifications: Map<string, ErrorClassification> = new Map([
    // Transient Errors
    ['ECONNREFUSED', {
      category: ErrorCategory.TRANSIENT,
      type: ErrorType.CONNECTION_REFUSED,
      severity: 'MEDIUM',
      retryable: true,
      requiresUserAction: false,
      requiresAdminAction: false
    }],
    
    ['ETIMEDOUT', {
      category: ErrorCategory.TRANSIENT,
      type: ErrorType.NETWORK_TIMEOUT,
      severity: 'MEDIUM',
      retryable: true,
      requiresUserAction: false,
      requiresAdminAction: false
    }],
    
    ['429', {
      category: ErrorCategory.TRANSIENT,
      type: ErrorType.RATE_LIMIT_EXCEEDED,
      severity: 'LOW',
      retryable: true,
      requiresUserAction: false,
      requiresAdminAction: false
    }],
    
    // Permanent Errors
    ['401', {
      category: ErrorCategory.PERMANENT,
      type: ErrorType.AUTHENTICATION_FAILED,
      severity: 'HIGH',
      retryable: false,
      requiresUserAction: false,
      requiresAdminAction: true
    }],
    
    ['403', {
      category: ErrorCategory.PERMANENT,
      type: ErrorType.INSUFFICIENT_PERMISSIONS,
      severity: 'HIGH',
      retryable: false,
      requiresUserAction: false,
      requiresAdminAction: true
    }],
    
    // Business Errors
    ['ValidationError', {
      category: ErrorCategory.BUSINESS,
      type: ErrorType.DATA_VALIDATION_FAILED,
      severity: 'MEDIUM',
      retryable: false,
      requiresUserAction: true,
      requiresAdminAction: false
    }]
  ])
  
  static classify(error: Error): ErrorClassification {
    // Check HTTP status codes
    if ('status' in error && error.status) {
      const statusClassification = this.classifications.get(error.status.toString())
      if (statusClassification) return statusClassification
    }
    
    // Check error codes
    if ('code' in error && error.code) {
      const codeClassification = this.classifications.get(error.code)
      if (codeClassification) return codeClassification
    }
    
    // Check error constructor name
    const nameClassification = this.classifications.get(error.constructor.name)
    if (nameClassification) return nameClassification
    
    // Check error message patterns
    const messageClassification = this.classifyByMessage(error.message)
    if (messageClassification) return messageClassification
    
    // Default to system error
    return {
      category: ErrorCategory.SYSTEM,
      type: ErrorType.TEMPORARY_SERVER_ERROR,
      severity: 'HIGH',
      retryable: false,
      requiresUserAction: false,
      requiresAdminAction: true
    }
  }
  
  private static classifyByMessage(message: string): ErrorClassification | null {
    const lowerMessage = message.toLowerCase()
    
    if (lowerMessage.includes('timeout') || lowerMessage.includes('timed out')) {
      return this.classifications.get('ETIMEDOUT')!
    }
    
    if (lowerMessage.includes('connection refused') || lowerMessage.includes('econnrefused')) {
      return this.classifications.get('ECONNREFUSED')!
    }
    
    if (lowerMessage.includes('rate limit') || lowerMessage.includes('too many requests')) {
      return this.classifications.get('429')!
    }
    
    if (lowerMessage.includes('authentication') || lowerMessage.includes('unauthorized')) {
      return this.classifications.get('401')!
    }
    
    if (lowerMessage.includes('validation') || lowerMessage.includes('invalid')) {
      return this.classifications.get('ValidationError')!
    }
    
    return null
  }
}
```

## Retry Strategies

### 1. Exponential Backoff with Jitter

```typescript
interface RetryConfig {
  maxAttempts: number
  baseDelay: number // milliseconds
  maxDelay: number // milliseconds
  backoffFactor: number
  jitterType: 'NONE' | 'FULL' | 'EQUAL' | 'DECORRELATED'
}

class ExponentialBackoffRetry {
  constructor(private config: RetryConfig) {}
  
  async execute<T>(
    operation: () => Promise<T>,
    context: RetryContext
  ): Promise<T> {
    let lastError: Error
    
    for (let attempt = 1; attempt <= this.config.maxAttempts; attempt++) {
      try {
        const result = await operation()
        
        // Log successful retry
        if (attempt > 1) {
          this.logger.info('Operation succeeded after retry', {
            attempt,
            context,
            duration: Date.now() - context.startTime
          })
        }
        
        return result
        
      } catch (error) {
        lastError = error
        
        // Check if error is retryable
        const classification = ErrorClassifier.classify(error)
        if (!classification.retryable) {
          throw error
        }
        
        // Don't retry on last attempt
        if (attempt === this.config.maxAttempts) {
          break
        }
        
        // Calculate delay
        const delay = this.calculateDelay(attempt)
        
        this.logger.warn('Operation failed, retrying', {
          attempt,
          nextAttempt: attempt + 1,
          delay,
          error: error.message,
          context
        })
        
        // Wait before next attempt
        await this.sleep(delay)
      }
    }
    
    // All attempts failed
    throw new MaxRetriesExceededError(
      `Operation failed after ${this.config.maxAttempts} attempts`,
      lastError,
      context
    )
  }
  
  private calculateDelay(attempt: number): number {
    // Base exponential backoff: baseDelay * (backoffFactor ^ (attempt - 1))
    const exponentialDelay = this.config.baseDelay * 
      Math.pow(this.config.backoffFactor, attempt - 1)
    
    // Cap at maxDelay
    const cappedDelay = Math.min(exponentialDelay, this.config.maxDelay)
    
    // Apply jitter
    return this.applyJitter(cappedDelay)
  }
  
  private applyJitter(delay: number): number {
    switch (this.config.jitterType) {
      case 'NONE':
        return delay
      
      case 'FULL':
        // Random delay between 0 and calculated delay
        return Math.random() * delay
      
      case 'EQUAL':
        // Half fixed delay + half random delay
        return (delay / 2) + (Math.random() * delay / 2)
      
      case 'DECORRELATED':
        // AWS-style decorrelated jitter
        return Math.random() * delay * 3
      
      default:
        return delay
    }
  }
  
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }
}
```

### 2. Retry Policy Factory

```typescript
class RetryPolicyFactory {
  static createPolicy(errorType: ErrorType): RetryConfig {
    switch (errorType) {
      case ErrorType.NETWORK_TIMEOUT:
        return {
          maxAttempts: 5,
          baseDelay: 1000,
          maxDelay: 30000,
          backoffFactor: 2,
          jitterType: 'EQUAL'
        }
      
      case ErrorType.CONNECTION_REFUSED:
        return {
          maxAttempts: 3,
          baseDelay: 2000,
          maxDelay: 10000,
          backoffFactor: 2,
          jitterType: 'FULL'
        }
      
      case ErrorType.RATE_LIMIT_EXCEEDED:
        return {
          maxAttempts: 10,
          baseDelay: 5000,
          maxDelay: 60000,
          backoffFactor: 1.5,
          jitterType: 'DECORRELATED'
        }
      
      case ErrorType.SERVICE_UNAVAILABLE:
        return {
          maxAttempts: 7,
          baseDelay: 3000,
          maxDelay: 45000,
          backoffFactor: 2,
          jitterType: 'EQUAL'
        }
      
      default:
        return {
          maxAttempts: 3,
          baseDelay: 1000,
          maxDelay: 10000,
          backoffFactor: 2,
          jitterType: 'NONE'
        }
    }
  }
}
```

### 3. Adaptive Retry Strategy

```typescript
class AdaptiveRetryStrategy {
  private successRates: Map<string, SuccessRateTracker> = new Map()
  
  async execute<T>(
    operation: () => Promise<T>,
    context: RetryContext
  ): Promise<T> {
    const operationKey = this.getOperationKey(context)
    const tracker = this.getOrCreateTracker(operationKey)
    
    // Adjust retry policy based on recent success rates
    const retryConfig = this.adaptRetryConfig(tracker)
    const retryStrategy = new ExponentialBackoffRetry(retryConfig)
    
    try {
      const result = await retryStrategy.execute(operation, context)
      tracker.recordSuccess()
      return result
      
    } catch (error) {
      tracker.recordFailure()
      throw error
    }
  }
  
  private adaptRetryConfig(tracker: SuccessRateTracker): RetryConfig {
    const successRate = tracker.getSuccessRate()
    const baseConfig = RetryPolicyFactory.createPolicy(ErrorType.NETWORK_TIMEOUT)
    
    if (successRate < 0.5) {
      // Low success rate - be more aggressive with retries
      return {
        ...baseConfig,
        maxAttempts: Math.min(baseConfig.maxAttempts + 2, 10),
        baseDelay: baseConfig.baseDelay * 1.5,
        backoffFactor: Math.min(baseConfig.backoffFactor + 0.5, 3)
      }
    } else if (successRate > 0.9) {
      // High success rate - be more conservative
      return {
        ...baseConfig,
        maxAttempts: Math.max(baseConfig.maxAttempts - 1, 2),
        baseDelay: baseConfig.baseDelay * 0.8
      }
    }
    
    return baseConfig
  }
  
  private getOperationKey(context: RetryContext): string {
    return `${context.operationType}:${context.resource}`
  }
  
  private getOrCreateTracker(key: string): SuccessRateTracker {
    if (!this.successRates.has(key)) {
      this.successRates.set(key, new SuccessRateTracker(100)) // 100 operation window
    }
    return this.successRates.get(key)!
  }
}

class SuccessRateTracker {
  private operations: boolean[] = [] // true = success, false = failure
  
  constructor(private windowSize: number) {}
  
  recordSuccess(): void {
    this.operations.push(true)
    this.trimWindow()
  }
  
  recordFailure(): void {
    this.operations.push(false)
    this.trimWindow()
  }
  
  getSuccessRate(): number {
    if (this.operations.length === 0) return 1.0
    
    const successes = this.operations.filter(op => op).length
    return successes / this.operations.length
  }
  
  private trimWindow(): void {
    if (this.operations.length > this.windowSize) {
      this.operations = this.operations.slice(-this.windowSize)
    }
  }
}
```

## Circuit Breaker Pattern

### 1. Advanced Circuit Breaker Implementation

```typescript
interface CircuitBreakerConfig {
  failureThreshold: number
  recoveryTimeout: number
  halfOpenMaxCalls: number
  monitoringWindow: number
  errorRateThreshold: number
}

class AdvancedCircuitBreaker {
  private state: CircuitBreakerState = CircuitBreakerState.CLOSED
  private failureCount = 0
  private halfOpenCallCount = 0
  private lastFailureTime?: Date
  private nextAttemptTime?: Date
  private recentCalls: CallResult[] = []
  
  constructor(
    private config: CircuitBreakerConfig,
    private metrics: CircuitBreakerMetrics
  ) {}
  
  async execute<T>(operation: () => Promise<T>): Promise<T> {
    const callStartTime = Date.now()
    
    if (this.state === CircuitBreakerState.OPEN) {
      if (this.shouldAttemptReset()) {
        this.transitionToHalfOpen()
      } else {
        this.metrics.recordRejection()
        throw new CircuitBreakerOpenError('Circuit breaker is OPEN')
      }
    }
    
    if (this.state === CircuitBreakerState.HALF_OPEN) {
      if (this.halfOpenCallCount >= this.config.halfOpenMaxCalls) {
        this.metrics.recordRejection()
        throw new CircuitBreakerOpenError('Half-open call limit exceeded')
      }
      this.halfOpenCallCount++
    }
    
    try {
      const result = await operation()
      this.onSuccess(Date.now() - callStartTime)
      return result
      
    } catch (error) {
      this.onFailure(error, Date.now() - callStartTime)
      throw error
    }
  }
  
  private onSuccess(duration: number): void {
    this.recordCall(true, duration)
    this.failureCount = 0
    
    if (this.state === CircuitBreakerState.HALF_OPEN) {
      // If we've had enough successful calls, close the circuit
      const recentSuccesses = this.recentCalls
        .slice(-this.config.halfOpenMaxCalls)
        .filter(call => call.success).length
      
      if (recentSuccesses >= this.config.halfOpenMaxCalls) {
        this.transitionToClosed()
      }
    }
    
    this.metrics.recordSuccess(duration)
  }
  
  private onFailure(error: Error, duration: number): void {
    this.recordCall(false, duration)
    this.failureCount++
    this.lastFailureTime = new Date()
    
    // Check if we should open the circuit
    if (this.shouldOpenCircuit()) {
      this.transitionToOpen()
    }
    
    this.metrics.recordFailure(duration, error)
  }
  
  private shouldOpenCircuit(): boolean {
    // Traditional failure count threshold
    if (this.failureCount >= this.config.failureThreshold) {
      return true
    }
    
    // Error rate threshold within monitoring window
    const recentCalls = this.getRecentCalls()
    if (recentCalls.length >= 10) { // Minimum calls for statistical significance
      const errorRate = recentCalls.filter(call => !call.success).length / recentCalls.length
      return errorRate >= this.config.errorRateThreshold
    }
    
    return false
  }
  
  private shouldAttemptReset(): boolean {
    if (!this.nextAttemptTime) return false
    return Date.now() >= this.nextAttemptTime.getTime()
  }
  
  private transitionToOpen(): void {
    this.state = CircuitBreakerState.OPEN
    this.nextAttemptTime = new Date(Date.now() + this.config.recoveryTimeout)
    this.halfOpenCallCount = 0
    
    this.logger.warn('Circuit breaker opened', {
      failureCount: this.failureCount,
      lastFailure: this.lastFailureTime,
      nextAttempt: this.nextAttemptTime
    })
    
    this.metrics.recordStateChange(CircuitBreakerState.OPEN)
  }
  
  private transitionToHalfOpen(): void {
    this.state = CircuitBreakerState.HALF_OPEN
    this.halfOpenCallCount = 0
    
    this.logger.info('Circuit breaker half-open - testing recovery')
    this.metrics.recordStateChange(CircuitBreakerState.HALF_OPEN)
  }
  
  private transitionToClosed(): void {
    this.state = CircuitBreakerState.CLOSED
    this.failureCount = 0
    this.lastFailureTime = undefined
    this.nextAttemptTime = undefined
    
    this.logger.info('Circuit breaker closed - service recovered')
    this.metrics.recordStateChange(CircuitBreakerState.CLOSED)
  }
  
  private recordCall(success: boolean, duration: number): void {
    this.recentCalls.push({
      success,
      duration,
      timestamp: new Date()
    })
    
    // Keep only recent calls within monitoring window
    const cutoffTime = Date.now() - this.config.monitoringWindow
    this.recentCalls = this.recentCalls.filter(
      call => call.timestamp.getTime() > cutoffTime
    )
  }
  
  private getRecentCalls(): CallResult[] {
    const cutoffTime = Date.now() - this.config.monitoringWindow
    return this.recentCalls.filter(call => call.timestamp.getTime() > cutoffTime)
  }
  
  getState(): CircuitBreakerState {
    return this.state
  }
  
  getMetrics(): CircuitBreakerHealthMetrics {
    const recentCalls = this.getRecentCalls()
    const successfulCalls = recentCalls.filter(call => call.success).length
    const errorRate = recentCalls.length > 0 
      ? (recentCalls.length - successfulCalls) / recentCalls.length 
      : 0
    
    return {
      state: this.state,
      failureCount: this.failureCount,
      errorRate,
      recentCallCount: recentCalls.length,
      successfulCallCount: successfulCalls,
      lastFailureTime: this.lastFailureTime,
      nextAttemptTime: this.nextAttemptTime
    }
  }
}

enum CircuitBreakerState {
  CLOSED = 'CLOSED',
  OPEN = 'OPEN',
  HALF_OPEN = 'HALF_OPEN'
}

interface CallResult {
  success: boolean
  duration: number
  timestamp: Date
}
```

## Bulkhead Pattern

### 1. Resource Isolation

```typescript
class BulkheadedOdooService {
  private orderSyncPool: ResourcePool
  private supplierQueryPool: ResourcePool
  private reportingPool: ResourcePool
  
  constructor() {
    // Separate resource pools for different operations
    this.orderSyncPool = new ResourcePool('order-sync', {
      maxConcurrency: 5,
      queueSize: 100,
      timeout: 30000
    })
    
    this.supplierQueryPool = new ResourcePool('supplier-query', {
      maxConcurrency: 10,
      queueSize: 50,
      timeout: 15000
    })
    
    this.reportingPool = new ResourcePool('reporting', {
      maxConcurrency: 2,
      queueSize: 20,
      timeout: 60000
    })
  }
  
  async syncOrder(orderId: string): Promise<SyncResult> {
    return this.orderSyncPool.execute(async () => {
      // Order sync implementation
      return await this.performOrderSync(orderId)
    })
  }
  
  async querySuppliers(filters: SupplierFilter): Promise<Supplier[]> {
    return this.supplierQueryPool.execute(async () => {
      // Supplier query implementation
      return await this.performSupplierQuery(filters)
    })
  }
  
  async generateReport(reportType: string): Promise<Report> {
    return this.reportingPool.execute(async () => {
      // Report generation implementation
      return await this.performReportGeneration(reportType)
    })
  }
}

class ResourcePool {
  private activeTasks = 0
  private waitQueue: Array<{
    task: () => Promise<any>
    resolve: (result: any) => void
    reject: (error: Error) => void
    timestamp: Date
  }> = []
  
  constructor(
    private name: string,
    private config: {
      maxConcurrency: number
      queueSize: number
      timeout: number
    }
  ) {}
  
  async execute<T>(task: () => Promise<T>): Promise<T> {
    return new Promise<T>((resolve, reject) => {
      // Check if we can execute immediately
      if (this.activeTasks < this.config.maxConcurrency) {
        this.executeTask(task, resolve, reject)
        return
      }
      
      // Check queue capacity
      if (this.waitQueue.length >= this.config.queueSize) {
        reject(new ResourcePoolFullError(`Resource pool ${this.name} is full`))
        return
      }
      
      // Add to queue
      this.waitQueue.push({
        task,
        resolve,
        reject,
        timestamp: new Date()
      })
      
      // Set timeout
      setTimeout(() => {
        const index = this.waitQueue.findIndex(item => item.resolve === resolve)
        if (index > -1) {
          this.waitQueue.splice(index, 1)
          reject(new TimeoutError(`Task timeout in pool ${this.name}`))
        }
      }, this.config.timeout)
    })
  }
  
  private async executeTask<T>(
    task: () => Promise<T>,
    resolve: (result: T) => void,
    reject: (error: Error) => void
  ): Promise<void> {
    this.activeTasks++
    
    try {
      const result = await task()
      resolve(result)
    } catch (error) {
      reject(error)
    } finally {
      this.activeTasks--
      this.processQueue()
    }
  }
  
  private processQueue(): void {
    if (this.waitQueue.length === 0 || this.activeTasks >= this.config.maxConcurrency) {
      return
    }
    
    const nextTask = this.waitQueue.shift()
    if (nextTask) {
      this.executeTask(nextTask.task, nextTask.resolve, nextTask.reject)
    }
  }
  
  getMetrics(): ResourcePoolMetrics {
    return {
      name: this.name,
      activeTasks: this.activeTasks,
      queuedTasks: this.waitQueue.length,
      maxConcurrency: this.config.maxConcurrency,
      utilization: this.activeTasks / this.config.maxConcurrency
    }
  }
}
```

## Fallback Mechanisms

### 1. Graceful Degradation

```typescript
class FallbackService {
  constructor(
    private primaryService: IOdooService,
    private cacheService: ICacheService,
    private localStorageService: ILocalStorageService
  ) {}
  
  async getSuppliers(filters: SupplierFilter): Promise<Supplier[]> {
    try {
      // Try primary service first
      const suppliers = await this.primaryService.getSuppliers(filters)
      
      // Cache successful result
      await this.cacheService.set(
        this.getCacheKey('suppliers', filters),
        suppliers,
        300000 // 5 minutes
      )
      
      return suppliers
      
    } catch (error) {
      this.logger.warn('Primary service failed, trying fallbacks', { error: error.message })
      
      // Fallback 1: Try cache
      try {
        const cachedSuppliers = await this.cacheService.get<Supplier[]>(
          this.getCacheKey('suppliers', filters)
        )
        
        if (cachedSuppliers) {
          this.logger.info('Returned cached suppliers')
          return cachedSuppliers
        }
      } catch (cacheError) {
        this.logger.warn('Cache fallback failed', { error: cacheError.message })
      }
      
      // Fallback 2: Try local storage with stale data
      try {
        const staleSuppliers = await this.localStorageService.getSuppliers(filters)
        if (staleSuppliers && staleSuppliers.length > 0) {
          this.logger.info('Returned stale suppliers from local storage')
          return staleSuppliers
        }
      } catch (storageError) {
        this.logger.warn('Local storage fallback failed', { error: storageError.message })
      }
      
      // Fallback 3: Return minimal default data
      this.logger.warn('All fallbacks failed, returning default data')
      return this.getDefaultSuppliers()
    }
  }
  
  async syncOrder(orderId: string): Promise<SyncResult> {
    try {
      return await this.primaryService.syncOrder(orderId)
      
    } catch (error) {
      // For critical operations like order sync, store for later retry
      await this.localStorageService.queueFailedSync({
        orderId,
        operation: 'SYNC_ORDER',
        timestamp: new Date(),
        error: error.message,
        retryCount: 0
      })
      
      return {
        success: false,
        localOrderId: orderId,
        operation: 'CREATE',
        timestamp: new Date(),
        duration: 0,
        error: {
          message: 'Service unavailable - queued for retry',
          type: 'FallbackQueued',
          timestamp: new Date()
        },
        warnings: ['Order queued for retry when service is available']
      }
    }
  }
  
  private getCacheKey(operation: string, params: any): string {
    return `${operation}:${JSON.stringify(params)}`
  }
  
  private getDefaultSuppliers(): Supplier[] {
    // Return hardcoded fallback suppliers for critical operations
    return [
      {
        id: '0',
        name: 'Default Supplier',
        status: 'FALLBACK',
        products: []
      }
    ]
  }
}
```

### 2. Timeout and Deadline Management

```typescript
class TimeoutManager {
  static async withTimeout<T>(
    promise: Promise<T>,
    timeoutMs: number,
    timeoutMessage?: string
  ): Promise<T> {
    const timeoutPromise = new Promise<never>((_, reject) => {
      setTimeout(() => {
        reject(new TimeoutError(timeoutMessage || `Operation timed out after ${timeoutMs}ms`))
      }, timeoutMs)
    })
    
    return Promise.race([promise, timeoutPromise])
  }
  
  static async withDeadline<T>(
    promise: Promise<T>,
    deadline: Date,
    deadlineMessage?: string
  ): Promise<T> {
    const timeoutMs = deadline.getTime() - Date.now()
    
    if (timeoutMs <= 0) {
      throw new DeadlineExceededError(deadlineMessage || 'Deadline already passed')
    }
    
    return this.withTimeout(promise, timeoutMs, deadlineMessage)
  }
  
  static async withCancellation<T>(
    promise: Promise<T>,
    cancellationToken: CancellationToken
  ): Promise<T> {
    return new Promise<T>((resolve, reject) => {
      const cleanup = () => {
        cancellationToken.removeListener('cancelled', onCancelled)
      }
      
      const onCancelled = () => {
        cleanup()
        reject(new OperationCancelledError('Operation was cancelled'))
      }
      
      cancellationToken.on('cancelled', onCancelled)
      
      promise
        .then(result => {
          cleanup()
          resolve(result)
        })
        .catch(error => {
          cleanup()
          reject(error)
        })
    })
  }
}

class CancellationToken extends EventEmitter {
  private _cancelled = false
  
  get cancelled(): boolean {
    return this._cancelled
  }
  
  cancel(): void {
    if (!this._cancelled) {
      this._cancelled = true
      this.emit('cancelled')
    }
  }
  
  throwIfCancelled(): void {
    if (this._cancelled) {
      throw new OperationCancelledError('Operation was cancelled')
    }
  }
}
```

## Error Monitoring and Alerting

### 1. Error Aggregation and Analysis

```typescript
class ErrorMonitor {
  private errorBuffer: ErrorEvent[] = []
  private alertRules: AlertRule[] = []
  private lastFlush = Date.now()
  
  constructor(
    private alertService: IAlertService,
    private metricsService: IMetricsService
  ) {
    // Flush errors periodically
    setInterval(() => this.flushErrors(), 60000) // Every minute
    
    this.setupDefaultAlertRules()
  }
  
  recordError(error: Error, context: ErrorContext): void {
    const classification = ErrorClassifier.classify(error)
    
    const errorEvent: ErrorEvent = {
      id: crypto.randomUUID(),
      timestamp: new Date(),
      error: {
        message: error.message,
        stack: error.stack,
        type: error.constructor.name
      },
      classification,
      context,
      resolved: false
    }
    
    this.errorBuffer.push(errorEvent)
    
    // Check immediate alert rules
    this.checkAlertRules([errorEvent])
    
    // Update metrics
    this.metricsService.increment('errors.total', {
      category: classification.category,
      type: classification.type,
      severity: classification.severity
    })
  }
  
  private async flushErrors(): Promise<void> {
    if (this.errorBuffer.length === 0) return
    
    const errors = [...this.errorBuffer]
    this.errorBuffer = []
    
    // Analyze error patterns
    const analysis = this.analyzeErrors(errors)
    
    // Send to monitoring system
    await this.metricsService.batch('errors.batch', analysis.metrics)
    
    // Check batch alert rules
    this.checkBatchAlertRules(analysis)
    
    this.lastFlush = Date.now()
  }
  
  private analyzeErrors(errors: ErrorEvent[]): ErrorAnalysis {
    const metrics: Metric[] = []
    const patterns: ErrorPattern[] = []
    
    // Group by error type
    const errorGroups = new Map<string, ErrorEvent[]>()
    for (const error of errors) {
      const key = `${error.classification.category}:${error.classification.type}`
      if (!errorGroups.has(key)) {
        errorGroups.set(key, [])
      }
      errorGroups.get(key)!.push(error)
    }
    
    // Analyze each group
    for (const [key, groupErrors] of errorGroups) {
      const [category, type] = key.split(':')
      
      metrics.push({
        name: 'error.count',
        value: groupErrors.length,
        tags: { category, type }
      })
      
      // Check for error spikes
      if (groupErrors.length > 5) {
        patterns.push({
          type: 'SPIKE',
          category: category as ErrorCategory,
          errorType: type as ErrorType,
          count: groupErrors.length,
          timeWindow: 60000, // 1 minute
          severity: this.calculateSpikeSeverity(groupErrors.length)
        })
      }
      
      // Check for error correlation
      const correlatedErrors = this.findCorrelatedErrors(groupErrors)
      if (correlatedErrors.length > 0) {
        patterns.push({
          type: 'CORRELATION',
          category: category as ErrorCategory,
          errorType: type as ErrorType,
          correlations: correlatedErrors,
          severity: 'MEDIUM'
        })
      }
    }
    
    return { metrics, patterns }
  }
  
  private setupDefaultAlertRules(): void {
    this.alertRules = [
      // Critical errors - immediate alert
      {
        condition: (errors) => errors.some(e => e.classification.severity === 'CRITICAL'),
        alert: {
          level: 'CRITICAL',
          message: 'Critical error detected',
          channels: ['slack', 'email', 'sms']
        }
      },
      
      // Authentication failures - security alert
      {
        condition: (errors) => errors.some(e => 
          e.classification.type === ErrorType.AUTHENTICATION_FAILED
        ),
        alert: {
          level: 'HIGH',
          message: 'Authentication failure detected',
          channels: ['slack', 'email']
        }
      },
      
      // Error spike - operational alert
      {
        condition: (errors) => errors.length > 10,
        alert: {
          level: 'MEDIUM',
          message: 'Error spike detected',
          channels: ['slack']
        }
      }
    ]
  }
  
  private checkAlertRules(errors: ErrorEvent[]): void {
    for (const rule of this.alertRules) {
      if (rule.condition(errors)) {
        this.alertService.sendAlert(rule.alert, { errors })
      }
    }
  }
  
  private checkBatchAlertRules(analysis: ErrorAnalysis): void {
    for (const pattern of analysis.patterns) {
      if (pattern.type === 'SPIKE' && pattern.severity === 'HIGH') {
        this.alertService.sendAlert({
          level: 'HIGH',
          message: `Error spike detected: ${pattern.count} ${pattern.errorType} errors`,
          channels: ['slack', 'email']
        }, { pattern })
      }
    }
  }
}
```

This comprehensive error handling strategy provides robust foundation for handling all types of errors in the Odoo integration system, with intelligent retry mechanisms, circuit breakers, bulkheads for isolation, and comprehensive monitoring.