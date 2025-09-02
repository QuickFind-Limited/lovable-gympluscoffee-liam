#!/usr/bin/env python3
"""
Odoo Connection Manager
======================

Handles XML-RPC connections to Odoo with connection pooling,
retry logic, and robust error handling.

Agent: Connection Management Specialist
"""

import xmlrpc.client
import logging
import time
from contextlib import contextmanager
from typing import Optional, Dict, Any
from dataclasses import dataclass
import threading
import socket


@dataclass
class ConnectionConfig:
    """Connection configuration parameters"""
    url: str
    db: str
    username: str
    password: str
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 2.0


class OdooConnection:
    """
    Odoo XML-RPC Connection Wrapper
    ==============================
    
    Provides authenticated connection with automatic retry
    and error handling capabilities.
    """
    
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._common = None
        self._models = None
        self._uid = None
        self._authenticated = False
        self._lock = threading.Lock()
    
    def authenticate(self) -> bool:
        """
        Authenticate with Odoo server
        
        Returns:
            bool: True if authentication successful
        """
        with self._lock:
            try:
                if self._authenticated:
                    return True
                
                # Create common endpoint connection
                self._common = xmlrpc.client.ServerProxy(
                    f'{self.config.url}/xmlrpc/2/common',
                    timeout=self.config.timeout,
                    allow_none=True
                )
                
                # Test server version (validates connection)
                version_info = self._common.version()
                self.logger.info(f"Connected to Odoo {version_info.get('server_version', 'unknown')}")
                
                # Authenticate user
                self._uid = self._common.authenticate(
                    self.config.db,
                    self.config.username,
                    self.config.password,
                    {}
                )
                
                if not self._uid:
                    self.logger.error("Authentication failed - invalid credentials")
                    return False
                
                # Create models endpoint connection
                self._models = xmlrpc.client.ServerProxy(
                    f'{self.config.url}/xmlrpc/2/object',
                    timeout=self.config.timeout,
                    allow_none=True
                )
                
                self._authenticated = True
                self.logger.info(f"Authenticated as user ID: {self._uid}")
                
                return True
                
            except xmlrpc.client.Fault as e:
                self.logger.error(f"XML-RPC authentication fault: {e}")
                return False
            except (ConnectionError, socket.timeout, socket.error) as e:
                self.logger.error(f"Connection error during authentication: {e}")
                return False
            except Exception as e:
                self.logger.error(f"Unexpected error during authentication: {e}")
                return False
    
    def execute_kw(self, model: str, method: str, args: list, kwargs: dict = None) -> Any:
        """
        Execute Odoo model method with retry logic
        
        Args:
            model: Odoo model name (e.g., 'product.product')
            method: Method to execute (e.g., 'search', 'read', 'create')
            args: Method arguments
            kwargs: Method keyword arguments
            
        Returns:
            Method execution result
        """
        if not self._authenticated and not self.authenticate():
            raise ConnectionError("Not authenticated and authentication failed")
        
        if kwargs is None:
            kwargs = {}
        
        # Retry logic for transient errors
        last_exception = None
        
        for attempt in range(self.config.max_retries):
            try:
                result = self._models.execute_kw(
                    self.config.db,
                    self._uid,
                    self.config.password,
                    model,
                    method,
                    args,
                    kwargs
                )
                
                return result
                
            except xmlrpc.client.Fault as e:
                # Don't retry server-side validation errors
                if 'ValidationError' in str(e) or 'UserError' in str(e):
                    self.logger.error(f"Server validation error: {e}")
                    raise
                
                self.logger.warning(f"XML-RPC fault on attempt {attempt + 1}: {e}")
                last_exception = e
                
                # Try to re-authenticate on auth errors
                if 'Access Denied' in str(e):
                    self._authenticated = False
                    if not self.authenticate():
                        raise ConnectionError("Re-authentication failed")
                
            except (ConnectionError, socket.timeout, socket.error) as e:
                self.logger.warning(f"Connection error on attempt {attempt + 1}: {e}")
                last_exception = e
                
                # Reset connection on network errors
                self._authenticated = False
                self._common = None
                self._models = None
                
                # Try to re-establish connection
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (2 ** attempt))  # Exponential backoff
                    if not self.authenticate():
                        continue
            
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                raise
        
        # All retries failed
        raise ConnectionError(f"Failed after {self.config.max_retries} attempts. Last error: {last_exception}")
    
    def test_connection(self) -> bool:
        """
        Test connection health
        
        Returns:
            bool: True if connection is healthy
        """
        try:
            # Simple test - get current user info
            result = self.execute_kw('res.users', 'read', [[self._uid]], {'fields': ['name']})
            return bool(result)
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
    
    def close(self):
        """Close connection and cleanup resources"""
        with self._lock:
            self._authenticated = False
            self._common = None
            self._models = None
            self._uid = None
            self.logger.debug("Connection closed")


class OdooConnectionManager:
    """
    Odoo Connection Manager with Pooling
    ====================================
    
    Manages multiple connections with connection pooling,
    health checks, and automatic reconnection.
    """
    
    def __init__(self, config):
        self.config = ConnectionConfig(
            url=config.url,
            db=config.db,
            username=config.username,
            password=config.password,
            timeout=config.connection_timeout,
            max_retries=config.max_retries,
            retry_delay=config.retry_delay
        )
        self.logger = logging.getLogger(__name__)
        self._pool = []
        self._pool_lock = threading.Lock()
        self._max_pool_size = 5
    
    @contextmanager
    def get_connection(self):
        """
        Get connection from pool or create new one
        
        Yields:
            OdooConnection: Authenticated connection instance
        """
        connection = None
        
        try:
            # Try to get connection from pool
            with self._pool_lock:
                if self._pool:
                    connection = self._pool.pop()
                    
                    # Test connection health
                    if not connection.test_connection():
                        self.logger.info("Pooled connection unhealthy, creating new one")
                        connection.close()
                        connection = None
            
            # Create new connection if needed
            if connection is None:
                connection = OdooConnection(self.config)
                if not connection.authenticate():
                    raise ConnectionError("Failed to authenticate new connection")
                
                self.logger.debug("Created new Odoo connection")
            
            yield connection
            
        finally:
            # Return connection to pool if healthy
            if connection:
                with self._pool_lock:
                    if len(self._pool) < self._max_pool_size and connection.test_connection():
                        self._pool.append(connection)
                        self.logger.debug("Returned connection to pool")
                    else:
                        connection.close()
                        self.logger.debug("Closed connection (pool full or unhealthy)")
    
    def test_connection_config(self) -> Dict[str, Any]:
        """
        Test connection configuration
        
        Returns:
            dict: Connection test results
        """
        results = {
            'success': False,
            'error': None,
            'server_version': None,
            'user_id': None,
            'database': self.config.db
        }
        
        try:
            with self.get_connection() as conn:
                # Get server version
                version_info = conn._common.version()
                results['server_version'] = version_info.get('server_version')
                results['user_id'] = conn._uid
                results['success'] = True
                
        except Exception as e:
            results['error'] = str(e)
            self.logger.error(f"Connection test failed: {e}")
        
        return results
    
    def cleanup_pool(self):
        """Close all pooled connections"""
        with self._pool_lock:
            for connection in self._pool:
                connection.close()
            self._pool.clear()
            self.logger.info("Connection pool cleaned up")
    
    def get_pool_stats(self) -> Dict[str, int]:
        """Get connection pool statistics"""
        with self._pool_lock:
            return {
                'pooled_connections': len(self._pool),
                'max_pool_size': self._max_pool_size
            }