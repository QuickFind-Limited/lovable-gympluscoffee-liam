import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.7';

export interface User {
  id: string;
  email: string;
  role?: string;
  app_metadata?: any;
  user_metadata?: any;
}

export async function requireAuth(req: Request): Promise<User> {
  const authHeader = req.headers.get('authorization');
  
  if (!authHeader) {
    throw new Error('Missing authorization header');
  }

  const token = authHeader.replace('Bearer ', '');
  
  if (!token) {
    throw new Error('Missing auth token');
  }

  const supabaseUrl = Deno.env.get('SUPABASE_URL');
  const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
  
  if (!supabaseUrl || !supabaseServiceKey) {
    throw new Error('Missing Supabase configuration');
  }

  // Service role key should never be accepted as a user auth token
  // This would be a major security vulnerability
  if (token === supabaseServiceKey) {
    throw new Error('Service role key cannot be used for user authentication');
  }

  const supabase = createClient(supabaseUrl, supabaseServiceKey);

  // Verify the JWT token
  const { data: { user }, error } = await supabase.auth.getUser(token);
  
  if (error || !user) {
    throw new Error('Invalid auth token');
  }

  return {
    id: user.id,
    email: user.email!,
    role: user.role,
    app_metadata: user.app_metadata,
    user_metadata: user.user_metadata
  };
}

export async function getOptionalAuth(req: Request): Promise<User | null> {
  try {
    return await requireAuth(req);
  } catch {
    return null;
  }
}

export async function validateRequest(req: Request): Promise<{ success: boolean; user?: User; error?: string }> {
  try {
    const user = await requireAuth(req);
    return { success: true, user };
  } catch (error) {
    return { 
      success: false, 
      error: error instanceof Error ? error.message : 'Authentication failed' 
    };
  }
}

