# Supabase Authentication Architecture Plan

## Overview
This document outlines the complete architecture for replacing the fake authentication system with real Supabase authentication, including email verification.

## Current State Analysis
- **Fake Auth**: Currently using localStorage to simulate authentication
- **Components**: AuthForm, UserContext, ProtectedRoute in App.tsx
- **User Flow**: Simple email/password form → localStorage → redirect to dashboard
- **Missing**: Real backend auth, email verification, password reset, session management

## New Architecture Design

### 1. File Structure Changes

```
src/
├── lib/
│   ├── supabase/
│   │   ├── client.ts          # Supabase client initialization
│   │   └── types.ts           # TypeScript types for auth
│   └── auth/
│       ├── auth-helpers.ts    # Auth utility functions
│       └── auth-errors.ts     # Error handling utilities
├── contexts/
│   ├── AuthContext.tsx        # NEW: Centralized auth state
│   └── UserContext.tsx        # MODIFIED: Integrate with AuthContext
├── components/
│   ├── auth/
│   │   ├── AuthForm.tsx       # MOVED & MODIFIED: Enhanced auth form
│   │   ├── EmailVerification.tsx  # NEW: Email verification UI
│   │   ├── PasswordReset.tsx     # NEW: Password reset flow
│   │   └── AuthGuard.tsx         # NEW: Route protection wrapper
│   └── ui/
│       └── auth-loading.tsx   # NEW: Auth loading states
├── pages/
│   ├── Auth.tsx               # MODIFIED: Support multiple auth states
│   ├── VerifyEmail.tsx        # NEW: Email verification page
│   └── ResetPassword.tsx      # NEW: Password reset page
└── App.tsx                    # MODIFIED: Use AuthContext
```

### 2. Component Architecture

#### A. Supabase Client Setup (`/src/lib/supabase/client.ts`)
```typescript
import { createClient } from '@supabase/supabase-js'
import type { Database } from './types'

export const supabase = createClient<Database>(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
)
```

#### B. AuthContext (`/src/contexts/AuthContext.tsx`)
```typescript
interface AuthContextType {
  user: User | null
  session: Session | null
  loading: boolean
  signIn: (email: string, password: string) => Promise<void>
  signUp: (email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
  resetPassword: (email: string) => Promise<void>
  updatePassword: (password: string) => Promise<void>
}
```

#### C. Enhanced AuthForm Component
- Email/password validation
- Loading states during auth operations
- Error handling with user-friendly messages
- Support for sign in/sign up toggle
- Email verification reminder

#### D. Email Verification Flow
1. User signs up → Supabase sends verification email
2. Redirect to `/verify-email` with instructions
3. User clicks email link → redirected back to app
4. App detects verification → completes sign in
5. Update UI to show verified status

#### E. Route Protection
```typescript
// AuthGuard component
const AuthGuard = ({ children, requireVerified = true }) => {
  const { user, session, loading } = useAuth()
  
  if (loading) return <AuthLoading />
  if (!session) return <Navigate to="/auth" />
  if (requireVerified && !user?.email_confirmed_at) {
    return <Navigate to="/verify-email" />
  }
  
  return children
}
```

### 3. Data Flow Diagram

```
User Action → AuthForm → AuthContext → Supabase Client → Supabase Backend
                ↓             ↓              ↓                ↓
            Validation    State Mgmt    API Calls      Email Service
                ↓             ↓              ↓                ↓
            Error UI    Loading UI    Session Token    Verification Email
                              ↓              ↓
                         UserContext    localStorage
                              ↓              ↓
                         Protected      Persistence
                           Routes
```

### 4. Implementation Steps

#### Phase 1: Setup (Priority: HIGH)
1. Install Supabase dependencies
2. Create Supabase client configuration
3. Set up environment variables
4. Create type definitions

#### Phase 2: Core Auth (Priority: HIGH)
1. Create AuthContext with Supabase integration
2. Implement auth state management
3. Create auth helper functions
4. Set up error handling

#### Phase 3: UI Components (Priority: HIGH)
1. Refactor AuthForm for real auth
2. Create EmailVerification component
3. Build loading states
4. Implement error displays

#### Phase 4: Route Protection (Priority: HIGH)
1. Create AuthGuard component
2. Update App.tsx routing
3. Integrate with existing ProtectedRoute
4. Add verification requirements

#### Phase 5: Email Verification (Priority: MEDIUM)
1. Create verification page
2. Handle email confirmation flow
3. Add resend email functionality
4. Update user feedback

#### Phase 6: Additional Features (Priority: MEDIUM)
1. Password reset flow
2. Remember me functionality
3. Session persistence
4. Logout functionality

#### Phase 7: Migration (Priority: LOW)
1. Clean up old auth code
2. Remove fake auth logic
3. Update all auth dependencies
4. Test all protected routes

### 5. Error Handling Strategy

```typescript
enum AuthError {
  INVALID_CREDENTIALS = 'Invalid email or password',
  EMAIL_NOT_VERIFIED = 'Please verify your email',
  NETWORK_ERROR = 'Connection error. Please try again',
  RATE_LIMITED = 'Too many attempts. Please wait',
  WEAK_PASSWORD = 'Password must be at least 6 characters',
  EMAIL_IN_USE = 'Email already registered'
}
```

### 6. Security Considerations

- Store tokens securely using Supabase's built-in session management
- Implement PKCE flow for additional security
- Use secure HTTP-only cookies when possible
- Add rate limiting on auth endpoints
- Sanitize all user inputs
- Use environment variables for sensitive config

### 7. Migration Strategy

1. **Parallel Development**: Build new auth alongside existing
2. **Feature Flag**: Use environment variable to toggle auth systems
3. **Gradual Rollout**: Test with internal users first
4. **Data Migration**: Help existing users set passwords
5. **Cleanup**: Remove old auth code after verification

### 8. Testing Plan

- Unit tests for auth helpers
- Integration tests for auth flows
- E2E tests for critical paths
- Manual testing of email flows
- Load testing for concurrent users
- Security testing for vulnerabilities

## Next Steps

1. AuthImplementer agent will handle core auth implementation
2. UIBuilder agent will create auth UI components
3. TestEngineer agent will write comprehensive tests
4. Coordinator will manage the migration process