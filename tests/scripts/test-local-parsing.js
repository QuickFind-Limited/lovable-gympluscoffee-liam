// Test XML parsing locally
const xml = `<array><data>
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

function parseValue(xml) {
  console.log('Parsing XML:', xml.substring(0, 50), '...');
  
  // String
  if (xml.includes('<string>')) {
    console.log('Found string tag');
    const match = xml.match(/<string>(.*?)<\/string>/s);
    return match ? match[1] : '';
  }

  // Integer
  if (xml.includes('<int>') || xml.includes('<i4>')) {
    console.log('Found int tag');
    const match = xml.match(/<(?:int|i4)>(-?\d+)<\/(?:int|i4)>/);
    return match ? parseInt(match[1]) : 0;
  }

  // Double
  if (xml.includes('<double>')) {
    console.log('Found double tag');
    const match = xml.match(/<double>(-?[\d.]+)<\/double>/);
    return match ? parseFloat(match[1]) : 0;
  }

  // Boolean
  if (xml.includes('<boolean>')) {
    console.log('Found boolean tag');
    const match = xml.match(/<boolean>([01])<\/boolean>/);
    return match ? match[1] === '1' : false;
  }

  // Array
  if (xml.includes('<array>')) {
    console.log('Found array tag');
    const dataMatch = xml.match(/<data>(.*?)<\/data>/s);
    if (!dataMatch) {
      console.log('No data tag found');
      return [];
    }
    
    console.log('Data content length:', dataMatch[1].length);
    const values = [];
    const valueRegex = /<value>(.*?)<\/value>/gs;
    let match;
    while ((match = valueRegex.exec(dataMatch[1])) !== null) {
      values.push(parseValue(match[1]));
    }
    console.log('Parsed array with', values.length, 'values');
    return values;
  }

  // Struct
  if (xml.includes('<struct>')) {
    console.log('Found struct tag');
    const obj = {};
    const memberRegex = /<member>\s*<name>(.*?)<\/name>\s*<value>(.*?)<\/value>\s*<\/member>/gs;
    let match;
    while ((match = memberRegex.exec(xml)) !== null) {
      obj[match[1]] = parseValue(match[2]);
    }
    console.log('Parsed struct with keys:', Object.keys(obj));
    return obj;
  }

  // Default to string
  console.log('No known tag found, returning as string');
  return xml.trim();
}

const result = parseValue(xml);
console.log('\nFinal result:', JSON.stringify(result, null, 2));