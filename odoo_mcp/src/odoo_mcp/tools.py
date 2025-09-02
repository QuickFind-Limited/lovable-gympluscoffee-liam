"""MCP tool implementations for Odoo operations."""

from typing import Any

from fastmcp import FastMCP

from .connection import ConnectionPoolManager
from .errors import ValidationError
from .types import (
    validate_record_data,
    validate_search_domain,
)


class ToolRegistry:
    """Registry for MCP tools."""

    def __init__(self, mcp: FastMCP, connection_pool: ConnectionPoolManager):
        """Initialize tool registry and register all tools.

        Args:
            mcp: FastMCP server instance
            connection_pool: Connection pool manager
        """
        self.mcp = mcp
        self.connection_pool = connection_pool
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all Odoo MCP tools."""

        @self.mcp.tool()
        async def odoo_create(
            instance_id: str, model: str, values: dict[str, Any]
        ) -> int:
            """Create a new record in Odoo.

            Args:
                instance_id: Odoo instance identifier
                model: Model name (e.g., 'res.partner')
                values: Field values for the new record

            Returns:
                ID of the created record

            Raises:
                ValidationError: If values are invalid
                Various OdooMCPError subclasses
            """
            if not validate_record_data(values):
                raise ValidationError("Invalid record data", {"values": values})

            async with self.connection_pool.get_connection(instance_id) as client:
                return await client.execute_kw(model, "create", [values])

        @self.mcp.tool()
        async def odoo_read(
            instance_id: str,
            model: str,
            ids: list[int],
            fields: list[str] | None = None,
        ) -> list[dict[str, Any]]:
            """Read records from Odoo.

            Args:
                instance_id: Odoo instance identifier
                model: Model name
                ids: List of record IDs to read
                fields: Optional list of fields to return

            Returns:
                List of record dictionaries
            """
            async with self.connection_pool.get_connection(instance_id) as client:
                return await client.execute_kw(
                    model, "read", [ids], {"fields": fields} if fields else {}
                )

        @self.mcp.tool()
        async def odoo_search(
            instance_id: str,
            model: str,
            domain: list[Any],  # Changed from OdooSearchDomain for schema compatibility
            limit: int | None = None,
            offset: int | None = None,
            order: str | None = None,
        ) -> list[int]:
            """Search for records in Odoo.

            Args:
                instance_id: Odoo instance identifier
                model: Model name
                domain: Search domain
                limit: Maximum number of records
                offset: Number of records to skip
                order: Sort order (e.g., 'name asc')

            Returns:
                List of matching record IDs

            Raises:
                ValidationError: If domain is invalid
            """
            if not validate_search_domain(domain):
                raise ValidationError("Invalid search domain", {"domain": domain})

            kwargs: dict[str, Any] = {}
            if limit is not None:
                kwargs["limit"] = limit
            if offset is not None:
                kwargs["offset"] = offset
            if order is not None:
                kwargs["order"] = order

            async with self.connection_pool.get_connection(instance_id) as client:
                return await client.execute_kw(model, "search", [domain], kwargs)

        @self.mcp.tool()
        async def odoo_search_read(
            instance_id: str,
            model: str,
            domain: list[Any],  # Changed from OdooSearchDomain for schema compatibility
            fields: list[str] | None = None,
            limit: int | None = None,
            offset: int | None = None,
            order: str | None = None,
        ) -> list[dict[str, Any]]:
            """Search and read records in one operation.

            Args:
                instance_id: Odoo instance identifier
                model: Model name
                domain: Search domain
                fields: Optional list of fields to return
                limit: Maximum number of records
                offset: Number of records to skip
                order: Sort order

            Returns:
                List of matching records
            """
            if not validate_search_domain(domain):
                raise ValidationError("Invalid search domain", {"domain": domain})

            kwargs: dict[str, Any] = {}
            if fields:
                kwargs["fields"] = fields
            if limit is not None:
                kwargs["limit"] = limit
            if offset is not None:
                kwargs["offset"] = offset
            if order is not None:
                kwargs["order"] = order

            async with self.connection_pool.get_connection(instance_id) as client:
                return await client.execute_kw(model, "search_read", [domain], kwargs)

        @self.mcp.tool()
        async def odoo_update(
            instance_id: str, model: str, ids: list[int], values: dict[str, Any]
        ) -> bool:
            """Update existing records.

            Args:
                instance_id: Odoo instance identifier
                model: Model name
                ids: List of record IDs to update
                values: Field values to update

            Returns:
                True if successful
            """
            if not validate_record_data(values):
                raise ValidationError("Invalid record data", {"values": values})

            async with self.connection_pool.get_connection(instance_id) as client:
                return await client.execute_kw(model, "write", [ids, values])

        @self.mcp.tool()
        async def odoo_delete(instance_id: str, model: str, ids: list[int]) -> bool:
            """Delete records.

            Args:
                instance_id: Odoo instance identifier
                model: Model name
                ids: List of record IDs to delete

            Returns:
                True if successful
            """
            async with self.connection_pool.get_connection(instance_id) as client:
                return await client.execute_kw(model, "unlink", [ids])

        @self.mcp.tool()
        async def odoo_execute(
            instance_id: str,
            model: str,
            method: str,
            args: list[Any],
            kwargs: dict[str, Any] | None = None,
        ) -> Any:
            """Execute any method on an Odoo model.

            Args:
                instance_id: Odoo instance identifier
                model: Model name
                method: Method name
                args: Method arguments
                kwargs: Method keyword arguments

            Returns:
                Method result
            """
            async with self.connection_pool.get_connection(instance_id) as client:
                return await client.execute_kw(model, method, args, kwargs or {})

        @self.mcp.tool()
        async def odoo_fields_get(
            instance_id: str, model: str, fields: list[str] | None = None
        ) -> dict[str, Any]:
            """Get field definitions for a model.

            Args:
                instance_id: Odoo instance identifier
                model: Model name
                fields: Optional list of specific fields

            Returns:
                Dictionary of field definitions
            """
            async with self.connection_pool.get_connection(instance_id) as client:
                return await client.execute_kw(
                    model, "fields_get", [], {"allfields": fields} if fields else {}
                )

        @self.mcp.tool()
        async def odoo_search_count(
            instance_id: str,
            model: str,
            domain: list[Any],  # Changed from OdooSearchDomain for schema compatibility
        ) -> int:
            """Count records matching a domain.

            Args:
                instance_id: Odoo instance identifier
                model: Model name
                domain: Search domain

            Returns:
                Number of matching records
            """
            if not validate_search_domain(domain):
                raise ValidationError("Invalid search domain", {"domain": domain})

            async with self.connection_pool.get_connection(instance_id) as client:
                return await client.execute_kw(model, "search_count", [domain])
