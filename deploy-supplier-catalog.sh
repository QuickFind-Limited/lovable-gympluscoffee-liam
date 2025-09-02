#!/bin/bash

echo "Deploying supplier-catalog edge function..."

# Use the supabase CLI to deploy the function
npx supabase functions deploy supplier-catalog --project-ref xvmnweqtqkkuqsxvcouy

echo "Deployment complete!"