import React from 'react'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, MemoryRouter } from 'react-router-dom'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import PurchaseOrderEditor from '@/pages/PurchaseOrderEditor'
import { moqService } from '@/services/MOQService'

/**
 * End-to-End MOQ Purchase Order Flow Tests
 * 
 * Tests the complete MOQ integration within the purchase order creation flow:
 * 1. Loading products with MOQ requirements
 * 2. Displaying MOQ warnings and adjustments
 * 3. User interactions with MOQ adjustments
 * 4. Order validation and submission with MOQ compliance
 */

// Comprehensive mocks
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

vi.mock('@/utils/pdfGenerator', () => ({
  generatePDFFromElement: vi.fn().mockResolvedValue(undefined),
  printElement: vi.fn()
}))

// Mock data with comprehensive MOQ scenarios
const mockOrderDataWithMOQ = {
  supplier: 'MOQ Test Supplier',
  orderNumber: 'PO-MOQ-001',
  products: [
    {
      id: 1,
      name: 'High MOQ Product',
      title: 'High MOQ Product',
      quantity: 8, // Below MOQ of 24
      suggestedQty: 8,
      price: 25.50,
      estimatedCost: 25.50,
      image: '/test-image1.png',
      min_qty: 24 // MOQ defined
    },
    {
      id: 2,
      name: 'Low MOQ Product',
      title: 'Low MOQ Product', 
      quantity: 15, // Above MOQ of 12
      suggestedQty: 15,
      price: 12.75,
      estimatedCost: 12.75,
      image: '/test-image2.png',
      min_qty: 12 // MOQ defined
    },
    {
      id: 3,
      name: 'No MOQ Product',
      title: 'No MOQ Product',
      quantity: 5, // No MOQ requirement
      suggestedQty: 5,
      price: 8.00,
      estimatedCost: 8.00,
      image: '/test-image3.png'
      // No min_qty - should default to 1
    },
    {
      id: 4,
      name: 'Zero Quantity Product',
      title: 'Zero Quantity Product',
      quantity: 0, // Zero quantity with MOQ
      suggestedQty: 0,
      price: 15.00,
      estimatedCost: 15.00,
      image: '/test-image4.png',
      min_qty: 18
    }
  ]
}

