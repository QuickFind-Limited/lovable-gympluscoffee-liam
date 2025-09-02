# ADR-002: Per-Instance Connection Pooling

## Status
Accepted

## Context
The MCP server needs to connect to multiple Odoo instances simultaneously, each potentially having different configurations, rate limits, and performance characteristics. A single global connection pool would not provide adequate isolation or control.

## Decision
Implement per-instance connection pooling with:
- Separate `aiohttp.TCPConnector` for each Odoo instance
- Configurable pool size per instance
- Rate limiting using `asyncio.Semaphore`
- Health checking and automatic reconnection

## Consequences

### Positive
- Isolation between different Odoo instances
- Per-instance configuration flexibility
- Better rate limit management
- Prevents one slow instance from affecting others

### Negative
- Higher memory usage (multiple pools)
- More complex connection management
- Need to track metrics per pool

### Mitigation
- Implement connection pool cleanup for idle instances
- Monitor and alert on pool exhaustion
- Provide configuration to limit total connections

## Implementation Details

```python
class ConnectionPoolManager:
    def __init__(self):
        self._pools: Dict[str, aiohttp.TCPConnector] = {}
        self._semaphores: Dict[str, asyncio.Semaphore] = {}
        
    async def add_connection(self, instance_id: str, config: OdooConnectionConfig):
        connector = aiohttp.TCPConnector(
            limit=config.max_connections,
            limit_per_host=config.max_connections,
            force_close=True
        )
        self._pools[instance_id] = connector
        self._semaphores[instance_id] = asyncio.Semaphore(config.max_connections)
```

## Alternatives Considered
1. **Single global pool**: Simpler but no isolation
2. **No pooling**: Poor performance
3. **Thread pool**: Not compatible with async architecture

## References
- [aiohttp connection pooling](https://docs.aiohttp.org/en/stable/client_advanced.html#connectors)
- [asyncio semaphore patterns](https://docs.python.org/3/library/asyncio-sync.html#semaphore)