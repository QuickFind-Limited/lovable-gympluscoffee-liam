# Odoo MCP Server - Complete Usage Guide

## Table of Contents
1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Starting the Server](#starting-the-server)
4. [Using with Claude Desktop](#using-with-claude-desktop)
5. [Available Tools](#available-tools)
6. [Available Prompts](#available-prompts)
7. [Resources](#resources)
8. [Examples](#examples)
9. [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites
- Python 3.13+ (Python 3.12 also supported)
- Access to an Odoo instance with API enabled
- Odoo credentials (username/password or API key)

### Install with uv (Recommended)
```bash
# Clone the repository
git clone https://github.com/your-org/odoo-mcp-server
cd odoo-mcp-server

# Install dependencies
uv pip install -e .
```

### Install with pip
```bash
# Clone and install
git clone https://github.com/your-org/odoo-mcp-server
cd odoo-mcp-server
pip install -e .
```

## Configuration

### 1. Environment Variables

Create a `.env` file in the project root:

```env
# Primary Odoo instance
ODOO_URL=https://your-instance.odoo.com
ODOO_DATABASE=your-database
ODOO_USERNAME=your-username
ODOO_PASSWORD=your-password

# Optional: Multiple instances
ODOO_INSTANCE_PRODUCTION_URL=https://prod.odoo.com
ODOO_INSTANCE_PRODUCTION_DATABASE=prod
ODOO_INSTANCE_PRODUCTION_USERNAME=prod-user
ODOO_INSTANCE_PRODUCTION_PASSWORD=prod-pass

# MCP Server settings (optional)
MCP_LOG_LEVEL=INFO
```

### 2. Configuration File (Optional)

Create `config.json` for multiple instances:

```json
{
  "instances": {
    "default": {
      "url": "https://your-instance.odoo.com",
      "database": "your-database",
      "username": "your-username",
      "password": "your-password"  # pragma: allowlist secret
    },
    "production": {
      "url": "https://prod.odoo.com",
      "database": "prod",
      "username": "prod-user",
      "password": "prod-pass"  # pragma: allowlist secret
    }
  }
}
```

## Starting the Server

### Standalone Mode
```bash
# Start the server
uv run odoo-mcp-server

# Or with Python
python -m odoo_mcp
```

### Test the Server
```bash
# Run the test client
uv run python test_mcp_client.py
```

## Using with Claude Desktop

### 1. Add to Claude Desktop Configuration

Edit your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

Add the Odoo MCP server:

```json
{
  "mcpServers": {
    "odoo": {
      "command": "uv",
      "args": ["run", "odoo-mcp-server"],
      "cwd": "/path/to/odoo-mcp-server",
      "env": {
        "ODOO_URL": "https://your-instance.odoo.com",
        "ODOO_DATABASE": "your-database",
        "ODOO_USERNAME": "your-username",
        "ODOO_PASSWORD": "your-password"  # pragma: allowlist secret
      }
    }
  }
}
```

### 2. Restart Claude Desktop

After updating the configuration, restart Claude Desktop to load the MCP server.

### 3. Verify Connection

In Claude Desktop, you can verify the connection by asking:
- "What MCP tools are available?"
- "Show me the Odoo MCP server status"

## Available Tools

### 1. odoo_create
Create new records in Odoo.

```typescript
// Parameters
{
  "instance_id": "default",  // Optional, defaults to "default"
  "model": "res.partner",    // Required: Odoo model name
  "values": {                 // Required: Field values
    "name": "John Doe",
    "email": "john@example.com"
  }
}

// Example usage in Claude
"Create a new customer named John Doe with email john@example.com"
```

### 2. odoo_read
Read existing records by ID.

```typescript
// Parameters
{
  "instance_id": "default",
  "model": "res.partner",
  "ids": [1, 2, 3],         // List of record IDs
  "fields": ["name", "email"] // Optional: specific fields
}

// Example usage in Claude
"Show me the details of partner with ID 5"
```

### 3. odoo_search
Search for record IDs matching criteria.

```typescript
// Parameters
{
  "instance_id": "default",
  "model": "sale.order",
  "domain": [["state", "=", "sale"]], // Odoo domain syntax
  "limit": 10,              // Optional
  "offset": 0,              // Optional
  "order": "date_order desc" // Optional
}

// Example usage in Claude
"Find all confirmed sales orders"
```

### 4. odoo_search_read
Search and read records in one operation.

```typescript
// Parameters
{
  "instance_id": "default",
  "model": "product.product",
  "domain": [["qty_available", "<", 10]],
  "fields": ["name", "qty_available", "list_price"],
  "limit": 20
}

// Example usage in Claude
"Show me products with less than 10 units in stock"
```

### 5. odoo_update
Update existing records.

```typescript
// Parameters
{
  "instance_id": "default",
  "model": "res.partner",
  "ids": [5, 6],
  "values": {
    "phone": "+1234567890",
    "city": "New York"
  }
}

// Example usage in Claude
"Update partner 5's phone number to +1234567890"
```

### 6. odoo_delete
Delete records (use with caution!).

```typescript
// Parameters
{
  "instance_id": "default",
  "model": "res.partner",
  "ids": [10, 11]
}

// Example usage in Claude
"Delete test partners with IDs 10 and 11"
```

### 7. odoo_search_count
Count records matching criteria.

```typescript
// Parameters
{
  "instance_id": "default",
  "model": "sale.order",
  "domain": [["state", "=", "draft"]]
}

// Example usage in Claude
"How many draft sales orders are there?"
```

### 8. odoo_fields_get
Get field definitions for a model.

```typescript
// Parameters
{
  "instance_id": "default",
  "model": "res.partner",
  "attributes": ["string", "type", "required", "readonly"]
}

// Example usage in Claude
"Show me all fields available on the partner model"
```

### 9. odoo_execute
Execute any model method.

```typescript
// Parameters
{
  "instance_id": "default",
  "model": "sale.order",
  "method": "action_confirm",
  "args": [[5]],  // Method arguments
  "kwargs": {}    // Keyword arguments
}

// Example usage in Claude
"Confirm sales order with ID 5"
```

## Available Prompts

### 1. analyze_inventory
Get a comprehensive inventory analysis report.

```typescript
// Parameters
{
  "instance_id": "default",
  "warehouse": "all",
  "include_forecast": true
}

// Example usage in Claude
"Analyze our current inventory levels"
```

### 2. optimize_procurement
Generate procurement optimization suggestions.

```typescript
// Parameters
{
  "instance_id": "default",
  "supplier_id": null,  // Optional: specific supplier
  "lead_time_days": 7
}

// Example usage in Claude
"Give me procurement suggestions for products running low"
```

### 3. generate_report
Generate various business reports.

```typescript
// Parameters
{
  "instance_id": "default",
  "report_type": "sales_summary", // or "inventory_valuation"
  "period": "this_month"
}

// Example usage in Claude
"Generate a sales summary report for this month"
```

## Resources

Resources provide URI-based access to Odoo data:

### 1. List Models
```
odoo://default
```
Returns a list of common Odoo models.

### 2. Browse Model Records
```
odoo://default/res.partner
```
Returns the first 100 records of the specified model.

### 3. Get Specific Record
```
odoo://default/res.partner/5
```
Returns details of a specific record.

## Examples

### Example 1: Customer Management

```python
# Create a new customer
"Create a new customer 'Acme Corp' with email contact@acme.com and mark them as a company"

# Search for customers
"Find all customers in New York"

# Update customer info
"Update Acme Corp's phone number to +1-555-0123"
```

### Example 2: Inventory Management

```python
# Check stock levels
"Show me all products with less than 5 units in stock"

# Analyze inventory
"Analyze our inventory and show me products that need reordering"

# Update stock
"Update product 'Widget A' quantity to 100 units"
```

### Example 3: Sales Operations

```python
# View orders
"Show me all draft sales orders"

# Create order
"Create a sales order for customer 'Acme Corp'"

# Generate reports
"Generate a sales summary for this month"
```

### Example 4: Multi-Instance Operations

```python
# Specify instance
"On the production instance, show me today's sales orders"

# Compare instances
"Compare customer count between default and production instances"
```

## Troubleshooting

### Common Issues

#### 1. Authentication Failed
```
Error: Authentication failed: Invalid credentials
```
**Solution**:
- Verify your username and password in `.env`
- Ensure your Odoo user has API access enabled
- For Odoo Online, ensure password is set (not just using SSO)

#### 2. Connection Timeout
```
Error: Connection timeout
```
**Solution**:
- Check your ODOO_URL is correct and accessible
- Verify no firewall is blocking the connection
- Try increasing timeout in connection settings

#### 3. Field Does Not Exist
```
Error: Field 'customer_rank' does not exist
```
**Solution**:
- Different Odoo versions have different fields
- Use `odoo_fields_get` to check available fields
- Adjust your queries based on your Odoo version

#### 4. Access Denied
```
Error: Access denied to model 'sale.order'
```
**Solution**:
- Check user permissions in Odoo
- Ensure user has access to the required models
- May need to assign user to appropriate groups

### Debug Mode

Enable debug logging:
```bash
MCP_LOG_LEVEL=DEBUG uv run odoo-mcp-server
```

### Test Connection

Use the simple test script:
```bash
uv run python test_connection_simple.py
```

## Best Practices

1. **Use Search Before Delete**: Always search and verify records before deleting
2. **Limit Large Queries**: Use `limit` parameter to avoid overwhelming responses
3. **Check Field Names**: Use `odoo_fields_get` to verify field names for your Odoo version
4. **Handle Errors Gracefully**: Implement proper error handling in your automations
5. **Use Appropriate Instances**: Keep test and production data separate

## Security Considerations

1. **Credentials**: Never commit `.env` files to version control
2. **Permissions**: Use Odoo users with minimum required permissions
3. **API Keys**: Prefer API keys over passwords when available
4. **Network**: Use HTTPS connections only
5. **Logging**: Ensure sensitive data is not logged

## Advanced Usage

### Custom Domains

Odoo uses Polish notation for complex queries:

```python
# AND condition (implicit)
[["state", "=", "draft"], ["partner_id", "!=", False]]

# OR condition
["|", ["state", "=", "draft"], ["state", "=", "sent"]]

# Complex conditions
["&", "|", ["state", "=", "draft"], ["state", "=", "sent"], ["amount_total", ">", 1000]]
```

### Batch Operations

For better performance with large datasets:

```python
# Instead of multiple single creates
for data in large_dataset:
    odoo_create(model="res.partner", values=data)

# Use batch create (if implementing)
odoo_execute(
    model="res.partner",
    method="create",
    args=[large_dataset]  # List of all records
)
```

### Working with Relations

Many2one fields return `[id, name]`:
```python
# Reading a many2one field
partner = odoo_read(model="sale.order", ids=[5], fields=["partner_id"])
# Returns: {"partner_id": [3, "Acme Corp"]}
```

One2many and many2many return lists of IDs:
```python
# Reading a one2many field
order = odoo_read(model="sale.order", ids=[5], fields=["order_line"])
# Returns: {"order_line": [10, 11, 12]}
```

---

For more information, see the [API Reference](./API_REFERENCE.md) or [Troubleshooting Guide](./TROUBLESHOOTING.md).
