# Odoo Purchase Order PDF Attachment Guide

## Overview

This guide demonstrates how to attach PDF documents to purchase orders in Odoo using the API. The implementation uses the `ir.attachment` model via XML-RPC.

## Implementation

### 1. PDF Generation with Base64 Output

The `generatePDFFromElement` function has been updated to optionally return base64 data:

```typescript
// Generate PDF and get base64 data
const pdfBase64 = await generatePDFFromElement(
  'purchase-order-preview',  // Element ID
  'PO-12345.pdf',           // Filename
  true                      // Return base64 instead of downloading
);
```

### 2. Attaching PDF to Purchase Order

The `OdooService` now includes an `attachDocumentToPurchaseOrder` method:

```typescript
const attachmentId = await odooService.attachDocumentToPurchaseOrder(
  orderId,        // Odoo purchase order ID
  fileName,       // e.g., "PO-12345.pdf"
  base64Data      // Base64 encoded PDF content
);
```

### 3. Complete Example

Here's how to create a purchase order and attach a PDF:

```typescript
import { OdooService } from '@/services/OdooService';
import { generatePDFFromElement } from '@/utils/pdfGenerator';

async function createPurchaseOrderWithPDF() {
  const odooService = new OdooService();
  
  try {
    // Step 1: Create the purchase order in Odoo
    const orderData = {
      partner_id: 25,  // Supplier ID
      date_order: new Date().toISOString(),
      order_line: [
        {
          product_id: 42,
          name: 'Test Product',
          product_qty: 10,
          price_unit: 25.00
        }
      ]
    };
    
    const orderId = await odooService.createPurchaseOrder(orderData);
    console.log('Purchase order created:', orderId);
    
    // Step 2: Generate PDF from the UI element
    // Make sure you have a rendered purchase order element with the correct ID
    const pdfBase64 = await generatePDFFromElement(
      'purchase-order-preview',
      `PO-${orderId}.pdf`,
      true  // Return base64
    );
    
    if (pdfBase64) {
      // Step 3: Attach the PDF to the purchase order
      const attachmentId = await odooService.attachDocumentToPurchaseOrder(
        orderId,
        `PO-${orderId}.pdf`,
        pdfBase64 as string
      );
      
      console.log('PDF attached successfully:', attachmentId);
    }
  } catch (error) {
    console.error('Error:', error);
  }
}
```

## Integration Points

### Purchase Order Editor

To integrate this into the PurchaseOrderEditor component:

```typescript
const handleSaveAndAttachPDF = async () => {
  // Save the order to Odoo
  const orderId = await saveToOdoo(orderData);
  
  // Generate and attach PDF
  const pdfBase64 = await generatePDFFromElement('purchase-order-preview', `PO-${orderId}.pdf`, true);
  if (pdfBase64) {
    await odooService.attachDocumentToPurchaseOrder(orderId, `PO-${orderId}.pdf`, pdfBase64);
  }
};
```

### Purchase Order Dialog

For the PurchaseOrderDialog component:

```typescript
const handleConfirmAndAttachPDF = async () => {
  // Confirm the order in Odoo
  const orderId = await confirmOrder();
  
  // Generate and attach PDF
  const pdfBase64 = await generatePDFFromElement('purchase-order-content', `PO-${orderId}.pdf`, true);
  if (pdfBase64) {
    await odooService.attachDocumentToPurchaseOrder(orderId, `PO-${orderId}.pdf`, pdfBase64);
  }
};
```

## API Details

### Odoo Attachment Model

The attachment is created using these fields:
- `name`: Filename of the attachment
- `datas`: Base64 encoded file content
- `res_model`: 'purchase.order' (the model to attach to)
- `res_id`: The ID of the specific purchase order
- `mimetype`: 'application/pdf'
- `type`: 'binary'

### Error Handling

Always wrap the attachment process in try-catch blocks:

```typescript
try {
  const attachmentId = await odooService.attachDocumentToPurchaseOrder(orderId, fileName, base64Data);
  // Success handling
} catch (error) {
  // The order was created successfully, just the attachment failed
  console.error('Failed to attach PDF:', error);
  // Show partial success message to user
}
```

## Notes

1. The PDF must be generated after the purchase order is created in Odoo to get the order ID
2. The attachment is linked directly to the purchase order record
3. Multiple attachments can be added to the same purchase order
4. The attachment will be visible in Odoo's purchase order view under the attachments section
5. Make sure the PDF generation element is rendered and visible before generating the PDF