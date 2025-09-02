"""Unit tests for connection management."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp

from odoo_mcp.connection import (
    OdooConnectionConfig,
    ConnectionPoolManager,
    OdooAsyncClient,
    ConnectionError,
    AuthenticationError,
)


class TestOdooConnectionConfig:
    """Test connection configuration."""

    def test_config_with_defaults(self) -> None:
        """Test creating config with default values."""
        config = OdooConnectionConfig(
            url="https://odoo.example.com",
            database="testdb",
            username="admin",
            password="secret",
        )
        
        assert config.url == "https://odoo.example.com"
        assert config.database == "testdb"
        assert config.username == "admin"
        assert config.password == "secret"
        assert config.timeout == 30  # default
        assert config.max_connections == 10  # default

    def test_config_with_custom_values(self) -> None:
        """Test creating config with custom values."""
        config = OdooConnectionConfig(
            url="https://odoo.example.com",
            database="testdb",
            username="admin",
            password="secret",
            timeout=60,
            max_connections=20,
        )
        
        assert config.timeout == 60
        assert config.max_connections == 20

    def test_config_validation(self) -> None:
        """Test config validation for required fields."""
        with pytest.raises(TypeError):
            # Missing required fields
            OdooConnectionConfig()  # type: ignore


class TestConnectionPoolManager:
    """Test connection pool management."""

    @pytest.fixture
    def pool_manager(self) -> ConnectionPoolManager:
        """Create a test pool manager."""
        return ConnectionPoolManager()

    async def test_initialize_pool_manager(self, pool_manager: ConnectionPoolManager) -> None:
        """Test pool manager initialization."""
        await pool_manager.initialize()
        assert pool_manager._initialized
        await pool_manager.cleanup()

    async def test_add_connection(self, pool_manager: ConnectionPoolManager) -> None:
        """Test adding a new connection to the pool."""
        await pool_manager.initialize()
        
        config = OdooConnectionConfig(
            url="https://odoo.example.com",
            database="testdb",
            username="admin",
            password="secret",
        )
        
        await pool_manager.add_connection("test_instance", config)
        
        assert "test_instance" in pool_manager._configs
        assert "test_instance" in pool_manager._sessions
        assert "test_instance" in pool_manager._connectors
        
        await pool_manager.cleanup()

    async def test_get_connection(self, pool_manager: ConnectionPoolManager) -> None:
        """Test getting a connection from the pool."""
        await pool_manager.initialize()
        
        config = OdooConnectionConfig(
            url="https://odoo.example.com",
            database="testdb",
            username="admin",
            password="secret",
        )
        
        await pool_manager.add_connection("test_instance", config)
        
        async with pool_manager.get_connection("test_instance") as client:
            assert isinstance(client, OdooAsyncClient)
            assert client.config == config
        
        await pool_manager.cleanup()

    async def test_get_nonexistent_connection(self, pool_manager: ConnectionPoolManager) -> None:
        """Test getting a connection that doesn't exist."""
        await pool_manager.initialize()
        
        with pytest.raises(ValueError, match="No connection for instance: nonexistent"):
            async with pool_manager.get_connection("nonexistent"):
                pass
        
        await pool_manager.cleanup()

    async def test_remove_connection(self, pool_manager: ConnectionPoolManager) -> None:
        """Test removing a connection from the pool."""
        await pool_manager.initialize()
        
        config = OdooConnectionConfig(
            url="https://odoo.example.com",
            database="testdb",
            username="admin",
            password="secret",
        )
        
        await pool_manager.add_connection("test_instance", config)
        await pool_manager.remove_connection("test_instance")
        
        assert "test_instance" not in pool_manager._configs
        assert "test_instance" not in pool_manager._sessions
        assert "test_instance" not in pool_manager._connectors
        
        await pool_manager.cleanup()

    async def test_cleanup_closes_all_connections(self, pool_manager: ConnectionPoolManager) -> None:
        """Test that cleanup closes all connections."""
        await pool_manager.initialize()
        
        # Add multiple connections
        for i in range(3):
            config = OdooConnectionConfig(
                url=f"https://odoo{i}.example.com",
                database="testdb",
                username="admin",
                password="secret",
            )
            await pool_manager.add_connection(f"instance_{i}", config)
        
        # Mock session close
        for session in pool_manager._sessions.values():
            session.close = AsyncMock()
        
        await pool_manager.cleanup()
        
        # Verify all sessions were closed
        for session in pool_manager._sessions.values():
            session.close.assert_called_once()


