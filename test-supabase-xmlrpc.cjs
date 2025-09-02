// Test the actual Supabase XML-RPC client vs Node.js xmlrpc library
const xmlrpc = require('xmlrpc');

// Simulate the Supabase XmlRpcClient
class SupabaseXmlRpcClient {
  constructor(url) {
    this.url = url;
  }

  async methodCall(method, params) {
    const xmlRequest = this.buildXmlRequest(method, params);
    console.log('🔵 Supabase XML-RPC Request:');
    console.log(xmlRequest);
    console.log('\n📊 Parameters structure:');
    console.log('Method:', method);
    console.log('Params array:', JSON.stringify(params, null, 2));
    
    const response = await fetch(this.url, {
      method: 'POST',
      headers: {
        'Content-Type': 'text/xml',
        'Accept': 'text/xml'
      },
      body: xmlRequest
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const xmlResponse = await response.text();
    return this.parseXmlResponse(xmlResponse);
  }

  buildXmlRequest(method, params) {
    const xmlParams = params.map(param => this.valueToXml(param)).join('');
    
    return `<?xml version="1.0"?>
<methodCall>
  <methodName>${method}</methodName>
  <params>
    ${xmlParams}
  </params>
</methodCall>`;
  }

  valueToXml(value) {
    if (value === null || value === undefined) {
      return '<param><value><nil/></value></param>';
    }

    if (typeof value === 'string') {
      return `<param><value><string>${this.escapeXml(value)}</string></value></param>`;
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
        this.valueToXml(item).replace(/<\/?param>/g, '')
      ).join('');
      return `<param><value><array><data>${arrayItems}</data></array></value></param>`;
    }

    if (typeof value === 'object') {
      const members = Object.entries(value).map(([key, val]) => 
        `<member>
          <name>${this.escapeXml(key)}</name>
          ${this.valueToXml(val).replace(/<\/?param>/g, '')}
        </member>`
      ).join('');
      return `<param><value><struct>${members}</struct></value></param>`;
    }

    return '<param><value><string></string></value></param>';
  }

  escapeXml(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&apos;');
  }

  parseXmlResponse(xml) {
    // Simplified parsing for testing
    if (xml.includes('<fault>')) {
      const faultMatch = xml.match(/<fault>(.*?)<\/fault>/s);
      if (faultMatch) {
        throw new Error(`XML-RPC Fault: ${faultMatch[1]}`);
      }
    }
    return { success: true, xml };
  }
}

async function compareXmlRpcClients() {
  console.log('🔍 COMPARING XML-RPC CLIENT IMPLEMENTATIONS\n');
  
  const config = {
    url: 'https://source-animalfarmacy.odoo.com',
    db: 'source-animalfarmacy',
    username: 'admin@quickfindai.com',
    password: 'BJ62wX2J4yzjS$i'
  };

  try {
    // Test 1: Node.js xmlrpc library (WORKING)
    console.log('===== NODE.JS XMLRPC LIBRARY (WORKING) =====');
    const nodeClient = xmlrpc.createClient({ url: `${config.url}/xmlrpc/2/object` });
    
    console.log('🔵 Node.js XML-RPC call structure:');
    console.log('methodCall("execute_kw", [db, uid, password, model, method, args, options])');
    console.log('- args[0] = domain array');
    console.log('- Second parameter = options object\n');

    // Test 2: Supabase XmlRpcClient (BROKEN?)
    console.log('===== SUPABASE XML-RPC CLIENT (POTENTIALLY BROKEN) =====');
    const supabaseClient = new SupabaseXmlRpcClient(`${config.url}/xmlrpc/2/object`);
    
    // Test parameters that I'm using in the fixed searchRead
    const testParams = [
      config.db,           // db
      2,                   // uid (from previous test)
      config.password,     // password
      'product.supplierinfo', // model
      'search_read',       // method
      [[['partner_id', '=', 25]]], // domain wrapped in array
      {                    // options object
        fields: ['id', 'partner_id'],
        offset: 0,
        limit: 3
      }
    ];

    console.log('🔵 Testing Supabase client with same parameters...');
    try {
      await supabaseClient.methodCall('execute_kw', testParams);
    } catch (error) {
      console.log('❌ Supabase client would send this XML but gets error:', error.message);
    }

    console.log('\n🔍 KEY INSIGHT:');
    console.log('The issue might be that the Supabase XML-RPC client serializes');
    console.log('the options object differently than the Node.js xmlrpc library.');
    console.log('');
    console.log('✅ Node.js xmlrpc: Treats 7th parameter as separate options');
    console.log('❌ Supabase client: Might serialize all parameters as array items');

  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

compareXmlRpcClients();