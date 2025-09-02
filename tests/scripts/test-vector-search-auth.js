// Test the vector search edge function with proper authentication
import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = 'https://rumaiumnoobdyzdxuumt.supabase.co';
const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ1bWFpdW1ub29iZHl6ZHh1dW10Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzgwMDE2NTQsImV4cCI6MjA1MzU3NzY1NH0.YqLvJvMQJCDW0tJ-GjnxcLbOvdlKGnD82cEp-S1xf0g';

const supabase = createClient(SUPABASE_URL, ANON_KEY);

async function testVectorSearch() {
  try {
    console.log('Testing vector search edge function with auth...');
    
    // Sign in first (you can replace with actual credentials if needed)
    const { data: { session }, error: authError } = await supabase.auth.getSession();
    
    const accessToken = session?.access_token || ANON_KEY;
    console.log('Using token:', accessToken ? 'Session token' : 'Anon key');
    
    const response = await fetch(`${SUPABASE_URL}/functions/v1/vector-search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
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