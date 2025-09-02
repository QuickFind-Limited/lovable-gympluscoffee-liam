/**
 * Memory Leak Detection Utility for Order Flow
 * Performance Validator Agent - Hive Mind Swarm
 * 
 * This utility detects and measures memory leaks in the order creation flow,
 * particularly focusing on React component lifecycle and cleanup issues.
 */

interface MemorySnapshot {
  timestamp: number;
  heapUsed: number;
  heapTotal: number;
  external: number;
  arrayBuffers: number;
  componentCount?: number;
  eventListenerCount?: number;
}

interface PerformanceMetrics {
  renderTime: number;
  updateTime: number;
  memoryDelta: number;
  rerenderCount: number;
}

class MemoryLeakDetector {
  private snapshots: MemorySnapshot[] = [];
  private initialSnapshot: MemorySnapshot | null = null;
  private componentCountMap = new Map<string, number>();
  private eventListenerCount = 0;
  private renderTimes: number[] = [];
  private updateTimes: number[] = [];
  private rerenderCounts = new Map<string, number>();

  constructor() {
    this.setupPerformanceObserver();
    this.patchEventListeners();
  }

  /**
   * Setup performance observer to track React component renders
   */
  private setupPerformanceObserver(): void {
    if (typeof window !== 'undefined' && 'PerformanceObserver' in window) {
      try {
        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.name.includes('React')) {
              this.renderTimes.push(entry.duration);
            }
          }
        });
        observer.observe({ entryTypes: ['measure'] });
      } catch (error) {
        console.warn('Performance observer not available:', error);
      }
    }
  }

  /**
   * Patch addEventListener/removeEventListener to track listener leaks
   */
  private patchEventListeners(): void {
    if (typeof window !== 'undefined') {
      const originalAddEventListener = EventTarget.prototype.addEventListener;
      const originalRemoveEventListener = EventTarget.prototype.removeEventListener;

      EventTarget.prototype.addEventListener = function(type, listener, options) {
        this.dataset = this.dataset || {};
        this.dataset.listenerCount = (parseInt(this.dataset.listenerCount || '0') + 1).toString();
        return originalAddEventListener.call(this, type, listener, options);
      };

      EventTarget.prototype.removeEventListener = function(type, listener, options) {
        this.dataset = this.dataset || {};
        this.dataset.listenerCount = Math.max(0, parseInt(this.dataset.listenerCount || '0') - 1).toString();
        return originalRemoveEventListener.call(this, type, listener, options);
      };
    }
  }

  /**
   * Take a memory snapshot
   */
  takeSnapshot(label?: string): MemorySnapshot {
    const snapshot: MemorySnapshot = {
      timestamp: Date.now(),
      heapUsed: 0,
      heapTotal: 0,
      external: 0,
      arrayBuffers: 0,
    };

    // Try to get memory info from different sources
    if (typeof window !== 'undefined') {
      // Chrome DevTools Memory API
      if ('memory' in performance) {
        const perfMemory = (performance as any).memory;
        snapshot.heapUsed = perfMemory.usedJSHeapSize || 0;
        snapshot.heapTotal = perfMemory.totalJSHeapSize || 0;
      }

      // Count DOM elements as proxy for component count
      snapshot.componentCount = document.querySelectorAll('[data-testid], [data-component]').length;
      
      // Count event listeners
      snapshot.eventListenerCount = this.countEventListeners();
    }

    // Node.js environment
    if (typeof process !== 'undefined' && process.memoryUsage) {
      const memory = process.memoryUsage();
      snapshot.heapUsed = memory.heapUsed;
      snapshot.heapTotal = memory.heapTotal;
      snapshot.external = memory.external;
      snapshot.arrayBuffers = memory.arrayBuffers;
    }

    this.snapshots.push(snapshot);
    
    if (label) {
      console.log(`Memory snapshot (${label}):`, this.formatMemorySnapshot(snapshot));
    }

    return snapshot;
  }

  /**
   * Count active event listeners in the DOM
   */
  private countEventListeners(): number {
    if (typeof document === 'undefined') return 0;
    
    let count = 0;
    const elements = document.querySelectorAll('*');
    
    elements.forEach(element => {
      const el = element as any;
      if (el.dataset && el.dataset.listenerCount) {
        count += parseInt(el.dataset.listenerCount);
      }
    });
    
    return count;
  }

  /**
   * Start monitoring from this point
   */
  startMonitoring(): void {
    this.initialSnapshot = this.takeSnapshot('initial');
    this.snapshots = [this.initialSnapshot];
    this.renderTimes = [];
    this.updateTimes = [];
    this.rerenderCounts.clear();
  }

  /**
   * Record a component render
   */
  recordRender(componentName: string, duration: number): void {
    this.renderTimes.push(duration);
    const currentCount = this.rerenderCounts.get(componentName) || 0;
    this.rerenderCounts.set(componentName, currentCount + 1);
  }

  /**
   * Record a component update
   */
  recordUpdate(componentName: string, duration: number): void {
    this.updateTimes.push(duration);
  }

  /**
   * Detect memory leaks by analyzing snapshots
   */
  detectLeaks(): {
    hasLeak: boolean;
    severity: 'low' | 'medium' | 'high';
    issues: string[];
    recommendations: string[];
    metrics: PerformanceMetrics;
  } {
    if (this.snapshots.length < 2) {
      return {
        hasLeak: false,
        severity: 'low',
        issues: ['Insufficient data for leak detection'],
        recommendations: ['Take more snapshots during operations'],
        metrics: this.calculateMetrics(),
      };
    }

    const issues: string[] = [];
    const recommendations: string[] = [];
    let severity: 'low' | 'medium' | 'high' = 'low';

    // Analyze memory growth
    const memoryGrowth = this.analyzeMemoryGrowth();
    if (memoryGrowth.isGrowing) {
      issues.push(`Memory usage increased by ${this.formatBytes(memoryGrowth.totalGrowth)}`);
      if (memoryGrowth.growthRate > 5 * 1024 * 1024) { // > 5MB
        severity = 'high';
        recommendations.push('Investigate large memory allocations');
      } else if (memoryGrowth.growthRate > 1024 * 1024) { // > 1MB
        severity = 'medium';
        recommendations.push('Monitor memory usage patterns');
      }
    }

    // Analyze render performance
    const renderStats = this.analyzeRenderPerformance();
    if (renderStats.averageRenderTime > 100) {
      issues.push(`Slow renders detected: ${renderStats.averageRenderTime.toFixed(2)}ms average`);
      recommendations.push('Consider memoization or component optimization');
      severity = severity === 'low' ? 'medium' : severity;
    }

    if (renderStats.excessiveRerenders.length > 0) {
      issues.push(`Excessive re-renders: ${renderStats.excessiveRerenders.join(', ')}`);
      recommendations.push('Check for unnecessary state updates or missing dependencies');
      severity = 'high';
    }

    // Analyze event listeners
    const listenerLeak = this.analyzeEventListeners();
    if (listenerLeak.hasLeak) {
      issues.push(`Event listener leak detected: ${listenerLeak.count} listeners`);
      recommendations.push('Ensure proper cleanup in useEffect or componentWillUnmount');
      severity = severity === 'low' ? 'medium' : severity;
    }

    return {
      hasLeak: issues.length > 0,
      severity,
      issues,
      recommendations,
      metrics: this.calculateMetrics(),
    };
  }

  /**
   * Analyze memory growth patterns
   */
  private analyzeMemoryGrowth(): {
    isGrowing: boolean;
    growthRate: number;
    totalGrowth: number;
  } {
    if (this.snapshots.length < 2) {
      return { isGrowing: false, growthRate: 0, totalGrowth: 0 };
    }

    const first = this.snapshots[0];
    const last = this.snapshots[this.snapshots.length - 1];
    const totalGrowth = last.heapUsed - first.heapUsed;
    const timeSpan = last.timestamp - first.timestamp;
    const growthRate = totalGrowth / (timeSpan / 1000); // bytes per second

    return {
      isGrowing: totalGrowth > 1024 * 1024, // > 1MB growth
      growthRate,
      totalGrowth,
    };
  }

  /**
   * Analyze render performance
   */
  private analyzeRenderPerformance(): {
    averageRenderTime: number;
    maxRenderTime: number;
    excessiveRerenders: string[];
  } {
    const averageRenderTime = this.renderTimes.length > 0 
      ? this.renderTimes.reduce((sum, time) => sum + time, 0) / this.renderTimes.length 
      : 0;

    const maxRenderTime = this.renderTimes.length > 0 
      ? Math.max(...this.renderTimes) 
      : 0;

    const excessiveRerenders: string[] = [];
    this.rerenderCounts.forEach((count, component) => {
      if (count > 10) { // More than 10 renders is suspicious
        excessiveRerenders.push(`${component} (${count} renders)`);
      }
    });

    return {
      averageRenderTime,
      maxRenderTime,
      excessiveRerenders,
    };
  }

  /**
   * Analyze event listener patterns
   */
  private analyzeEventListeners(): {
    hasLeak: boolean;
    count: number;
  } {
    const currentCount = this.countEventListeners();
    const hasLeak = currentCount > 50; // Arbitrary threshold
    
    return {
      hasLeak,
      count: currentCount,
    };
  }

  /**
   * Calculate overall performance metrics
   */
  private calculateMetrics(): PerformanceMetrics {
    const memoryDelta = this.snapshots.length >= 2 
      ? this.snapshots[this.snapshots.length - 1].heapUsed - this.snapshots[0].heapUsed 
      : 0;

    const averageRenderTime = this.renderTimes.length > 0 
      ? this.renderTimes.reduce((sum, time) => sum + time, 0) / this.renderTimes.length 
      : 0;

    const averageUpdateTime = this.updateTimes.length > 0 
      ? this.updateTimes.reduce((sum, time) => sum + time, 0) / this.updateTimes.length 
      : 0;

    const totalRerenders = Array.from(this.rerenderCounts.values()).reduce((sum, count) => sum + count, 0);

    return {
      renderTime: averageRenderTime,
      updateTime: averageUpdateTime,
      memoryDelta,
      rerenderCount: totalRerenders,
    };
  }

  /**
   * Format memory snapshot for display
   */
  private formatMemorySnapshot(snapshot: MemorySnapshot): string {
    return `
      Heap Used: ${this.formatBytes(snapshot.heapUsed)}
      Heap Total: ${this.formatBytes(snapshot.heapTotal)}
      External: ${this.formatBytes(snapshot.external)}
      Components: ${snapshot.componentCount || 'N/A'}
      Event Listeners: ${snapshot.eventListenerCount || 'N/A'}
    `.trim();
  }

  /**
   * Format bytes into human-readable format
   */
  private formatBytes(bytes: number): string {
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  }

  /**
   * Generate a comprehensive report
   */
  generateReport(): string {
    const analysis = this.detectLeaks();
    const metrics = analysis.metrics;

    return `
🔍 Memory Leak Detection Report
=====================================

📊 Performance Metrics:
- Average Render Time: ${metrics.renderTime.toFixed(2)}ms
- Average Update Time: ${metrics.updateTime.toFixed(2)}ms
- Memory Delta: ${this.formatBytes(metrics.memoryDelta)}
- Total Re-renders: ${metrics.rerenderCount}

🚨 Analysis Results:
- Has Memory Leak: ${analysis.hasLeak ? 'YES' : 'NO'}
- Severity: ${analysis.severity.toUpperCase()}

📋 Issues Found:
${analysis.issues.length > 0 ? analysis.issues.map(issue => `• ${issue}`).join('\n') : '• No issues detected'}

💡 Recommendations:
${analysis.recommendations.length > 0 ? analysis.recommendations.map(rec => `• ${rec}`).join('\n') : '• No recommendations needed'}

📈 Memory Snapshots (${this.snapshots.length} taken):
${this.snapshots.map((snapshot, index) => 
  `${index + 1}. ${new Date(snapshot.timestamp).toLocaleTimeString()} - ${this.formatBytes(snapshot.heapUsed)}`
).join('\n')}

⚡ Performance Benchmarks:
- Render Time: ${metrics.renderTime < 16 ? '✅ GOOD' : metrics.renderTime < 50 ? '⚠️ FAIR' : '❌ POOR'} (${metrics.renderTime.toFixed(2)}ms)
- Memory Usage: ${metrics.memoryDelta < 5 * 1024 * 1024 ? '✅ GOOD' : metrics.memoryDelta < 20 * 1024 * 1024 ? '⚠️ FAIR' : '❌ POOR'} (${this.formatBytes(metrics.memoryDelta)})
- Re-render Count: ${metrics.rerenderCount < 10 ? '✅ GOOD' : metrics.rerenderCount < 50 ? '⚠️ FAIR' : '❌ POOR'} (${metrics.rerenderCount})

🎯 Recommendations for Order Flow Optimization:
1. Use React.memo() for product list items to prevent unnecessary re-renders
2. Implement useMemo() for expensive calculations (totals, filtering)
3. Use useCallback() for event handlers passed to child components
4. Consider virtualizing large product lists to reduce DOM nodes
5. Implement proper cleanup in useEffect hooks
6. Use debouncing for search inputs to reduce API calls
7. Consider lazy loading for non-critical components
8. Monitor bundle size and implement code splitting if needed

Generated at: ${new Date().toLocaleString()}
=====================================
    `.trim();
  }

  /**
   * Clean up and reset monitoring
   */
  cleanup(): void {
    this.snapshots = [];
    this.initialSnapshot = null;
    this.componentCountMap.clear();
    this.renderTimes = [];
    this.updateTimes = [];
    this.rerenderCounts.clear();
  }
}

export default MemoryLeakDetector;