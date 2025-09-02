"""Connection management for Odoo instances."""

import asyncio
import xmlrpc.client
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, Optional, Protocol

import aiohttp

from .errors import AuthenticationError, ConnectionError, parse_odoo_error


@dataclass
class OdooConnectionConfig:
    """Configuration for an Odoo connection."""
    
    url: str
    database: str
    username: str
    password: str
    timeout: int = 30
    max_connections: int = 10


class OdooConnection(Protocol):
    """Protocol for Odoo connections."""
    
    async def execute(self, model: str, method: str, *args, **kwargs) -> Any:
        """Execute a method on an Odoo model."""
        ...
    
    async def authenticate(self) -> int:
        """Authenticate and return user ID."""
        ...


class OdooAsyncClient:
    """Async client for Odoo XML-RPC operations."""
    
    def __init__(self, session: aiohttp.ClientSession, config: OdooConnectionConfig):
        """Initialize the async client.
        
        Args:
            session: aiohttp session for making requests
            config: Connection configuration
        """
        self.session = session
        self.config = config
        self._uid: Optional[int] = None
    
    async def authenticate(self) -> int:
        """Authenticate with Odoo and get user ID.
        
        Returns:
            User ID
            
        Raises:
            AuthenticationError: If authentication fails
            ConnectionError: If connection fails
        """
        if self._uid:
            return self._uid
        
        endpoint = f"{self.config.url}/xmlrpc/2/common"
        
        # Build XML-RPC request
        params = xmlrpc.client.dumps(
            (self.config.database, self.config.username, self.config.password, {}),
            'authenticate'
        )
        
        try:
            async with self.session.post(
                endpoint,
                data=params,
                headers={'Content-Type': 'text/xml'}
            ) as response:
                response_data = await response.read()
                
                # Parse XML-RPC response
                try:
                    result, method_name = xmlrpc.client.loads(response_data)
                    if result and result[0]:
                        self._uid = int(result[0])
                        return self._uid
                    else:
                        raise AuthenticationError(
                            "Authentication failed: Invalid credentials"
                        )
                except xmlrpc.client.Fault as fault:
                    # Handle XML-RPC fault
                    if "Invalid credentials" in fault.faultString:
                        raise AuthenticationError(fault.faultString)
                    else:
                        raise ConnectionError(
                            f"XML-RPC fault: {fault.faultString}",
                            {"code": fault.faultCode}
                        ) from fault
                        
        except asyncio.TimeoutError as e:
            raise ConnectionError(
                "Connection timeout during authentication",
                {"timeout": self.config.timeout}
            ) from e
        except aiohttp.ClientError as e:
            raise ConnectionError(
                f"Connection error: {str(e)}",
                {"url": endpoint}
            ) from e
    
    async def execute_kw(
        self,
        model: str,
        method: str,
        args: list[Any],
        kwargs: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute a method on an Odoo model.
        
        Args:
            model: Odoo model name (e.g., 'res.partner')
            method: Method name (e.g., 'search', 'read', 'create')
            args: Positional arguments for the method
            kwargs: Keyword arguments for the method
            
        Returns:
            Method result
            
        Raises:
            Various OdooMCPError subclasses based on the error
        """
        if not self._uid:
            await self.authenticate()
        
        endpoint = f"{self.config.url}/xmlrpc/2/object"
        kwargs = kwargs or {}
        
        # Build XML-RPC request
        params = xmlrpc.client.dumps(
            (
                self.config.database,
                self._uid,
                self.config.password,
                model,
                method,
                args,
                kwargs
            ),
            'execute_kw'
        )
        
        try:
            async with self.session.post(
                endpoint,
                data=params,
                headers={'Content-Type': 'text/xml'}
            ) as response:
                response_data = await response.read()
                
                # Parse XML-RPC response
                try:
                    result, method_name = xmlrpc.client.loads(response_data)
                    return result[0] if result else None
                except xmlrpc.client.Fault as fault:
                    # Parse Odoo error and raise appropriate exception
                    error_data = {
                        "message": fault.faultString,
                        "data": {
                            "name": "xmlrpc.Fault",
                            "debug": fault.faultString,
                        }
                    }
                    raise parse_odoo_error(error_data) from fault
                    
        except asyncio.TimeoutError as e:
            raise ConnectionError(
                f"Timeout executing {method} on {model}",
                {"timeout": self.config.timeout, "model": model, "method": method}
            ) from e
        except aiohttp.ClientError as e:
            raise ConnectionError(
                f"Connection error: {str(e)}",
                {"url": endpoint, "model": model, "method": method}
            ) from e


class ConnectionPoolManager:
    """Manages connection pools for multiple Odoo instances."""
    
    def __init__(self) -> None:
        """Initialize the connection pool manager."""
        self._pools: Dict[str, aiohttp.TCPConnector] = {}
        self._sessions: Dict[str, aiohttp.ClientSession] = {}
        self._configs: Dict[str, OdooConnectionConfig] = {}
        self._connectors: Dict[str, aiohttp.TCPConnector] = {}
        self._lock = asyncio.Lock()
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the pool manager."""
        self._initialized = True
    
    async def add_connection(
        self,
        instance_id: str,
        config: OdooConnectionConfig
    ) -> None:
        """Add a new Odoo instance connection.
        
        Args:
            instance_id: Unique identifier for the instance
            config: Connection configuration
        """
        async with self._lock:
            # Create connector with connection limits
            connector = aiohttp.TCPConnector(
                limit=config.max_connections,
                limit_per_host=config.max_connections,
                force_close=True,
                enable_cleanup_closed=True
            )
            
            # Create session with timeout
            session = aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=config.timeout)
            )
            
            # Store references
            self._connectors[instance_id] = connector
            self._sessions[instance_id] = session
            self._configs[instance_id] = config
    
    @asynccontextmanager
    async def get_connection(self, instance_id: str) -> AsyncIterator[OdooAsyncClient]:
        """Get a connection from the pool.
        
        Args:
            instance_id: Instance identifier
            
        Yields:
            OdooAsyncClient instance
            
        Raises:
            ValueError: If instance not found
        """
        if instance_id not in self._sessions:
            raise ValueError(f"No connection for instance: {instance_id}")
        
        client = OdooAsyncClient(
            session=self._sessions[instance_id],
            config=self._configs[instance_id]
        )
        
        yield client
    
    async def remove_connection(self, instance_id: str) -> None:
        """Remove a connection from the pool.
        
        Args:
            instance_id: Instance identifier
        """
        async with self._lock:
            if instance_id in self._sessions:
                # Close session
                await self._sessions[instance_id].close()
                
                # Remove references
                del self._sessions[instance_id]
                del self._configs[instance_id]
                del self._connectors[instance_id]
    
    async def cleanup(self) -> None:
        """Clean up all connections."""
        async with self._lock:
            # Close all sessions
            for session in self._sessions.values():
                await session.close()
            
            # Clear all references
            self._sessions.clear()
            self._configs.clear()
            self._connectors.clear()
            self._initialized = False
