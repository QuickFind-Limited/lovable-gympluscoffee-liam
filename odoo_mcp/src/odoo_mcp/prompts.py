"""MCP prompts for common Odoo operations."""

from typing import TYPE_CHECKING, Any

from .connection import ConnectionPoolManager

if TYPE_CHECKING:
    from fastmcp import FastMCP


class PromptRegistry:
    """Registry for MCP prompts."""

    def __init__(self, mcp: "FastMCP[Any]", connection_pool: ConnectionPoolManager):
        """Initialize prompt registry.

        Args:
            mcp: FastMCP server instance
            connection_pool: Connection pool manager
        """
        self.mcp = mcp
        self.connection_pool = connection_pool
        self._register_prompts()

    def _register_prompts(self) -> None:
        """Register all prompts."""

        @self.mcp.prompt("analyze_inventory")
        async def analyze_inventory_prompt(
            instance_id: str = "default",
            warehouse: str = "all",
            include_forecast: bool = True,
        ) -> str:
            """Analyze current inventory levels and provide insights.

            Args:
                instance_id: Odoo instance to analyze
                warehouse: Specific warehouse or 'all'
                include_forecast: Include demand forecast analysis

            Returns:
                Formatted inventory analysis report
            """
            async with self.connection_pool.get_connection(instance_id) as client:
                # Get product inventory
                products = await client.execute_kw(
                    "product.product",
                    "search_read",
                    [[]],
                    {
                        "fields": [
                            "name",
                            "qty_available",
                            "virtual_available",
                            "list_price",
                        ],
                        "limit": 50,
                        "order": "qty_available asc",
                    },
                )

                # Build analysis
                report = "# Inventory Analysis Report\n\n"
                report += f"**Instance**: {instance_id}\n"
                report += f"**Warehouse**: {warehouse}\n\n"

                report += "## Low Stock Alert (Bottom 10 Products)\n\n"
                low_stock_threshold = 10
                low_stock = [
                    p for p in products if p["qty_available"] < low_stock_threshold
                ][:10]

                if low_stock:
                    report += "| Product | On Hand | Forecasted | Price |\n"
                    report += "|---------|---------|------------|-------|\n"
                    for product in low_stock:
                        report += f"| {product['name'][:30]} | {product['qty_available']} | {product['virtual_available']} | ${product['list_price']:.2f} |\n"
                else:
                    report += "No products with low stock found.\n"

                if include_forecast:
                    report += "\n## Forecast Analysis\n\n"
                    report += "Based on current stock levels and pending orders:\n"
                    negative_forecast = [
                        p for p in products if p["virtual_available"] < 0
                    ]
                    if negative_forecast:
                        report += f"- **{len(negative_forecast)} products** will have negative stock after fulfilling pending orders\n"
                        report += "- Immediate procurement action required\n"
                    else:
                        report += "- All products have sufficient stock to meet pending demand\n"

                report += "\n## Recommendations\n\n"
                report += "1. Review and reorder products with low stock levels\n"
                report += "2. Consider safety stock adjustments for frequently ordered items\n"
                report += "3. Analyze seasonal patterns for better forecasting\n"

                return report

        @self.mcp.prompt("optimize_procurement")
        async def optimize_procurement_prompt(
            instance_id: str = "default",
            supplier_id: int | None = None,
            lead_time_days: int = 7,
        ) -> str:
            """Generate optimized procurement suggestions based on current needs.

            Args:
                instance_id: Odoo instance to analyze
                supplier_id: Specific supplier or None for all
                lead_time_days: Lead time for procurement planning

            Returns:
                Procurement optimization recommendations
            """
            async with self.connection_pool.get_connection(instance_id) as client:
                # Get products needing reorder
                products = await client.execute_kw(
                    "product.product",
                    "search_read",
                    [[["qty_available", "<", 10]]],
                    {
                        "fields": [
                            "name",
                            "qty_available",
                            "virtual_available",
                            "reordering_min_qty",
                            "reordering_max_qty",
                        ],
                        "limit": 20,
                    },
                )

                report = "# Procurement Optimization Report\n\n"
                report += f"**Lead Time**: {lead_time_days} days\n"
                if supplier_id:
                    report += f"**Supplier ID**: {supplier_id}\n"
                report += "\n## Products Requiring Reorder\n\n"

                if products:
                    report += (
                        "| Product | Current Stock | After Orders | Suggested Qty |\n"
                    )
                    report += (
                        "|---------|--------------|--------------|---------------|\n"
                    )

                    for product in products:
                        suggested_qty = max(
                            20,  # Minimum order
                            product.get("reordering_max_qty", 50)
                            - product["qty_available"],
                        )
                        report += f"| {product['name'][:30]} | {product['qty_available']} | {product['virtual_available']} | {suggested_qty} |\n"

                    report += f"\n**Total Products**: {len(products)}\n"
                else:
                    report += "No products currently require reordering.\n"

                # Get pending purchase orders
                pending_pos = await client.execute_kw(
                    "purchase.order",
                    "search_count",
                    [[["state", "in", ["draft", "sent"]]]],
                )

                report += "\n## Current Procurement Status\n\n"
                report += f"- **Pending Purchase Orders**: {pending_pos}\n"
                report += f"- **Products Below Reorder Point**: {len(products)}\n"

                report += "\n## Optimization Strategies\n\n"
                report += "1. **Consolidate Orders**: Group products by supplier to reduce shipping costs\n"
                report += (
                    "2. **Lead Time Buffer**: Add "
                    + str(lead_time_days)
                    + " days buffer for critical items\n"
                )
                report += "3. **Volume Discounts**: Consider bulk ordering for high-turnover items\n"
                report += "4. **Automate Reordering**: Set up reordering rules for consistent items\n"

                return report

        @self.mcp.prompt("generate_report")
        async def generate_report_prompt(
            instance_id: str = "default",
            report_type: str = "sales_summary",
            period: str = "this_month",
        ) -> str:
            """Generate various business reports from Odoo data.

            Args:
                instance_id: Odoo instance to analyze
                report_type: Type of report (sales_summary, inventory_valuation, etc.)
                period: Time period for the report

            Returns:
                Formatted business report
            """
            async with self.connection_pool.get_connection(instance_id) as client:
                report = "# Odoo Business Report\n\n"
                report += f"**Type**: {report_type.replace('_', ' ').title()}\n"
                report += f"**Period**: {period.replace('_', ' ').title()}\n\n"

                if report_type == "sales_summary":
                    # Get sales orders
                    orders = await client.execute_kw(
                        "sale.order",
                        "search_read",
                        [[["state", "in", ["sale", "done"]]]],
                        {
                            "fields": ["name", "partner_id", "amount_total", "state"],
                            "limit": 10,
                            "order": "date_order desc",
                        },
                    )

                    if orders:
                        total_sales = sum(order["amount_total"] for order in orders)
                        report += "## Sales Overview\n\n"
                        report += f"- **Total Orders**: {len(orders)}\n"
                        report += f"- **Total Revenue**: ${total_sales:,.2f}\n"
                        report += f"- **Average Order Value**: ${total_sales/len(orders):,.2f}\n\n"

                        report += "### Recent Orders\n\n"
                        report += "| Order | Customer | Amount | Status |\n"
                        report += "|-------|----------|--------|--------|\n"
                        for order in orders[:5]:
                            customer = (
                                order["partner_id"][1] if order["partner_id"] else "N/A"
                            )
                            report += f"| {order['name']} | {customer[:20]} | ${order['amount_total']:,.2f} | {order['state']} |\n"
                    else:
                        report += "No sales orders found for the specified period.\n"

                elif report_type == "inventory_valuation":
                    # Get inventory valuation
                    products = await client.execute_kw(
                        "product.product",
                        "search_read",
                        [[["qty_available", ">", 0]]],
                        {
                            "fields": ["name", "qty_available", "standard_price"],
                            "limit": 50,
                        },
                    )

                    if products:
                        total_value = sum(
                            p["qty_available"] * p["standard_price"] for p in products
                        )
                        total_units = sum(p["qty_available"] for p in products)

                        report += "## Inventory Valuation\n\n"
                        report += f"- **Total Products**: {len(products)}\n"
                        report += f"- **Total Units**: {total_units:,.0f}\n"
                        report += f"- **Total Value**: ${total_value:,.2f}\n"
                        report += f"- **Average Value per Unit**: ${total_value/total_units:,.2f}\n\n"

                        # Top valuable products
                        products_by_value = sorted(
                            products,
                            key=lambda p: p["qty_available"] * p["standard_price"],
                            reverse=True,
                        )

                        report += "### Top 5 Products by Value\n\n"
                        report += "| Product | Quantity | Unit Cost | Total Value |\n"
                        report += "|---------|----------|-----------|-------------|\n"
                        for product in products_by_value[:5]:
                            value = product["qty_available"] * product["standard_price"]
                            report += f"| {product['name'][:30]} | {product['qty_available']} | ${product['standard_price']:.2f} | ${value:,.2f} |\n"
                    else:
                        report += "No inventory found.\n"

                report += "\n---\n*Report generated automatically by Odoo MCP Server*"
                return report
