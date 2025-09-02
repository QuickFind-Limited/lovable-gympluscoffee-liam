#!/bin/bash

echo "🚀 Deploying fixed supplier-catalog function..."
echo ""
echo "This deployment includes:"
echo "✅ Fixed searchRead method parameter format"
echo "✅ Enhanced logging for debugging"
echo "✅ Individual parameter passing for Odoo XML-RPC"
echo ""

# Deploy the supplier-catalog function with the fixed searchRead method
npx supabase functions deploy supplier-catalog --project-ref xvmnweqtqkkuqsxvcouy

echo ""
echo "🎯 Expected result after deployment:"
echo "- Products should appear when expanding suppliers"
echo "- Console will show detailed searchRead logs"
echo "- data array should contain actual product records"
echo ""
echo "✅ Deployment complete!"