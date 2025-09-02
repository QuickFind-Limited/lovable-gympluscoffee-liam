// Test direct Odoo XML-RPC search_read
import fetch from 'node-fetch';

const ODOO_URL = 'https://source-animalfarmacy.odoo.com';
const ODOO_DB = 'source-animalfarmacy';
const ODOO_USERNAME = 'admin@quickfindai.com';
const ODOO_PASSWORD = 'BJ62wX2J4yzjS$i';

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

async function authenticate() {
  const xmlRequest = buildXmlRequest('authenticate', [
    ODOO_DB,
    ODOO_USERNAME,
    ODOO_PASSWORD,
    {}
  ]);

  const response = await fetch(`${ODOO_URL}/xmlrpc/2/common`, {
    method: 'POST',
    headers: {
      'Content-Type': 'text/xml',
      'Accept': 'text/xml'
    },
    body: xmlRequest
  });

  const xmlResponse = await response.text();
  // Simple extraction of integer from response
  const match = xmlResponse.match(/<int>(\d+)<\/int>/);
  return match ? parseInt(match[1]) : null;
}

async function searchRead(uid, model, domain, fields) {
  // Test different parameter formats for search_read
  console.log('\nTesting search_read with domain:', JSON.stringify(domain));
  console.log('Fields:', fields);
  
  // Try format 1: domain and fields in single object
  const xmlRequest1 = buildXmlRequest('execute_kw', [
    ODOO_DB,
    uid,
    ODOO_PASSWORD,
    model,
    'search_read',
    [domain],
    { fields: fields, limit: 10 }
  ]);

  const response1 = await fetch(`${ODOO_URL}/xmlrpc/2/object`, {
    method: 'POST',
    headers: {
      'Content-Type': 'text/xml',
      'Accept': 'text/xml'
    },
    body: xmlRequest1
  });

  const xmlResponse1 = await response1.text();
  
  if (xmlResponse1.includes('<fault>')) {
    console.log('❌ Method failed with fault');
    const faultMatch = xmlResponse1.match(/<string>(.*?)<\/string>/s);
    if (faultMatch) {
      console.log('Error:', faultMatch[1].substring(0, 200) + '...');
    }
  } else {
    // Count array items
    const arrayMatches = xmlResponse1.match(/<struct>/g);
    const count = arrayMatches ? arrayMatches.length : 0;
    console.log(`✅ Success! Found ${count} records`);
    
    // Extract first record details if any
    if (count > 0) {
      const nameMatch = xmlResponse1.match(/<member>\s*<name>name<\/name>\s*<value><string>(.*?)<\/string><\/value>/);
      const idMatch = xmlResponse1.match(/<member>\s*<name>id<\/name>\s*<value><int>(\d+)<\/int><\/value>/);
      if (nameMatch && idMatch) {
        console.log(`First record: ${nameMatch[1]} (ID: ${idMatch[1]})`);
      }
    }
  }
}

async function testOdooSearchRead() {
  try {
    console.log('=== Testing Direct Odoo XML-RPC ===\n');
    
    // Authenticate
    console.log('1. Authenticating...');
    const uid = await authenticate();
    if (!uid) {
      throw new Error('Authentication failed');
    }
    console.log('✅ Authenticated with UID:', uid);
    
    // Test 1: Search all partners
    console.log('\n2. Search all partners (no domain)...');
    await searchRead(uid, 'res.partner', [], ['id', 'name', 'supplier_rank']);
    
    // Test 2: Search suppliers
    console.log('\n3. Search suppliers (supplier_rank > 0)...');
    await searchRead(uid, 'res.partner', [['supplier_rank', '>', 0]], ['id', 'name', 'supplier_rank']);
    
    // Test 3: Search by name
    console.log('\n4. Search by name (FastPet)...');
    await searchRead(uid, 'res.partner', [['name', 'ilike', 'FastPet']], ['id', 'name', 'supplier_rank']);
    
  } catch (error) {
    console.error('Error:', error);
  }
}

testOdooSearchRead();