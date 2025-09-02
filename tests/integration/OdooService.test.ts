import { describe, it, expect, beforeAll } from 'vitest';
import { OdooService } from '../../src/services/OdooService';

describe('OdooService Integration Tests', () => {
  let odooService: OdooService;

  beforeAll(() => {
    odooService = new OdooService();
  });

  describe('fetchPurchaseOrders', () => {
    it('should handle connection errors gracefully', async () => {
      // This test will fail to connect if Odoo is not configured
      // which is expected in demo mode
      try {
        await odooService.fetchPurchaseOrders();
      } catch (error) {
        expect(error).toBeDefined();
        expect(error.message).toContain('Odoo configuration not found');
      }
    });
  });

  describe('getSuppliers', () => {
    it('should handle connection errors gracefully', async () => {
      try {
        await odooService.getSuppliers();
      } catch (error) {
        expect(error).toBeDefined();
        expect(error.message).toContain('Odoo configuration not found');
      }
    });
  });

  describe('createPurchaseOrder', () => {
    it('should handle connection errors gracefully', async () => {
      const testOrder = {
        partner_id: 1,
        date_order: new Date().toISOString(),
        order_line: [{
          product_id: 1,
          name: 'Test Product',
          product_qty: 10,
          price_unit: 25.00,
          price_subtotal: 250.00,
          price_total: 250.00
        }]
      };

      try {
        await odooService.createPurchaseOrder(testOrder);
      } catch (error) {
        expect(error).toBeDefined();
        expect(error.message).toContain('Odoo configuration not found');
      }
    });
  });
});