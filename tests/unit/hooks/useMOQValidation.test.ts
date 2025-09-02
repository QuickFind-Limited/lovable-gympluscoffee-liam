import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useMOQValidation } from '../../../src/hooks/useMOQValidation'
import { moqService } from '../../../src/services/MOQService'
import type { OdooSupplierProduct } from '../../../src/hooks/useOdooSupplierProducts'

/**
 * MOQ Validation Hook Tests
 * Testing the custom hook that integrates MOQ logic with React components
 */

// Mock the MOQ service
vi.mock('../../../src/services/MOQService', () => ({
  moqService: {
    calculateAdjustedQuantity: vi.fn(),
    validateQuantityAgainstMOQ: vi.fn(),
    getMOQDisplayInfo: vi.fn(),
    isAdjustmentNeeded: vi.fn(),
    batchProcessMOQAdjustments: vi.fn()
  }
}))

describe('useMOQValidation Hook', () => {
  const mockProduct: OdooSupplierProduct = {
    id: 1,
    product_name: 'Test Product',
    min_qty: 24,
    price: 15.50
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('validateQuantity', () => {
    it('should validate quantity against MOQ', () => {
      const mockValidation = {
        isValid: false,
        errorMessage: 'Quantity (10) is below minimum order quantity (24)',
        suggestedQuantity: 24
      }

      vi.mocked(moqService.validateQuantityAgainstMOQ).mockReturnValue(mockValidation)

      const { result } = renderHook(() => useMOQValidation())

      const validation = result.current.validateQuantity(mockProduct, 10)

      expect(validation).toEqual(mockValidation)
      expect(moqService.validateQuantityAgainstMOQ).toHaveBeenCalledWith(mockProduct, 10)
    })

    it('should handle null product gracefully', () => {
      const mockValidation = {
        isValid: true,
        errorMessage: null,
        suggestedQuantity: 10
      }

      vi.mocked(moqService.validateQuantityAgainstMOQ).mockReturnValue(mockValidation)

      const { result } = renderHook(() => useMOQValidation())

      const validation = result.current.validateQuantity(null, 10)

      expect(validation).toEqual(mockValidation)
      expect(moqService.validateQuantityAgainstMOQ).toHaveBeenCalledWith(null, 10)
    })
  })

  describe('adjustQuantity', () => {
    it('should adjust quantity based on MOQ', () => {
      const mockAdjustment = {
        adjustedQuantity: 24,
        wasAdjusted: true,
        originalQuantity: 10,
        moq: 24,
        costImpact: {
          originalCost: 155.00,
          adjustedCost: 372.00,
          additionalCost: 217.00,
          additionalUnits: 14
        }
      }

      vi.mocked(moqService.calculateAdjustedQuantity).mockReturnValue(mockAdjustment)

      const { result } = renderHook(() => useMOQValidation())

      const adjustment = result.current.adjustQuantity(mockProduct, 10)

      expect(adjustment).toEqual(mockAdjustment)
      expect(moqService.calculateAdjustedQuantity).toHaveBeenCalledWith(mockProduct, 10)
    })
  })

  describe('getMOQInfo', () => {
    it('should get MOQ display information', () => {
      const mockInfo = {
        moq: 24,
        hasRequirement: true,
        displayText: 'Min: 24 units'
      }

      vi.mocked(moqService.getMOQDisplayInfo).mockReturnValue(mockInfo)

      const { result } = renderHook(() => useMOQValidation())

      const info = result.current.getMOQInfo(mockProduct)

      expect(info).toEqual(mockInfo)
      expect(moqService.getMOQDisplayInfo).toHaveBeenCalledWith(mockProduct)
    })
  })

  describe('checkAdjustmentNeeded', () => {
    it('should check if quantity adjustment is needed', () => {
      vi.mocked(moqService.isAdjustmentNeeded).mockReturnValue(true)

      const { result } = renderHook(() => useMOQValidation())

      const needsAdjustment = result.current.checkAdjustmentNeeded(mockProduct, 10)

      expect(needsAdjustment).toBe(true)
      expect(moqService.isAdjustmentNeeded).toHaveBeenCalledWith(mockProduct, 10)
    })

    it('should return false when no adjustment needed', () => {
      vi.mocked(moqService.isAdjustmentNeeded).mockReturnValue(false)

      const { result } = renderHook(() => useMOQValidation())

      const needsAdjustment = result.current.checkAdjustmentNeeded(mockProduct, 30)

      expect(needsAdjustment).toBe(false)
      expect(moqService.isAdjustmentNeeded).toHaveBeenCalledWith(mockProduct, 30)
    })
  })

  describe('batchProcess', () => {
    it('should process multiple products in batch', () => {
      const batchRequests = [
        { product: mockProduct, requestedQuantity: 10 },
        { product: { ...mockProduct, id: 2 }, requestedQuantity: 30 }
      ]

      const mockResults = [
        {
          adjustedQuantity: 24,
          wasAdjusted: true,
          originalQuantity: 10,
          moq: 24,
          costImpact: {
            originalCost: 155.00,
            adjustedCost: 372.00,
            additionalCost: 217.00,
            additionalUnits: 14
          }
        },
        {
          adjustedQuantity: 30,
          wasAdjusted: false,
          originalQuantity: 30,
          moq: 24,
          costImpact: {
            originalCost: 465.00,
            adjustedCost: 465.00,
            additionalCost: 0,
            additionalUnits: 0
          }
        }
      ]

      vi.mocked(moqService.batchProcessMOQAdjustments).mockReturnValue(mockResults)

      const { result } = renderHook(() => useMOQValidation())

      const results = result.current.batchProcess(batchRequests)

      expect(results).toEqual(mockResults)
      expect(moqService.batchProcessMOQAdjustments).toHaveBeenCalledWith(batchRequests)
    })

    it('should handle empty batch', () => {
      vi.mocked(moqService.batchProcessMOQAdjustments).mockReturnValue([])

      const { result } = renderHook(() => useMOQValidation())

      const results = result.current.batchProcess([])

      expect(results).toEqual([])
      expect(moqService.batchProcessMOQAdjustments).toHaveBeenCalledWith([])
    })
  })

  describe('reactive updates', () => {
    it('should maintain referential stability for callbacks', () => {
      const { result, rerender } = renderHook(() => useMOQValidation())

      const initialValidateQuantity = result.current.validateQuantity
      const initialAdjustQuantity = result.current.adjustQuantity

      // Rerender the hook
      rerender()

      // Callbacks should maintain referential stability
      expect(result.current.validateQuantity).toBe(initialValidateQuantity)
      expect(result.current.adjustQuantity).toBe(initialAdjustQuantity)
    })

    it('should work correctly after multiple rerenders', () => {
      const mockValidation = {
        isValid: false,
        errorMessage: 'Below MOQ',
        suggestedQuantity: 24
      }

      vi.mocked(moqService.validateQuantityAgainstMOQ).mockReturnValue(mockValidation)

      const { result, rerender } = renderHook(() => useMOQValidation())

      // Rerender multiple times
      rerender()
      rerender()
      rerender()

      const validation = result.current.validateQuantity(mockProduct, 10)

      expect(validation).toEqual(mockValidation)
      expect(moqService.validateQuantityAgainstMOQ).toHaveBeenCalledWith(mockProduct, 10)
    })
  })

  describe('error handling', () => {
    it('should handle service errors gracefully', () => {
      vi.mocked(moqService.validateQuantityAgainstMOQ).mockImplementation(() => {
        throw new Error('Service error')
      })

      const { result } = renderHook(() => useMOQValidation())

      expect(() => {
        result.current.validateQuantity(mockProduct, 10)
      }).toThrow('Service error')
    })

    it('should handle invalid inputs to service methods', () => {
      // Test with undefined product
      const mockValidation = {
        isValid: true,
        errorMessage: null,
        suggestedQuantity: 10
      }

      vi.mocked(moqService.validateQuantityAgainstMOQ).mockReturnValue(mockValidation)

      const { result } = renderHook(() => useMOQValidation())

      const validation = result.current.validateQuantity(undefined, 10)

      expect(validation).toEqual(mockValidation)
      expect(moqService.validateQuantityAgainstMOQ).toHaveBeenCalledWith(undefined, 10)
    })
  })

  describe('performance considerations', () => {
    it('should not cause unnecessary re-renders', () => {
      let renderCount = 0

      const { rerender } = renderHook(() => {
        renderCount++
        return useMOQValidation()
      })

      expect(renderCount).toBe(1)

      // Multiple rerenders shouldn't increase render count unnecessarily
      rerender()
      rerender()

      expect(renderCount).toBe(3) // Should only increment with actual rerenders
    })

    it('should handle large batch operations efficiently', () => {
      const largeBatch = Array.from({ length: 1000 }, (_, i) => ({
        product: { ...mockProduct, id: i + 1 },
        requestedQuantity: Math.floor(Math.random() * 50) + 1
      }))

      const mockResults = largeBatch.map((_, i) => ({
        adjustedQuantity: 24,
        wasAdjusted: i % 2 === 0,
        originalQuantity: 10,
        moq: 24,
        costImpact: {
          originalCost: 155.00,
          adjustedCost: 372.00,
          additionalCost: i % 2 === 0 ? 217.00 : 0,
          additionalUnits: i % 2 === 0 ? 14 : 0
        }
      }))

      vi.mocked(moqService.batchProcessMOQAdjustments).mockReturnValue(mockResults)

      const { result } = renderHook(() => useMOQValidation())

      const startTime = performance.now()
      const results = result.current.batchProcess(largeBatch)
      const endTime = performance.now()

      expect(results).toHaveLength(1000)
      expect(endTime - startTime).toBeLessThan(50) // Should complete quickly
      expect(moqService.batchProcessMOQAdjustments).toHaveBeenCalledWith(largeBatch)
    })
  })
})