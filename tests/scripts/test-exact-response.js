// Test with the exact response from Odoo
const xmlResponse = `<?xml version="1.0"?>
<methodResponse>
<params>
<param>
<value><array><data>
<value><struct>
<member>
<name>id</name>
<value><int>42</int></value>
</member>
<member>
<name>name</name>
<value><string>15Ft Spare Hose For Ergo Pro Single Motor Dryer</string></value>
</member>
<member>
<name>list_price</name>
<value><double>70.0</double></value>
</member>
</struct></value>
<value><struct>
<member>
<name>id</name>
<value><int>43</int></value>
</member>
<member>
<name>name</name>
<value><string>19462</string></value>
</member>
<member>
<name>list_price</name>
<value><double>16.0</double></value>
</member>
</struct></value>
</data></array></value>
</param>
</params>

</methodResponse>`;

// Parse using the fixed logic
function parseXmlResponse(xml) {
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
    return parseValue(altMatch[1]);
  }

  return parseValue(valueMatch[1]);
}

function parseValue(xml) {
  // Trim the XML first
  xml = xml.trim();
  
  // Check for complex types first (they contain simple types)
  
  // Array - check if XML starts with <array>
  if (xml.startsWith('<array>')) {
    const dataMatch = xml.match(/<data>(.*?)<\/data>/s);
    if (!dataMatch) return [];
    
    const values = [];
    const valueRegex = /<value>(.*?)<\/value>/gs;
    let match;
    while ((match = valueRegex.exec(dataMatch[1])) !== null) {
      values.push(parseValue(match[1]));
    }
    return values;
  }

  // Struct - check if XML starts with <struct>
  if (xml.startsWith('<struct>')) {
    const obj = {};
    const memberRegex = /<member>\s*<name>(.*?)<\/name>\s*<value>(.*?)<\/value>\s*<\/member>/gs;
    let match;
    while ((match = memberRegex.exec(xml)) !== null) {
      obj[match[1]] = parseValue(match[2]);
    }
    return obj;
  }

  // Now check for simple types
  
  // String
  if (xml.startsWith('<string>')) {
    const match = xml.match(/^<string>(.*?)<\/string>$/s);
    return match ? match[1] : '';
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

try {
  const result = parseXmlResponse(xmlResponse);
  console.log('Parsed result:', JSON.stringify(result, null, 2));
  console.log('\nIs array?', Array.isArray(result));
  console.log('Length:', result.length);
  console.log('\nFirst product:', result[0]);
} catch (error) {
  console.error('Error:', error.message);
}