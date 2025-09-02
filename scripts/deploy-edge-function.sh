#!/bin/bash

# Deploy edge function using Supabase CLI with project reference

PROJECT_REF="vkxoqaansgbyzcppdiii"
FUNCTION_NAME="odoo-suppliers-final"

echo "Deploying edge function: $FUNCTION_NAME"
echo "Project: $PROJECT_REF"

# Deploy with project reference
npx supabase functions deploy $FUNCTION_NAME --project-ref $PROJECT_REF --no-verify-jwt

echo "Deployment complete!"