-- Supabase Setup SQL
-- Run this in your Supabase SQL Editor to enable data import

-- 1. Create the jobs table (if it doesn't exist)
CREATE TABLE IF NOT EXISTS public.jobs (
  id BIGSERIAL PRIMARY KEY,
  title TEXT,
  company TEXT,
  searched_city TEXT,
  searched_role TEXT,
  location TEXT,
  job_url TEXT,
  date_posted DATE,
  extracted_skills JSONB DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Create indexes for better query performance
CREATE INDEX IF NOT EXISTS jobs_city_idx ON public.jobs (searched_city);
CREATE INDEX IF NOT EXISTS jobs_role_idx ON public.jobs (searched_role);
CREATE INDEX IF NOT EXISTS jobs_date_idx ON public.jobs (date_posted DESC);
CREATE INDEX IF NOT EXISTS jobs_skills_gin ON public.jobs USING GIN (extracted_skills jsonb_path_ops);

-- 3. Disable RLS for public read access (since this is public job data)
--    If you want to keep RLS enabled, use Option 4 below instead
ALTER TABLE public.jobs DISABLE ROW LEVEL SECURITY;

-- 4. ALTERNATIVE: If you want to keep RLS enabled, uncomment these policies:
-- CREATE POLICY "Allow public reads" ON public.jobs
--   FOR SELECT USING (true);
-- 
-- CREATE POLICY "Allow public inserts" ON public.jobs
--   FOR INSERT WITH CHECK (true);
-- 
-- CREATE POLICY "Allow public updates" ON public.jobs
--   FOR UPDATE USING (true);

-- 5. Create unique constraint for upsert operations (prevents duplicates)
--    This allows the import script to use ON CONFLICT
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint 
    WHERE conname = 'jobs_title_company_city_unique'
  ) THEN
    ALTER TABLE public.jobs 
    ADD CONSTRAINT jobs_title_company_city_unique 
    UNIQUE (title, company, searched_city);
  END IF;
END $$;

-- 6. Create subscriptions table for email alerts
CREATE TABLE IF NOT EXISTS public.subscriptions (
  id BIGSERIAL PRIMARY KEY,
  email TEXT NOT NULL,
  keyword TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(email, keyword)
);

-- 7. Create index for faster subscription lookups
CREATE INDEX IF NOT EXISTS subscriptions_email_idx ON public.subscriptions (email);
CREATE INDEX IF NOT EXISTS subscriptions_keyword_idx ON public.subscriptions (keyword);

-- 8. Disable RLS for subscriptions (or create policies if you prefer)
ALTER TABLE public.subscriptions DISABLE ROW LEVEL SECURITY;

-- Verify the tables were created
SELECT 
  'Tables created successfully!' as status,
  (SELECT COUNT(*) FROM public.jobs) as jobs_count,
  (SELECT COUNT(*) FROM public.subscriptions) as subscriptions_count;

