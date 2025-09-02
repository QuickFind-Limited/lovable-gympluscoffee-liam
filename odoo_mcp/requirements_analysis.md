# Odoo MCP Integration Requirements Analysis

## Executive Summary

This document outlines the key requirements and best practices for building a FastMCP server that integrates with Odoo 17's API. The integration will provide async Python access to Odoo's XML-RPC/JSON-RPC interfaces through the Model Context Protocol.

## Key Integration Patterns

### 1. Odoo API Authentication & Connection

**XML-RPC Endpoints:**
- Authentication: `/xmlrpc/2/common`
- Object operations: `/xmlrpc/2/object`

**Authentication Requirements:**
```python
# Standard synchronous pattern
import xmlrpc.client

url = 'https://yourcompany.odoo.com'
db = 'yourcompany'
username = 'your_user@example.com'
password = 'your_password'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
```

**Important Constraints:**
- API access requires Custom Odoo pricing plan (not available on Free/Standard)
- Odoo Online requires password setup via UI for API users
- Custom models must start with `x_` prefix
- State must be set to 'manual' for custom models

### 2. FastMCP Server Architecture

**Core Patterns:**
```python
from fastmcp import FastMCP
import httpx
from contextlib import asynccontextmanager

# Lifespan management for connections
@asynccontextmanager
async def app_lifespan(server: FastMCP):
    # Initialize Odoo connection
    odoo_client = await OdooAsyncClient.connect()
    yield {"odoo": odoo_client}
    # Cleanup
    await odoo_client.disconnect()

mcp = FastMCP("Odoo-MCP", lifespan=app_lifespan)

# Async tool pattern
@mcp.tool
async def search_records(model: str, domain: list, fields: list = None) -> list:
    """Search Odoo records with domain filters"""
    async with httpx.AsyncClient() as client:
        # Implementation using async XML-RPC
        pass
```

**Best Practices:**
- Use `@mcp.tool` decorator for all Odoo operations
- Implement async handlers for I/O operations
- Use `run_async()` in async contexts, `run()` in sync
- Handle errors gracefully with proper exception handling

### 3. Async XML-RPC Implementation

**Library Options:**
1. **aiohttp-xmlrpc** - Based on aiohttp and lxml
2. **aioxmlrpc** - Based on httpx

**Example async pattern:**
```python
from aiohttp_xmlrpc.client import ServerProxy
import asyncio

async def odoo_async_auth(url, db, username, password):
    async with ServerProxy(f"{url}/xmlrpc/2/common") as common:
        uid = await common.authenticate(db, username, password, {})
    return uid

async def odoo_async_search(url, db, uid, password, model, domain):
    async with ServerProxy(f"{url}/xmlrpc/2/object") as models:
        records = await models.execute_kw(
            db, uid, password,
            model, 'search_read',
            [domain],
            {'fields': ['name', 'id']}
        )
    return records
```

### 4. Common Pitfalls to Avoid

1. **Authentication Issues:**
   - Not setting password for API users on Odoo Online
   - Using wrong database name (instance name for Odoo Online)
   - Not handling authentication token refresh

2. **API Limitations:**
   - Trying to use API on Free/Standard pricing plans
   - Not respecting rate limits
   - Attempting to add methods to custom models (only fields allowed)

3. **Async Programming:**
   - Calling `run()` from inside async functions
   - Not properly handling connection pooling
   - Blocking operations in async handlers

4. **Security:**
   - Hardcoding credentials
   - Not using HTTPS for connections
   - Missing input validation for user-provided domains

### 5. Recommended MCP Tools Structure

```python
# Core CRUD operations
@mcp.tool
async def create_record(model: str, values: dict) -> int
@mcp.tool
async def read_records(model: str, ids: list, fields: list = None) -> list
@mcp.tool
async def update_record(model: str, id: int, values: dict) -> bool
@mcp.tool
async def delete_records(model: str, ids: list) -> bool

# Search operations
@mcp.tool
async def search_records(model: str, domain: list, limit: int = None) -> list
@mcp.tool
async def search_count(model: str, domain: list) -> int

# Advanced operations
@mcp.tool
async def execute_workflow(model: str, id: int, signal: str) -> bool
@mcp.tool
async def get_fields(model: str) -> dict
@mcp.tool
async def get_metadata(model: str, ids: list) -> list
```

### 6. Modern Alternatives

Consider implementing both XML-RPC and JSON-RPC:
- **JSON-RPC**: Better permission handling, more RESTful
- **GraphQL-like queries**: Use `web_search_read` for complex queries
- **Batch operations**: Group multiple operations for performance

### 7. Performance Optimizations

1. **Connection Pooling**: Reuse connections across requests
2. **Batch Operations**: Send multiple operations in single call
3. **Field Selection**: Only request needed fields
4. **Pagination**: Implement proper pagination for large datasets
5. **Caching**: Cache frequently accessed metadata

## Conclusion

Building an Odoo MCP server requires careful attention to:
- Async patterns for non-blocking operations
- Proper authentication and session management
- Error handling and retry logic
- Security best practices
- Performance optimization

The combination of FastMCP's async capabilities with Odoo's powerful API provides a robust foundation for AI-assisted ERP operations.