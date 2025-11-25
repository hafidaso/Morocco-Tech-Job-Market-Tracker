# 🧠 Semantic Search Setup Guide

This guide will help you set up AI-powered semantic search for your Job Market Tracker.

## Overview

Semantic search uses vector embeddings to find jobs by **meaning**, not just keywords. For example:
- Searching "AI" will find jobs mentioning "Machine Learning", "LLM", "Artificial Intelligence"
- Searching "Web Dev" will find "Frontend Engineer", "React Developer", "Full Stack"
- Much more intelligent than simple keyword matching!

## Prerequisites

1. ✅ **Supabase Database** - Already set up
2. ✅ **Python 3.13+** - Already installed
3. ⚠️ **sentence-transformers** - Need to install
4. ⚠️ **pgvector extension** - Need to enable in Supabase

## Step 1: Enable pgvector in Supabase

Run this SQL in your Supabase SQL Editor:

```sql
-- Copy contents from: supabase_vector_setup.sql
-- Or run the SQL directly
```

The SQL will:
1. Enable the `vector` extension
2. Add an `embedding` column to the `jobs` table (384 dimensions)
3. Create an HNSW index for fast similarity search
4. Create a search function `search_jobs_semantic()`

**Important**: Make sure to run this before generating embeddings!

## Step 2: Install sentence-transformers

```bash
pip install sentence-transformers
```

This installs the AI model library we'll use to generate embeddings.

**Model Used**: `all-MiniLM-L6-v2`
- 384 dimensions (compact)
- Fast inference
- Good quality for job descriptions
- Free, no API key needed!

## Step 3: Generate Embeddings for Existing Jobs

Run the embedding generation script:

```bash
python3 generate_embeddings.py
```

This will:
1. Load all jobs from Supabase
2. Generate embeddings for each job description
3. Store embeddings in the `embedding` column
4. Process in batches for efficiency

**Expected output**:
```
🤖 Loading sentence transformer model...
✅ Model loaded: all-MiniLM-L6-v2 (384 dimensions)

🔌 Connecting to Supabase...
📊 Fetching jobs from Supabase...
   Found 505 jobs

🔍 Checking which jobs need embeddings...
   0 jobs already have embeddings
   505 jobs need embeddings

🧮 Generating embeddings in batches of 32...
   ✅ Batch 1/16: Generated 32 embeddings
      💾 Saved 32 embeddings to Supabase (32/505)
   ...

🎉 Embedding generation complete!
   Processed: 505/505 jobs
```

**Time**: ~2-5 minutes for 500 jobs (depends on your machine)

## Step 4: Test Semantic Search

1. **Start your backend**:
   ```bash
   uvicorn main:app --reload
   ```

2. **Test the API endpoint**:
   ```bash
   curl "http://127.0.0.1:8000/jobs/search?query=Machine%20Learning&limit=5"
   ```

   Or visit in browser:
   ```
   http://127.0.0.1:8000/jobs/search?query=AI&limit=10
   ```

3. **Try different queries**:
   - `AI` → finds "Machine Learning", "LLM", "Artificial Intelligence"
   - `Web Development` → finds "Frontend", "React", "Full Stack"
   - `Data Science` → finds "Data Analyst", "ML Engineer", "Data Scientist"

## Step 5: Use in Frontend

The frontend already has semantic search integrated!

1. **Start your frontend**:
   ```bash
   cd client
   npm run dev
   ```

2. **Open the dashboard** and look for the search bar

3. **Toggle AI search**:
   - Click the "🔍 Keyword" button to switch to "🧠 AI"
   - Now your search uses semantic matching!

4. **Try searching**:
   - Type "AI" and see it find Machine Learning jobs
   - Type "Web Dev" and see it find Frontend roles
   - Much smarter than keyword search!

## How It Works

### 1. Embedding Generation
- Each job description is converted to a 384-dimensional vector
- The model understands semantic meaning, not just words
- Stored in PostgreSQL using pgvector

### 2. Query Processing
- User's search query is converted to the same vector space
- Uses cosine similarity to find closest matches
- Returns jobs ordered by semantic similarity

### 3. Search Function
- Supabase RPC function `search_jobs_semantic()` does the heavy lifting
- Uses HNSW index for fast approximate nearest neighbor search
- Configurable similarity threshold (default: 0.3)

## API Endpoint

### `GET /jobs/search`

**Parameters**:
- `query` (required): Search query string
- `limit` (optional, default: 20): Max results (1-50)
- `threshold` (optional, default: 0.3): Similarity threshold (0.0-1.0)

**Example**:
```bash
GET /jobs/search?query=Machine%20Learning&limit=10&threshold=0.4
```

**Response**:
```json
{
  "query": "Machine Learning",
  "total": 10,
  "data": [
    {
      "id": 123,
      "title": "Data Scientist",
      "company": "Tech Corp",
      "similarity": 0.87
      ...
    }
  ],
  "threshold": 0.4
}
```

## Troubleshooting

### "Semantic search is not available"
- Install sentence-transformers: `pip install sentence-transformers`
- Restart your backend server

### "Failed to load embedding model"
- Check that sentence-transformers is installed
- The model downloads automatically on first use (~90MB)
- Ensure you have internet connection for first run

### "pgvector extension not found"
- Run `supabase_vector_setup.sql` in Supabase SQL Editor
- Make sure the `vector` extension is enabled

### "No embeddings found"
- Run `python3 generate_embeddings.py` to generate embeddings
- Check that jobs have embeddings: `SELECT COUNT(*) FROM jobs WHERE embedding IS NOT NULL;`

### "Semantic search returns no results"
- Lower the `threshold` parameter (try 0.2 or 0.1)
- Check that embeddings were generated successfully
- Verify the search function exists: `SELECT * FROM search_jobs_semantic(...)`

### Slow search performance
- Ensure the HNSW index was created: `\d+ jobs` in psql
- The index is created automatically by `supabase_vector_setup.sql`

## Performance

- **Embedding Generation**: ~2-5 minutes for 500 jobs
- **Search Query**: <100ms (thanks to HNSW index)
- **Model Size**: ~90MB (downloads once)
- **Memory Usage**: ~200MB for model + embeddings

## Future Enhancements

- [ ] Hybrid search (combine keyword + semantic)
- [ ] Search by job description (not just title/company)
- [ ] Multi-language support
- [ ] Personalized search (learn from user clicks)
- [ ] Search history and suggestions

## Next Steps

1. ✅ Run `supabase_vector_setup.sql` in Supabase
2. ✅ Install `sentence-transformers`
3. ✅ Run `python3 generate_embeddings.py`
4. ✅ Test with `curl` or browser
5. ✅ Try semantic search in the frontend!

Once set up, your job search will be **magical** - finding jobs by meaning, not just keywords! 🎉

