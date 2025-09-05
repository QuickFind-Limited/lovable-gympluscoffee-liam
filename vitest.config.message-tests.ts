import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react-swc'
import path from 'path'

/**
 * Vitest Configuration for Message Flow Tests
 * Optimized configuration for testing message components
 */

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'happy-dom',
    setupFiles: ['./src/__tests__/setup/test-setup.ts'],
    include: [
      'src/__tests__/**/*.test.{ts,tsx}',
    ],
    exclude: [
      'node_modules/**',
      'dist/**',
      '**/*.d.ts',
    ],
    globals: true,
    coverage: {
      provider: 'v8',
      include: [
        'src/components/dashboard/SearchBar.tsx',
        'src/components/dashboard/ChatInterface.tsx',
        'src/components/dashboard/StreamingConversation.tsx',
        'src/pages/Dashboard.tsx',
      ],
      exclude: [
        'src/__tests__/**',
        'node_modules/**',
        'dist/**',
      ],
      reporter: ['text', 'json', 'html'],
      reportsDirectory: './coverage/message-tests',
      thresholds: {
        global: {
          branches: 75,
          functions: 80,
          lines: 80,
          statements: 80,
        },
      },
    },
    testTimeout: 10000,
    hookTimeout: 10000,
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});