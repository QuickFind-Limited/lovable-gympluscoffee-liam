import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import OrderSummary from '@/pages/OrderSummary';

// Mock navigation
const mockNavigate = vi.fn();
vi.mock('react-router-dom', () => ({
  ...vi.importActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useLocation: () => ({ search: '?query=test' })
}));

// Mock Supabase
vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    auth: {
      signOut: vi.fn().mockResolvedValue({ error: null }),
      getUser: vi.fn().mockResolvedValue({ data: { user: { email: 'test@example.com' } } })
    },
  },
}));

// Mock hooks
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

vi.mock('@/hooks/useVectorSearch', () => ({
  useVectorSearch: vi.fn(() => ({
    searchByVendor: vi.fn(),
    setSearchQuery: vi.fn(),
    setSearchStrategy: vi.fn(),
    products: [],
    isLoading: false,
    error: null,
    performanceMetrics: null,
    trackSearchAnalytics: vi.fn(),
    getSimilarProducts: vi.fn(),
  })),
}));

vi.mock('@/hooks/useMOQLogic', () => ({
  useMOQLogic: () => ({
    processProductsWithMOQ: vi.fn((products) => ({ products, moqInfo: null })),
    isProcessing: false,
  }),
}));

// Mock sessionStorage
const mockSessionStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn()
};
Object.defineProperty(window, 'sessionStorage', {
  value: mockSessionStorage
});

describe('Vendor from First Product', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should set vendor from the first product in search results', async () => {
    // Mock search results with multiple products from different vendors
    const mockOrderData = {
      searchResults: [
        {
          id: 1,
          name: 'Product 1',
          supplier: 'Vendor ABC',  // First product's vendor
          vendor: 'Vendor ABC',
          unitPrice: '$10.00',
          quantity: 5,
          minQuantity: 1,
          image: '/test1.jpg'
        },
        {
          id: 2,
          name: 'Product 2',
          supplier: 'Vendor XYZ',  // Different vendor
          vendor: 'Vendor XYZ',
          unitPrice: '$20.00',
          quantity: 3,
          minQuantity: 1,
          image: '/test2.jpg'
        }
      ],
      parsedData: {
        products: [
          { name: 'Product 1', quantity: 5 },
          { name: 'Product 2', quantity: 3 }
        ]
      }
    };

    mockSessionStorage.getItem.mockReturnValue(JSON.stringify(mockOrderData));

    render(
      <BrowserRouter>
        <OrderSummary />
      </BrowserRouter>
    );

    // Wait for the component to process the search results
    await waitFor(() => {
      // Check that sessionStorage was called to retrieve the data
      expect(mockSessionStorage.getItem).toHaveBeenCalledWith('orderSummaryData');
    });

    // Click the Generate Purchase Order button
    const generatePOButton = await screen.findByText('📄 Generate Purchase Order');
    generatePOButton.click();

    // Wait for the PO generation process
    await waitFor(() => {
      // Check that the purchase order data was stored with the correct vendor
      const storedDataCalls = mockSessionStorage.setItem.mock.calls;
      const purchaseOrderCall = storedDataCalls.find(
        call => call[0] === 'purchaseOrderData'
      );

      expect(purchaseOrderCall).toBeDefined();
      
      const storedData = JSON.parse(purchaseOrderCall[1]);
      
      // Verify the vendor is set from the first product
      expect(storedData.supplier).toBe('Vendor ABC');
      expect(storedData.supplier).not.toBe('Vendor XYZ');
    });
  });

  it('should handle case when products have no vendor', async () => {
    // Mock search results without vendor information
    const mockOrderData = {
      searchResults: [
        {
          id: 1,
          name: 'Product 1',
          // No supplier/vendor field
          unitPrice: '$10.00',
          quantity: 5,
          minQuantity: 1,
          image: '/test1.jpg'
        }
      ],
      parsedData: {
        products: [{ name: 'Product 1', quantity: 5 }]
      }
    };

    mockSessionStorage.getItem.mockReturnValue(JSON.stringify(mockOrderData));

    render(
      <BrowserRouter>
        <OrderSummary />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(mockSessionStorage.getItem).toHaveBeenCalledWith('orderSummaryData');
    });

    const generatePOButton = await screen.findByText('📄 Generate Purchase Order');
    generatePOButton.click();

    await waitFor(() => {
      const storedDataCalls = mockSessionStorage.setItem.mock.calls;
      const purchaseOrderCall = storedDataCalls.find(
        call => call[0] === 'purchaseOrderData'
      );

      const storedData = JSON.parse(purchaseOrderCall[1]);
      
      // Should default to 'Unknown Supplier' when no vendor is present
      expect(storedData.supplier).toBe('Unknown Supplier');
    });
  });
});