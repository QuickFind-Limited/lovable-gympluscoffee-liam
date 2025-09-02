// Test the fixed array parsing logic

function parseValue(xml) {
  // Trim the XML first
  xml = xml.trim();
  
  // Check for complex types first (they contain simple types)
  
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
        values.push(parseValue(valueContent));
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

// Test with the array XML
const arrayXml = `<array><data>
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
</data></array>`;

const result = parseValue(arrayXml);
console.log('Parsed result:', JSON.stringify(result, null, 2));
console.log('\nIs array?', Array.isArray(result));
console.log('Length:', result.length);
console.log('\nFirst product:', result[0]);
console.log('Second product:', result[1]);