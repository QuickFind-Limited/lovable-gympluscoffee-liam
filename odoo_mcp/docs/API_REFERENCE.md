# Odoo MCP Server - API Reference

## Overview

The Odoo MCP Server provides a Model Context Protocol interface to Odoo ERP systems. This reference documents all available tools, prompts, resources, and their parameters.

## Base Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `ODOO_URL` | Odoo instance URL | Yes | None |
| `ODOO_DATABASE` | Database name | Yes | None |
| `ODOO_USERNAME` | Username for authentication | Yes | None |
| `ODOO_PASSWORD` | Password for authentication | Yes | None |
| `MCP_LOG_LEVEL` | Logging level | No | INFO |

### Multiple Instances

For multiple Odoo instances, use the pattern:
- `ODOO_INSTANCE_{NAME}_URL`
- `ODOO_INSTANCE_{NAME}_DATABASE`
- `ODOO_INSTANCE_{NAME}_USERNAME`
- `ODOO_INSTANCE_{NAME}_PASSWORD`

## Tools API

### odoo_create

Create new records in Odoo.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `instance_id` | string | No | Odoo instance ID (default: "default") |
| `model` | string | Yes | Odoo model name (e.g., "res.partner") |
| `values` | object | Yes | Field values for the new record |

**Example:**
```json
{
  "instance_id": "default",
  "model": "res.partner",
  "values": {
    "name": "John Doe",
    "email": "john@example.com",
    "is_company": false,
    "phone": "+1234567890"
  }
}
```

**Returns:** Integer ID of the created record

### odoo_read

Read existing records by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `instance_id` | string | No | Odoo instance ID (default: "default") |
| `model` | string | Yes | Odoo model name |
| `ids` | array | Yes | List of record IDs to read |
| `fields` | array | No | Specific fields to return (default: all) |

**Example:**
```json
{
  "model": "res.partner",
  "ids": [1, 2, 3],
  "fields": ["name", "email", "phone"]
}
```

**Returns:** Array of record dictionaries

### odoo_update

Update existing records.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `instance_id` | string | No | Odoo instance ID (default: "default") |
| `model` | string | Yes | Odoo model name |
| `ids` | array | Yes | List of record IDs to update |
| `values` | object | Yes | Field values to update |

**Example:**
```json
{
  "model": "res.partner",
  "ids": [5],
  "values": {
    "phone": "+9876543210",
    "city": "New York"
  }
}
```

**Returns:** Boolean indicating success

### odoo_delete

Delete records (use with caution).

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `instance_id` | string | No | Odoo instance ID (default: "default") |
| `model` | string | Yes | Odoo model name |
| `ids` | array | Yes | List of record IDs to delete |

**Example:**
```json
{
  "model": "res.partner",
  "ids": [10, 11]
}
```

**Returns:** Boolean indicating success

### odoo_search

Search for record IDs matching criteria.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `instance_id` | string | No | Odoo instance ID (default: "default") |
| `model` | string | Yes | Odoo model name |
| `domain` | array | Yes | Odoo domain syntax search criteria |
| `limit` | integer | No | Maximum records to return |
| `offset` | integer | No | Number of records to skip |
| `order` | string | No | Sort order (e.g., "name asc") |

**Domain Syntax:**
- Basic: `[["field", "operator", "value"]]`
- AND (implicit): `[["field1", "=", "value1"], ["field2", "=", "value2"]]`
- OR: `["|", ["field1", "=", "value1"], ["field2", "=", "value2"]]`
- Complex: `["&", "|", ["field1", "=", "value1"], ["field2", "=", "value2"], ["field3", ">", 100]]`

**Example:**
```json
{
  "model": "sale.order",
  "domain": [["state", "=", "sale"], ["amount_total", ">", 1000]],
  "limit": 10,
  "order": "date_order desc"
}
```

**Returns:** Array of record IDs

### odoo_search_read

Search and read records in one operation.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `instance_id` | string | No | Odoo instance ID (default: "default") |
| `model` | string | Yes | Odoo model name |
| `domain` | array | Yes | Search criteria |
| `fields` | array | No | Fields to return |
| `limit` | integer | No | Maximum records |
| `offset` | integer | No | Skip records |
| `order` | string | No | Sort order |

**Example:**
```json
{
  "model": "product.product",
  "domain": [["qty_available", "<", 10]],
  "fields": ["name", "qty_available", "list_price"],
  "limit": 20
}
```

**Returns:** Array of record dictionaries with specified fields

### odoo_search_count

Count records matching criteria.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `instance_id` | string | No | Odoo instance ID (default: "default") |
| `model` | string | Yes | Odoo model name |
| `domain` | array | Yes | Search criteria |

**Example:**
```json
{
  "model": "sale.order",
  "domain": [["state", "=", "draft"]]
}
```

**Returns:** Integer count of matching records

### odoo_fields_get

Get field definitions for a model.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `instance_id` | string | No | Odoo instance ID (default: "default") |
| `model` | string | Yes | Odoo model name |
| `attributes` | array | No | Field attributes to return |

**Example:**
```json
{
  "model": "res.partner",
  "attributes": ["string", "type", "required", "readonly", "help"]
}
```

**Returns:** Dictionary of field definitions

### odoo_execute

