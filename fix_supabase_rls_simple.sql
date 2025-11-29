-- Simple Fix for Supabase RLS Permissions (No Errors!)
-- Run this in your Supabase SQL Editor
-- This version safely handles all table types (BIGSERIAL, UUID, etc.)

-- ============================================
-- Step 1: Disable RLS (safely handles missing tables)
-- ============================================
DO $$
BEGIN
  -- Disable RLS on jobs table if it exists
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'jobs') THEN
    ALTER TABLE public.jobs DISABLE ROW LEVEL SECURITY;
    RAISE NOTICE 'RLS disabled on jobs table';
  END IF;
END $$;

-- ============================================
-- Step 2: Grant table permissions
-- ============================================
-- Jobs table permissions
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'jobs') THEN
    GRANT SELECT, INSERT, UPDATE, DELETE ON public.jobs TO anon;
    GRANT SELECT, INSERT, UPDATE, DELETE ON public.jobs TO authenticated;
    RAISE NOTICE 'Permissions granted on jobs table';
  END IF;
END $$;

-- ============================================
-- Step 3: Grant sequence permissions (only if sequences exist)
-- ============================================
DO $$
BEGIN
  -- Jobs sequence (if table uses BIGSERIAL)
  IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'jobs_id_seq') THEN
    GRANT USAGE, SELECT ON SEQUENCE public.jobs_id_seq TO anon;
    GRANT USAGE, SELECT ON SEQUENCE public.jobs_id_seq TO authenticated;
    RAISE NOTICE 'Sequence permissions granted for jobs_id_seq';
  END IF;
END $$;

-- ============================================
-- Step 4: Verify the fix
-- ============================================
SELECT 
  '✅ RLS Fixed!' as status,
  tablename,
  rowsecurity as rls_enabled,
  (SELECT COUNT(*) FROM public.jobs) as jobs_count
FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename = 'jobs';

