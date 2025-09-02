# Odoo MCP Server - C4 Architecture Diagrams

## Level 1: System Context Diagram

```mermaid
C4Context
    title System Context diagram for Odoo MCP Server

    Person(ai_agent, "AI Agent", "Claude or other AI agents using MCP protocol")
    Person(developer, "Developer", "Source platform developers")
    
    System_Boundary(mcp_boundary, "Source Platform") {
        System(odoo_mcp, "Odoo MCP Server", "Provides AI agents with access to Odoo ERP data and operations")
    }
    
    System_Ext(odoo1, "Client Odoo Instance", "Customer's Odoo ERP system")
    System_Ext(odoo2, "Test Odoo Instance", "source2.odoo.com test environment")
    
    Rel(ai_agent, odoo_mcp, "Uses", "MCP Protocol")
    Rel(developer, odoo_mcp, "Configures & monitors")
    Rel(odoo_mcp, odoo1, "Reads/writes data", "XML-RPC/JSON-RPC over HTTPS")
    Rel(odoo_mcp, odoo2, "Tests against", "XML-RPC/JSON-RPC over HTTPS")
    
    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

## Level 2: Container Diagram

```mermaid
C4Container
    title Container diagram for Odoo MCP Server

    Person(ai_agent, "AI Agent", "Claude or other AI agents")
    
    System_Boundary(mcp_system, "Odoo MCP Server") {
        Container(mcp_server, "MCP Server", "Python 3.13, FastMCP", "Handles MCP protocol communication")
        Container(connection_pool, "Connection Pool", "Python, aiohttp", "Manages Odoo connections")
        Container(async_client, "Async Client", "Python, aiohttp", "XML-RPC/JSON-RPC client")
        Container(tool_registry, "Tool Registry", "Python", "MCP tool implementations")
        Container(resource_handler, "Resource Handler", "Python", "URI-based resource access")
        Container(auth_manager, "Auth Manager", "Python, cryptography", "Credential encryption")
        Container(cache_layer, "Cache Layer", "Python", "LRU cache for performance")
        Container(metrics, "Metrics Collector", "Python, prometheus", "Performance monitoring")
    }
    
    System_Ext(odoo, "Odoo Instance", "Customer ERP system")
    
    Rel(ai_agent, mcp_server, "Sends requests", "MCP Protocol")
    Rel(mcp_server, tool_registry, "Routes tool calls")
    Rel(mcp_server, resource_handler, "Routes resource requests")
    Rel(tool_registry, connection_pool, "Gets connections")
    Rel(resource_handler, connection_pool, "Gets connections")
    Rel(connection_pool, async_client, "Creates clients")
    Rel(async_client, odoo, "API calls", "XML-RPC/HTTPS")
    Rel(connection_pool, auth_manager, "Gets credentials")
    Rel(tool_registry, cache_layer, "Caches results")
    Rel(metrics, mcp_server, "Collects metrics")
    
    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

## Level 3: Component Diagram - Connection Pool

```mermaid
C4Component
    title Component diagram for Connection Pool Manager

    Container_Boundary(connection_pool, "Connection Pool Manager") {
        Component(pool_manager, "Pool Manager", "Python class", "Manages connection lifecycle")
        Component(connection_config, "Connection Config", "TypedDict", "Type-safe configuration")
        Component(session_factory, "Session Factory", "Python", "Creates aiohttp sessions")
        Component(health_checker, "Health Checker", "Python", "Validates connections")
        Component(rate_limiter, "Rate Limiter", "asyncio.Semaphore", "Prevents API overload")
        Component(connection_metrics, "Metrics", "Python", "Tracks performance")
    }
    
    Container_Ext(async_client, "Async Client", "Uses connections")
    Container_Ext(auth_manager, "Auth Manager", "Provides credentials")
    
    Rel(pool_manager, connection_config, "Uses")
    Rel(pool_manager, session_factory, "Creates sessions")
    Rel(pool_manager, health_checker, "Validates")
    Rel(pool_manager, rate_limiter, "Enforces limits")
    Rel(pool_manager, connection_metrics, "Records metrics")
    Rel(async_client, pool_manager, "Requests connection")
    Rel(pool_manager, auth_manager, "Gets credentials")
    
    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

## Level 3: Component Diagram - Tool Registry

```mermaid
C4Component
    title Component diagram for Tool Registry

    Container_Boundary(tool_registry, "Tool Registry") {
        Component(crud_tools, "CRUD Tools", "MCP Tools", "Create, Read, Update, Delete")
        Component(search_tools, "Search Tools", "MCP Tools", "Search and filter operations")
        Component(batch_tools, "Batch Tools", "MCP Tools", "Bulk operations")
        Component(workflow_tools, "Workflow Tools", "MCP Tools", "Execute Odoo workflows")
        Component(metadata_tools, "Metadata Tools", "MCP Tools", "Model introspection")
        Component(tool_validator, "Tool Validator", "Python", "Input validation")
    }
    
    Container_Ext(mcp_server, "MCP Server", "Routes requests")
    Container_Ext(connection_pool, "Connection Pool", "Provides connections")
    Container_Ext(cache_layer, "Cache Layer", "Caches results")
    
    Rel(mcp_server, crud_tools, "Invokes")
    Rel(mcp_server, search_tools, "Invokes")
    Rel(mcp_server, batch_tools, "Invokes")
    Rel(crud_tools, tool_validator, "Validates input")
    Rel(search_tools, tool_validator, "Validates input")
    Rel(crud_tools, connection_pool, "Gets connection")
    Rel(search_tools, cache_layer, "Checks cache")
    
    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

