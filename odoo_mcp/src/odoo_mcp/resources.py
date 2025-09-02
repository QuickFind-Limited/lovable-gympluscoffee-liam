"""MCP resource handler for Odoo records."""

from typing import Any, Dict
from fastmcp import FastMCP

from .connection import ConnectionPoolManager
from .errors import NotFoundError, ValidationError


class ResourceHandler:
    """Handle MCP resource URIs for Odoo records."""
    
    def __init__(self, mcp: "FastMCP[Any]", connection_pool: ConnectionPoolManager):
        """Initialize resource handler.
        
        Args:
            mcp: FastMCP server instance
            connection_pool: Connection pool manager
        """
        self.mcp = mcp
        self.connection_pool = connection_pool
        self._register_resources()
    
    def _register_resources(self) -> None:
        """Register resource handlers."""
        
        @self.mcp.resource("odoo://{instance}/{model}/{id}")
        async def get_record(instance: str, model: str, id: str) -> Dict[str, Any]:
            """Get a specific Odoo record.
            
            Args:
                instance: Instance ID
                model: Model name
                id: Record ID
                
            Returns:
                Resource dictionary with URI, mimeType, and data
                
            Raises:
                NotFoundError: If record not found
            """
            record_id = int(id)
            uri = f"odoo://{instance}/{model}/{id}"
            
            async with self.connection_pool.get_connection(instance) as client:
                records = await client.execute_kw(
                    model,
                    'read',
                    [[record_id]]
                )
                
                if not records:
                    raise NotFoundError(
                        f"Record {model}/{record_id} not found",
                        {"model": model, "id": record_id}
                    )
                
                return {
                    "uri": uri,
                    "mimeType": "application/json",
                    "data": records[0]
                }
        
        @self.mcp.resource("odoo://{instance}/{model}")
        async def list_records(instance: str, model: str) -> Dict[str, Any]:
            """List records of a model.
            
            Args:
                instance: Instance ID
                model: Model name
                
            Returns:
                Resource dictionary with list of records
            """
            uri = f"odoo://{instance}/{model}"
            
            async with self.connection_pool.get_connection(instance) as client:
                # Get first 100 records by default
                record_ids = await client.execute_kw(
                    model,
                    'search',
                    [[]],
                    {'limit': 100, 'order': 'id desc'}
                )
                
                if record_ids:
                    records = await client.execute_kw(
                        model,
                        'read',
                        [record_ids],
                        {'fields': ['id', 'display_name']}
                    )
                else:
                    records = []
                
                return {
                    "uri": uri,
                    "mimeType": "application/json",
                    "data": {
                        "model": model,
                        "count": len(records),
                        "records": records
                    }
                }
        
        @self.mcp.resource("odoo://{instance}")
        async def list_models(instance: str) -> Dict[str, Any]:
            """List available models for an instance.
            
            Args:
                instance: Instance ID
                
            Returns:
                Resource dictionary with list of models
            """
            uri = f"odoo://{instance}"
            
            async with self.connection_pool.get_connection(instance) as client:
                # Get common models
                models = [
                    "res.partner",
                    "res.users", 
                    "res.company",
                    "product.product",
                    "product.template",
                    "sale.order",
                    "sale.order.line",
                    "purchase.order",
                    "purchase.order.line",
                    "stock.move",
                    "stock.picking",
                    "account.move",
                    "account.move.line"
                ]
                
                return {
                    "uri": uri,
                    "mimeType": "application/json",
                    "data": {
                        "instance": instance,
                        "models": models
                    }
                }