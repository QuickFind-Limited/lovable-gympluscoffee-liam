// Compare the exact XML output between working Node.js and our custom client
const fetch = require('node-fetch');

// Test what our custom client would generate for the exact same parameters
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

// Test the exact parameters that should work
const testParams = [
  'source-animalfarmacy', // db
  2,                      // uid
  'BJ62wX2J4yzjS$i',     // password
  'product.supplierinfo', // model
  'search_read',          // method
  [[['partner_id', '=', 25]]], // args (domain wrapped in array)
  { fields: ['id', 'product_name'], limit: 3 } // kwargs
];

console.log('=== CUSTOM CLIENT XML OUTPUT ===');
console.log('Parameters:', JSON.stringify(testParams, null, 2));
console.log('\nGenerated XML:');
const customXml = buildXmlRequest('execute_kw', testParams);
console.log(customXml);

console.log('\n=== COMPARISON WITH WORKING NODE.JS XML ===');
console.log('Working Node.js XML (from earlier debug):');
console.log('<?xml version="1.0"?><methodCall><methodName>execute_kw</methodName><params><param><value><string>source-animalfarmacy</string></value></param><param><value><int>2</int></value></param><param><value><string>BJ62wX2J4yzjS$i</string></value></param><param><value><string>product.supplierinfo</string></value></param><param><value><string>search_read</string></value></param><param><value><array><data><value><array><data><value><array><data><value><string>partner_id</string></value><value><string>=</string></value><value><int>25</int></value></data></array></value></data></array></value></data></array></value></param><param><value><struct><member><name>fields</name><value><array><data><value><string>id</string></value><value><string>product_name</string></value></data></array></value></member><member><name>limit</name><value><int>3</int></value></member></struct></value></param></params></methodCall>');

console.log('\n=== DIFFERENCE ANALYSIS ===');
console.log('Key differences to check:');
console.log('1. Array nesting levels for domain parameter');
console.log('2. Struct member formatting'); 
console.log('3. XML spacing and formatting');
console.log('4. Parameter order and typing');