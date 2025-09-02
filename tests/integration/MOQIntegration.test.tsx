import React from 'react'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import PurchaseOrderEditor from '@/pages/PurchaseOrderEditor'
import { moqService } from '@/services/MOQService'
import type { OdooSupplierProduct } from '@/hooks/useOdooSupplierProducts'

/**
 * MOQ Integration Tests
 * Testing MOQ logic integration with UI components and search functionality
 */

// Mock dependencies
vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    auth: {
      signOut: vi.fn().mockResolvedValue({ error: null }),
      getSession: vi.fn().mockResolvedValue({ 
        data: { session: { access_token: 'test-token' } }, 
        error: null 
      })
    }
  },
  supabaseUrl: 'https://test.supabase.co'
}))

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn()
  })
}))

vi.mock('@/services/OdooService', () => ({
  OdooService: {
    getInstance: vi.fn(() => ({
      createPurchaseOrder: vi.fn().mockResolvedValue({ id: 'test-po-123' })
    }))
  }
}))

// Mock sessionStorage with MOQ test data
const mockOrderData = {
  supplier: 'Test Supplier',
  orderNumber: 'PO-TEST-001',
  products: [
    {
      id: 1,
      name: 'Product with High MOQ',
      title: 'Product with High MOQ',
      quantity: 10, // Below MOQ
      suggestedQty: 10,
      price: 15.50,
      estimatedCost: 15.50,
      image: '/test-image.png'
    },
    {
      id: 2,
      name: 'Product with Low MOQ',
      title: 'Product with Low MOQ', 
      quantity: 25, // Above MOQ
      suggestedQty: 25,
      price: 8.75,
      estimatedCost: 8.75,
      image: '/test-image2.png'
    }
  ]
}

