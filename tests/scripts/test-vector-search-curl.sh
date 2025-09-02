#!/bin/bash

# Test vector search edge function with curl
SUPABASE_URL="https://rumaiumnoobdyzdxuumt.supabase.co"
ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ1bWFpdW1ub29iZHl6ZHh1dW10Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzgwMDE2NTQsImV4cCI6MjA1MzU3NzY1NH0.YqLvJvMQJCDW0tJ-GjnxcLbOvdlKGnD82cEp-S1xf0g"

echo "Testing vector search edge function..."

curl -X POST "${SUPABASE_URL}/functions/v1/vector-search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ANON_KEY}" \
  -H "apikey: ${ANON_KEY}" \
  -d '{
    "query": "black rug",
    "strategy": "combined",
    "max_results": 5
  }' | jq .