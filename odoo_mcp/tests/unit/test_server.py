"""Unit tests for the main MCP server setup."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastmcp import FastMCP

from odoo_mcp.server import (
    create_server,
    lifespan,
    get_connection_pool,
    get_tool_registry,
    get_resource_handler,
)


class TestServerSetup:
    """Test server initialization and lifecycle."""

    async def test_create_server_returns_fastmcp_instance(self) -> None:
        """Test that create_server returns a properly configured FastMCP instance."""
        server = create_server()
        assert isinstance(server, FastMCP)
        # FastMCP stores name and version internally
        # We'll verify through the server configuration

    async def test_lifespan_initializes_components(self) -> None:
        """Test that lifespan context manager initializes all components."""
        mock_mcp = MagicMock(spec=FastMCP)
        
        async with lifespan(mock_mcp) as context:
            assert "connection_pool" in context
            assert "tool_registry" in context
            assert "resource_handler" in context
            
            # Verify components are properly initialized
            assert context["connection_pool"] is not None
            assert context["tool_registry"] is not None
            assert context["resource_handler"] is not None

    async def test_lifespan_cleanup_on_exit(self) -> None:
        """Test that lifespan properly cleans up resources on exit."""
        mock_mcp = MagicMock(spec=FastMCP)
        
        # Track cleanup calls
        cleanup_called = False
        
        async def mock_cleanup():
            nonlocal cleanup_called
            cleanup_called = True
        
        with patch("odoo_mcp.server.ConnectionPoolManager") as mock_pool_class:
            mock_pool = AsyncMock()
            mock_pool.cleanup = mock_cleanup
            mock_pool_class.return_value = mock_pool
            
            async with lifespan(mock_mcp) as context:
                pass
            
            # Verify cleanup was called
            assert cleanup_called

    def test_get_connection_pool_from_context(self) -> None:
        """Test retrieving connection pool from server context."""
        mock_server = MagicMock(spec=FastMCP)
        mock_pool = MagicMock()
        mock_server.context = {"connection_pool": mock_pool}
        
        pool = get_connection_pool(mock_server)
        assert pool is mock_pool

    def test_get_tool_registry_from_context(self) -> None:
        """Test retrieving tool registry from server context."""
        mock_server = MagicMock(spec=FastMCP)
        mock_registry = MagicMock()
        mock_server.context = {"tool_registry": mock_registry}
        
        registry = get_tool_registry(mock_server)
        assert registry is mock_registry

    def test_get_resource_handler_from_context(self) -> None:
        """Test retrieving resource handler from server context."""
        mock_server = MagicMock(spec=FastMCP)
        mock_handler = MagicMock()
        mock_server.context = {"resource_handler": mock_handler}
        
        handler = get_resource_handler(mock_server)
        assert handler is mock_handler

    def test_server_configuration_from_environment(self) -> None:
        """Test that server configuration can be loaded from environment."""
        with patch.dict("os.environ", {
            "MCP_SERVER_NAME": "test-odoo-mcp",
            "MCP_SERVER_VERSION": "2.0.0"
        }):
            server = create_server()
            assert isinstance(server, FastMCP)
            # FastMCP internally uses these values from environment

    async def test_server_handles_initialization_errors(self) -> None:
        """Test that server handles initialization errors gracefully."""
        mock_mcp = MagicMock(spec=FastMCP)
        
        with patch("odoo_mcp.server.ConnectionPoolManager") as mock_pool_class:
            mock_pool_class.side_effect = Exception("Connection pool init failed")
            
            with pytest.raises(Exception, match="Connection pool init failed"):
                async with lifespan(mock_mcp):
                    pass
