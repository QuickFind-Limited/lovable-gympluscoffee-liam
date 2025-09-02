// Test the vector search edge function
const SUPABASE_URL = 'https://rumaiumnoobdyzdxuumt.supabase.co';
const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ1bWFpdW1ub29iZHl6ZHh1dW10Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzgwMDE2NTQsImV4cCI6MjA1MzU3NzY1NH0.YqLvJvMQJCDW0tJ-GjnxcLbOvdlKGnD82cEp-S1xf0g';

async function testVectorSearch() {
  try {
    console.log('Testing vector search edge function...');
    
    const response = await fetch(`${SUPABASE_URL}/functions/v1/vector-search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${ANON_KEY}`,
      },
      body: JSON.stringify({
        query: "black rug",
        strategy: "combined",
        max_results: 5
      })
    });

    const result = await response.json();
    console.log('Response status:', response.status);
    console.log('Response:', JSON.stringify(result, null, 2));

    if (result.products && result.products.length > 0) {
      console.log('\nFirst product:', result.products[0]);
    }

    if (result.debug) {
      console.log('\nDebug info:', result.debug);
    }

  } catch (error) {
    console.error('Test failed:', error);
  }
}

testVectorSearch();