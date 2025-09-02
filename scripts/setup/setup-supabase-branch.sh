#!/bin/bash

# Supabase Branch Setup Script
# This script automates the creation of a Supabase development branch and sets up secrets

set -e

echo "🚀 Supabase Branch Setup Script"
echo "================================"

# Configuration
PROJECT_REF="rumaiumnoobdyzdxuumt"
BRANCH_NAME="${1:-develop}"
OPENAI_API_KEY="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"

echo "📋 Configuration:"
echo "  - Project Ref: $PROJECT_REF"
echo "  - Branch Name: $BRANCH_NAME"
echo ""

# Step 1: Create branch
echo "1️⃣ Creating branch '$BRANCH_NAME'..."
if npx supabase branches create "$BRANCH_NAME" --persistent; then
    echo "✅ Branch created successfully!"
else
    echo "⚠️  Branch creation failed or already exists. Continuing..."
fi

# Step 2: List branches to get the branch project ref
echo ""
echo "2️⃣ Listing branches..."
npx supabase branches list

# Step 3: Set secrets
echo ""
echo "3️⃣ Setting OpenAI API key secret..."
if npx supabase secrets set OPENAI_API_KEY="$OPENAI_API_KEY"; then
    echo "✅ Secret set successfully!"
else
    echo "❌ Failed to set secret"
    exit 1
fi

# Step 4: Verify secrets
echo ""
echo "4️⃣ Verifying secrets..."
npx supabase secrets list

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "  1. Switch to your branch: npx supabase branches switch $BRANCH_NAME"
echo "  2. Deploy edge functions: npx supabase functions deploy <function-name>"
echo "  3. Test your functions with the branch URL"
echo ""
echo "💡 Tip: To get branch-specific credentials, run:"
echo "   npx supabase branches get $BRANCH_NAME -o env"