// Test the deployed edge function directly
const fetch = require('node-fetch');

async function testEdgeFunction() {
  try {
    console.log('🔵 Testing deployed edge function...');
    
    // Test the edge function endpoint directly
    const url = 'https://vkxoqaansgbyzcppdiii.supabase.co/functions/v1/supplier-catalog?supplierId=25&offset=0&limit=5';
    
    console.log('📤 Request URL:', url);
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        // Use the correct anon key from the frontend config
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE'
      }
    });

    console.log('📥 Response Status:', response.status);
    console.log('📥 Response Headers:', response.headers.raw());

    const responseText = await response.text();
    console.log('📥 Response Body:', responseText);

    if (response.ok) {
      const data = JSON.parse(responseText);
      console.log('\n✅ SUCCESS! Edge function returned:');
      console.log('- Data length:', data.data?.length || 0);
      console.log('- Total:', data.total);
      console.log('- Has more:', data.hasMore);
      
      if (data.data && data.data.length > 0) {
        console.log('\n🎉 FIRST PRODUCT:');
        console.log(JSON.stringify(data.data[0], null, 2));
      } else {
        console.log('\n⚠️  NO PRODUCTS RETURNED - Still empty data array');
      }
    } else {
      console.log('\n❌ FAILED! Edge function returned error');
      
      try {
        const errorData = JSON.parse(responseText);
        console.log('Error details:', errorData);
      } catch (e) {
        console.log('Raw error:', responseText);
      }
    }

  } catch (error) {
    console.error('❌ Error testing edge function:', error.message);
  }
}

testEdgeFunction();