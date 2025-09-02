import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { MOQFeedback } from '../../../src/components/orders/MOQFeedback'
import type { OdooSupplierProduct } from '../../../src/hooks/useOdooSupplierProducts'

/**
 * MOQ Feedback Component Tests
 * Testing UI feedback when quantities are adjusted due to MOQ requirements
 */

describe('MOQFeedback Component', () => {
  const mockProduct: OdooSupplierProduct = {
    id: 1,
    product_name: 'Test Product',
    min_qty: 24,
    price: 15.50
  }

  const defaultProps = {
    product: mockProduct,
    requestedQuantity: 10,
    onQuantityChange: vi.fn(),
    onAcceptAdjustment: vi.fn()
  }

  describe('renders correctly', () => {
    it('should display MOQ warning when quantity is below minimum', () => {
      render(<MOQFeedback {...defaultProps} />)

      expect(screen.getByText('Below Minimum Order Quantity')).toBeInTheDocument()
      expect(screen.getByText(/Requested: 10 units/)).toBeInTheDocument()
      expect(screen.getByText(/Minimum required: 24 units/)).toBeInTheDocument()
    })

    it('should show cost impact of MOQ adjustment', () => {
      render(<MOQFeedback {...defaultProps} />)

      expect(screen.getByText(/Additional cost:/)).toBeInTheDocument()
      expect(screen.getByText(/\$217\.00/)).toBeInTheDocument() // (24-10) * 15.50
      expect(screen.getByText(/14 extra units/)).toBeInTheDocument()
    })

    it('should display accept adjustment button', () => {
      render(<MOQFeedback {...defaultProps} />)

      const acceptButton = screen.getByRole('button', { name: /Accept MOQ Adjustment/i })
      expect(acceptButton).toBeInTheDocument()
    })

    it('should display manual adjustment input', () => {
      render(<MOQFeedback {...defaultProps} />)

      const quantityInput = screen.getByDisplayValue('10')
      expect(quantityInput).toBeInTheDocument()
      expect(quantityInput).toHaveAttribute('min', '24')
    })
  })

  describe('user interactions', () => {
    it('should call onAcceptAdjustment when accept button is clicked', () => {
      const mockOnAcceptAdjustment = vi.fn()
      render(
        <MOQFeedback 
          {...defaultProps} 
          onAcceptAdjustment={mockOnAcceptAdjustment}
        />
      )

      const acceptButton = screen.getByRole('button', { name: /Accept MOQ Adjustment/i })
      fireEvent.click(acceptButton)

      expect(mockOnAcceptAdjustment).toHaveBeenCalledWith(24) // MOQ value
    })

    it('should call onQuantityChange when input value changes', () => {
      const mockOnQuantityChange = vi.fn()
      render(
        <MOQFeedback 
          {...defaultProps} 
          onQuantityChange={mockOnQuantityChange}
        />
      )

      const quantityInput = screen.getByDisplayValue('10')
      fireEvent.change(quantityInput, { target: { value: '30' } })

      expect(mockOnQuantityChange).toHaveBeenCalledWith(30)
    })

    it('should prevent input values below MOQ', () => {
      const mockOnQuantityChange = vi.fn()
      render(
        <MOQFeedback 
          {...defaultProps} 
          onQuantityChange={mockOnQuantityChange}
        />
      )

      const quantityInput = screen.getByDisplayValue('10')
      fireEvent.change(quantityInput, { target: { value: '20' } }) // Below MOQ of 24

      // Should either prevent the change or show validation error
      expect(screen.getByText(/Minimum required: 24 units/)).toBeInTheDocument()
    })

    it('should update cost calculation when quantity changes', () => {
      const { rerender } = render(<MOQFeedback {...defaultProps} />)

      // Initial cost display
      expect(screen.getByText(/\$217\.00/)).toBeInTheDocument()

      // Rerender with new quantity
      rerender(
        <MOQFeedback 
          {...defaultProps} 
          requestedQuantity={30} // Above MOQ, so no adjustment needed
        />
      )

      // Should show no additional cost
      expect(screen.queryByText(/Additional cost:/)).not.toBeInTheDocument()
    })
  })

  describe('different MOQ scenarios', () => {
    it('should not render when quantity meets MOQ', () => {
      const { container } = render(
        <MOQFeedback 
          {...defaultProps} 
          requestedQuantity={30} // Above MOQ of 24
        />
      )

      expect(container.firstChild).toBeNull()
    })

    it('should handle products without MOQ', () => {
      const productWithoutMOQ: OdooSupplierProduct = {
        id: 1,
        product_name: 'Flexible Product',
        price: 10.00
        // No min_qty specified
      }

      const { container } = render(
        <MOQFeedback 
          {...defaultProps} 
          product={productWithoutMOQ}
          requestedQuantity={5}
        />
      )

      expect(container.firstChild).toBeNull()
    })

    it('should handle zero MOQ by treating as no requirement', () => {
      const productWithZeroMOQ: OdooSupplierProduct = {
        id: 1,
        product_name: 'No Minimum Product',
        min_qty: 0,
        price: 10.00
      }

      const { container } = render(
        <MOQFeedback 
          {...defaultProps} 
          product={productWithZeroMOQ}
          requestedQuantity={5}
        />
      )

      expect(container.firstChild).toBeNull()
    })

    it('should display different styling for high cost impact', () => {
      const expensiveProduct: OdooSupplierProduct = {
        id: 1,
        product_name: 'Expensive Product',
        min_qty: 50,
        price: 100.00
      }

      render(
        <MOQFeedback 
          {...defaultProps} 
          product={expensiveProduct}
          requestedQuantity={10} // Need 40 extra units at $100 each = $4000 additional
        />
      )

      expect(screen.getByText(/\$4,000\.00/)).toBeInTheDocument()
      
      // Should show warning styling for high cost impact
      const costElement = screen.getByText(/Additional cost:/)
      expect(costElement.closest('div')).toHaveClass('text-red-600') // Or similar warning class
    })
  })

  describe('accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<MOQFeedback {...defaultProps} />)

      const quantityInput = screen.getByDisplayValue('10')
      expect(quantityInput).toHaveAttribute('aria-label', 'Adjust quantity to meet minimum order requirement')

      const acceptButton = screen.getByRole('button', { name: /Accept MOQ Adjustment/i })
      expect(acceptButton).toHaveAttribute('aria-describedby')
    })

    it('should announce changes to screen readers', () => {
      render(<MOQFeedback {...defaultProps} />)

      const announcement = screen.getByRole('status')
      expect(announcement).toHaveTextContent(/Quantity below minimum.*Additional cost.*\$217\.00/)
    })

    it('should support keyboard navigation', () => {
      render(<MOQFeedback {...defaultProps} />)

      const quantityInput = screen.getByDisplayValue('10')
      const acceptButton = screen.getByRole('button', { name: /Accept MOQ Adjustment/i })

      // Both elements should be focusable
      expect(quantityInput).toHaveAttribute('tabindex', '0')
      expect(acceptButton).toHaveAttribute('tabindex', '0')
    })
  })

  describe('error handling', () => {
    it('should handle null product gracefully', () => {
      const { container } = render(
        <MOQFeedback 
          {...defaultProps} 
          product={null}
        />
      )

      expect(container.firstChild).toBeNull()
    })

    it('should handle undefined product gracefully', () => {
      const { container } = render(
        <MOQFeedback 
          {...defaultProps} 
          product={undefined}
        />
      )

      expect(container.firstChild).toBeNull()
    })

    it('should handle invalid quantity values', () => {
      render(
        <MOQFeedback 
          {...defaultProps} 
          requestedQuantity={-5} // Invalid negative quantity
        />
      )

      // Should still render with adjusted calculations
      expect(screen.getByText('Below Minimum Order Quantity')).toBeInTheDocument()
      expect(screen.getByText(/Minimum required: 24 units/)).toBeInTheDocument()
    })

    it('should handle missing price gracefully', () => {
      const productWithoutPrice: OdooSupplierProduct = {
        id: 1,
        product_name: 'Product Without Price',
        min_qty: 24
        // No price specified
      }

      render(
        <MOQFeedback 
          {...defaultProps} 
          product={productWithoutPrice}
        />
      )

      // Should show MOQ requirement but cost should be $0
      expect(screen.getByText('Below Minimum Order Quantity')).toBeInTheDocument()
      expect(screen.getByText(/Additional cost:.*\$0\.00/)).toBeInTheDocument()
    })
  })

  describe('responsive design', () => {
    it('should adapt layout for mobile screens', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375
      })

      render(<MOQFeedback {...defaultProps} />)

      const container = screen.getByText('Below Minimum Order Quantity').closest('div')
      expect(container).toHaveClass('flex-col') // Should stack vertically on mobile
    })

    it('should maintain functionality on different screen sizes', () => {
      // Test desktop layout
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1024
      })

      const { rerender } = render(<MOQFeedback {...defaultProps} />)

      const acceptButton = screen.getByRole('button', { name: /Accept MOQ Adjustment/i })
      expect(acceptButton).toBeInTheDocument()

      // Switch to mobile
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375
      })

      rerender(<MOQFeedback {...defaultProps} />)

      // Button should still be present and functional
      const mobileAcceptButton = screen.getByRole('button', { name: /Accept MOQ Adjustment/i })
      expect(mobileAcceptButton).toBeInTheDocument()
    })
  })
})