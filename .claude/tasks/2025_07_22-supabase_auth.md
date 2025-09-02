# Instruction: Implement Supabase Authentication with Email Verification

## Goal

Replace the fake authentication system with real Supabase authentication using email/password with mandatory email verification. Users must verify their email before accessing the application.

## Existing files

- src/components/AuthForm.tsx - Contains fake authentication logic with localStorage
- src/pages/Auth.tsx - Auth page wrapper component
- src/contexts/UserContext.tsx - Basic user context with userType state
- src/App.tsx - Route protection using localStorage check
- src/components/LoginTransition.tsx - Login animation component
- src/components/dashboard/UserNavigation.tsx - User dropdown with logout
- .env.local - Contains Supabase environment variables

### New files to create

- src/lib/supabase/client.ts - Supabase client initialization
- src/lib/supabase/types.ts - TypeScript types for authentication
- src/lib/auth/auth-helpers.ts - Authentication utility functions  
- src/lib/auth/auth-errors.ts - Error handling utilities
- src/contexts/AuthContext.tsx - Centralized authentication state management
- src/components/auth/EmailVerification.tsx - Email verification UI component
- src/pages/VerifyEmail.tsx - Email verification page
- src/pages/auth/confirm/route.ts - Email confirmation callback handler

## Grouped tasks

### Setup & Configuration

> Initialize Supabase client and configure the authentication environment

- Install @supabase/supabase-js dependency via npm
- Create Supabase client configuration in src/lib/supabase/client.ts using environment variables from .env.local
- Define TypeScript interfaces for User, Session, and AuthError types in src/lib/supabase/types.ts
- Configure Vite environment variable types for VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY

### Core Authentication Implementation

> Build the centralized authentication system with Supabase integration

- Create AuthContext provider with Supabase session management, including auto-refresh and persistence
- Implement auth helper functions: signUp with email verification redirect, signIn with password, signOut, and resetPassword
- Add comprehensive error handling utilities mapping Supabase error codes to user-friendly messages
- Set up onAuthStateChange listener to sync authentication state across tabs and handle token refresh

### UI Components Update

> Refactor existing components and create new ones for real authentication

- Refactor AuthForm to use Supabase signUp/signIn with proper validation, loading states, and error display
- Create EmailVerification component showing verification instructions and resend email functionality
- Add email verification page at /verify-email route with clear messaging and redirect after verification
- Update LoginTransition to work with async authentication flow and handle errors gracefully
- Modify protected route logic in App.tsx to check Supabase session instead of localStorage

### Email Verification Flow

> Implement the complete email verification user journey

- Configure email redirect URL in signUp options to point to /auth/confirm callback route
- Create auth confirmation handler to process token_hash and type parameters from Supabase email links
- Implement automatic session establishment after successful email verification
- Add user feedback for unverified email attempts with clear instructions to check inbox

### Integration & Cleanup

> Update all components and remove fake authentication code

- Update UserNavigation and all 7 protected pages to use Supabase signOut method
- Replace UserContext integration with AuthContext for user state management
- Remove all localStorage-based authentication checks and fake user data
- Update route protection to require both authentication and email verification
- Clean up unused authentication-related localStorage keys

## Validation checkpoints

- User can sign up with email/password and receives verification email within 60 seconds
- Clicking email verification link successfully verifies account and redirects to dashboard
- Unverified users cannot access protected routes and see clear verification instructions
- Sign in works for verified users with correct session persistence
- Sign out clears session and redirects to auth page
- Authentication state persists across page refreshes and browser tabs
- Error messages are user-friendly and actionable for common scenarios
- Loading states provide appropriate feedback during authentication operations

## Estimations

- Confidence: 9/10 - Clear requirements with comprehensive Supabase documentation
- Time to implement: 4-6 hours for complete implementation and testing