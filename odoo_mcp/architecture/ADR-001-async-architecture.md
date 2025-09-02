# ADR-001: Async-First Architecture with aiohttp

## Status
Accepted

## Context
The Odoo MCP Server needs to handle multiple concurrent requests to different Odoo instances while maintaining sub-second response times for read operations. Traditional synchronous XML-RPC clients like Python's built-in `xmlrpc.client` would block the event loop and limit concurrency.

## Decision
We will implement a fully asynchronous architecture using:
- `aiohttp` as the HTTP client library
- Custom async XML-RPC/JSON-RPC client implementation
- `asyncio` for concurrency management
- Connection pooling per Odoo instance

## Consequences

### Positive
- Non-blocking I/O enables handling 100+ concurrent operations
- Better resource utilization with connection pooling
- Improved response times through parallel execution
- Natural fit with FastMCP's async design

### Negative
- Increased complexity in error handling
- Requires careful management of connection lifecycle
- All code must be async-aware
- Debugging async code is more challenging

### Mitigation
- Comprehensive error handling with retry logic
- Extensive logging for debugging
- Strong type hints for better IDE support
- Thorough testing with real Odoo instances

## Implementation Details

```python
# Example async client pattern
class OdooAsyncClient:
    async def execute_kw(self, model: str, method: str, args: List[Any]) -> Any:
        async with self.session.post(
            f"{self.url}/xmlrpc/2/object",
            data=self._build_request(model, method, args),
            headers={'Content-Type': 'text/xml'}
        ) as response:
            return await self._parse_response(response)
```

## References
- [aiohttp documentation](https://docs.aiohttp.org/)
- [FastMCP async patterns](https://github.com/modelcontextprotocol/fastmcp)
- [Python asyncio best practices](https://docs.python.org/3/library/asyncio.html)