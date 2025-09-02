#!/bin/bash

PROJECT_REF="fttkapvhobelvodnqxgu"

# List of all edge functions
functions=(
  "debug-odoo-connection"
  "ai-product-search"
  "supplier-catalog-test"
  "search-query-parser"
  "purchase-orders"
  "product-search-enhanced"
  "product-search"
  "product-images"
  "product-catalog"
  "generate-search-embeddings"
  "fetch-moq"
  "debug-xml-response"
  "update-stock-levels"
  "test-xml-import"
  "test-xml-generation"
  "test-searchread"
  "test-products"
  "test-odoo"
  "sync-supplier-products"
  "supplier-list-legacy"
  "supplier-catalog"
)

echo "Starting deployment of edge functions to project: $PROJECT_REF"

# Deploy each function
for func in "${functions[@]}"; do
  echo "Deploying function: $func"
  npx supabase functions deploy "$func" --project-ref "$PROJECT_REF" --no-verify-jwt 2>&1
  if [ $? -eq 0 ]; then
    echo "✅ Successfully deployed: $func"
  else
    echo "❌ Failed to deploy: $func"
  fi
done

echo "✅ All functions deployment completed!"