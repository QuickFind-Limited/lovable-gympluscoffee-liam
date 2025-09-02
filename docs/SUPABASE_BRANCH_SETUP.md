# Supabase Branch and Secrets Setup Guide

This guide provides step-by-step instructions for creating a Supabase development branch and configuring secrets for edge functions.

## Project Information
- **Project URL**: https://hnidjsfbggiyagwwklpc.supabase.co
- **Project Ref**: hnidjsfbggiyagwwklpc

## Prerequisites
- Supabase CLI (available via `npx supabase`)
- Project must be linked (already configured)
- OpenAI API key from `.env.local`

## Branch Creation Methods

### Method 1: Using Supabase CLI (Recommended)

1. **Create a persistent development branch**:
   ```bash
   npx supabase branches create develop --persistent
   ```

2. **Create a feature branch** (non-persistent):
   ```bash
   npx supabase branches create feature-name
   ```

3. **List all branches**:
   ```bash
   npx supabase branches list
   ```

### Method 2: Using MCP Tools (Programmatic)

```javascript
// First, confirm the cost
const costConfirmation = await mcp__supabase__confirm_cost({
  action: "create_branch",
  project_id: "hnidjsfbggiyagwwklpc"
});

// Then create the branch
const branch = await mcp__supabase__create_branch({
  confirm_cost_id: costConfirmation.cost_id,
  name: "develop"
});
```

### Method 3: Dashboard UI (Branching 2.0)

If Branching 2.0 is enabled:
1. Navigate to the Supabase Dashboard
2. Click the branch dropdown in the top menu
3. Select "Create branch"
4. Choose branch type (preview/persistent)

## Setting Secrets for Edge Functions

### Option 1: Set Individual Secrets

```bash
# Set the OpenAI API key for edge functions
npx supabase secrets set OPENAI_API_KEY="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"

# Set multiple secrets at once
npx supabase secrets set OPENAI_API_KEY="..." ANOTHER_SECRET="value"
```

### Option 2: Use Environment File

1. **Create a `.env` file** in the `supabase` directory:
   ```bash
   mkdir -p supabase
   touch supabase/.env
   ```

2. **Add secrets to the file**:
   ```env
   # supabase/.env
   OPENAI_API_KEY=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
   ```

3. **Load all secrets from the file**:
   ```bash
   npx supabase secrets set --env-file ./supabase/.env
   ```

### Setting Secrets for Specific Branches

When working with branches, you need to specify the branch project ref:

```bash
# Set secrets for a specific branch
npx supabase secrets set OPENAI_API_KEY="..." --project-ref <branch-project-ref>

# Or use environment switching
npx supabase branches get develop -o env >> .env.branch
source .env.branch
npx supabase secrets set OPENAI_API_KEY="..."
```

## Edge Functions Deployment to Branch

1. **Deploy edge functions to a branch**:
   ```bash
   # First, switch to the branch
   npx supabase branches switch develop
   
   # Then deploy functions
   npx supabase functions deploy function-name
   ```

2. **Or deploy with specific project ref**:
   ```bash
   npx supabase functions deploy function-name --project-ref <branch-project-ref>
   ```

## Workflow Summary

1. **Create a development branch**:
   ```bash
   npx supabase branches create develop --persistent
   ```

2. **Set the OpenAI API key secret**:
   ```bash
   npx supabase secrets set OPENAI_API_KEY="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"
   ```

3. **Deploy edge functions**:
   ```bash
   npx supabase functions deploy <function-name>
   ```

4. **List and verify secrets**:
   ```bash
   npx supabase secrets list
   ```

## Important Notes

1. **Branch Isolation**: Each branch has its own:
   - Database instance
   - API endpoints
   - Authentication settings
   - Storage buckets
   - Edge Functions
   - Secrets

2. **Cost Considerations**: 
   - Persistent branches incur ongoing costs
   - Preview branches are temporary and auto-pause
   - Check pricing at https://supabase.com/pricing

3. **Security Best Practices**:
   - Never commit secrets to Git
   - Use `.gitignore` for `.env` files
   - Rotate API keys regularly
   - Use branch-specific secrets for testing

4. **Migration Management**:
   - Branches start with production schema
   - Apply migrations sequentially
   - Test migrations on branches before production

## Troubleshooting

### Branch Creation Issues
- Ensure you have proper permissions
- Check if branching is enabled for your project
- Verify billing is set up for persistent branches

### Secrets Not Working
- Secrets are branch-specific
- Verify you're deploying to the correct branch
- Check secret names match exactly (case-sensitive)
- Use `npx supabase secrets list` to verify

### Network Restrictions
If you have network restrictions enabled:
- Add the branching cluster CIDR: `2600:1f18:2b7d:f600::/56`
- Configure in Dashboard > Settings > Database

## Next Steps

1. Create your development branch
2. Set up the OpenAI API key secret
3. Deploy your edge functions
4. Test the functionality on the branch
5. Merge to production when ready

For more information, see:
- [Supabase Branching Documentation](https://supabase.com/docs/guides/deployment/branching)
- [Edge Functions Documentation](https://supabase.com/docs/guides/functions)
- [Secrets Management](https://supabase.com/docs/reference/cli/supabase-secrets)