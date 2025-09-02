# Odoo MCP Usage Examples

## Common Use Cases

### 1. Customer Management

#### Create a New Customer
```python
# Create a new customer
result = await odoo_create(
    instance_id="default",
    model="res.partner",
    values={
        "name": "Acme Corporation",
        "is_company": True,
        "email": "contact@acme.com",
        "phone": "+1-555-0123",
        "street": "123 Main St",
        "city": "New York",
        "website": "https://acme.com"
    }
)
# Returns: partner_id (e.g., 57)
```

#### Search Customers by Criteria
```python
# Find all companies
company_ids = await odoo_search(
    instance_id="default",
    model="res.partner",
    domain=[["is_company", "=", True]]
)

# Find customers by email domain
customer_ids = await odoo_search(
    instance_id="default",
    model="res.partner",
    domain=[["email", "ilike", "%@acme.com"]]
)
```

#### Get Customer Details
```python
# Read specific customer details
customers = await odoo_read(
    instance_id="default",
    model="res.partner",
    ids=[57, 58, 59]
)
```

### 2. Product Management

#### Create a Product
```python
# Create a new product
product_id = await odoo_create(
    instance_id="default",
    model="product.product",
    values={
        "name": "Premium Widget",
        "list_price": 99.99,
        "standard_price": 45.00,
        "type": "product",
        "categ_id": 1  # All / Saleable
    }
)
```

#### Update Product Prices
```python
# Bulk update product prices
await odoo_update(
    instance_id="default",
    model="product.product",
    ids=[10, 11, 12],
    values={
        "list_price": 149.99
    }
)
```

### 3. Sales Order Management

#### Search Recent Orders
```python
# Find confirmed sales orders
order_ids = await odoo_search(
    instance_id="default",
    model="sale.order",
    domain=[
        ["state", "=", "sale"],
        ["date_order", ">=", "2025-01-01"]
    ]
)

# Get order count
order_count = await odoo_search_count(
    instance_id="default",
    model="sale.order",
    domain=[["state", "=", "draft"]]
)
```

### 4. Complex Queries

#### Multi-Condition Search
```python
# Find high-value customers
valuable_customers = await odoo_search(
    instance_id="default",
    model="res.partner",
    domain=[
        "&",
        ["is_company", "=", True],
        ["customer_rank", ">", 0],
        "|",
        ["total_invoiced", ">", 10000],
        ["sale_order_count", ">", 50]
    ]
)
```

### 5. Working with Invoices

#### Create an Invoice
```python
# Create a customer invoice
invoice_id = await odoo_create(
    instance_id="default",
    model="account.move",
    values={
        "move_type": "out_invoice",
        "partner_id": 57,
        "invoice_date": "2025-01-15",
        "invoice_line_ids": [
            [0, 0, {
                "product_id": 10,
                "quantity": 2,
                "price_unit": 99.99
            }]
        ]
    }
)
```

### 6. Batch Operations

#### Bulk Partner Updates
```python
# Update multiple partners
partner_ids = await odoo_search(
    instance_id="default",
    model="res.partner",
    domain=[["customer_rank", ">", 0]]
)

# Update in batches to avoid timeouts
batch_size = 50
for i in range(0, len(partner_ids), batch_size):
    batch = partner_ids[i:i+batch_size]
    await odoo_update(
        instance_id="default",
        model="res.partner",
        ids=batch,
        values={"active": True}
    )
```

### 7. Error Handling Pattern

```python
try:
    # Attempt to create a partner
    partner_id = await odoo_create(
        instance_id="default",
        model="res.partner",
        values={"name": "Test Partner"}
    )
except ValidationError as e:
    print(f"Validation failed: {e}")
except Exception as e:
    print(f"Operation failed: {e}")
```

## Best Practices

1. **Always specify fields when reading**: Reduces response size and avoids computed field errors
2. **Use batch operations**: Process records in groups to avoid timeouts
3. **Handle errors gracefully**: Odoo operations can fail for various reasons
4. **Use search_count before large searches**: Check dataset size before retrieving
5. **Leverage domain operators**: Use AND (&), OR (|), and NOT (!) for complex queries
6. **Test with small datasets first**: Verify your logic before running on production data

## Common Domain Patterns

```python
# Equals
[["field", "=", value]]

# Not equals
[["field", "!=", value]]

# Contains (case-sensitive)
[["field", "like", "%value%"]]

# Contains (case-insensitive)
[["field", "ilike", "%value%"]]

# Greater than
[["field", ">", value]]

# In list
[["field", "in", [1, 2, 3]]]

# Is set/not set
[["field", "!=", False]]
[["field", "=", False]]

# Date ranges
[["date_field", ">=", "2025-01-01"]]
[["date_field", "<=", "2025-12-31"]]

# Combined conditions (AND)
["&", ["field1", "=", value1], ["field2", "=", value2]]

# Combined conditions (OR)
["|", ["field1", "=", value1], ["field2", "=", value2]]

# Complex nested conditions
[
    "&",
    ["active", "=", True],
    "|",
    ["customer_rank", ">", 0],
    ["supplier_rank", ">", 0]
]
```
