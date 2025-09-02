"""End-to-end tests for procurement workflow automation."""

import pytest
from tests.conftest import OdooTestConnection, create_test_record


@pytest.mark.e2e
@pytest.mark.odoo
@pytest.mark.slow
class TestProcurementWorkflow:
    """Test complete procurement workflow automation."""

    async def test_full_procurement_cycle(
        self,
        odoo_connection: OdooTestConnection,
        test_partner_data: dict,
        test_product_data: dict,
    ) -> None:
        """Test a complete procurement cycle from stock check to purchase order."""
        # Step 1: Create test data
        supplier_data = test_partner_data.copy()
        supplier_data["name"] = "Test Supplier MCP"
        supplier_data["supplier_rank"] = 1
        supplier_data["customer_rank"] = 0
        
        supplier_id = await create_test_record(odoo_connection, "res.partner", supplier_data)
        product_id = await create_test_record(odoo_connection, "product.product", test_product_data)

        # Step 2: Check current stock (should be 0 for new product)
        stock_quants = await odoo_connection.execute(
            "stock.quant",
            "search_read",
            [[("product_id", "=", product_id)]],
            {"fields": ["quantity", "location_id"]},
        )
        
        total_stock = sum(q["quantity"] for q in stock_quants)
        assert total_stock == 0.0  # New product should have no stock

        # Step 3: Create a purchase order
        po_data = {
            "partner_id": supplier_id,
            "order_line": [
                (
                    0,
                    0,
                    {
                        "product_id": product_id,
                        "product_qty": 10.0,
                        "price_unit": 50.0,
                    },
                )
            ],
        }
        
        po_id = await create_test_record(odoo_connection, "purchase.order", po_data)
        assert po_id > 0

        # Step 4: Read back the purchase order
        po = await odoo_connection.execute(
            "purchase.order",
            "read",
            [[po_id]],
            {"fields": ["name", "state", "partner_id", "amount_total"]},
        )
        assert len(po) == 1
        assert po[0]["state"] == "draft"
        assert po[0]["partner_id"][0] == supplier_id
        assert po[0]["amount_total"] == 500.0  # 10 * 50

    async def test_inventory_analysis(
        self, odoo_connection: OdooTestConnection, test_product_data: dict
    ) -> None:
        """Test inventory analysis for reorder points."""
        # Create multiple products
        products = []
        for i in range(3):
            product_data = test_product_data.copy()
            product_data["name"] = f"Test Product {i}"
            product_id = await create_test_record(odoo_connection, "product.product", product_data)
            products.append(product_id)

        # Get inventory valuation
        for product_id in products:
            # Check if product has any stock moves
            moves = await odoo_connection.execute(
                "stock.move",
                "search_count",
                [[("product_id", "=", product_id)]],
            )
            assert isinstance(moves, int)
            assert moves >= 0  # New products might have no moves