## Level 3: Component Diagram - Async Client

```mermaid
C4Component
    title Component diagram for Async Odoo Client

    Container_Boundary(async_client, "Async Odoo Client") {
        Component(xmlrpc_client, "XML-RPC Client", "Python, aiohttp", "XML-RPC protocol handler")
        Component(jsonrpc_client, "JSON-RPC Client", "Python, aiohttp", "JSON-RPC protocol handler")
        Component(request_builder, "Request Builder", "Python", "Builds RPC requests")
        Component(response_parser, "Response Parser", "Python", "Parses RPC responses")
        Component(error_translator, "Error Translator", "Python", "Maps Odoo errors")
        Component(retry_handler, "Retry Handler", "Python", "Exponential backoff")
    }
    
    System_Ext(odoo, "Odoo Instance", "ERP system")
    Container_Ext(error_handler, "Error Handler", "Reports errors")
    
    Rel(xmlrpc_client, request_builder, "Uses")
    Rel(jsonrpc_client, request_builder, "Uses")
    Rel(xmlrpc_client, response_parser, "Uses")
    Rel(response_parser, error_translator, "Maps errors")
    Rel(error_translator, error_handler, "Reports")
    Rel(xmlrpc_client, retry_handler, "Retries on failure")
    Rel(xmlrpc_client, odoo, "API calls", "HTTPS")
    
    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

## Level 4: Code Diagram - Connection Pool Implementation

```mermaid
classDiagram
    class ConnectionPoolManager {
        -Dict pools
        -Dict sessions
        -Dict configs
        -asyncio.Lock lock
        +add_connection(instance_id, config)
        +get_connection(instance_id)
        +remove_connection(instance_id)
        +cleanup()
        +get_metrics(instance_id)
    }
    
    class OdooConnectionConfig {
        +str url
        +str database
        +str username
        +str password
        +int timeout
        +int max_connections
    }
    
    class OdooAsyncClient {
        -ClientSession session
        -OdooConnectionConfig config
        -Optional~int~ uid
        +authenticate()
        +execute_kw(model, method, args, kwargs)
        +search_read(model, domain, fields)
    }
    
    class ConnectionMetrics {
        +int total_requests
        +int failed_requests
        +float avg_response_time
        +datetime last_used
    }
    
    class HealthChecker {
        +check_connection(client)
        +validate_credentials(client)
        +ping(client)
    }
    
    ConnectionPoolManager --> OdooConnectionConfig : uses
    ConnectionPoolManager --> OdooAsyncClient : creates
    ConnectionPoolManager --> ConnectionMetrics : tracks
    ConnectionPoolManager --> HealthChecker : uses
    OdooAsyncClient --> OdooConnectionConfig : configured by
```

## Data Flow Sequence Diagrams

### Authentication Flow

```mermaid
sequenceDiagram
    participant Agent as AI Agent
    participant MCP as MCP Server
    participant Auth as Auth Manager
    participant Pool as Connection Pool
    participant Client as Async Client
    participant Odoo as Odoo Instance
    
    Agent->>MCP: Connect to instance
    MCP->>Auth: Get credentials
    Auth->>Auth: Decrypt credentials
    Auth-->>MCP: Username, password
    MCP->>Pool: Add connection
    Pool->>Client: Create client
    Client->>Odoo: authenticate()
    Odoo-->>Client: User ID
    Client-->>Pool: Store authenticated
    Pool-->>MCP: Connection ready
    MCP-->>Agent: Connected
