-- Vector Search Setup for Semantic Search
-- Run this in your Supabase SQL Editor to enable pgvector
-- 
-- IMPORTANT: Run this ENTIRE script in one go. Don't skip the DROP statements!

-- 1. Enable the pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Add embedding column to jobs table
-- Using 384 dimensions for sentence-transformers/all-MiniLM-L6-v2 model
ALTER TABLE public.jobs 
ADD COLUMN IF NOT EXISTS embedding vector(384);

-- 3. Create index for fast vector similarity search
-- Using HNSW index for approximate nearest neighbor search (fast and efficient)
CREATE INDEX IF NOT EXISTS jobs_embedding_idx 
ON public.jobs 
USING hnsw (embedding vector_cosine_ops);

-- 4. CRITICAL: Drop the function if it exists (to allow changing return type)
-- You MUST run these DROP statements before creating the new function
-- Drop all possible variations of the function signature
DROP FUNCTION IF EXISTS public.search_jobs_semantic(vector, double precision, integer) CASCADE;
DROP FUNCTION IF EXISTS public.search_jobs_semantic(vector, float, int) CASCADE;
DROP FUNCTION IF EXISTS public.search_jobs_semantic(vector, real, integer) CASCADE;
DROP FUNCTION IF EXISTS public.search_jobs_semantic(vector, numeric, integer) CASCADE;
DROP FUNCTION IF EXISTS public.search_jobs_semantic(vector, double precision, int) CASCADE;
DROP FUNCTION IF EXISTS public.search_jobs_semantic(vector, float, integer) CASCADE;

-- 5. Create a function to search jobs by semantic similarity
-- NOTE: Using CREATE (not CREATE OR REPLACE) because we dropped it above
CREATE FUNCTION public.search_jobs_semantic(
  query_embedding vector(384),
  match_threshold float DEFAULT 0.5,
  match_count int DEFAULT 20
)
RETURNS TABLE (
  id bigint,
  title text,
  company text,
  location text,
  searched_city text,
  searched_role text,
  job_url text,
  date_posted text,
  extracted_skills jsonb,
  similarity float
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  RETURN QUERY
  SELECT
    j.id,
    j.title,
    j.company,
    j.location,
    j.searched_city,
    j.searched_role,
    j.job_url,
    COALESCE(CAST(j.date_posted AS text), '') as date_posted,
    j.extracted_skills,
    1 - (j.embedding <=> query_embedding) as similarity
  FROM public.jobs j
  WHERE j.embedding IS NOT NULL
    AND 1 - (j.embedding <=> query_embedding) > match_threshold
  ORDER BY j.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- 6. Grant execute permission to authenticated and anon users
GRANT EXECUTE ON FUNCTION public.search_jobs_semantic(vector, float, int) TO authenticated;
GRANT EXECUTE ON FUNCTION public.search_jobs_semantic(vector, float, int) TO anon;

-- 7. Verify the setup
SELECT 
  'Vector search setup complete!' as status,
  COUNT(*) FILTER (WHERE embedding IS NOT NULL) as jobs_with_embeddings,
  COUNT(*) as total_jobs
FROM public.jobs;

