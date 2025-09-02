import { serve } from 'https://deno.land/std@0.190.0/http/server.ts';

// Inline XML-RPC client with debug logging
class XmlRpcClient {
  private url: string;

  constructor(url: string) {
    this.url = url;
  }

  async methodCall(method: string, params: any[]): Promise<any> {
    const xmlRequest = this.buildXmlRequest(method, params);
    console.log('XML Request:', xmlRequest);
    
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
    console.log('XML Response:', xmlResponse.substring(0, 500) + '...');
    return this.parseXmlResponse(xmlResponse);
  }

  private buildXmlRequest(method: string, params: any[]): string {
    const xmlParams = params.map(param => this.valueToXml(param)).join('');
    
    return `<?xml version="1.0"?>
<methodCall>
  <methodName>${method}</methodName>
  <params>
    ${xmlParams}
  </params>
</methodCall>`;
  }

  private valueToXml(value: any): string {
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

  private escapeXml(str: string): string {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&apos;');
  }

  private parseXmlResponse(xml: string): any {
    if (xml.includes('<fault>')) {
      const faultMatch = xml.match(/<fault>(.*?)<\/fault>/s);
      if (faultMatch) {
        throw new Error(`XML-RPC Fault: ${faultMatch[1]}`);
      }
    }

    const valueMatch = xml.match(/<params>\s*<param>\s*<value>(.*?)<\/value>\s*<\/param>\s*<\/params>/s);
    if (!valueMatch) {
      const altMatch = xml.match(/<param>\s*<value>(.*?)<\/value>\s*<\/param>/s);
      if (!altMatch) {
        throw new Error('Invalid XML-RPC response');
      }
      return this.parseValue(altMatch[1]);
    }

    return this.parseValue(valueMatch[1]);
  }

  private parseValue(xml: string): any {
    xml = xml.trim();
    
    if (xml.startsWith('<array>')) {
      const dataMatch = xml.match(/<data>(.*?)<\/data>/s);
      if (!dataMatch) return [];
      
      const values: any[] = [];
      const dataContent = dataMatch[1];
      
      let pos = 0;
      while (pos < dataContent.length) {
        const valueStart = dataContent.indexOf('<value>', pos);
        if (valueStart === -1) break;
        
        let depth = 1;
        let currentPos = valueStart + 7;
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
            currentPos = nextClose + 8;
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

    if (xml.startsWith('<struct>')) {
      const obj: any = {};
      const memberRegex = /<member>\s*<name>(.*?)<\/name>\s*<value>(.*?)<\/value>\s*<\/member>/gs;
      let match;
      while ((match = memberRegex.exec(xml)) !== null) {
        obj[this.unescapeXml(match[1])] = this.parseValue(match[2]);
      }
      return obj;
    }

    if (xml.startsWith('<string>')) {
      const match = xml.match(/^<string>(.*?)<\/string>$/s);
      return match ? this.unescapeXml(match[1]) : '';
    }

    if (xml.startsWith('<int>') || xml.startsWith('<i4>')) {
      const match = xml.match(/^<(?:int|i4)>(-?\d+)<\/(?:int|i4)>$/);
      return match ? parseInt(match[1]) : 0;
    }

    if (xml.startsWith('<double>')) {
      const match = xml.match(/^<double>(-?[\d.]+)<\/double>$/);
      return match ? parseFloat(match[1]) : 0;
    }

    if (xml.startsWith('<boolean>')) {
      const match = xml.match(/^<boolean>([01])<\/boolean>$/);
      return match ? match[1] === '1' : false;
    }

    if (xml === '<nil/>' || xml.startsWith('<nil/>')) {
      return null;
    }

    return xml;
  }

  private unescapeXml(str: string): string {
    return str
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"')
      .replace(/&apos;/g, "'");
  }
}

// CORS headers
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE',
};

// Main function
serve(async (req: Request) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const url = 'https://source-animalfarmacy.odoo.com';
    const db = 'source-animalfarmacy';
    const username = 'admin@quickfindai.com';
    const password = 'BJ62wX2J4yzjS$i';

    // Connect and authenticate
    const common = new XmlRpcClient(`${url}/xmlrpc/2/common`);
    const uid = await common.methodCall('authenticate', [db, username, password, {}]);

    if (!uid) {
      throw new Error('Authentication failed');
    }

    const object = new XmlRpcClient(`${url}/xmlrpc/2/object`);

    const tests = [];

    // Test 1: Count products
    console.log('Test 1: Counting products...');
    const count = await object.methodCall('execute_kw', [
      db, uid, password,
      'product.product', 'search_count',
      [[]]
    ]);
    tests.push({ test: 'count', result: count });

    // Test 2: Search for product IDs
    console.log('Test 2: Searching for product IDs...');
    const productIds = await object.methodCall('execute_kw', [
      db, uid, password,
      'product.product', 'search',
      [[], 0, 10]
    ]);
    tests.push({ test: 'search', result: productIds });

    // Test 3: Read products if we have IDs
    if (productIds && productIds.length > 0) {
      console.log('Test 3: Reading products...');
      const products = await object.methodCall('execute_kw', [
        db, uid, password,
        'product.product', 'read',
        [productIds.slice(0, 5), ['id', 'name', 'default_code']]
      ]);
      tests.push({ test: 'read', result: products });
    }

    // Test 4: Search_read with different parameter styles
    console.log('Test 4: Search_read...');
    try {
      const searchReadResult = await object.methodCall('execute_kw', [
        db, uid, password,
        'product.product', 'search_read',
        [[]],
        {'fields': ['id', 'name'], 'limit': 5}
      ]);
      tests.push({ test: 'search_read', result: searchReadResult });
    } catch (e) {
      tests.push({ test: 'search_read', error: e.message });
    }

    // Test 5: Check permissions
    console.log('Test 5: Checking permissions...');
    const hasAccess = await object.methodCall('execute_kw', [
      db, uid, password,
      'ir.model.access', 'check',
      ['product.product', 'read']
    ]);
    tests.push({ test: 'permissions', result: hasAccess });

    return new Response(
      JSON.stringify({
        uid: uid,
        tests: tests
      }, null, 2),
      {
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
        },
      }
    );
  } catch (error) {
    console.error('Error:', error);
    return new Response(
      JSON.stringify({ 
        error: error.message || 'Failed to debug',
        details: error.stack 
      }),
      {
        status: 500,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
        },
      }
    );
  }
});