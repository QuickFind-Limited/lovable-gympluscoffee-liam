import 'dotenv/config';

// Function to make authenticated API request
async function makeOdooRequest(method, params = {}) {
  const supabaseUrl = process.env.VITE_SUPABASE_URL;
  const supabaseAnonKey = process.env.VITE_SUPABASE_ANON_KEY;
  
  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error('Missing Supabase configuration in environment variables');
  }

  const response = await fetch(`${supabaseUrl}/functions/v1/purchase-orders`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${supabaseAnonKey}`,
      'x-application-name': 'animal-farmacy',
      'apikey': supabaseAnonKey
    },
    body: JSON.stringify({
      method,
      ...params
    })
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HTTP ${response.status}: ${errorText}`);
  }

  return response.json();
}

async function testSupplierDetails() {
  try {
    console.log('Testing Odoo Supplier Details Fetching...\n');
    
    // Step 1: Get list of suppliers
    console.log('1. Fetching supplier list...');
    const suppliersResult = await makeOdooRequest('search_read', {
      model: 'res.partner',
      domain: [['supplier_rank', '>', 0]],
      fields: ['id', 'name'],
      limit: 5,
      order: 'name'
    });
    
    const suppliers = suppliersResult.partners || [];
    console.log(`Found ${suppliers.length} suppliers:`);
    suppliers.forEach(s => console.log(`  - ID: ${s.id}, Name: ${s.name}`));
    
    if (suppliers.length === 0) {
      console.log('\nNo suppliers found in Odoo.');
      return;
    }
    
    // Step 2: Get detailed info for the first supplier
    const firstSupplier = suppliers[0];
    console.log(`\n2. Fetching details for supplier "${firstSupplier.name}" (ID: ${firstSupplier.id})...`);
    
    const detailsResult = await makeOdooRequest('read', {
      model: 'res.partner',
      ids: [firstSupplier.id],
      fields: [
        'id', 'name', 'email', 'street', 'street2', 
        'city', 'state_id', 'zip', 'country_id', 
        'phone', 'mobile', 'vat', 'supplier_rank'
      ]
    });
    
    const supplierDetails = detailsResult[0];
    console.log('\nSupplier Details:');
    console.log(`  Name: ${supplierDetails.name}`);
    console.log(`  Email: ${supplierDetails.email || 'Not set'}`);
    console.log(`  Phone: ${supplierDetails.phone || 'Not set'}`);
    console.log(`  Mobile: ${supplierDetails.mobile || 'Not set'}`);
    console.log(`  Address:`);
    console.log(`    Street: ${supplierDetails.street || 'Not set'}`);
    console.log(`    Street2: ${supplierDetails.street2 || 'Not set'}`);
    console.log(`    City: ${supplierDetails.city || 'Not set'}`);
    console.log(`    State: ${Array.isArray(supplierDetails.state_id) ? supplierDetails.state_id[1] : 'Not set'}`);
    console.log(`    ZIP: ${supplierDetails.zip || 'Not set'}`);
    console.log(`    Country: ${Array.isArray(supplierDetails.country_id) ? supplierDetails.country_id[1] : 'Not set'}`);
    console.log(`  VAT: ${supplierDetails.vat || 'Not set'}`);
    console.log(`  Supplier Rank: ${supplierDetails.supplier_rank}`);
    
    // Step 3: Search by name
    console.log(`\n3. Testing search by name for "${firstSupplier.name}"...`);
    const searchResult = await makeOdooRequest('search_read', {
      model: 'res.partner',
      domain: [
        '&',
        ['supplier_rank', '>', 0],
        ['name', 'ilike', firstSupplier.name]
      ],
      fields: [
        'id', 'name', 'email', 'street', 'street2', 
        'city', 'state_id', 'zip', 'country_id', 
        'phone', 'mobile', 'vat'
      ],
      limit: 1
    });
    
    const searchedSupplier = searchResult.partners?.[0];
    if (searchedSupplier) {
      console.log(`Found supplier by name search: ID ${searchedSupplier.id}`);
      console.log(`Email from search: ${searchedSupplier.email || 'Not set'}`);
    } else {
      console.log('No supplier found by name search.');
    }
    
    // Step 4: Test with a known supplier name (if "Impala" exists)
    console.log(`\n4. Testing search for "Impala" supplier...`);
    const impalaResult = await makeOdooRequest('search_read', {
      model: 'res.partner',
      domain: [
        '&',
        ['supplier_rank', '>', 0],
        ['name', 'ilike', 'Impala']
      ],
      fields: [
        'id', 'name', 'email', 'street', 'street2', 
        'city', 'state_id', 'zip', 'country_id', 
        'phone', 'mobile', 'vat'
      ],
      limit: 1
    });
    
    const impalaSupplier = impalaResult.partners?.[0];
    if (impalaSupplier) {
      console.log(`Found Impala supplier:`);
      console.log(`  ID: ${impalaSupplier.id}`);
      console.log(`  Name: ${impalaSupplier.name}`);
      console.log(`  Email: ${impalaSupplier.email || 'Not set'}`);
      console.log(`  City: ${impalaSupplier.city || 'Not set'}`);
    } else {
      console.log('No supplier named "Impala" found.');
    }
    
    console.log('\n✅ Supplier details test completed successfully!');
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    if (error.stack) {
      console.error('\nStack trace:', error.stack);
    }
  }
}

// Run the test
testSupplierDetails();