```

### CRUD Operation Flow

```mermaid
sequenceDiagram
    participant Agent as AI Agent
    participant MCP as MCP Server
    participant Tool as Tool Registry
    participant Valid as Validator
    participant Pool as Connection Pool
    participant Cache as Cache Layer
    participant Client as Async Client
    participant Odoo as Odoo Instance
    
    Agent->>MCP: odoo_read(model, ids)
    MCP->>Tool: Route to tool
    Tool->>Valid: Validate input
    Valid-->>Tool: Valid
    Tool->>Cache: Check cache
    
    alt Cache hit
        Cache-->>Tool: Cached data
        Tool-->>MCP: Return data
    else Cache miss
        Tool->>Pool: Get connection
        Pool-->>Tool: Client instance
        Tool->>Client: execute_kw('read')
        Client->>Odoo: XML-RPC call
        Odoo-->>Client: Record data
        Client-->>Tool: Parse response
        Tool->>Cache: Store in cache
        Tool-->>MCP: Return data
    end
    
    MCP-->>Agent: Tool response
```

### Error Handling Flow

```mermaid
sequenceDiagram
    participant Agent as AI Agent
    participant MCP as MCP Server
    participant Tool as Tool
    participant Client as Async Client
    participant Error as Error Handler
    participant Retry as Retry Handler
    participant Odoo as Odoo Instance
    
    Agent->>MCP: Tool request
    MCP->>Tool: Execute
    Tool->>Client: API call
    Client->>Odoo: Request
    Odoo-->>Client: Error response
    Client->>Error: Translate error
    Error->>Retry: Check if retryable
    
    alt Retryable error
        Retry->>Retry: Wait (backoff)
        Retry->>Client: Retry request
        Client->>Odoo: Request
        Odoo-->>Client: Success
        Client-->>Tool: Data
    else Non-retryable
        Error->>Error: Format error
        Error-->>Tool: OdooMCPError
        Tool-->>MCP: Error response
    end
    
    MCP-->>Agent: Response/Error
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Development Environment"
        Dev[Developer Machine]
        Test[source2.odoo.com]
    end
    
    subgraph "CI/CD Pipeline"
        GH[GitHub Actions]
        Tests[Test Suite]
        Build[Build Container]
    end
    
    subgraph "Production Environment"
        subgraph "Container Orchestration"
            LB[Load Balancer]
            MCP1[MCP Server 1]
            MCP2[MCP Server 2]
            MCPn[MCP Server N]
        end
        
        subgraph "Supporting Services"
            Metrics[Prometheus]
            Logs[Log Aggregator]
            Secrets[Secret Manager]
        end
    end
    
    subgraph "External Services"
        O1[Client Odoo 1]
        O2[Client Odoo 2]
        On[Client Odoo N]
    end
    
    Dev --> GH
    GH --> Tests
    Tests --> Test
    Tests --> Build
    Build --> LB
    
    LB --> MCP1
    LB --> MCP2
    LB --> MCPn
    
    MCP1 --> Metrics
    MCP2 --> Metrics
    MCPn --> Metrics
    
    MCP1 --> Logs
    MCP2 --> Logs
    MCPn --> Logs
    
    MCP1 --> Secrets
    MCP2 --> Secrets
    MCPn --> Secrets
    
    MCP1 --> O1
    MCP1 --> O2
    MCP2 --> O1
    MCP2 --> On
```

## Security Architecture

```mermaid
graph TB
    subgraph "Security Layers"
        subgraph "Network Security"
            TLS[TLS 1.3+ Only]
            FW[Firewall Rules]
        end
        
        subgraph "Authentication"
            APIKey[API Key Auth]
            Encrypt[Credential Encryption]
        end
        
        subgraph "Authorization"
            RBAC[Role-Based Access]
            Scope[Scoped Permissions]
        end
        
        subgraph "Data Protection"
            Sanitize[Input Sanitization]
            NoLog[No Sensitive Logging]
            Audit[Audit Trail]
        end
    end
    
    subgraph "Threat Mitigation"
        RateLimit[Rate Limiting]
        Timeout[Request Timeouts]
        Validation[Input Validation]
        ErrorMask[Error Masking]
    end
    
    TLS --> APIKey
    APIKey --> RBAC
    RBAC --> Sanitize
    Sanitize --> RateLimit
```