-- Fix Supabase Row Level Security (RLS) Permissions
-- Run this in your Supabase SQL Editor to fix the sync issue
-- 
-- This script will:
-- 1. Check if RLS is enabled
-- 2. Either disable RLS OR create policies to allow inserts/updates
-- 3. Grant necessary permissions

-- ============================================
-- OPTION 1: Disable RLS (Simplest - for public job data)
-- ============================================
-- This is recommended since job listings are public data
ALTER TABLE public.jobs DISABLE ROW LEVEL SECURITY;

-- Verify RLS is disabled
SELECT 
  tablename,
  rowsecurity as rls_enabled
FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename = 'jobs';

-- ============================================
-- OPTION 2: Keep RLS enabled but allow all operations (More secure)
-- ============================================
-- Uncomment this section if you prefer to keep RLS enabled

/*
-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Allow public reads" ON public.jobs;
DROP POLICY IF EXISTS "Allow public inserts" ON public.jobs;
DROP POLICY IF EXISTS "Allow public updates" ON public.jobs;
DROP POLICY IF EXISTS "Allow public deletes" ON public.jobs;

-- Enable RLS
ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;

-- Create policies for jobs table
CREATE POLICY "Allow public reads" 
  ON public.jobs 
  FOR SELECT 
  USING (true);

CREATE POLICY "Allow public inserts" 
  ON public.jobs 
  FOR INSERT 
  WITH CHECK (true);

CREATE POLICY "Allow public updates" 
  ON public.jobs 
  FOR UPDATE 
  USING (true);

CREATE POLICY "Allow public deletes" 
  ON public.jobs 
  FOR DELETE 
  USING (true);
*/

-- ============================================
-- Grant permissions to authenticated and anon users
-- ============================================
-- Grant SELECT, INSERT, UPDATE permissions to the anon role
GRANT SELECT, INSERT, UPDATE, DELETE ON public.jobs TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.jobs TO authenticated;

-- Grant usage on sequences (for auto-increment IDs)
-- Only grant if sequences exist (jobs uses BIGSERIAL)
DO $$
BEGIN
  -- Grant permissions on jobs sequence (always exists if jobs table uses BIGSERIAL)
  IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'jobs_id_seq') THEN
    GRANT USAGE, SELECT ON SEQUENCE public.jobs_id_seq TO anon;
    GRANT USAGE, SELECT ON SEQUENCE public.jobs_id_seq TO authenticated;
  END IF;
END $$;

-- Verify permissions
SELECT 
  'RLS Fixed! Jobs table is ready for sync.' as status,
  (SELECT COUNT(*) FROM public.jobs) as current_jobs_count;

