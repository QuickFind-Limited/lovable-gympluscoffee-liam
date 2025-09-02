import { describe, it, expect, beforeEach, vi } from 'vitest'
import { MOQService } from '../../../src/services/MOQService'
import type { OdooSupplierProduct } from '../../../src/hooks/useOdooSupplierProducts'
import type { Product } from '../../../src/types/search.types'

/**
 * MOQ (Minimum Order Quantity) Service Unit Tests
 * Testing the core logic for MOQ calculations and validations
 */

describe('MOQService', () => {
  let moqService: MOQService

  beforeEach(() => {
    moqService = new MOQService()
  })

  describe('calculateAdjustedQuantity', () => {
    it('should return max(MOQ, requested_quantity) when MOQ is greater', () => {
      const product: OdooSupplierProduct = {
        id: 1,
        product_name: 'Test Product',
        min_qty: 24, // MOQ
        price: 10.50
      }
      const requestedQuantity = 10

      const result = moqService.calculateAdjustedQuantity(product, requestedQuantity)

      expect(result.adjustedQuantity).toBe(24)
      expect(result.wasAdjusted).toBe(true)
      expect(result.originalQuantity).toBe(10)
      expect(result.moq).toBe(24)
    })

    it('should return requested quantity when it meets or exceeds MOQ', () => {
      const product: OdooSupplierProduct = {
        id: 1,
        product_name: 'Test Product',
        min_qty: 12,
        price: 10.50
      }
      const requestedQuantity = 36

      const result = moqService.calculateAdjustedQuantity(product, requestedQuantity)

      expect(result.adjustedQuantity).toBe(36)
      expect(result.wasAdjusted).toBe(false)
      expect(result.originalQuantity).toBe(36)
      expect(result.moq).toBe(12)
    })

    it('should handle missing MOQ by defaulting to 1', () => {
      const product: OdooSupplierProduct = {
        id: 1,
        product_name: 'Test Product',
        price: 10.50
        // min_qty is undefined
      }
      const requestedQuantity = 5

      const result = moqService.calculateAdjustedQuantity(product, requestedQuantity)

      expect(result.adjustedQuantity).toBe(5)
      expect(result.wasAdjusted).toBe(false)
      expect(result.originalQuantity).toBe(5)
      expect(result.moq).toBe(1)
    })

    it('should handle zero MOQ by defaulting to 1', () => {
      const product: OdooSupplierProduct = {
        id: 1,
        product_name: 'Test Product',
        min_qty: 0,
        price: 10.50
      }
      const requestedQuantity = 5

      const result = moqService.calculateAdjustedQuantity(product, requestedQuantity)

      expect(result.adjustedQuantity).toBe(5)
      expect(result.wasAdjusted).toBe(false)
      expect(result.originalQuantity).toBe(5)
      expect(result.moq).toBe(1)
    })

    it('should handle negative MOQ by defaulting to 1', () => {
      const product: OdooSupplierProduct = {
        id: 1,
        product_name: 'Test Product',
        min_qty: -5,
        price: 10.50
      }
      const requestedQuantity = 3

      const result = moqService.calculateAdjustedQuantity(product, requestedQuantity)

      expect(result.adjustedQuantity).toBe(3)
      expect(result.wasAdjusted).toBe(false)
      expect(result.originalQuantity).toBe(3)
      expect(result.moq).toBe(1)
    })

    it('should handle zero requested quantity', () => {
      const product: OdooSupplierProduct = {
        id: 1,
        product_name: 'Test Product',
        min_qty: 12,
        price: 10.50
      }
      const requestedQuantity = 0

      const result = moqService.calculateAdjustedQuantity(product, requestedQuantity)

      expect(result.adjustedQuantity).toBe(12)
      expect(result.wasAdjusted).toBe(true)
      expect(result.originalQuantity).toBe(0)
      expect(result.moq).toBe(12)
    })

    it('should handle negative requested quantity', () => {
      const product: OdooSupplierProduct = {
        id: 1,
        product_name: 'Test Product',
        min_qty: 12,
        price: 10.50
      }
      const requestedQuantity = -5

      const result = moqService.calculateAdjustedQuantity(product, requestedQuantity)

      expect(result.adjustedQuantity).toBe(12)
      expect(result.wasAdjusted).toBe(true)
      expect(result.originalQuantity).toBe(-5)
      expect(result.moq).toBe(12)
    })

    it('should handle exactly equal quantities', () => {
      const product: OdooSupplierProduct = {
        id: 1,
        product_name: 'Test Product',
        min_qty: 24,
        price: 10.50
      }
      const requestedQuantity = 24

      const result = moqService.calculateAdjustedQuantity(product, requestedQuantity)

      expect(result.adjustedQuantity).toBe(24)
      expect(result.wasAdjusted).toBe(false)
      expect(result.originalQuantity).toBe(24)
      expect(result.moq).toBe(24)
    })
  })

  describe('validateQuantityAgainstMOQ', () => {
    it('should return valid when quantity meets MOQ', () => {
      const product: OdooSupplierProduct = {
        id: 1,
        product_name: 'Test Product',
        min_qty: 12,
        price: 10.50
      }
      const quantity = 24

      const result = moqService.validateQuantityAgainstMOQ(product, quantity)

      expect(result.isValid).toBe(true)
      expect(result.errorMessage).toBeNull()
      expect(result.suggestedQuantity).toBe(24)
    })

    it('should return invalid when quantity is below MOQ', () => {
      const product: OdooSupplierProduct = {
        id: 1,
        product_name: 'Test Product',
        min_qty: 24,
        price: 10.50
      }
      const quantity = 10

      const result = moqService.validateQuantityAgainstMOQ(product, quantity)

      expect(result.isValid).toBe(false)
      expect(result.errorMessage).toBe('Quantity (10) is below minimum order quantity (24)')
      expect(result.suggestedQuantity).toBe(24)
    })

    it('should handle missing product gracefully', () => {
      const result = moqService.validateQuantityAgainstMOQ(null, 10)

      expect(result.isValid).toBe(true)
      expect(result.errorMessage).toBeNull()
      expect(result.suggestedQuantity).toBe(10)
    })

    it('should handle undefined product gracefully', () => {
      const result = moqService.validateQuantityAgainstMOQ(undefined, 10)

      expect(result.isValid).toBe(true)
      expect(result.errorMessage).toBeNull()
      expect(result.suggestedQuantity).toBe(10)
    })
  })

  describe('calculateMOQAdjustmentCost', () => {
    it('should calculate additional cost when quantity is adjusted up', () => {
      const product: OdooSupplierProduct = {
        id: 1,
        product_name: 'Test Product',
        min_qty: 24,
        price: 10.50
      }
      const originalQuantity = 10
      const adjustedQuantity = 24

      const result = moqService.calculateMOQAdjustmentCost(product, originalQuantity, adjustedQuantity)

      expect(result.originalCost).toBe(105.00) // 10 * 10.50
      expect(result.adjustedCost).toBe(252.00) // 24 * 10.50
      expect(result.additionalCost).toBe(147.00) // 252 - 105
      expect(result.additionalUnits).toBe(14) // 24 - 10
    })

    it('should return zero additional cost when no adjustment needed', () => {
      const product: OdooSupplierProduct = {
        id: 1,
        product_name: 'Test Product',
        min_qty: 12,
        price: 10.50
      }
      const originalQuantity = 24
      const adjustedQuantity = 24

      const result = moqService.calculateMOQAdjustmentCost(product, originalQuantity, adjustedQuantity)

      expect(result.originalCost).toBe(252.00)
      expect(result.adjustedCost).toBe(252.00)
      expect(result.additionalCost).toBe(0)
      expect(result.additionalUnits).toBe(0)
    })

    it('should handle missing price by defaulting to 0', () => {
      const product: OdooSupplierProduct = {
        id: 1,
        product_name: 'Test Product',
        min_qty: 24
        // price is undefined
      }
      const originalQuantity = 10
      const adjustedQuantity = 24

      const result = moqService.calculateMOQAdjustmentCost(product, originalQuantity, adjustedQuantity)

      expect(result.originalCost).toBe(0)
      expect(result.adjustedCost).toBe(0)
      expect(result.additionalCost).toBe(0)
      expect(result.additionalUnits).toBe(14)
    })
  })

  describe('batchProcessMOQAdjustments', () => {
    it('should process multiple products with MOQ adjustments', () => {
      const requests = [
        {
          product: { id: 1, product_name: 'Product A', min_qty: 12, price: 10.00 } as OdooSupplierProduct,
          requestedQuantity: 8
        },
        {
          product: { id: 2, product_name: 'Product B', min_qty: 24, price: 15.00 } as OdooSupplierProduct,
          requestedQuantity: 30
        },
        {
          product: { id: 3, product_name: 'Product C', min_qty: 6, price: 5.00 } as OdooSupplierProduct,
          requestedQuantity: 4
        }
      ]

      const results = moqService.batchProcessMOQAdjustments(requests)

      expect(results).toHaveLength(3)
      
      // Product A - adjusted up
      expect(results[0].adjustedQuantity).toBe(12)
      expect(results[0].wasAdjusted).toBe(true)
      expect(results[0].costImpact.additionalCost).toBe(40.00) // (12-8) * 10
      
      // Product B - no adjustment needed
      expect(results[1].adjustedQuantity).toBe(30)
      expect(results[1].wasAdjusted).toBe(false)
      expect(results[1].costImpact.additionalCost).toBe(0)
      
      // Product C - adjusted up
      expect(results[2].adjustedQuantity).toBe(6)
      expect(results[2].wasAdjusted).toBe(true)
      expect(results[2].costImpact.additionalCost).toBe(10.00) // (6-4) * 5
    })

    it('should handle empty batch gracefully', () => {
      const results = moqService.batchProcessMOQAdjustments([])
      expect(results).toEqual([])
    })

    it('should handle batch with invalid products', () => {
      const requests = [
        {
          product: null as any,
          requestedQuantity: 10
        },
        {
          product: undefined as any,
          requestedQuantity: 5
        }
      ]

      const results = moqService.batchProcessMOQAdjustments(requests)

      expect(results).toHaveLength(2)
      expect(results[0].adjustedQuantity).toBe(10)
      expect(results[0].wasAdjusted).toBe(false)
      expect(results[1].adjustedQuantity).toBe(5)
      expect(results[1].wasAdjusted).toBe(false)
    })
  })

  describe('getMOQComplianceReport', () => {
    it('should generate compliance report for mixed compliance', () => {
      const orderItems = [
        { product: { id: 1, min_qty: 12 } as OdooSupplierProduct, quantity: 15 },
        { product: { id: 2, min_qty: 24 } as OdooSupplierProduct, quantity: 10 },
        { product: { id: 3, min_qty: 6 } as OdooSupplierProduct, quantity: 8 }
      ]

      const report = moqService.getMOQComplianceReport(orderItems)

      expect(report.totalItems).toBe(3)
      expect(report.compliantItems).toBe(2) // items 1 and 3
      expect(report.nonCompliantItems).toBe(1) // item 2
      expect(report.complianceRate).toBe(66.67) // 2/3 * 100
      expect(report.nonCompliantDetails).toHaveLength(1)
      expect(report.nonCompliantDetails[0].productId).toBe(2)
      expect(report.nonCompliantDetails[0].currentQuantity).toBe(10)
      expect(report.nonCompliantDetails[0].requiredMOQ).toBe(24)
      expect(report.nonCompliantDetails[0].shortfall).toBe(14)
    })

    it('should generate 100% compliance report when all items comply', () => {
      const orderItems = [
        { product: { id: 1, min_qty: 12 } as OdooSupplierProduct, quantity: 15 },
        { product: { id: 2, min_qty: 24 } as OdooSupplierProduct, quantity: 30 }
      ]

      const report = moqService.getMOQComplianceReport(orderItems)

      expect(report.totalItems).toBe(2)
      expect(report.compliantItems).toBe(2)
      expect(report.nonCompliantItems).toBe(0)
      expect(report.complianceRate).toBe(100)
      expect(report.nonCompliantDetails).toHaveLength(0)
    })

    it('should handle empty order items', () => {
      const report = moqService.getMOQComplianceReport([])

      expect(report.totalItems).toBe(0)
      expect(report.compliantItems).toBe(0)
      expect(report.nonCompliantItems).toBe(0)
      expect(report.complianceRate).toBe(0)
      expect(report.nonCompliantDetails).toHaveLength(0)
    })
  })

  describe('error handling and edge cases', () => {
    it('should handle very large MOQ values', () => {
      const product: OdooSupplierProduct = {
        id: 1,
        product_name: 'Bulk Product',
        min_qty: 999999,
        price: 0.01
      }
      const requestedQuantity = 1000

      const result = moqService.calculateAdjustedQuantity(product, requestedQuantity)

      expect(result.adjustedQuantity).toBe(999999)
      expect(result.wasAdjusted).toBe(true)
      expect(result.moq).toBe(999999)
    })

    it('should handle floating point MOQ values by rounding up', () => {
      const product: OdooSupplierProduct = {
        id: 1,
        product_name: 'Test Product',
        min_qty: 12.7,
        price: 10.50
      }
      const requestedQuantity = 10

      const result = moqService.calculateAdjustedQuantity(product, requestedQuantity)

      expect(result.adjustedQuantity).toBe(13) // Math.ceil(12.7)
      expect(result.wasAdjusted).toBe(true)
      expect(result.moq).toBe(13)
    })

    it('should handle NaN MOQ values by defaulting to 1', () => {
      const product: OdooSupplierProduct = {
        id: 1,
        product_name: 'Test Product',
        min_qty: NaN,
        price: 10.50
      }
      const requestedQuantity = 5

      const result = moqService.calculateAdjustedQuantity(product, requestedQuantity)

      expect(result.adjustedQuantity).toBe(5)
      expect(result.wasAdjusted).toBe(false)
      expect(result.moq).toBe(1)
    })

    it('should handle Infinity MOQ values by defaulting to 1', () => {
      const product: OdooSupplierProduct = {
        id: 1,
        product_name: 'Test Product',
        min_qty: Infinity,
        price: 10.50
      }
      const requestedQuantity = 5

      const result = moqService.calculateAdjustedQuantity(product, requestedQuantity)

      expect(result.adjustedQuantity).toBe(5)
      expect(result.wasAdjusted).toBe(false)
      expect(result.moq).toBe(1)
    })
  })

  describe('performance with large datasets', () => {
    it('should handle batch processing of 1000 products efficiently', () => {
      const requests = Array.from({ length: 1000 }, (_, i) => ({
        product: {
          id: i + 1,
          product_name: `Product ${i + 1}`,
          min_qty: Math.floor(Math.random() * 48) + 12, // Random MOQ 12-60
          price: Math.random() * 100 + 1 // Random price 1-101
        } as OdooSupplierProduct,
        requestedQuantity: Math.floor(Math.random() * 30) + 1 // Random quantity 1-31
      }))

      const startTime = performance.now()
      const results = moqService.batchProcessMOQAdjustments(requests)
      const endTime = performance.now()

      expect(results).toHaveLength(1000)
      expect(endTime - startTime).toBeLessThan(100) // Should complete in under 100ms
      
      // Verify all results have required properties
      results.forEach(result => {
        expect(result).toHaveProperty('adjustedQuantity')
        expect(result).toHaveProperty('wasAdjusted')
        expect(result).toHaveProperty('originalQuantity')
        expect(result).toHaveProperty('moq')
        expect(result).toHaveProperty('costImpact')
      })
    })
  })
})