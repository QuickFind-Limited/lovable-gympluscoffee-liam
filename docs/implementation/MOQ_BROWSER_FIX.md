# MOQ Browser Environment Fix

## 🐛 **Issue Fixed**
`ReferenceError: process is not defined` when running MOQ service in browser environment.

## 🔍 **Root Cause**
The `MOQService` was trying to access `process.env.SUPABASE_ANON_KEY` in the browser, but `process` is a Node.js global that's not available in browser environments.

## ✅ **Solution Applied**

### 1. **Export Supabase Anon Key**
Updated `/src/integrations/supabase/client.ts`:
```typescript
// Before: (private)
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'fallback-key'

// After: (exported)
export const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'fallback-key'
```

### 2. **Update MOQ Service Import**
Updated `/src/services/moqService.ts`:
```typescript
// Before:
import { supabaseUrl } from '@/integrations/supabase/client';

// After:
import { supabaseUrl, supabaseAnonKey } from '@/integrations/supabase/client';
```

### 3. **Fix Authorization Header**
Updated MOQ service fetch call:
```typescript
// Before: (causes process error)
'Authorization': `Bearer ${process.env.SUPABASE_ANON_KEY || 'fallback'}`

// After: (uses proper browser env)
'Authorization': `Bearer ${supabaseAnonKey}`
```

## 🎯 **Why This Works**

1. **Vite Environment Variables**: Uses `import.meta.env.VITE_*` which is the correct way to access environment variables in Vite/browser environment
2. **Proper Module Exports**: Makes the anon key available to other modules that need it
3. **Consistent Pattern**: Follows the same pattern already used in the Supabase client setup
4. **Fallback Safety**: Maintains the fallback key if environment variable is not available

## ✅ **Verification**
- ✅ Build completes without errors
- ✅ No more `process is not defined` errors
- ✅ MOQ service can now properly authenticate with Supabase Edge Functions
- ✅ Maintains existing functionality and error handling

## 🚀 **Result**
The MOQ system now works correctly in the browser environment and can successfully call the Supabase Edge Function to fetch MOQ data from Odoo!