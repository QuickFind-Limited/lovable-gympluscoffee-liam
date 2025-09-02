# Supabase Email Verification in Codespaces

## Issue
When working in GitHub Codespaces, the email verification link redirects to `localhost:3000` which doesn't match your development server running on port `8080`.

## Quick Fix

1. **Copy the verification link** you received in your email
2. **Modify the URL** by replacing the redirect_to parameter:

### Original URL:
```
https://hnidjsfbggiyagwwklpc.supabase.co/auth/v1/verify?token=pkce_2829b4d6755f7991249a379a65573bb37dac961efd3c019598f58298&type=signup&redirect_to=http://localhost:3000
```

### Modified URL for Codespaces:
Replace `redirect_to=http://localhost:3000` with your Codespaces URL:

```
https://hnidjsfbggiyagwwklpc.supabase.co/auth/v1/verify?token=pkce_2829b4d6755f7991249a379a65573bb37dac961efd3c019598f58298&type=signup&redirect_to=https://https://sturdy-space-garbanzo-w9wjq4px74qcvv7r.github.dev/auth/confirm
```

Or if you want to test locally, use:
```
https://hnidjsfbggiyagwwklpc.supabase.co/auth/v1/verify?token=pkce_2829b4d6755f7991249a379a65573bb37dac961efd3c019598f58298&type=signup&redirect_to=http://localhost:8080/auth/confirm
```

## Permanent Solution

To fix this permanently, you need to:

1. **Update Supabase Dashboard Settings**:
   - Go to your Supabase project dashboard
   - Navigate to Authentication > URL Configuration
   - Update the "Site URL" to your Codespaces URL
   - Add your Codespaces URL to "Redirect URLs" whitelist

2. **For Development**, you can also set the redirect URL dynamically:

```typescript
// In src/integrations/supabase/auth.ts
const getRedirectUrl = () => {
  // Check if running in Codespaces
  if (window.location.hostname.includes('github.dev')) {
    return `${window.location.origin}/auth/confirm`;
  }
  // Default for local development
  return `http://localhost:8080/auth/confirm`;
};

// Then in signUp:
emailRedirectTo: getRedirectUrl(),
```

## Alternative: Direct Verification

You can also verify your email directly by:

1. Opening the Supabase SQL Editor in your project dashboard
2. Running this query (replace with your email):

```sql
UPDATE auth.users 
SET email_confirmed_at = now() 
WHERE email = 'your-email@example.com';
```

This will mark your email as verified and you can then sign in normally.