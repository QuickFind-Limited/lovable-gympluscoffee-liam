// Test parsing of false values in XML

function parseValue(xml) {
  xml = xml.trim();
  
  // Boolean
  if (xml.startsWith('<boolean>')) {
    const match = xml.match(/^<boolean>([01])<\/boolean>$/);
    return match ? match[1] === '1' : false;
  }
  
  // Check if it's literally "false" without tags
  if (xml === 'false' || xml === 'False') {
    return false;
  }
  
  // Default
  return xml;
}

// Test cases
const testCases = [
  '<boolean>0</boolean>',
  '<boolean>1</boolean>',
  'false',
  'False',
  'true',
  ''
];

console.log('Testing false value parsing:');
testCases.forEach(test => {
  console.log(`${test} => ${JSON.stringify(parseValue(test))}`);
});