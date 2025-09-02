#!/bin/bash

# Test vector search edge function with apikey header
SUPABASE_URL="https://rumaiumnoobdyzdxuumt.supabase.co"
ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ1bWFpdW1ub29iZHl6ZHh1dW10Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzgwMDE2NTQsImV4cCI6MjA1MzU3NzY1NH0.YqLvJvMQJCDW0tJ-GjnxcLbOvdlKGnD82cEp-S1xf0g"

echo "Testing vector search edge function with apikey..."

# Try with just apikey header (some Supabase functions accept this)
curl -X POST "${SUPABASE_URL}/functions/v1/vector-search" \
  -H "Content-Type: application/json" \
  -H "apikey: ${ANON_KEY}" \
  -d '{
    "query": "black rug",
    "strategy": "combined",
    "max_results": 5
  }' 2>&1