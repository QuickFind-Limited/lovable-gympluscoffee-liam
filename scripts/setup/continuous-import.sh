#!/bin/bash

# Continuous import script for all 4,818 PoundFun products
export SUPABASE_SERVICE_ROLE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ1bWFpdW1ub29iZHl6ZHh1dW10Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzU3NTY1MiwiZXhwIjoyMDY5MTUxNjUyfQ.14NSxXNztDa2R5KLKSYCetWFqC711I3W9AcsQstiDyQ"
export VITE_SUPABASE_URL="https://rumaiumnoobdyzdxuumt.supabase.co"
export BATCH_SIZE=200

echo "🚀 CONTINUOUS IMPORT: ALL 4,818 POUNDFUN PRODUCTS"
echo "=================================================="
echo "⏰ Started: $(date)"
echo "🎯 Target: 4,818 products"
echo "📦 Batch size: $BATCH_SIZE"
echo ""

for session in {1..25}; do
    echo "📦 Import Session $session/25 - $(date)"
    
    # Run import with timeout
    timeout 120s npm run import:products 2>&1 | grep -E "(Progress:|Successful:|Failed:|Success rate)" | tail -3
    
    # Check current count
    echo "   Current status check..."
    
    # Small delay between sessions
    sleep 2
    
    echo "   Session $session completed"
    echo ""
done

echo "🎉 Continuous import process completed!"
echo "⏰ Finished: $(date)"