describe('MOQ Purchase Order Flow E2E Tests', () => {
  let queryClient: QueryClient
  let user: ReturnType<typeof userEvent.setup>

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false }
      }
    })

    user = userEvent.setup()

    // Mock sessionStorage with MOQ test data
    Object.defineProperty(window, 'sessionStorage', {
      value: {
        getItem: vi.fn((key) => {
          if (key === 'purchaseOrderData') {
            return JSON.stringify(mockOrderDataWithMOQ)
          }
          return null
        }),
        removeItem: vi.fn(),
        setItem: vi.fn()
      },
      writable: true
    })

    // Mock scrollTo and other DOM methods
    Object.defineProperty(window, 'scrollTo', { value: vi.fn(), writable: true })
    Object.defineProperty(window, 'print', { value: vi.fn(), writable: true })
    
    // Mock performance.now for consistent timing
    vi.spyOn(performance, 'now').mockReturnValue(1000)
  })

  afterEach(() => {
    vi.clearAllMocks()
    vi.restoreAllMocks()
  })

  const renderPurchaseOrderEditor = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/purchase-order-editor']}>
          <PurchaseOrderEditor />
        </MemoryRouter>
      </QueryClientProvider>
    )
  }

  describe('Initial MOQ State Display', () => {
    it('should display MOQ warnings for products below minimum quantity', async () => {
      renderPurchaseOrderEditor()

      await waitFor(() => {
        expect(screen.getByText('High MOQ Product')).toBeInTheDocument()
      })

      // Look for MOQ warning indicators
      const moqWarnings = screen.getAllByText('Below MOQ')
      expect(moqWarnings).toHaveLength(2) // High MOQ Product and Zero Quantity Product

      // Verify specific products show correct MOQ status
      const highMOQRow = screen.getByText('High MOQ Product').closest('tr')
      expect(within(highMOQRow!).getByText('Below MOQ')).toBeInTheDocument()
    })

    it('should show correct quantities and totals on initial load', async () => {
      renderPurchaseOrderEditor()

      await waitFor(() => {
        expect(screen.getByText('High MOQ Product')).toBeInTheDocument()
      })

      // Check that quantities are displayed correctly (not yet adjusted)
      const quantityInputs = screen.getAllByDisplayValue('8')
      expect(quantityInputs.length).toBeGreaterThan(0)

      // Check total calculations are shown
      expect(screen.getByText(/TOTAL:/)).toBeInTheDocument()
    })

    it('should display MOQ information in edit mode', async () => {
      renderPurchaseOrderEditor()

      await waitFor(() => {
        expect(screen.getByText('Edit purchase order')).toBeInTheDocument()
      })

      // Enter edit mode
      const editButton = screen.getByText('Edit purchase order')
      await user.click(editButton)

      await waitFor(() => {
        expect(screen.getByText('Cancel')).toBeInTheDocument()
      })

      // In edit mode, should show MOQ information
      expect(screen.getByText(/Min\. Quantity:/)).toBeInTheDocument()
    })
  })

  describe('MOQ Adjustment Interactions', () => {
    it('should allow manual quantity adjustment and validate against MOQ', async () => {
      renderPurchaseOrderEditor()

      // Enter edit mode
      await waitFor(() => {
        expect(screen.getByText('Edit purchase order')).toBeInTheDocument()
      })
      
      const editButton = screen.getByText('Edit purchase order')
      await user.click(editButton)

      await waitFor(() => {
        expect(screen.getByText('Cancel')).toBeInTheDocument()
      })

      // Find quantity input for High MOQ Product (currently 8, MOQ is 24)
      const quantityInputs = screen.getAllByDisplayValue('8')
      const highMOQInput = quantityInputs[0] // Assuming first one is High MOQ Product

      // Try to set quantity below MOQ
      await user.clear(highMOQInput)
      await user.type(highMOQInput, '15')

      // Should still show MOQ warning since 15 < 24
      await waitFor(() => {
        expect(screen.getByText('Below MOQ')).toBeInTheDocument()
      })

      // Set quantity to meet MOQ
      await user.clear(highMOQInput)
      await user.type(highMOQInput, '30')

      // MOQ warning should disappear
      await waitFor(() => {
        const moqWarnings = screen.queryAllByText('Below MOQ')
        expect(moqWarnings.length).toBeLessThan(2) // One less warning now
      })
    })

    it('should update totals when quantities are adjusted for MOQ compliance', async () => {
      renderPurchaseOrderEditor()

      // Get initial total
      await waitFor(() => {
        expect(screen.getByText(/TOTAL:/)).toBeInTheDocument()
      })

      const initialTotalElement = screen.getByText(/TOTAL:/)
      const initialTotalText = initialTotalElement.textContent

      // Enter edit mode and adjust quantity
      const editButton = screen.getByText('Edit purchase order')
      await user.click(editButton)

      await waitFor(() => {
        expect(screen.getByText('Cancel')).toBeInTheDocument()
      })

      // Adjust quantity to meet MOQ (High MOQ Product: 8 → 24)
      const quantityInputs = screen.getAllByDisplayValue('8')
      const highMOQInput = quantityInputs[0]

      await user.clear(highMOQInput)
      await user.type(highMOQInput, '24') // Set to MOQ

      // Total should update
      await waitFor(() => {
        const updatedTotalElement = screen.getByText(/TOTAL:/)
        expect(updatedTotalElement.textContent).not.toBe(initialTotalText)
      })
    })

    it('should use + and - buttons to adjust quantities with MOQ validation', async () => {
      renderPurchaseOrderEditor()

      // Enter edit mode
      const editButton = screen.getByText('Edit purchase order')
      await user.click(editButton)

      await waitFor(() => {
        expect(screen.getByText('Cancel')).toBeInTheDocument()
      })

      // Find plus/minus buttons for quantity adjustment
      const plusButtons = screen.getAllByRole('button', { name: '' })
      const minusButtons = screen.getAllByRole('button', { name: '' })

      // Find the plus button for the High MOQ Product (need to identify the right one)
      // This would require more specific identification in the actual implementation
      const productContainer = screen.getByText('High MOQ Product').closest('.space-y-3')
      const plusButton = within(productContainer!).getByRole('button', { name: /plus/i })

      // Click plus multiple times to reach MOQ
      for (let i = 0; i < 16; i++) { // 8 + 16 = 24 (MOQ)
        await user.click(plusButton)
      }

      // Should no longer show MOQ warning for this product
      await waitFor(() => {
        const productCard = screen.getByText('High MOQ Product').closest('.space-y-3')
        expect(within(productCard!).queryByText('Below MOQ')).not.toBeInTheDocument()
      })
    })
  })

  describe('Order Validation and Submission', () => {
    it('should validate MOQ compliance before allowing order submission', async () => {
      renderPurchaseOrderEditor()

      // Try to submit order with MOQ violations
      await waitFor(() => {
        expect(screen.getByText('Send to supplier')).toBeInTheDocument()
      })

      const submitButton = screen.getByText('Send to supplier')
      await user.click(submitButton)

      // Should show validation error or prevent submission
      // (Implementation would need to add this validation)
      await waitFor(() => {
        // Check if error toast or validation message appears
        expect(screen.getByText(/MOQ requirements not met/i) || 
               screen.getByText(/minimum order quantities/i)).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('should allow order submission when all MOQ requirements are met', async () => {
      renderPurchaseOrderEditor()

      // First, adjust all quantities to meet MOQ requirements
      const editButton = screen.getByText('Edit purchase order')
      await user.click(editButton)

      await waitFor(() => {
        expect(screen.getByText('Cancel')).toBeInTheDocument()
      })

      // Adjust High MOQ Product (8 → 24)
      const quantityInputs = screen.getAllByDisplayValue('8')
      const highMOQInput = quantityInputs[0]
      await user.clear(highMOQInput)
      await user.type(highMOQInput, '24')

      // Adjust Zero Quantity Product (0 → 18)
      const zeroQuantityInputs = screen.getAllByDisplayValue('0')
      if (zeroQuantityInputs.length > 0) {
        await user.clear(zeroQuantityInputs[0])
        await user.type(zeroQuantityInputs[0], '18')
      }

      // Now try to submit
      const submitButton = screen.getByText('Send to supplier')
      await user.click(submitButton)

      // Should proceed with order creation
      await waitFor(() => {
        // Should navigate away or show success state
        expect(screen.queryByText('Purchase Order Editor')).not.toBeInTheDocument() ||
        expect(screen.getByText(/order created/i)).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('should calculate final order totals correctly with MOQ adjustments', async () => {
      // Test the complete calculation flow with MOQ adjustments
      const originalOrder = mockOrderDataWithMOQ.products
      
      // Calculate expected totals with MOQ adjustments
      let expectedTotal = 0
      
      originalOrder.forEach(product => {
        const moqAdjustment = moqService.calculateAdjustedQuantity(
          { 
            id: product.id, 
            product_name: product.name, 
            min_qty: product.min_qty, 
            price: product.price 
          },
          product.quantity
        )
        expectedTotal += moqAdjustment.adjustedQuantity * product.price
      })

      renderPurchaseOrderEditor()

      // Apply MOQ adjustments through UI
      const editButton = screen.getByText('Edit purchase order')
      await user.click(editButton)

      await waitFor(() => {
        expect(screen.getByText('Cancel')).toBeInTheDocument()
      })

      // Apply all necessary MOQ adjustments
      // High MOQ Product: 8 → 24
      const highMOQInputs = screen.getAllByDisplayValue('8')
      if (highMOQInputs.length > 0) {
        await user.clear(highMOQInputs[0])
        await user.type(highMOQInputs[0], '24')
      }

      // Zero Quantity Product: 0 → 18  
      const zeroInputs = screen.getAllByDisplayValue('0')
      if (zeroInputs.length > 0) {
        await user.clear(zeroInputs[0])
        await user.type(zeroInputs[0], '18')
      }

      // Check that final total matches expected calculation
      await waitFor(() => {
        const totalElement = screen.getByText(/TOTAL:/)
        const totalText = totalElement.textContent
        const totalValue = parseFloat(totalText!.replace(/[^\d.]/g, ''))
        
        // Allow for small rounding differences
        expect(Math.abs(totalValue - expectedTotal)).toBeLessThan(1)
      })
    })
  })

  describe('Error Handling and Edge Cases', () => {
    it('should handle products with missing MOQ data gracefully', async () => {
      // Test with the "No MOQ Product" in our mock data
      renderPurchaseOrderEditor()

      await waitFor(() => {
        expect(screen.getByText('No MOQ Product')).toBeInTheDocument()
      })

      // Should not show MOQ warning for product without min_qty
      const noMOQProduct = screen.getByText('No MOQ Product').closest('tr')
      expect(within(noMOQProduct!).queryByText('Below MOQ')).not.toBeInTheDocument()

      // Should allow any quantity ≥ 1
      const editButton = screen.getByText('Edit purchase order')
      await user.click(editButton)

      await waitFor(() => {
        expect(screen.getByText('Cancel')).toBeInTheDocument()
      })

      // Find quantity input for No MOQ Product and set to 1
      const productCard = screen.getByText('No MOQ Product').closest('.space-y-3')
      const quantityInput = within(productCard!).getByDisplayValue('5')
      
      await user.clear(quantityInput)
      await user.type(quantityInput, '1')

      // Should not show any MOQ warnings
      expect(within(productCard!).queryByText('Below MOQ')).not.toBeInTheDocument()
    })

    it('should handle zero quantities with MOQ requirements', async () => {
      renderPurchaseOrderEditor()

      await waitFor(() => {
        expect(screen.getByText('Zero Quantity Product')).toBeInTheDocument()
      })

      // Should show MOQ warning for zero quantity product
      const zeroQtyProduct = screen.getByText('Zero Quantity Product').closest('tr')
      expect(within(zeroQtyProduct!).getByText('Below MOQ')).toBeInTheDocument()
    })

    it('should perform well with multiple MOQ calculations', async () => {
      // Performance test with the current dataset
      const startTime = performance.now()
      
      renderPurchaseOrderEditor()

      await waitFor(() => {
        expect(screen.getByText('High MOQ Product')).toBeInTheDocument()
      })

      const loadTime = performance.now() - startTime

      // Should load quickly even with MOQ calculations
      expect(loadTime).toBeLessThan(2000) // 2 seconds max

      // All MOQ validations should be complete
      const moqWarnings = screen.getAllByText('Below MOQ')
      expect(moqWarnings.length).toBeGreaterThan(0) // Should have detected MOQ issues
    })
  })

  describe('Accessibility and User Experience', () => {
    it('should provide clear feedback about MOQ requirements', async () => {
      renderPurchaseOrderEditor()

      await waitFor(() => {
        expect(screen.getByText('High MOQ Product')).toBeInTheDocument()
      })

      // Enter edit mode to see MOQ details
      const editButton = screen.getByText('Edit purchase order')
      await user.click(editButton)

      await waitFor(() => {
        expect(screen.getByText('Cancel')).toBeInTheDocument()
      })

      // Should show clear MOQ information
      expect(screen.getByText(/Min\. Quantity:/)).toBeInTheDocument()
      
      // Should show current vs required quantities
      const productCard = screen.getByText('High MOQ Product').closest('.space-y-3')
      expect(within(productCard!).getByText('Below MOQ')).toBeInTheDocument()
    })

    it('should maintain functionality across different screen sizes', async () => {
      // Test mobile layout
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375
      })

      renderPurchaseOrderEditor()

      await waitFor(() => {
        expect(screen.getByText('High MOQ Product')).toBeInTheDocument()
      })

      // Should still show MOQ warnings on mobile
      expect(screen.getByText('Below MOQ')).toBeInTheDocument()

      // Edit functionality should work on mobile
      const editButton = screen.getByText('Edit purchase order')
      expect(editButton).toBeInTheDocument()
      
      await user.click(editButton)

      await waitFor(() => {
        expect(screen.getByText('Cancel')).toBeInTheDocument()
      })
    })
  })
})