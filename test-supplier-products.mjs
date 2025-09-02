import fetch from 'node-fetch';

const ODOO_URL = 'https://source-animalfarmacy.odoo.com';
const ODOO_DB = 'source-animalfarmacy';
const ODOO_USERNAME = 'admin@quickfindai.com';
const ODOO_PASSWORD = 'BJ62wX2J4yzjS$i';

// Helper to build XML-RPC request
function buildXmlRequest(method, params) {
  const xmlParams = params.map(param => valueToXml(param)).join('');
  return `<?xml version="1.0"?>
<methodCall>
  <methodName>${method}</methodName>
  <params>
    ${xmlParams}
  </params>
</methodCall>`;
}

function valueToXml(value) {
  if (value === null || value === undefined) {
    return '<param><value><nil/></value></param>';
  }
  if (typeof value === 'string') {
    return `<param><value><string>${escapeXml(value)}</string></value></param>`;
  }
  if (typeof value === 'number') {
    if (Number.isInteger(value)) {
      return `<param><value><int>${value}</int></value></param>`;
    }
    return `<param><value><double>${value}</double></value></param>`;
  }
  if (typeof value === 'boolean') {
    return `<param><value><boolean>${value ? 1 : 0}</boolean></value></param>`;
  }
  if (Array.isArray(value)) {
    const arrayItems = value.map(item => 
      valueToXml(item).replace(/<\/?param>/g, '')
    ).join('');
    return `<param><value><array><data>${arrayItems}</data></array></value></param>`;
  }
  if (typeof value === 'object') {
    const members = Object.entries(value).map(([key, val]) => 
      `<member>
        <name>${escapeXml(key)}</name>
        ${valueToXml(val).replace(/<\/?param>/g, '')}
      </member>`
    ).join('');
    return `<param><value><struct>${members}</struct></value></param>`;
  }
  return '<param><value><string></string></value></param>';
}

function escapeXml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

// Parse simple XML response
function parseSimpleValue(xml) {
  // Extract integer
  const intMatch = xml.match(/<int>(\d+)<\/int>/);
  if (intMatch) return parseInt(intMatch[1]);
  
  // Extract string
  const stringMatch = xml.match(/<string>(.*?)<\/string>/s);
  if (stringMatch) return stringMatch[1];
  
  // Extract array
  if (xml.includes('<array>')) {
    const values = [];
    const valueRegex = /<value>(.*?)<\/value>/gs;
    let match;
    while ((match = valueRegex.exec(xml)) !== null) {
      values.push(parseSimpleValue(match[1]));
    }
    return values;
  }
  
  return null;
}

async function testSupplierProducts() {
  try {
    // 1. Authenticate
    console.log('1. Authenticating...');
    const authXml = buildXmlRequest('authenticate', [ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {}]);
    const authResponse = await fetch(`${ODOO_URL}/xmlrpc/2/common`, {
      method: 'POST',
      headers: { 'Content-Type': 'text/xml' },
      body: authXml
    });
    const authResult = await authResponse.text();
    const uid = parseSimpleValue(authResult);
    console.log('Authenticated with UID:', uid);

    // 2. Check if product.supplierinfo table has any records
    console.log('\n2. Checking product.supplierinfo table...');
    const countXml = buildXmlRequest('execute_kw', [
      ODOO_DB, uid, ODOO_PASSWORD,
      'product.supplierinfo', 'search_count',
      [[]]
    ]);
    const countResponse = await fetch(`${ODOO_URL}/xmlrpc/2/object`, {
      method: 'POST',
      headers: { 'Content-Type': 'text/xml' },
      body: countXml
    });
    const countResult = await countResponse.text();
    const totalCount = parseSimpleValue(countResult);
    console.log('Total product.supplierinfo records:', totalCount);

    // 3. Get a sample of supplier info records
    console.log('\n3. Getting sample supplier info records...');
    const searchXml = buildXmlRequest('execute_kw', [
      ODOO_DB, uid, ODOO_PASSWORD,
      'product.supplierinfo', 'search',
      [[]], 0, 10
    ]);
    const searchResponse = await fetch(`${ODOO_URL}/xmlrpc/2/object`, {
      method: 'POST',
      headers: { 'Content-Type': 'text/xml' },
      body: searchXml
    });
    const searchResult = await searchResponse.text();
    const recordIds = parseSimpleValue(searchResult);
    console.log('Found record IDs:', recordIds);

    // 4. Read the records to see what they contain
    if (recordIds && recordIds.length > 0) {
      console.log('\n4. Reading supplier info records...');
      const readXml = buildXmlRequest('execute_kw', [
        ODOO_DB, uid, ODOO_PASSWORD,
        'product.supplierinfo', 'read',
        [recordIds, ['id', 'partner_id', 'product_id', 'product_name', 'product_code', 'price']]
      ]);
      const readResponse = await fetch(`${ODOO_URL}/xmlrpc/2/object`, {
        method: 'POST',
        headers: { 'Content-Type': 'text/xml' },
        body: readXml
      });
      const readResult = await readResponse.text();
      console.log('Sample records (raw XML):', readResult.substring(0, 1000) + '...');
    }

    // 5. Check specific suppliers we know about
    const knownSupplierIds = [20, 21, 23, 25, 26]; // From the hardcoded data
    console.log('\n5. Checking known suppliers for products...');
    for (const supplierId of knownSupplierIds) {
      const supplierCountXml = buildXmlRequest('execute_kw', [
        ODOO_DB, uid, ODOO_PASSWORD,
        'product.supplierinfo', 'search_count',
        [[['partner_id', '=', supplierId]]]
      ]);
      const supplierCountResponse = await fetch(`${ODOO_URL}/xmlrpc/2/object`, {
        method: 'POST',
        headers: { 'Content-Type': 'text/xml' },
        body: supplierCountXml
      });
      const supplierCountResult = await supplierCountResponse.text();
      const count = parseSimpleValue(supplierCountResult);
      console.log(`Supplier ID ${supplierId}: ${count} products`);
    }

  } catch (error) {
    console.error('Error:', error);
  }
}

testSupplierProducts();