class TestOdooAsyncClient:
    """Test async Odoo client."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock aiohttp session."""
        session = AsyncMock(spec=aiohttp.ClientSession)
        return session

    @pytest.fixture
    def test_config(self) -> OdooConnectionConfig:
        """Create test configuration."""
        return OdooConnectionConfig(
            url="https://odoo.example.com",
            database="testdb",
            username="admin",
            password="secret",
        )

    @pytest.fixture
    def client(self, mock_session: AsyncMock, test_config: OdooConnectionConfig) -> OdooAsyncClient:
        """Create test client."""
        return OdooAsyncClient(session=mock_session, config=test_config)

    async def test_authenticate_success(self, client: OdooAsyncClient, mock_session: AsyncMock) -> None:
        """Test successful authentication."""
        # Mock successful response
        mock_response = AsyncMock()
        mock_response.read.return_value = b'<?xml version="1.0"?><methodResponse><params><param><value><int>2</int></value></param></params></methodResponse>'
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        uid = await client.authenticate()
        assert uid == 2
        assert client._uid == 2

    async def test_authenticate_caches_uid(self, client: OdooAsyncClient, mock_session: AsyncMock) -> None:
        """Test that authentication caches the user ID."""
        # Mock successful response
        mock_response = AsyncMock()
        mock_response.read.return_value = b'<?xml version="1.0"?><methodResponse><params><param><value><int>2</int></value></param></params></methodResponse>'
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        # First call
        uid1 = await client.authenticate()
        # Second call should use cache
        uid2 = await client.authenticate()
        
        assert uid1 == uid2 == 2
        # Should only call API once
        mock_session.post.assert_called_once()

    async def test_authenticate_failure(self, client: OdooAsyncClient, mock_session: AsyncMock) -> None:
        """Test authentication failure."""
        # Mock error response with proper fault structure
        mock_response = AsyncMock()
        mock_response.read.return_value = b'<?xml version="1.0"?><methodResponse><fault><value><struct><member><name>faultString</name><value><string>Invalid credentials</string></value></member><member><name>faultCode</name><value><int>2</int></value></member></struct></value></fault></methodResponse>'
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        with pytest.raises(AuthenticationError, match="Invalid credentials"):
            await client.authenticate()

    async def test_execute_kw_auto_authenticates(self, client: OdooAsyncClient, mock_session: AsyncMock) -> None:
        """Test that execute_kw automatically authenticates if needed."""
        # Mock authentication response
        auth_response = AsyncMock()
        auth_response.read.return_value = b'<?xml version="1.0"?><methodResponse><params><param><value><int>2</int></value></param></params></methodResponse>'
        
        # Mock execute response
        exec_response = AsyncMock()
        exec_response.read.return_value = b'<?xml version="1.0"?><methodResponse><params><param><value><array><data><value><int>1</int></value></data></array></value></param></params></methodResponse>'
        
        mock_session.post.return_value.__aenter__.side_effect = [auth_response, exec_response]
        
        result = await client.execute_kw("res.partner", "search", [[]])
        assert result == [1]
        
        # Should call authenticate then execute
        assert mock_session.post.call_count == 2

    async def test_execute_kw_with_args_and_kwargs(self, client: OdooAsyncClient, mock_session: AsyncMock) -> None:
        """Test execute_kw with both args and kwargs."""
        client._uid = 2  # Pre-authenticated
        
        # Mock execute response
        exec_response = AsyncMock()
        exec_response.read.return_value = b'<?xml version="1.0"?><methodResponse><params><param><value><boolean>1</boolean></value></param></params></methodResponse>'
        mock_session.post.return_value.__aenter__.return_value = exec_response
        
        result = await client.execute_kw(
            "res.partner",
            "write",
            [[1], {"name": "Test Partner"}],
            {"context": {"lang": "en_US"}}
        )
        assert result is True

    async def test_connection_timeout(self, client: OdooAsyncClient, mock_session: AsyncMock) -> None:
        """Test connection timeout handling."""
        mock_session.post.side_effect = asyncio.TimeoutError("Connection timeout")
        
        with pytest.raises(ConnectionError, match="Connection timeout"):
            await client.authenticate()
