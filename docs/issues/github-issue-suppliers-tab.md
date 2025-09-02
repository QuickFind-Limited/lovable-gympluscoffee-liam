# 🏢 Update Suppliers Tab with Odoo Database Suppliers

## Migration Priority: HIGH 🔴

### Overview
Update the suppliers/vendors tab in the application to display supplier data directly from the Odoo database. This aligns with the ongoing migration strategy to use Odoo as the primary data source.

### Current State
- **Suppliers data location**: Currently stored in Supabase or hardcoded
- **Display**: Basic supplier listing (if exists)
- **Integration**: No direct Odoo supplier integration

### Required Implementation

**Odoo Data to Integrate:**
- 🏢 **Supplier/Vendor information** from `res.partner` (with supplier flag)
- 📧 **Contact details** - Email, phone, address
- 🏷️ **Product associations** - Which products each supplier provides
- 💰 **Pricing information** - Supplier price lists
- 📦 **Delivery information** - Lead times, minimum orders
- 📄 **Supplier documents** - Contracts, certifications

### Implementation Tasks

**Phase 1: Data Integration**
- [ ] Identify suppliers tab location in the codebase
- [ ] Create Odoo edge function for supplier data retrieval
- [ ] Map Odoo `res.partner` fields to application schema
- [ ] Implement supplier filtering (active suppliers only)
- [ ] Add supplier-product relationship queries

**Phase 2: UI Implementation**
- [ ] Update suppliers tab component to fetch Odoo data
- [ ] Create supplier cards/list with key information
- [ ] Add supplier detail view with full information
- [ ] Implement search and filter functionality
- [ ] Add sorting options (name, location, products)

**Phase 3: Enhanced Features**
- [ ] Show products supplied by each vendor
- [ ] Display supplier ratings/performance metrics
- [ ] Add supplier contact quick actions
- [ ] Implement supplier document viewer
- [ ] Add export functionality for supplier lists

**Phase 4: Performance & Polish**
- [ ] Add caching for supplier data
- [ ] Implement pagination for large supplier lists
- [ ] Add loading states and error handling
- [ ] Create supplier data refresh mechanism
- [ ] Add supplier analytics dashboard

### Technical Implementation

```typescript
// Example Odoo supplier query
const suppliers = await odooClient.searchRead(
  'res.partner',
  [
    ['supplier_rank', '>', 0],
    ['active', '=', true]
  ],
  [
    'name', 'email', 'phone', 'street', 'city',
    'country_id', 'supplier_rank', 'product_ids'
  ]
);
```

### UI Components Needed
- `SuppliersList` - Main listing component
- `SupplierCard` - Individual supplier display
- `SupplierDetail` - Detailed view modal/page
- `SupplierFilter` - Search and filter controls
- `SupplierProducts` - Products by supplier view

### Expected Benefits
- **Real-time data** - Always shows current supplier information
- **Single source of truth** - Odoo manages all supplier data
- **Better relationships** - See supplier-product connections
- **Enhanced filtering** - Use Odoo's supplier categorization
- **Improved ordering** - Direct access to supplier details

### Dependencies
- Odoo API access with partner read permissions
- Existing authentication system
- Edge functions for Odoo communication
- UI components framework (existing)

### Acceptance Criteria
- [ ] Suppliers tab displays all active Odoo suppliers
- [ ] Each supplier shows key contact information
- [ ] Suppliers can be searched and filtered
- [ ] Supplier details include associated products
- [ ] Performance is acceptable (< 2s load time)
- [ ] Error states are handled gracefully

---
🤖 Generated with Claude Code - GitHub Issue Tracker