Execute any model method.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `instance_id` | string | No | Odoo instance ID (default: "default") |
| `model` | string | Yes | Odoo model name |
| `method` | string | Yes | Method name to execute |
| `args` | array | Yes | Method arguments |
| `kwargs` | object | No | Keyword arguments |

**Example:**
```json
{
  "model": "sale.order",
  "method": "action_confirm",
  "args": [[5]],
  "kwargs": {}
}
```

**Returns:** Method-specific return value

## Prompts API

### analyze_inventory

Analyze current inventory levels and provide insights.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `instance_id` | string | No | Odoo instance ID (default: "default") |
| `warehouse` | string | No | Warehouse to analyze (default: "all") |
| `include_forecast` | boolean | No | Include demand forecast (default: true) |

**Returns:** Formatted markdown report with:
- Low stock alerts
- Forecast analysis
- Recommendations

### optimize_procurement

Generate procurement optimization suggestions.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `instance_id` | string | No | Odoo instance ID (default: "default") |
| `supplier_id` | integer | No | Specific supplier ID |
| `lead_time_days` | integer | No | Lead time for planning (default: 7) |

**Returns:** Formatted markdown report with:
- Products requiring reorder
- Suggested quantities
- Optimization strategies

### generate_report

Generate various business reports.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `instance_id` | string | No | Odoo instance ID (default: "default") |
| `report_type` | string | No | Type of report (default: "sales_summary") |
| `period` | string | No | Time period (default: "this_month") |

**Report Types:**
- `sales_summary`: Sales overview with recent orders
- `inventory_valuation`: Inventory value analysis

**Returns:** Formatted markdown business report

## Resources API

### List Models

**URI:** `odoo://{instance_id}`

Returns a list of commonly used Odoo models.

**Example:** `odoo://default`

**Returns:**
```json
{
  "models": [
    "res.partner",
    "product.product",
    "sale.order",
    "purchase.order",
    "stock.picking",
    "account.move"
  ]
}
```

### Browse Model Records

**URI:** `odoo://{instance_id}/{model}`

Returns the first 100 records of the specified model.

**Example:** `odoo://default/res.partner`

**Returns:**
```json
{
  "model": "res.partner",
  "count": 100,
  "records": [
    {"id": 1, "name": "My Company"},
    {"id": 2, "name": "Administrator"}
  ]
}
```

### Get Specific Record

**URI:** `odoo://{instance_id}/{model}/{id}`

Returns detailed information about a specific record.

**Example:** `odoo://default/res.partner/5`

**Returns:**
```json
{
  "id": 5,
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "is_company": false,
  "create_date": "2024-01-15 10:30:00"
}
```

## Error Handling

All tools return errors in a consistent format:

```json
{
  "error": "Error type",
  "message": "Detailed error message",
  "details": {
    "model": "res.partner",
    "method": "create",
    "instance": "default"
  }
}
```

### Common Error Types

| Error | Description | Solution |
|-------|-------------|----------|
| `AuthenticationError` | Invalid credentials | Check username/password |
| `AccessError` | Insufficient permissions | Verify user access rights |
| `ValidationError` | Invalid field values | Check field requirements |
| `ConnectionError` | Cannot reach Odoo | Verify URL and network |
| `NotFoundError` | Record/model not found | Check ID/model name |

## Field Types

### Basic Field Types

| Type | Description | Example |
|------|-------------|---------|
| `char` | String field | "John Doe" |
| `text` | Long text | "Description..." |
| `integer` | Whole number | 42 |
| `float` | Decimal number | 99.99 |
| `boolean` | True/False | true |
| `date` | Date only | "2024-01-15" |
| `datetime` | Date and time | "2024-01-15 10:30:00" |

### Relational Field Types

| Type | Description | Read Format | Write Format |
|------|-------------|-------------|--------------|
| `many2one` | Link to one record | [id, "Name"] | id |
| `one2many` | Link to multiple records | [id1, id2, ...] | [[6, 0, [id1, id2]]] |
| `many2many` | Many-to-many relation | [id1, id2, ...] | [[6, 0, [id1, id2]]] |

### Special Commands for One2many/Many2many

| Command | Format | Description |
|---------|--------|-------------|
| Create | [0, 0, {...}] | Create and link new record |
| Update | [1, id, {...}] | Update linked record |
| Delete | [2, id, 0] | Delete linked record |
| Unlink | [3, id, 0] | Remove link (not delete) |
| Link | [4, id, 0] | Add existing record |
| Replace | [6, 0, [ids]] | Replace all with IDs |

## Rate Limiting

- Default: 100 requests per minute per instance
- Bulk operations count as single requests
- Use search_read instead of search + read for efficiency

## Performance Tips

1. **Use field filtering**: Only request fields you need
2. **Batch operations**: Use bulk create/update when possible
3. **Limit results**: Use limit parameter for large datasets
4. **Use search_read**: Combines search and read in one call
5. **Cache field definitions**: fields_get results rarely change

## Version Compatibility

This MCP server is tested with:
- Odoo 15.0+
- Odoo 16.0+
- Odoo 17.0+
- Odoo 18.0+

Note: Some fields and methods may vary between versions. Use `odoo_fields_get` to verify available fields for your version.
