"""Global pytest configuration and fixtures for Odoo MCP tests."""

import asyncio
import os
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple
import aiohttp
import pytest
from dotenv import load_dotenv

# Load test environment variables
load_dotenv()


class OdooTestConnection:
    """Test connection to real Odoo instance."""

    def __init__(self, session: aiohttp.ClientSession, url: str, db: str, username: str, password: str) -> None:
        """Initialize Odoo test connection."""
        self.session = session
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.uid: Optional[int] = None
        self._created_records: List[Tuple[str, int]] = []

    async def authenticate(self) -> None:
        """Authenticate with Odoo instance."""
        auth_url = f"{self.url}/jsonrpc"
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "common",
                "method": "authenticate",
                "args": [self.db, self.username, self.password, {}],
            },
            "id": 1,
        }
        
        async with self.session.post(auth_url, json=payload) as resp:
            result = await resp.json()
            if "error" in result:
                raise Exception(f"Authentication failed: {result['error']}")
            self.uid = result["result"]
            if not self.uid:
                raise Exception("Authentication failed: Invalid credentials")

    async def execute(
        self, model: str, method: str, args: List[Any], kwargs: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute an Odoo API method."""
        if not self.uid:
            await self.authenticate()

        execute_url = f"{self.url}/jsonrpc"
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "object",
                "method": "execute_kw",
                "args": [
                    self.db,
                    self.uid,
                    self.password,
                    model,
                    method,
                    args,
                    kwargs or {},
                ],
            },
            "id": 2,
        }

        async with self.session.post(execute_url, json=payload) as resp:
            result = await resp.json()
            if "error" in result:
                raise Exception(f"API call failed: {result['error']}")
            
            # Track created records for cleanup
            if method == "create" and isinstance(result.get("result"), int):
                self._created_records.append((model, result["result"]))
            
            return result["result"]

    async def cleanup(self) -> None:
        """Clean up all created test records."""
        # Delete in reverse order to handle dependencies
        for model, record_id in reversed(self._created_records):
            try:
                await self.execute(model, "unlink", [[record_id]])
            except Exception:
                # Record might already be deleted by cascade
                pass
        self._created_records.clear()

    async def close(self) -> None:
        """Close the connection."""
        await self.cleanup()


@pytest.fixture
async def odoo_connection() -> AsyncGenerator[OdooTestConnection, None]:
    """Create an Odoo connection for testing."""
    # Get test credentials from environment
    url = os.getenv("TEST_ODOO_URL", "https://source2.odoo.com")
    db = os.getenv("TEST_ODOO_DATABASE", "source2")
    username = os.getenv("TEST_ODOO_USERNAME", "")
    password = os.getenv("TEST_ODOO_PASSWORD", "")

    if not all([url, db, username, password]):
        pytest.skip("Odoo test credentials not configured")

    # Create session with proper configuration
    connector = aiohttp.TCPConnector(limit=10, force_close=True)
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        conn = OdooTestConnection(session, url, db, username, password)
        await conn.authenticate()
        
        yield conn
        
        # Cleanup any created test data
        await conn.close()


@pytest.fixture
def test_partner_data() -> Dict[str, Any]:
    """Sample partner data for testing."""
    return {
        "name": "Test Partner MCP",
        "email": "test.mcp@example.com",
        "phone": "+1234567890",
        "is_company": False,
    }


@pytest.fixture
def test_product_data() -> Dict[str, Any]:
    """Sample product data for testing."""
    return {
        "name": "Test Product MCP",
        "type": "consu",  # Consumable
        "list_price": 100.0,
        "standard_price": 50.0,
        "categ_id": 1,  # Default category
    }


@pytest.fixture
def test_sale_order_data() -> Dict[str, Any]:
    """Sample sale order data for testing."""
    return {
        "partner_id": None,  # Will be set in test
        "date_order": "2025-01-26",
        "state": "draft",
    }


# Helper functions for tests
async def create_test_record(
    conn: OdooTestConnection, model: str, values: Dict[str, Any]
) -> int:
    """Create a test record and track it for cleanup."""
    record_id = await conn.execute(model, "create", [values])
    return record_id


async def read_test_record(
    conn: OdooTestConnection, model: str, record_id: int, fields: List[str]
) -> Dict[str, Any]:
    """Read a test record."""
    records = await conn.execute(model, "read", [[record_id], fields])
    return records[0] if records else {}