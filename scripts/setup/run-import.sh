#!/bin/bash

# Get service role key from Supabase MCP
echo "Getting service role key from Supabase..."

# Set environment variables and run import
export VITE_SUPABASE_URL="https://rumaiumnoobdyzdxuumt.supabase.co"

# Run import with a smaller batch to test first
echo "Running product import..."
BATCH_SIZE=10 npm run import:products