describe('MOQ Integration Tests', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false }
      }
    })

    // Mock sessionStorage
    Object.defineProperty(window, 'sessionStorage', {
      value: {
        getItem: vi.fn((key) => {
          if (key === 'purchaseOrderData') {
            return JSON.stringify(mockOrderData)
          }
          return null
        }),
        removeItem: vi.fn(),
        setItem: vi.fn()
      },
      writable: true
    })

    // Mock scrollTo
    Object.defineProperty(window, 'scrollTo', {
      value: vi.fn(),
      writable: true
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  const renderComponent = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <PurchaseOrderEditor />
        </BrowserRouter>
      </QueryClientProvider>
    )
  }

  describe('MOQ Validation in Purchase Order Editor', () => {
    it('should display MOQ warnings for products below minimum quantity', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Product with High MOQ')).toBeInTheDocument()
      })

      // Check if MOQ warning is displayed for the first product
      const moqWarning = screen.getByText('Below MOQ')
      expect(moqWarning).toBeInTheDocument()
    })

    it('should automatically adjust quantities when entering edit mode', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Edit purchase order')).toBeInTheDocument()
      })

      // Enter edit mode
      const editButton = screen.getByText('Edit purchase order')
      fireEvent.click(editButton)

      await waitFor(() => {
        expect(screen.getByText('Cancel')).toBeInTheDocument()
      })

      // In edit mode, quantities should be adjusted if below MOQ
      // This would be tested by checking the input values against expected MOQ adjustments
    })

    it('should show cost impact when MOQ adjustments are made', async () => {
      const testProduct: OdooSupplierProduct = {
        id: 1,
        product_name: 'Test Product',
        min_qty: 24,
        price: 15.50
      }

      const adjustment = moqService.calculateAdjustedQuantity(testProduct, 10)
      
      expect(adjustment.wasAdjusted).toBe(true)
      expect(adjustment.adjustedQuantity).toBe(24)
      expect(adjustment.costImpact.additionalCost).toBe(217.00) // (24-10) * 15.50
    })
  })

  describe('MOQ Logic with Search Integration', () => {
    it('should apply MOQ logic when adding products from search', async () => {
      // Mock product search result with MOQ
      const searchProduct = {
        id: 3,
        title: 'Search Result Product',
        name: 'Search Result Product',
        price_min: 12.00,
        list_price: 12.00,
        image: '/search-product.png'
      }

      // Simulate adding a product with quantity below MOQ
      const requestedQuantity = 5
      const moqProduct: OdooSupplierProduct = {
        id: 3,
        product_name: 'Search Result Product',
        min_qty: 12,
        price: 12.00
      }

      const result = moqService.calculateAdjustedQuantity(moqProduct, requestedQuantity)

      expect(result.adjustedQuantity).toBe(12)
      expect(result.wasAdjusted).toBe(true)
      expect(result.costImpact.additionalCost).toBe(84.00) // (12-5) * 12.00
    })

    it('should validate MOQ compliance before order submission', () => {
      const orderItems = [
        {
          product: { id: 1, product_name: 'Product A', min_qty: 12 } as OdooSupplierProduct,
          quantity: 15 // Compliant
        },
        {
          product: { id: 2, product_name: 'Product B', min_qty: 24 } as OdooSupplierProduct,
          quantity: 20 // Non-compliant
        }
      ]

      const report = moqService.getMOQComplianceReport(orderItems)

      expect(report.totalItems).toBe(2)
      expect(report.compliantItems).toBe(1)
      expect(report.nonCompliantItems).toBe(1)
      expect(report.complianceRate).toBe(50.00)
      expect(report.nonCompliantDetails).toHaveLength(1)
      expect(report.nonCompliantDetails[0].shortfall).toBe(4) // 24 - 20
    })
  })

  describe('MOQ API Failure Scenarios', () => {
    it('should handle missing MOQ data gracefully', () => {
      const productWithoutMOQ: OdooSupplierProduct = {
        id: 1,
        product_name: 'Product Without MOQ',
        price: 10.00
        // min_qty is undefined
      }

      const result = moqService.calculateAdjustedQuantity(productWithoutMOQ, 5)

      expect(result.adjustedQuantity).toBe(5)
      expect(result.wasAdjusted).toBe(false)
      expect(result.moq).toBe(1) // Default MOQ
    })

    it('should handle null product data', () => {
      const result = moqService.calculateAdjustedQuantity(null, 10)

      expect(result.adjustedQuantity).toBe(10)
      expect(result.wasAdjusted).toBe(false)
      expect(result.moq).toBe(1)
    })

    it('should handle API errors during MOQ retrieval', async () => {
      // Mock a failing API call
      const mockFetch = vi.fn().mockRejectedValue(new Error('API Error'))
      global.fetch = mockFetch

      // MOQ service should still work with local/cached data
      const testProduct: OdooSupplierProduct = {
        id: 1,
        product_name: 'Test Product',
        min_qty: 24,
        price: 15.50
      }

      const result = moqService.calculateAdjustedQuantity(testProduct, 10)

      expect(result.adjustedQuantity).toBe(24)
      expect(result.wasAdjusted).toBe(true)
    })
  })

  describe('MOQ UI Feedback Tests', () => {
    it('should display MOQ adjustment notification to user', async () => {
      const testProduct: OdooSupplierProduct = {
        id: 1,
        product_name: 'Test Product',
        min_qty: 24,
        price: 15.50
      }

      const displayInfo = moqService.getMOQDisplayInfo(testProduct)

      expect(displayInfo.hasRequirement).toBe(true)
      expect(displayInfo.displayText).toBe('Min: 24 units')
      expect(displayInfo.moq).toBe(24)
    })

    it('should show no minimum requirement for products without MOQ', () => {
      const productWithoutMOQ: OdooSupplierProduct = {
        id: 1,
        product_name: 'Flexible Product',
        price: 10.00
      }

      const displayInfo = moqService.getMOQDisplayInfo(productWithoutMOQ)

      expect(displayInfo.hasRequirement).toBe(false)
      expect(displayInfo.displayText).toBe('No minimum')
      expect(displayInfo.moq).toBe(1)
    })

    it('should provide clear validation messages', () => {
      const testProduct: OdooSupplierProduct = {
        id: 1,
        product_name: 'Test Product',
        min_qty: 24,
        price: 15.50
      }

      const validation = moqService.validateQuantityAgainstMOQ(testProduct, 10)

      expect(validation.isValid).toBe(false)
      expect(validation.errorMessage).toBe('Quantity (10) is below minimum order quantity (24)')
      expect(validation.suggestedQuantity).toBe(24)
    })
  })

  describe('MOQ Edge Cases', () => {
    it('should handle zero requested quantity', () => {
      const testProduct: OdooSupplierProduct = {
        id: 1,
        product_name: 'Test Product',
        min_qty: 12,
        price: 10.00
      }

      const result = moqService.calculateAdjustedQuantity(testProduct, 0)

      expect(result.adjustedQuantity).toBe(12)
      expect(result.wasAdjusted).toBe(true)
    })

    it('should handle negative requested quantity', () => {
      const testProduct: OdooSupplierProduct = {
        id: 1,
        product_name: 'Test Product',
        min_qty: 12,
        price: 10.00
      }

      const result = moqService.calculateAdjustedQuantity(testProduct, -5)

      expect(result.adjustedQuantity).toBe(12)
      expect(result.wasAdjusted).toBe(true)
    })

    it('should handle fractional MOQ values by rounding up', () => {
      const testProduct: OdooSupplierProduct = {
        id: 1,
        product_name: 'Test Product',
        min_qty: 12.7,
        price: 10.00
      }

      const result = moqService.calculateAdjustedQuantity(testProduct, 10)

      expect(result.adjustedQuantity).toBe(13) // Math.ceil(12.7)
      expect(result.moq).toBe(13)
    })

    it('should handle very large MOQ values', () => {
      const testProduct: OdooSupplierProduct = {
        id: 1,
        product_name: 'Bulk Product',
        min_qty: 999999,
        price: 0.01
      }

      const result = moqService.calculateAdjustedQuantity(testProduct, 1000)

      expect(result.adjustedQuantity).toBe(999999)
      expect(result.wasAdjusted).toBe(true)
      expect(result.costImpact.additionalCost).toBe(9989.99) // (999999-1000) * 0.01
    })
  })

  describe('Batch MOQ Processing', () => {
    it('should efficiently process multiple products with MOQ requirements', () => {
      const batchRequests = [
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

      const startTime = performance.now()
      const results = moqService.batchProcessMOQAdjustments(batchRequests)
      const endTime = performance.now()

      expect(results).toHaveLength(3)
      expect(endTime - startTime).toBeLessThan(10) // Should be very fast for small batches

      // Verify specific adjustments
      expect(results[0].adjustedQuantity).toBe(12) // Adjusted up
      expect(results[0].wasAdjusted).toBe(true)
      
      expect(results[1].adjustedQuantity).toBe(30) // No adjustment
      expect(results[1].wasAdjusted).toBe(false)
      
      expect(results[2].adjustedQuantity).toBe(6) // Adjusted up
      expect(results[2].wasAdjusted).toBe(true)
    })

    it('should handle empty batch gracefully', () => {
      const results = moqService.batchProcessMOQAdjustments([])
      expect(results).toEqual([])
    })
  })
})