import fetch from 'node-fetch';

const ODOO_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co/functions/v1/odoo';
const AUTH_TOKEN = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE';

async function testAvailableFields() {
  console.log('=== Testing Available Fields ===\n');

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': AUTH_TOKEN,
    'x-application-name': 'animal-farmacy',
    'apikey': AUTH_TOKEN.replace('Bearer ', '')
  };

  try {
    // Test fields_get to see all available fields
    console.log('Getting field definitions for purchase.order:');
    const response = await fetch(ODOO_URL, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        method: 'fields_get',
        model: 'purchase.order',
        attributes: ['string', 'type', 'required']
      })
    });

    const data = await response.json();
    
    if (data.fields) {
      console.log('\nKey fields available:');
      Object.entries(data.fields).forEach(([fieldName, fieldDef]) => {
        const def = fieldDef;
        if (fieldName.includes('partner') || fieldName.includes('vendor') || fieldName.includes('supplier') || fieldName.includes('line')) {
          console.log(`\n${fieldName}:`);
          console.log(`  Label: ${def.string}`);
          console.log(`  Type: ${def.type}`);
          console.log(`  Required: ${def.required || false}`);
        }
      });
      
      // Now test which fields actually work
      console.log('\n\nTesting which supplier-related fields work:');
      const fieldsToTest = [
        'partner_ref',
        'vendor_ref',
        'partner_name',
        'supplier_name',
        'vendor_name'
      ];
      
      for (const field of fieldsToTest) {
        if (data.fields[field]) {
          const testResponse = await fetch(ODOO_URL, {
            method: 'POST',
            headers,
            body: JSON.stringify({
              method: 'search_read',
              model: 'purchase.order',
              fields: ['id', 'name', field],
              limit: 1
            })
          });
          
          const testData = await testResponse.json();
          console.log(`\n${field}: ${testData.orders?.length > 0 ? 'WORKS' : 'RETURNS 0'}`);
          if (testData.orders?.length > 0) {
            console.log(`  Value: ${testData.orders[0][field]}`);
          }
        }
      }
    }
  } catch (error) {
    console.error('Error:', error);
  }
}

testAvailableFields();