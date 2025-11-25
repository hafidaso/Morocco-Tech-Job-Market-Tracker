-- Subscriptions Table Setup for Email Alerts
-- Run this in your Supabase SQL Editor if you haven't already

-- Create subscriptions table for email alerts
CREATE TABLE IF NOT EXISTS public.subscriptions (
  id BIGSERIAL PRIMARY KEY,
  email TEXT NOT NULL,
  keyword TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(email, keyword)
);

-- Create indexes for faster subscription lookups
CREATE INDEX IF NOT EXISTS subscriptions_email_idx ON public.subscriptions (email);
CREATE INDEX IF NOT EXISTS subscriptions_keyword_idx ON public.subscriptions (keyword);

-- Disable RLS for subscriptions (public data)
ALTER TABLE public.subscriptions DISABLE ROW LEVEL SECURITY;

-- Verify the table was created
SELECT 
  'Subscriptions table created successfully!' as status,
  COUNT(*) as existing_subscriptions_count 
FROM public.subscriptions;

