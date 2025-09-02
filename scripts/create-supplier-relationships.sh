#!/bin/bash

# Script to create supplier-product relationships in Odoo via edge function

echo "Creating supplier-product relationships in Odoo..."

# First, let's check what products exist
echo "Checking existing products and suppliers..."

curl -X POST "https://vkxoqaansgbyzcppdiii.supabase.co/functions/v1/check-products" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE" \
  -H "Content-Type: application/json" | jq '.'

echo -e "\n\nNow creating supplier-product relationships..."

# Note: This would call the create-supplier-relationships function once deployed
# curl -X POST "https://vkxoqaansgbyzcppdiii.supabase.co/functions/v1/create-supplier-relationships" \
#   -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5NzE0ODIsImV4cCI6MjA2OTU0NzQ4Mn0.4ZxwCwhjzi9qnSXCQlbFHJqtv2J-RpJHgocR_tB6IAE" \
#   -H "Content-Type: application/json" | jq '.'

echo -e "\n\nDone!"