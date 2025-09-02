# Supabase Database Setup

This directory contains the database migrations and configuration for the Supabase backend.

## Running Migrations

### Option 1: Using Supabase CLI (Recommended)

1. Install Supabase CLI if you haven't already:
   ```bash
   npm install -g supabase
   ```

2. Link your project:
   ```bash
   supabase link --project-ref your-project-ref
   ```

3. Run migrations:
   ```bash
   supabase db push
   ```

### Option 2: Manual Migration

If you prefer to run migrations manually:

1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Run the migration files in order from the `migrations` directory

## Migration Files

- `20240122000001_create_profiles_table.sql` - Creates the profiles table with RLS policies and triggers

## Local Development

To run Supabase locally:

```bash
supabase start
```

This will start a local Supabase instance with all services including:
- PostgreSQL database
- Auth server
- Storage server
- Realtime server
- Studio interface

Access the local services at:
- Studio: http://localhost:54323
- API: http://localhost:54321
- Database: postgresql://postgres:postgres@localhost:54322/postgres