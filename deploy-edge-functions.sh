#!/bin/bash

# Deploy Edge Functions with Updated CORS Headers

echo "🚀 Deploying edge functions with updated CORS headers..."

# List of functions to deploy
FUNCTIONS=(
  "purchase-orders"
  "supplier-catalog"
)

# Deploy each function
for func in "${FUNCTIONS[@]}"; do
  echo "📦 Deploying $func..."
  supabase functions deploy $func --no-verify-jwt
  
  if [ $? -eq 0 ]; then
    echo "✅ $func deployed successfully"
  else
    echo "❌ Failed to deploy $func"
  fi
done

echo "🎉 Deployment complete!"
echo ""
echo "Note: The CORS headers have been updated to include 'x-application-name'."
echo "This should fix the CORS policy errors you were seeing."