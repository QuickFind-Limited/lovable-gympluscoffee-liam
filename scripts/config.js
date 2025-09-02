// Configuration for scripts
// WARNING: This contains sensitive keys and should NEVER be imported in client-side code

export const SUPABASE_URL = 'https://vkxoqaansgbyzcppdiii.supabase.co';

// Service role key - keep this secret!
// This key has full admin access to your Supabase project
export const SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || 
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZreG9xYWFuc2dieXpjcHBkaWlpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Mzk3MTQ4MiwiZXhwIjoyMDY5NTQ3NDgyfQ.Ip7h5Xiiv9V13ihQRNSGkCJHsKRGlY-1PiGtYPrpOk0';