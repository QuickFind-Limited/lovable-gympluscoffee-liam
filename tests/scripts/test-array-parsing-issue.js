// Test to show the array parsing issue

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

// Current parsing logic
function parseValueCurrent(xml) {
  xml = xml.trim();
  
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
  
  // ... rest of parsing logic
}

// The issue is the regex is matching ALL <value> tags, including nested ones
// Let's see what the regex captures
const dataMatch = arrayXml.match(/<data>(.*?)<\/data>/s);
if (dataMatch) {
  const valueRegex = /<value>(.*?)<\/value>/gs;
  let match;
  let count = 0;
  console.log('All <value> matches found:');
  while ((match = valueRegex.exec(dataMatch[1])) !== null) {
    count++;
    console.log(`\nMatch ${count}:`);
    console.log(match[1].substring(0, 100) + '...');
  }
}

// What we need is to match only the top-level <value> tags in the array
// This is tricky with regex because of nested tags