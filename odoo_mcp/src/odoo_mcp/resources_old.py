"""MCP resource handler for Odoo records."""

from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

from typing import Any
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
    
    def _parse_odoo_uri(self, uri: str) -> Tuple[str, str, Optional[int]]:
        """Parse odoo://instance/model/id URI.
        
        Args:
            uri: URI to parse
            
        Returns:
            Tuple of (instance_id, model, record_id)
            
        Raises:
            ValidationError: If URI format is invalid
        """
        parsed = urlparse(uri)
        if parsed.scheme != 'odoo':
            raise ValidationError(
                f"Invalid URI scheme: {parsed.scheme}",
                {"uri": uri, "expected_scheme": "odoo"}
            )
        
        instance_id = parsed.netloc
        if not instance_id:
            raise ValidationError(
                "Missing instance ID in URI",
                {"uri": uri}
            )
        
        path_parts = parsed.path.strip('/').split('/')
        
        if len(path_parts) == 0 or not path_parts[0]:
            raise ValidationError(
                "Missing model in URI",
                {"uri": uri}
            )
        elif len(path_parts) == 1:
            # Model list URI: odoo://instance/model
            return instance_id, path_parts[0], None
        elif len(path_parts) == 2:
            # Record URI: odoo://instance/model/id
            try:
                record_id = int(path_parts[1])
            except ValueError:
                raise ValidationError(
                    f"Invalid record ID: {path_parts[1]}",
                    {"uri": uri}
                )
            return instance_id, path_parts[0], record_id
        else:
            raise ValidationError(
                f"Invalid URI format: {uri}",
                {"uri": uri, "expected_format": "odoo://instance/model[/id]"}
            )
    
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
                ValidationError: If URI is invalid
                NotFoundError: If record not found
            """
            instance_id = instance
            record_id = int(id)
            
            if not record_id:
                raise ValidationError(
                    "Record ID required for single record resource",
                    {"uri": uri}
                )
            
            async with self.connection_pool.get_connection(instance_id) as client:
                records = await client.execute_kw(
                    model,
                    'read',
                    [[record_id]]
                )
                
                if not records:
                    raise NotFoundError(
                        f"Record not found: {model}/{record_id}",
                        {"uri": uri, "model": model, "id": record_id}
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
                uri: Resource URI
                
            Returns:
                Resource dictionary with list of records
            """
            instance_id, model, record_id = self._parse_odoo_uri(uri)
            
            if record_id is not None:
                # This should be handled by get_record
                return await get_record(uri)
            
            async with self.connection_pool.get_connection(instance_id) as client:
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
        async def list_models(uri: str) -> Dict[str, Any]:
            """List available models for an instance.
            
            Args:
                uri: Resource URI
                
            Returns:
                Resource dictionary with list of models
            """
            parsed = urlparse(uri)
            instance_id = parsed.netloc
            
            if not instance_id:
                raise ValidationError(
                    "Missing instance ID in URI",
                    {"uri": uri}
                )
            
            async with self.connection_pool.get_connection(instance_id) as client:
                # Get list of models using ir.model
                models = await client.execute_kw(
                    'ir.model',
                    'search_read',
                    [[]],
                    {
                        'fields': ['model', 'name', 'transient', 'state'],
                        'order': 'model',
                        'limit': 200
                    }
                )
                
                # Filter out transient models and only show installed models
                models = [
                    {
                        'model': m['model'],
                        'name': m['name'],
                        'uri': f"odoo://{instance_id}/{m['model']}"
                    }
                    for m in models
                    if not m.get('transient', False) and m.get('state') == 'base'
                ]
                
                return {
                    "uri": uri,
                    "mimeType": "application/json",
                    "data": {
                        "instance": instance_id,
                        "count": len(models),
                        "models": models
                    }
                }
