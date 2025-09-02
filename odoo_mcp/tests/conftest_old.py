"""Global pytest configuration and fixtures for Odoo MCP tests."""

import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from typing import Any, Protocol

import aiohttp
import pytest
import pytest_asyncio
from dotenv import load_dotenv

# Load test environment variables
load_dotenv()


class OdooConnection(Protocol):
    """Protocol for Odoo connection handling."""

    async def execute(
        self, model: str, method: str, args: list[Any], kwargs: dict[str, Any] | None = None
    ) -> Any:
        """Execute an Odoo API method."""
        ...

    async def close(self) -> None:
        """Close the connection."""
        ...


class OdooTestConnection:
    """Test connection to real Odoo instance."""

    def __init__(self, session: aiohttp.ClientSession, url: str, db: str, username: str, password: str) -> None:
        """Initialize Odoo test connection."""
        self.session = session
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.uid: int | None = None
        self._created_records: list[tuple[str, int]] = []

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
        self, model: str, method: str, args: list[Any], kwargs: dict[str, Any] | None = None
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


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def aiohttp_session() -> AsyncGenerator[aiohttp.ClientSession, None]:
    """Create a shared aiohttp session for all tests."""
    connector = aiohttp.TCPConnector(limit=100, force_close=True)
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        yield session


@pytest_asyncio.fixture
async def odoo_connection(aiohttp_session: aiohttp.ClientSession) -> AsyncGenerator[OdooTestConnection, None]:
    """Create an Odoo connection for testing."""
    # Get test credentials from environment
    url = os.getenv("TEST_ODOO_URL", "https://source2.odoo.com")
    db = os.getenv("TEST_ODOO_DATABASE", "source2")
    username = os.getenv("TEST_ODOO_USERNAME", "")
    password = os.getenv("TEST_ODOO_PASSWORD", "")

    if not all([url, db, username, password]):
        pytest.skip("Odoo test credentials not configured")

    conn = OdooTestConnection(aiohttp_session, url, db, username, password)
    await conn.authenticate()
    
    yield conn
    
    # Cleanup any created test data
    await conn.close()


@pytest.fixture
def test_partner_data() -> dict[str, Any]:
    """Sample partner data for testing."""
    return {
        "name": "Test Partner MCP",
        "email": "test.mcp@example.com",
        "phone": "+1234567890",
        "is_company": False,
        "customer_rank": 1,
        "supplier_rank": 0,
    }


@pytest.fixture
def test_product_data() -> dict[str, Any]:
    """Sample product data for testing."""
    return {
        "name": "Test Product MCP",
        "type": "consu",  # Consumable
        "list_price": 100.0,
        "standard_price": 50.0,
        "categ_id": 1,  # Default category
    }


@pytest.fixture
def test_sale_order_data() -> dict[str, Any]:
    """Sample sale order data for testing."""
    return {
        "partner_id": None,  # Will be set in test
        "date_order": "2025-01-26",
        "state": "draft",
    }


@pytest.fixture(autouse=True)
async def cleanup_test_data(request: pytest.FixtureRequest) -> AsyncGenerator[None, None]:
    """Automatically cleanup test data after each test."""
    # Run the test
    yield
    
    # Cleanup is handled by the odoo_connection fixture


@pytest.fixture
def skip_if_no_odoo(odoo_connection: OdooTestConnection) -> None:
    """Skip test if Odoo connection is not available."""
    if not odoo_connection:
        pytest.skip("Odoo connection not available")


# Test helpers
async def create_test_record(
    conn: OdooTestConnection, model: str, data: dict[str, Any]
) -> int:
    """Create a test record and return its ID."""
    return await conn.execute(model, "create", [data])


async def read_test_record(
    conn: OdooTestConnection, model: str, record_id: int, fields: list[str] | None = None
) -> dict[str, Any]:
    """Read a test record by ID."""
    records = await conn.execute(model, "read", [[record_id], fields or []])
    return records[0] if records else {}


async def search_test_records(
    conn: OdooTestConnection, model: str, domain: list[Any], limit: int | None = None
) -> list[int]:
    """Search for test records."""
    kwargs = {"limit": limit} if limit else {}
    return await conn.execute(model, "search", [domain], kwargs)


async def delete_test_record(conn: OdooTestConnection, model: str, record_id: int) -> bool:
    """Delete a test record."""
    return await conn.execute(model, "unlink", [[record_id]])