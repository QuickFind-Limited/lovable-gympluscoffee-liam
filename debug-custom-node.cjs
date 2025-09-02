// Debug our custom XML-RPC client in Node.js to see what XML it generates
const fetch = require('node-fetch');

class XmlRpcClient {
  constructor(url) {
    this.url = url;
  }

  async methodCall(method, params) {
    const xmlRequest = this.buildXmlRequest(method, params);
    
    console.log(`\n📤 SENDING XML TO ${this.url}:`);
    console.log(xmlRequest);
    console.log(`\n`);
    
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
    console.log(`\n📥 RECEIVED XML:`);
    console.log(xmlResponse);
    console.log(`\n`);
    
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
    // Check for fault
    if (xml.includes('<fault>')) {
      const faultMatch = xml.match(/<fault>(.*?)<\/fault>/s);
      if (faultMatch) {
        throw new Error(`XML-RPC Fault: ${faultMatch[1]}`);
      }
    }

    // Extract the value from the response - handle whitespace and newlines
    const valueMatch = xml.match(/<params>\s*<param>\s*<value>(.*?)<\/value>\s*<\/param>\s*<\/params>/s);
    if (!valueMatch) {
      // Try alternative pattern for nested values
      const altMatch = xml.match(/<param>\s*<value>(.*?)<\/value>\s*<\/param>/s);
      if (!altMatch) {
        throw new Error('Invalid XML-RPC response');
      }
      return this.parseValue(altMatch[1]);
    }

    return this.parseValue(valueMatch[1]);
  }

  parseValue(xml) {
    // Trim the XML first
    xml = xml.trim();
    
    // Array - check if XML starts with <array>
    if (xml.startsWith('<array>')) {
      const dataMatch = xml.match(/<data>(.*?)<\/data>/s);
      if (!dataMatch) return [];
      
      const values = [];
      const dataContent = dataMatch[1];
      
      // Parse array values manually to handle nested structures
      let pos = 0;
      while (pos < dataContent.length) {
        const valueStart = dataContent.indexOf('<value>', pos);
        if (valueStart === -1) break;
        
        // Find the matching closing tag by counting nested tags
        let depth = 1;
        let currentPos = valueStart + 7; // length of '<value>'
        let valueEnd = -1;
        
        while (depth > 0 && currentPos < dataContent.length) {
          const nextOpen = dataContent.indexOf('<value>', currentPos);
          const nextClose = dataContent.indexOf('</value>', currentPos);
          
          if (nextClose === -1) break;
          
          if (nextOpen !== -1 && nextOpen < nextClose) {
            depth++;
            currentPos = nextOpen + 7;
          } else {
            depth--;
            if (depth === 0) {
              valueEnd = nextClose;
            }
            currentPos = nextClose + 8; // length of '</value>'
          }
        }
        
        if (valueEnd !== -1) {
          const valueContent = dataContent.substring(valueStart + 7, valueEnd);
          values.push(this.parseValue(valueContent));
          pos = valueEnd + 8;
        } else {
          break;
        }
      }
      
      return values;
    }

    // Struct - check if XML starts with <struct>
    if (xml.startsWith('<struct>')) {
      const obj = {};
      const memberRegex = /<member>\s*<name>(.*?)<\/name>\s*<value>(.*?)<\/value>\s*<\/member>/gs;
      let match;
      while ((match = memberRegex.exec(xml)) !== null) {
        obj[this.unescapeXml(match[1])] = this.parseValue(match[2]);
      }
      return obj;
    }

    // String
    if (xml.startsWith('<string>')) {
      const match = xml.match(/^<string>(.*?)<\/string>$/s);
      return match ? this.unescapeXml(match[1]) : '';
    }

    // Integer
    if (xml.startsWith('<int>') || xml.startsWith('<i4>')) {
      const match = xml.match(/^<(?:int|i4)>(-?\d+)<\/(?:int|i4)>$/);
      return match ? parseInt(match[1]) : 0;
    }

    // Double
    if (xml.startsWith('<double>')) {
      const match = xml.match(/^<double>(-?[\d.]+)<\/double>$/);
      return match ? parseFloat(match[1]) : 0;
    }

    // Boolean
    if (xml.startsWith('<boolean>')) {
      const match = xml.match(/^<boolean>([01])<\/boolean>$/);
      return match ? match[1] === '1' : false;
    }

    // Nil/null
    if (xml === '<nil/>' || xml.startsWith('<nil/>')) {
      return null;
    }

    // Default to string
    return xml;
  }

  unescapeXml(str) {
    return str
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"')
      .replace(/&apos;/g, "'");
  }
}

function createClient(url) {
  return new XmlRpcClient(url);
}

async function testCustomXmlrpc() {
  try {
    console.log('=== TESTING CUSTOM XML-RPC CLIENT (with XML debug) ===');
    
    const config = {
      url: 'https://source-animalfarmacy.odoo.com',
      db: 'source-animalfarmacy',
      username: 'admin@quickfindai.com',
      password: 'BJ62wX2J4yzjS$i'
    };

    // Test authentication first
    console.log('🔵 Testing authentication...');
    const common = createClient(`${config.url}/xmlrpc/2/common`);
    
    const uid = await common.methodCall('authenticate', [
      config.db,
      config.username,
      config.password,
      {}
    ]);

    console.log('✅ Authenticated, UID:', uid);

    // Test the problematic search_read call
    console.log('\n🔵 Testing search_read call...');
    const object = createClient(`${config.url}/xmlrpc/2/object`);
    
    const domain = [['partner_id', '=', 25]];
    const fields = ['id', 'product_name'];
    const options = { fields: fields, limit: 3 };
    
    console.log('Parameters:');
    console.log('- domain:', JSON.stringify(domain));
    console.log('- fields:', JSON.stringify(fields));
    console.log('- options:', JSON.stringify(options));
    
    const result = await object.methodCall('execute_kw', [
      config.db,
      uid,
      config.password,
      'product.supplierinfo',
      'search_read',
      [domain],  // args: domain wrapped in array
      options    // kwargs: options as separate parameter
    ]);

    console.log(`\n✅ Got ${result?.length || 0} products`);
    if (result && result.length > 0) {
      console.log('First product:', JSON.stringify(result[0], null, 2));
    }
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    console.error('Stack:', error.stack);
  }
}

testCustomXmlrpc();