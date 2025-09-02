#!/usr/bin/env node

import fetch from 'node-fetch';
import fs from 'fs/promises';
import path from 'path';

// Configuration
const supabaseUrl = process.env.SUPABASE_URL || 'https://vkxoqaansgbyzcppdiii.supabase.co';
const supabaseAnonKey = process.env.SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function createPurchaseOrderWithAttachment() {
  try {
    console.log('🚀 Testing Odoo Purchase Order PDF Attachment...\n');

    // Step 1: Create a purchase order
    console.log('📝 Creating purchase order...');
    const orderData = {
      partner_id: 25, // FastPet Logistics
      date_order: new Date().toISOString().replace('T', ' ').slice(0, 19),
      order_line: [
        {
          product_id: 42,
          name: 'Test Product for PDF Attachment',
          product_qty: 5,
          price_unit: 10.00
        }
      ]
    };

    const createResponse = await fetch(`${supabaseUrl}/functions/v1/purchase-orders`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${supabaseAnonKey}`,
        'x-application-name': 'animal-farmacy',
        'apikey': supabaseAnonKey
      },
      body: JSON.stringify({
        method: 'create',
        model: 'purchase.order',
        data: orderData
      })
    });

    if (!createResponse.ok) {
      throw new Error(`Failed to create order: ${await createResponse.text()}`);
    }

    const createResult = await createResponse.json();
    const orderId = createResult.id;
    console.log(`✅ Purchase order created with ID: ${orderId}\n`);

    // Step 2: Create a sample PDF content (base64)
    // In a real scenario, this would be generated from the UI
    console.log('📄 Generating sample PDF content...');
    const samplePdfContent = `
Purchase Order #${orderId}
=======================
Date: ${new Date().toLocaleDateString()}
Supplier: FastPet Logistics

Items:
- Test Product for PDF Attachment
  Quantity: 5
  Unit Price: $10.00
  Total: $50.00

Grand Total: $50.00
    `;
    
    // Convert to base64 (simulating PDF content)
    const base64Data = Buffer.from(samplePdfContent).toString('base64');
    console.log('✅ PDF content generated (base64 length:', base64Data.length, 'chars)\n');

    // Step 3: Attach the PDF to the purchase order
    console.log('📎 Attaching PDF to purchase order...');
    const attachmentData = {
      name: `PO-${orderId}-test.pdf`,
      datas: base64Data,
      res_model: 'purchase.order',
      res_id: orderId,
      mimetype: 'application/pdf',
      type: 'binary'
    };

    const attachResponse = await fetch(`${supabaseUrl}/functions/v1/purchase-orders`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${supabaseAnonKey}`,
        'x-application-name': 'animal-farmacy',
        'apikey': supabaseAnonKey
      },
      body: JSON.stringify({
        method: 'create',
        model: 'ir.attachment',
        data: attachmentData
      })
    });

    if (!attachResponse.ok) {
      throw new Error(`Failed to attach PDF: ${await attachResponse.text()}`);
    }

    const attachResult = await attachResponse.json();
    const attachmentId = attachResult.id;
    console.log(`✅ PDF attached successfully with attachment ID: ${attachmentId}\n`);

    // Step 4: Verify the attachment
    console.log('🔍 Verifying attachment...');
    const verifyResponse = await fetch(`${supabaseUrl}/functions/v1/purchase-orders`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${supabaseAnonKey}`,
        'x-application-name': 'animal-farmacy',
        'apikey': supabaseAnonKey
      },
      body: JSON.stringify({
        method: 'search_read',
        model: 'ir.attachment',
        domain: [
          ['res_model', '=', 'purchase.order'],
          ['res_id', '=', orderId]
        ],
        fields: ['id', 'name', 'mimetype', 'file_size', 'create_date']
      })
    });

    if (verifyResponse.ok) {
      const attachments = await verifyResponse.json();
      console.log('📋 Attachments found for purchase order:', JSON.stringify(attachments, null, 2));
    }

    console.log('\n🎉 Success! Purchase order created and PDF attached.');
    console.log(`\n📌 Summary:`);
    console.log(`   - Purchase Order ID: ${orderId}`);
    console.log(`   - Attachment ID: ${attachmentId}`);
    console.log(`   - Attachment Name: ${attachmentData.name}`);
    console.log(`\n✨ You can now view the purchase order in Odoo with the attached PDF!`);

  } catch (error) {
    console.error('❌ Error:', error.message);
    console.error('Stack:', error.stack);
  }
}

// Run the test
createPurchaseOrderWithAttachment();