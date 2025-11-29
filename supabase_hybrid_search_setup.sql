-- Hybrid Search Setup: Combine Filters with Semantic Search
-- Run this in your Supabase SQL Editor after setting up vector search
-- This allows filtering by city/role/skill AND searching by meaning

-- 1. Create hybrid search function (filters + semantic search)
DROP FUNCTION IF EXISTS public.search_jobs_hybrid(vector, float, int, text, text, text) CASCADE;

CREATE FUNCTION public.search_jobs_hybrid(
  query_embedding vector(384),
  match_threshold float DEFAULT 0.3,
  match_count int DEFAULT 20,
  filter_city text DEFAULT NULL,
  filter_role text DEFAULT NULL,
  filter_skill text DEFAULT NULL
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
    -- Apply city filter if provided
    AND (filter_city IS NULL OR LOWER(j.searched_city) = LOWER(filter_city))
    -- Apply role filter if provided
    AND (filter_role IS NULL OR LOWER(j.searched_role) LIKE '%' || LOWER(filter_role) || '%' OR LOWER(j.title) LIKE '%' || LOWER(filter_role) || '%')
    -- Apply skill filter if provided (check if skill exists in extracted_skills JSONB array)
    AND (filter_skill IS NULL OR j.extracted_skills @> jsonb_build_array(filter_skill))
  ORDER BY j.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION public.search_jobs_hybrid(vector, float, int, text, text, text) TO authenticated;
GRANT EXECUTE ON FUNCTION public.search_jobs_hybrid(vector, float, int, text, text, text) TO anon;


-- 2. Create "More Like This" function (find similar jobs based on a job's embedding)
DROP FUNCTION IF EXISTS public.find_similar_jobs(bigint, float, int) CASCADE;

CREATE FUNCTION public.find_similar_jobs(
  source_job_id bigint,
  match_threshold float DEFAULT 0.3,
  match_count int DEFAULT 5
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
DECLARE
  source_embedding vector(384);
BEGIN
  -- Get the embedding of the source job
  SELECT embedding INTO source_embedding
  FROM public.jobs
  WHERE id = source_job_id AND embedding IS NOT NULL;
  
  -- If source job doesn't have embedding, return empty
  IF source_embedding IS NULL THEN
    RETURN;
  END IF;
  
  -- Find similar jobs (excluding the source job itself)
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
    1 - (j.embedding <=> source_embedding) as similarity
  FROM public.jobs j
  WHERE j.embedding IS NOT NULL
    AND j.id != source_job_id  -- Exclude the source job
    AND 1 - (j.embedding <=> source_embedding) > match_threshold
  ORDER BY j.embedding <=> source_embedding
  LIMIT match_count;
END;
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION public.find_similar_jobs(bigint, float, int) TO authenticated;
GRANT EXECUTE ON FUNCTION public.find_similar_jobs(bigint, float, int) TO anon;


-- 3. Verify the setup
SELECT 'Hybrid search functions created successfully!' as status;

-- Test the functions (optional - uncomment to test)
-- SELECT * FROM search_jobs_hybrid(
--   (SELECT embedding FROM jobs WHERE embedding IS NOT NULL LIMIT 1),
--   0.3, 5, 'Casablanca', NULL, NULL
-- );

-- SELECT * FROM find_similar_jobs(
--   (SELECT id FROM jobs WHERE embedding IS NOT NULL LIMIT 1),
--   0.3, 5
-- );

