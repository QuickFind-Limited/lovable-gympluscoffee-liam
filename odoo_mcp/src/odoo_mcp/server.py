"""Main MCP server implementation using FastMCP."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, cast

from .connection import ConnectionPoolManager, OdooConnectionConfig

if TYPE_CHECKING:
    from fastmcp import FastMCP


@asynccontextmanager
async def lifespan(mcp: "FastMCP[Any]") -> AsyncIterator[dict[str, Any]]:
    """Manage server lifecycle with connection pooling and component initialization.

    Args:
        mcp: FastMCP server instance

    Yields:
        Dict containing initialized components:
        - connection_pool: ConnectionPoolManager instance
        - tool_registry: ToolRegistry instance
        - resource_handler: ResourceHandler instance
    """
    # Initialize connection pool
    connection_pool = ConnectionPoolManager()
    await connection_pool.initialize()

    # Load environment variables
    from dotenv import load_dotenv

    load_dotenv()

    # Add default connection from environment variables if available
    odoo_url = os.getenv("ODOO_URL")
    odoo_database = os.getenv("ODOO_DATABASE")
    odoo_username = os.getenv("ODOO_USERNAME")
    odoo_password = os.getenv("ODOO_PASSWORD")

    if all([odoo_url, odoo_database, odoo_username, odoo_password]):
        # Create default connection config
        default_config = OdooConnectionConfig(
            url=odoo_url,
            database=odoo_database,
            username=odoo_username,
            password=odoo_password,
            timeout=int(os.getenv("ODOO_TIMEOUT", "30")),
            max_connections=int(os.getenv("ODOO_MAX_CONNECTIONS", "10")),
        )

        # Add the default connection
        await connection_pool.add_connection("default", default_config)
        print(
            f"✅ Added default Odoo connection to {odoo_url} (database: {odoo_database})"
        )
    else:
        print(
            "⚠️  No default Odoo connection configured. Set ODOO_URL, ODOO_DATABASE, ODOO_USERNAME, and ODOO_PASSWORD environment variables."
        )

    # Import here to avoid circular imports
    from .prompts import PromptRegistry
    from .resources import ResourceHandler
    from .tools import ToolRegistry
    from .types import ServerContext

    # Initialize registries with dependencies
    tool_registry = ToolRegistry(mcp, connection_pool)
    resource_handler = ResourceHandler(mcp, connection_pool)
    PromptRegistry(mcp, connection_pool)

    # Store in context
    context: ServerContext = {
        "connection_pool": connection_pool,
        "tool_registry": tool_registry,
        "resource_handler": resource_handler,
    }

    try:
        yield cast(dict[str, Any], context)
    finally:
        # Cleanup resources
        await connection_pool.cleanup()


def create_server(
    name: str | None = None, version: str | None = None
) -> "FastMCP[Any]":
    """Create and configure the MCP server.

    Args:
        name: Server name (defaults to env var or 'odoo-mcp-server')
        version: Server version (defaults to env var or '0.1.0')

    Returns:
        Configured FastMCP server instance
    """
    # Get configuration from environment or use defaults
    server_name = name or os.getenv("MCP_SERVER_NAME", "odoo-mcp-server")
    server_version = version or os.getenv("MCP_SERVER_VERSION", "0.1.0")

    # Create server with lifespan management
    from fastmcp import FastMCP

    return FastMCP(
        name=server_name,
        version=server_version,
        lifespan=lifespan,
    )


def get_connection_pool(server: "FastMCP[Any]") -> ConnectionPoolManager:
    """Get connection pool from server context.

    Args:
        server: FastMCP server instance

    Returns:
        ConnectionPoolManager instance

    Raises:
        RuntimeError: If connection pool not found in context
    """
    if not hasattr(server, "context") or "connection_pool" not in server.context:
        raise RuntimeError("Connection pool not initialized in server context")
    return server.context["connection_pool"]


def get_tool_registry(server: "FastMCP[Any]") -> Any:
    """Get tool registry from server context.

    Args:
        server: FastMCP server instance

    Returns:
        ToolRegistry instance

    Raises:
        RuntimeError: If tool registry not found in context
    """
    if not hasattr(server, "context") or "tool_registry" not in server.context:
        raise RuntimeError("Tool registry not initialized in server context")
    return server.context["tool_registry"]


def get_resource_handler(server: "FastMCP[Any]") -> Any:
    """Get resource handler from server context.

    Args:
        server: FastMCP server instance

    Returns:
        ResourceHandler instance

    Raises:
        RuntimeError: If resource handler not found in context
    """
    if not hasattr(server, "context") or "resource_handler" not in server.context:
        raise RuntimeError("Resource handler not initialized in server context")
    return server.context["resource_handler"]


# Create the main server instance
mcp_server = create_server()


# Entry point for running the server
if __name__ == "__main__":
    import uvicorn

    # Get host and port from environment
    host = os.getenv("MCP_SERVER_HOST", "localhost")
    port = int(os.getenv("MCP_SERVER_PORT", "3000"))

    # Run the server
    uvicorn.run(
        "odoo_mcp.server:mcp_server",
        host=host,
        port=port,
        reload=os.getenv("MCP_DEV_MODE", "false").lower() == "true",
    )
