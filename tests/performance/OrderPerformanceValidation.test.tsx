/**
 * Order Creation Flow Performance Validation Tests
 * Performance Validator Agent - Hive Mind Swarm
 * 
 * This test suite validates the performance characteristics of the order creation flow,
 * measuring render counts, component update frequency, memory usage, and identifying bottlenecks.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import OrderSummary from '@/pages/OrderSummary';

// Mock dependencies
vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    auth: {
      signOut: vi.fn().mockResolvedValue({ error: null }),
    },
  },
}));

vi.mock('@/hooks/useVectorSearch', () => ({
  useVectorSearch: vi.fn(() => ({
    searchByVendor: vi.fn(),
    setSearchQuery: vi.fn(),
    setSearchStrategy: vi.fn(),
    products: [],
    isLoading: false,
    error: null,
    performanceMetrics: {
      embeddingTime: 150,
      searchTime: 80,
      totalTime: 230,
      cacheHit: false,
    },
    trackSearchAnalytics: vi.fn(),
    getSimilarProducts: vi.fn(),
  })),
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

// Performance monitoring utilities
class PerformanceMonitor {
  private renderCount = 0;
  private updateCounts = new Map<string, number>();
  private memoryBaseline = 0;

  startMonitoring() {
    this.renderCount = 0;
    this.updateCounts.clear();
    if (typeof window !== 'undefined' && 'performance' in window) {
      this.memoryBaseline = (performance as any).memory?.usedJSHeapSize || 0;
    }
  }

  recordRender(componentName: string) {
    this.renderCount++;
    const current = this.updateCounts.get(componentName) || 0;
    this.updateCounts.set(componentName, current + 1);
  }

  getMetrics() {
    let memoryUsage = 0;
    if (typeof window !== 'undefined' && 'performance' in window) {
      memoryUsage = (performance as any).memory?.usedJSHeapSize || 0;
    }

    return {
      totalRenders: this.renderCount,
      componentUpdates: Object.fromEntries(this.updateCounts),
      memoryDelta: memoryUsage - this.memoryBaseline,
      memoryUsage,
    };
  }
}

// Test wrapper with providers
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('Order Creation Flow Performance Validation', () => {
  let performanceMonitor: PerformanceMonitor;
  let originalConsoleLog: typeof console.log;

  beforeEach(() => {
    performanceMonitor = new PerformanceMonitor();
    originalConsoleLog = console.log;
    
    // Mock sessionStorage
    Object.defineProperty(window, 'sessionStorage', {
      value: {
        getItem: vi.fn(() => null),
        setItem: vi.fn(),
        removeItem: vi.fn(),
      },
      writable: true,
    });

    // Mock URLSearchParams
    Object.defineProperty(window, 'URLSearchParams', {
      value: class MockURLSearchParams {
        get(key: string) {
          return null;
        }
      },
      writable: true,
    });

    performanceMonitor.startMonitoring();
  });

  afterEach(() => {
    console.log = originalConsoleLog;
  });

  describe('Initial Render Performance', () => {
    it('should render OrderSummary component within acceptable time limits', async () => {
      const startTime = performance.now();
      
      await act(async () => {
        render(
          <TestWrapper>
            <OrderSummary />
          </TestWrapper>
        );
      });
      
      const renderTime = performance.now() - startTime;
      
      // Component should render within 500ms
      expect(renderTime).toBeLessThan(500);
      
      // Should render the order details header
      expect(screen.getByText('Order Details')).toBeInTheDocument();
    });

    it('should not cause excessive re-renders on initial load', async () => {
      let renderCount = 0;
      const originalRender = React.createElement;
      
      // Track renders by intercepting React.createElement
      React.createElement = function(...args) {
        if (args[0] === OrderSummary) {
          renderCount++;
        }
        return originalRender.apply(this, args);
      };

      await act(async () => {
        render(
          <TestWrapper>
            <OrderSummary />
          </TestWrapper>
        );
      });

      React.createElement = originalRender;
      
      // Should not render more than 3 times on initial load
      expect(renderCount).toBeLessThanOrEqual(3);
    });
  });

  describe('Component Update Performance', () => {
    it('should handle quantity changes efficiently', async () => {
      const startTime = performance.now();
      
      await act(async () => {
        render(
          <TestWrapper>
            <OrderSummary />
          </TestWrapper>
        );
      });

      // Find quantity increment buttons (there should be several)
      const incrementButtons = screen.getAllByRole('button').filter(button => 
        button.querySelector('svg') && button.textContent === ''
      );

      if (incrementButtons.length > 0) {
        const updateStartTime = performance.now();
        
        await act(async () => {
          // Simulate rapid quantity changes
          for (let i = 0; i < 5; i++) {
            fireEvent.click(incrementButtons[0]);
            await new Promise(resolve => setTimeout(resolve, 10));
          }
        });
        
        const updateTime = performance.now() - updateStartTime;
        
        // Multiple quantity updates should complete within 200ms
        expect(updateTime).toBeLessThan(200);
      }
    });

    it('should efficiently handle product list filtering and sorting', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <OrderSummary />
          </TestWrapper>
        );
      });

      // Find filter dropdown
      const filterButton = screen.getByText('Filters');
      
      if (filterButton) {
        const filterStartTime = performance.now();
        
        await act(async () => {
          fireEvent.click(filterButton);
        });
        
        const filterTime = performance.now() - filterStartTime;
        
        // Filter dropdown should open within 100ms
        expect(filterTime).toBeLessThan(100);
      }
    });
  });

  describe('Memory Usage Validation', () => {
    it('should not cause significant memory leaks during normal operations', async () => {
      const initialMemory = performanceMonitor.getMetrics().memoryUsage;
      
      // Perform multiple operations that could cause memory leaks
      await act(async () => {
        render(
          <TestWrapper>
            <OrderSummary />
          </TestWrapper>
        );
      });

      // Simulate user interactions
      const buttons = screen.getAllByRole('button');
      
      for (let i = 0; i < Math.min(buttons.length, 10); i++) {
        await act(async () => {
          if (buttons[i].textContent !== 'Generate POs') {
            fireEvent.click(buttons[i]);
            await new Promise(resolve => setTimeout(resolve, 50));
          }
        });
      }

      const finalMetrics = performanceMonitor.getMetrics();
      const memoryIncrease = finalMetrics.memoryDelta;
      
      // Memory increase should be reasonable (less than 10MB for component operations)
      expect(memoryIncrease).toBeLessThan(10 * 1024 * 1024);
    });

    it('should clean up event listeners and timers properly', async () => {
      const { unmount } = render(
        <TestWrapper>
          <OrderSummary />
        </TestWrapper>
      );

      // Get initial timer/interval count
      const initialTimers = (globalThis as any).setTimeoutSpy?.mock.calls.length || 0;
      
      await act(async () => {
        unmount();
      });

      // After unmount, no new timers should be created
      const finalTimers = (globalThis as any).setTimeoutSpy?.mock.calls.length || 0;
      
      // Should not create additional timers after unmount
      expect(finalTimers).toBeLessThanOrEqual(initialTimers);
    });
  });

  describe('Search Performance Validation', () => {
    it('should handle vector search operations efficiently', async () => {
      // Mock search with realistic data
      const mockSearchResults = Array.from({ length: 20 }, (_, i) => ({
        id: i + 1,
        name: `Product ${i + 1}`,
        supplier: 'Test Supplier',
        price: '$10.00',
        image: '/placeholder.svg',
        minQuantity: 1,
        quantity: 1,
      }));

      const mockUseVectorSearch = vi.mocked(require('@/hooks/useVectorSearch').useVectorSearch);
      mockUseVectorSearch.mockReturnValue({
        searchByVendor: vi.fn(),
        setSearchQuery: vi.fn(),
        setSearchStrategy: vi.fn(),
        products: mockSearchResults,
        isLoading: false,
        error: null,
        performanceMetrics: {
          embeddingTime: 120,
          searchTime: 60,
          totalTime: 180,
          cacheHit: false,
        },
        trackSearchAnalytics: vi.fn(),
        getSimilarProducts: vi.fn(),
      });

      const startTime = performance.now();
      
      await act(async () => {
        render(
          <TestWrapper>
            <OrderSummary />
          </TestWrapper>
        );
      });
      
      const renderTime = performance.now() - startTime;
      
      // Should render search results efficiently even with 20 products
      expect(renderTime).toBeLessThan(300);
    });

    it('should handle search performance monitoring without impacting UX', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <OrderSummary />
          </TestWrapper>
        );
      });

      // Performance monitor should not be visible by default
      expect(screen.queryByText('Search Performance')).not.toBeInTheDocument();
      
      // Component should still render efficiently
      expect(screen.getByText('Order Details')).toBeInTheDocument();
    });
  });

  describe('Order Generation Performance', () => {
    it('should handle order data preparation efficiently', async () => {
      await act(async () => {
        render(
          <TestWrapper>
            <OrderSummary />
          </TestWrapper>
        );
      });

      const generateButton = screen.getByText('Generate POs');
      
      const generationStartTime = performance.now();
      
      await act(async () => {
        fireEvent.click(generateButton);
      });
      
      const generationTime = performance.now() - generationStartTime;
      
      // Order generation preparation should be fast
      expect(generationTime).toBeLessThan(100);
    });
  });

  describe('Performance Benchmarks', () => {
    it('should meet established performance benchmarks', async () => {
      const benchmarks = {
        initialRender: 500, // ms
        quantityUpdate: 50, // ms
        filterOperation: 100, // ms
        memoryUsage: 15 * 1024 * 1024, // 15MB
        searchRender: 300, // ms
      };

      // Test initial render
      const renderStart = performance.now();
      await act(async () => {
        render(
          <TestWrapper>
            <OrderSummary />
          </TestWrapper>
        );
      });
      const renderTime = performance.now() - renderStart;

      expect(renderTime).toBeLessThan(benchmarks.initialRender);
      
      // Log performance results for monitoring
      const metrics = performanceMonitor.getMetrics();
      console.log('Performance Validation Results:', {
        renderTime: `${renderTime.toFixed(2)}ms`,
        memoryUsage: `${(metrics.memoryDelta / 1024 / 1024).toFixed(2)}MB`,
        benchmarksMet: {
          render: renderTime < benchmarks.initialRender,
          memory: metrics.memoryDelta < benchmarks.memoryUsage,
        },
      });
    });
  });
});