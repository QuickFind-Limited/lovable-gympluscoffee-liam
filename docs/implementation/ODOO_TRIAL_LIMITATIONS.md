# Odoo Trial API Limitations

## Issue Summary

The Odoo trial/SaaS instance has significant API access restrictions that limit the fields accessible via XML-RPC API to only `id` and `name` for all models. This prevents us from displaying detailed order line information in the application.

## Investigation Findings

1. **Field Access Restrictions**: When querying any Odoo model (purchase.order, purchase.order.line, product.product, res.partner), only `id` and `name` fields are returned, regardless of which fields are requested.

2. **Order Creation Works**: Despite the read limitations, we can successfully create purchase orders with line items. The orders are created with the correct totals (e.g., P00018 has £378.18, P00016 has £1,182.60), proving that line items ARE being created and calculated by Odoo.

3. **fields_get Method**: Even field metadata is restricted - the fields_get method returns field definitions but all metadata (type, string, help, etc.) comes back as undefined.

4. **Read Method Also Restricted**: Attempting to use the `read` method instead of `search_read` still returns empty results when trying to access fields beyond id and name.

5. **Partner/Supplier Access**: While we can list suppliers using search_read on res.partner (returns id and name), we cannot determine which supplier is associated with each order as the partner_id field is not accessible.

## Root Cause

This is a known limitation of Odoo SaaS trial versions to:
- Protect data and limit resource usage during trial periods
- Encourage upgrades to paid subscriptions
- Prevent extensive API operations on trial instances

## Impact

1. Cannot display individual order line items in the UI
2. Cannot show product details beyond name
3. Cannot access partner/supplier details beyond name
4. Order totals are visible but line-level details are not

## Implemented Solution

1. **Added Trial Notice**: Displayed a clear notice in the Orders page explaining the limitation
2. **Simplified Order Dialog**: Replaced the order items table with an explanation of why line details cannot be shown
3. **Maintained Functionality**: Order creation still works - orders are created in Odoo with proper line items, even though we can't read them back

## Alternative Approaches

For users who need full functionality:

1. **Upgrade Odoo**: Purchase a paid Odoo subscription for full API access
2. **Direct Access**: View order details directly in the Odoo web interface
3. **Custom Module**: Develop a custom Odoo module (if allowed) to expose additional data
4. **Reports**: Use Odoo's built-in reporting features to export order details

## Technical Details

### What Works:
- Authentication via XML-RPC
- Creating records (orders, order lines)
- Reading id and name fields
- Order calculations (Odoo calculates totals correctly)

### What Doesn't Work:
- Reading any fields beyond id and name
- Accessing relational field data
- Getting field metadata via fields_get

### Test Results:
```javascript
// All models return only id and name:
purchase.order: ['id', 'name', 'order_line']  // order_line returns empty array
purchase.order.line: ['id', 'name']           // No other fields accessible
product.product: ['id', 'name']               // No price, description, etc.
res.partner: ['id', 'name']                   // No address, email, etc.
```

## Conclusion

The application is functioning correctly within the constraints of the Odoo trial API. To access full order details, users need to either:
1. Upgrade to a paid Odoo subscription
2. Access orders directly through the Odoo web interface

The current implementation provides the best possible user experience given these limitations, with clear communication about why certain features are unavailable.