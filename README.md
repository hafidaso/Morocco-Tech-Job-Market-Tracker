# 🇲🇦 Morocco Tech Job Market Tracker

A full-stack data intelligence platform that scrapes, analyzes, and visualizes tech job market trends across Morocco. Built with Python, FastAPI, Next.js, and real-time automation. Features **AI-powered semantic search** using vector embeddings.

![Status](https://img.shields.io/badge/status-active-success)
![Python](https://img.shields.io/badge/python-3.13-blue)
![Next.js](https://img.shields.io/badge/next.js-16.0.3-black)
![FastAPI](https://img.shields.io/badge/fastapi-0.121.3-green)
![AI Search](https://img.shields.io/badge/AI%20Search-Vector%20Embeddings-purple)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Data Pipeline](#data-pipeline)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Future Enhancements](#future-enhancements)

## 🎯 Overview

This project transforms raw job postings into actionable market intelligence. It automatically:

1. **Scrapes** job listings from Indeed, LinkedIn, Google, and Bayt across major Moroccan cities
2. **Extracts** technical skills using NLP and regex pattern matching
3. **Generates** AI embeddings for intelligent semantic search
4. **Analyzes** trends to identify in-demand technologies
5. **Visualizes** insights through an interactive dashboard with AI-powered search

**Current Dataset**: 505+ unique job postings with skill extraction, trend analysis, and **fully operational AI-powered semantic search** using vector embeddings.

## ✨ Features

- 🔄 **Automated Scraping**: Runs every 6 hours via APScheduler (configurable)
- 🧠 **NLP Skill Extraction**: Regex-based pattern matching for 60+ tech skills
- 📊 **Real-time Dashboard**: Live charts showing top skills, city distribution, and job listings
- 📈 **Historical Trends**: Line chart tracking monthly velocity for top tech stacks
- 🔍 **Search & Filter**: Find jobs by company, role, or city
- 🧠 **AI-Powered Semantic Search**: Vector search finds jobs by meaning, not just keywords (e.g., "AI" finds "Machine Learning", "LLM", "Artificial Intelligence")
- 🌐 **RESTful API**: FastAPI backend with automatic documentation
- ☁️ **Supabase Storage**: Processed jobs synced to PostgreSQL + JSONB for reliable persistence
- 📱 **Responsive UI**: Dark mode dashboard built with Next.js and Tailwind CSS
- 🔁 **Auto-refresh**: Frontend polls API every 60 seconds for fresh data
- 📬 **Email Alerts**: Users subscribe to keywords and get Resend-powered digests whenever new matching jobs land
- 📥 **Export Reports**: Download current job data as CSV (Excel-compatible) or PDF reports with one click

## 🏗️ Architecture

```
┌─────────────────┐
│   Job Sites     │ (Indeed, LinkedIn, Google, Bayt)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   scraper.py    │ → morocco_data_market.csv
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ analyze_skills.py│ → processed_jobs_for_api.json
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ generate_       │ → Vector embeddings (384-dim)
│ embeddings.py   │   for semantic search
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Supabase DB    │ PostgreSQL + pgvector
│  (PostgreSQL)   │ + JSONB + Vector embeddings
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    main.py      │ FastAPI + APScheduler
│  (Backend API)  │ + Semantic Search Endpoint
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Next.js App    │ React Dashboard
│   (Frontend)    │ + AI Search Toggle
└─────────────────┘
```

## 🛠️ Tech Stack

### Backend
- **Python 3.13**: Core language
- **FastAPI**: REST API framework
- **APScheduler**: Background job automation
- **pandas**: Data manipulation
- **python-jobspy**: Web scraping library
- **sentence-transformers**: AI embeddings for semantic search
- **supabase**: PostgreSQL database with pgvector extension
- **uvicorn**: ASGI server

### Frontend
- **Next.js 16**: React framework with SSR
- **TypeScript**: Type safety
- **Tailwind CSS**: Styling
- **Recharts**: Data visualization
- **Axios**: HTTP client
- **Lucide React**: Icons

## 📁 Project Structure

```
Job Market Trends Tracker/
├── scraper.py                      # Phase 1: Web scraping script
├── analyze_skills.py               # Phase 2: NLP skill extraction
├── main.py                         # Phase 3: FastAPI + automation + semantic search
├── generate_embeddings.py          # Generate vector embeddings for semantic search
├── import_to_supabase.py           # Import jobs to Supabase database
├── test_semantic_search.py         # Test script for semantic search
├── test_email.py                   # Test script for email alerts
├── test_semantic_search.py         # Test script for semantic search functionality
│
├── requirements.txt                 # Python dependencies
├── morocco_data_market.csv         # Raw scraped data
├── processed_jobs_for_api.json     # Analyzed data for API
│
├── supabase_setup.sql              # Initial Supabase table setup
├── supabase_vector_setup.sql       # Vector search setup (pgvector)
├── supabase_subscriptions_setup.sql # Email subscriptions table
│
├── EMAIL_ALERTS_SETUP.md          # Email alerts documentation
├── SEMANTIC_SEARCH_SETUP.md       # Semantic search documentation
│
├── client/                         # Next.js frontend
│   ├── app/
│   │   ├── page.tsx               # Main dashboard with semantic search UI
│   │   ├── layout.tsx             # Root layout
│   │   └── globals.css            # Global styles
│   ├── package.json
│   └── next.config.ts
│
└── README.md                       # This file
```

## 🚀 Installation

### Prerequisites

- Python 3.13+
- Node.js 18+
- npm or yarn

### Backend Setup

1. **Clone or navigate to the project directory**:
   ```bash
   cd "Job Market Trends Tracker"
   ```

2. **Install Python dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```
   
   Or install manually:
   ```bash
   pip3 install fastapi uvicorn apscheduler pandas python-jobspy supabase resend python-dotenv sentence-transformers
   ```

3. **Create a `.env` file** (preferred) or export variables manually:
   ```bash
   cat > .env <<'EOF'
   SUPABASE_URL="https://cajemqbnvxmtqfsnnvjt.supabase.co"
   SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   RESEND_API_KEY=""
   RESEND_FROM_EMAIL="jobs@resend.dev"
   EOF
   ```
   > Keep secrets private—never commit `.env` to git.

4. **Verify installation**:
   ```bash
   python3 --version
   python3 -c "import fastapi; import supabase; print('FastAPI + Supabase ready')"
   ```

### Frontend Setup

1. **Navigate to client directory**:
   ```bash
   cd client
   ```

2. **Install Node dependencies**:
   ```bash
   npm install
   ```

3. **Verify installation**:
   ```bash
   npm run dev
   # Should start on http://localhost:3000
   ```

### Semantic Search Setup (AI-Powered Search)

To enable semantic search (finding jobs by meaning, not just keywords):

1. **Set up Supabase Vector Extension**:
   - Open your Supabase SQL Editor
   - **Important**: Run the DROP statements first if the function already exists
   - Copy and paste the entire contents of `supabase_vector_setup.sql` into Supabase SQL Editor
   - This will:
     - Enable the `pgvector` extension
     - Add the `embedding` column (384 dimensions)
     - Create HNSW index for fast similarity search
     - Create the `search_jobs_semantic()` RPC function
     - Grant execute permissions

2. **Generate Embeddings**:
   - After importing jobs to Supabase, generate vector embeddings:
     ```bash
     python3 generate_embeddings.py
     ```
   - This will process all jobs and create 384-dimensional embeddings
   - The script automatically skips jobs that already have embeddings
   - Processes in batches of 32 for efficiency

3. **Test Semantic Search**:
   - Start the API: `uvicorn main:app --reload`
   - Test the search endpoint:
     ```bash
     curl "http://127.0.0.1:8000/jobs/search?query=AI&limit=5&threshold=0.2"
     ```
   - Or use the test script:
     ```bash
     python3 test_semantic_search.py
     ```
   - In the frontend, toggle the "🧠 AI" button to enable semantic search

**Note**: 
- The first time you run `generate_embeddings.py`, it will download the model (~90MB)
- Subsequent runs are faster and only process new jobs
- Search performance: <100ms per query thanks to HNSW indexing

## 💻 Usage

### Running the Full Stack

#### Terminal 1: Start Backend API
```bash
cd "Job Market Trends Tracker"
uvicorn main:app --reload
```

The API will be available at:
- **API**: http://127.0.0.1:8000
- **Docs**: http://127.0.0.1:8000/docs (Swagger UI)

#### Terminal 2: Start Frontend
```bash
cd client
npm run dev
```

The dashboard will be available at:
- **Dashboard**: http://localhost:3000

### Manual Pipeline Execution

If you want to run the scraping and analysis manually:

```bash
# Step 1: Scrape jobs
python3 scraper.py

# Step 2: Extract skills
python3 analyze_skills.py

# Step 3: Restart API to reload data
# (Ctrl+C the uvicorn process, then restart)
uvicorn main:app --reload
```

### Manual Integration Test Checklist

1. **Scraper (Data Collection)**
   - Command: `python scraper.py`
   - Check: `morocco_data_market.csv` exists and file size > 0 KB.
2. **Analyzer (Data Processing)**
   - Command: `python analyze_skills.py`
   - Check: `processed_jobs_for_api.json` exists, contains `job_url` plus `extracted_skills`.
3. **Database Sync (Persistence)**
   - Command: run `sync_supabase_from_disk()` or start the API (`uvicorn main:app --reload`).
   - Check: Supabase Table Editor shows rows in `jobs`, `job_url` is populated.
4. **Semantic Search Setup**
   - Command: Run `supabase_vector_setup.sql` in Supabase SQL Editor, then `python3 generate_embeddings.py`
   - Check: Run `python3 test_semantic_search.py` to verify embeddings and search functionality
5. **API (Serving)**
   - Command: `uvicorn main:app --reload`
   - Check: Visit `http://127.0.0.1:8000/jobs` and confirm JSON payload with Supabase data.
   - Check: Test semantic search: `curl "http://127.0.0.1:8000/jobs/search?query=AI&limit=5"`
6. **Frontend (Visualization)**
   - Command: `cd client && npm run dev`
   - Check: `http://localhost:3000` loads charts, job list, and the Apply button opens the source posting.
   - Check: Toggle "🧠 AI" button and test semantic search in the UI.

### Automation

The backend automatically runs the pipeline every **6 hours** via APScheduler. To change the interval, edit `main.py`:

```python
# For testing (1 minute - use with caution!)
scheduler.add_job(run_pipeline, "interval", minutes=1)

# Production (6 hours - recommended)
scheduler.add_job(run_pipeline, "interval", hours=6)
```

⚠️ **Warning**: Scraping too frequently (every minute) can result in IP bans. Use intervals of 4-12 hours for production.

## 📡 API Endpoints

### `GET /`
Health check and job count.

**Response**:
```json
{
  "status": "Live",
  "jobs_count": 454
}
```

### `GET /jobs`
Get job listings with optional filters. Data now comes directly from Supabase.

**Query Parameters**:
- `city` (optional): Filter by city (e.g., "Casablanca")
- `role` (optional): Filter by role (e.g., "Data Scientist")
- `skill` (optional): Filter by detected skill (e.g., "React")
- `limit` (optional, default: 20): Maximum results to return

**Example**:
```bash
curl "http://127.0.0.1:8000/jobs?city=Casablanca&skill=React&limit=10"
```

**Response**:
```json
{
  "total": 42,
  "data": [
    {
      "title": "Data Scientist",
      "company": "TechCorp",
      "searched_city": "Casablanca",
      "extracted_skills": ["Python", "SQL", "React"],
      "date_posted": "2025-11-10"
    }
  ]
}
```

### `GET /jobs/search`
AI-powered semantic search for jobs using vector embeddings. Finds jobs by meaning, not just exact keywords.

**Query Parameters**:
- `query` (required): Search query (e.g., "Machine Learning", "Web Development", "AI")
- `limit` (optional, default: 20, max: 50): Maximum number of results
- `threshold` (optional, default: 0.3, range: 0.0-1.0): Similarity threshold (higher = more strict matching)

**Example**:
```bash
curl "http://127.0.0.1:8000/jobs/search?query=AI&limit=10&threshold=0.3"
```

**Response**:
```json
{
  "query": "AI",
  "total": 15,
  "threshold": 0.3,
  "data": [
    {
      "title": "Machine Learning Engineer",
      "company": "TechCorp",
      "searched_city": "Casablanca",
      "extracted_skills": ["Python", "TensorFlow", "NLP"],
      "date_posted": "2025-11-10"
    }
  ]
}
```

**How it works**: 
- Uses `sentence-transformers/all-MiniLM-L6-v2` to convert job descriptions and queries into 384-dimensional vectors
- Finds jobs with similar semantic meaning using cosine similarity
- Powered by PostgreSQL's pgvector extension with HNSW indexing for fast search (<100ms)
- Results are ordered by similarity score (highest first)

**Example Queries**:
- `"AI"` → finds "Machine Learning Engineer", "LLM Specialist", "Artificial Intelligence", "AI Engineer"
- `"Web Dev"` → finds "Frontend Engineer", "React Developer", "Full Stack Developer", "Web Developer"
- `"Data Science"` → finds "Data Scientist", "Data Analyst", "ML Engineer", "Analytics Specialist"
- `"Backend"` → finds "Backend Engineer", "API Developer", "Server-side Developer", "Node.js Developer"

**Performance**:
- Search query latency: <100ms (thanks to HNSW index)
- Embedding generation: ~2-5 minutes for 500 jobs
- Model size: ~90MB (downloads once on first use)
- Similarity threshold: Adjustable (0.0-1.0), default 0.3
  - Lower threshold (0.1-0.2): More results, broader matches
  - Higher threshold (0.4-0.5): Fewer results, more precise matches

### `POST /subscribe`
Persist an email + keyword subscription. The backend will automatically email the subscriber after future scrapes uncover matching jobs.

**Payload**:
```json
{
  "email": "you@example.com",
  "keyword": "react"
}
```

**Responses**:
- `200 OK` + confirmation message if created or already exists
- `400 Bad Request` if the keyword is missing
- `500 Internal Server Error` if Supabase insert fails

### `GET /trends/skills`
Get top 10 most in-demand skills.

**Response**:
```json
[
  {"name": "Python", "value": 142},
  {"name": "SQL", "value": 142},
  {"name": "Machine Learning", "value": 102}
]
```

### `GET /trends/cities`
Get job distribution by city.

**Response**:
```json
[
  {"name": "Casablanca", "value": 200},
  {"name": "Rabat", "value": 150},
  {"name": "Morocco", "value": 104}
]
```

### `GET /trends/history`
Return month-over-month counts for the most in-demand skills (or a specific skill).

**Query Parameters**:
- `skill` (optional): Focus on a single skill
- `top` (optional, default: 5, max: 10): Number of skills to include when `skill` is not supplied

**Response**:
```json
{
  "skills": ["React", "Python", "SQL"],
  "data": [
    {"month": "2025-09", "React": 4, "Python": 8, "SQL": 5},
    {"month": "2025-10", "React": 7, "Python": 10, "SQL": 9},
    {"month": "2025-11", "React": 12, "Python": 14, "SQL": 11}
  ]
}
```

### `GET /export/csv`
Download job listings as a CSV file (Excel-compatible). Perfect for data analysis in spreadsheets.

**Query Parameters** (optional filters):
- `city` (optional): Filter by city (e.g., "Casablanca")
- `role` (optional): Filter by role (e.g., "Data Scientist")
- `skill` (optional): Filter by detected skill (e.g., "React")

**Example**:
```bash
curl "http://127.0.0.1:8000/export/csv?city=Casablanca" -o jobs.csv
```

**Response**: CSV file with columns:
- Title, Company, Location, City, Role, Date Posted, Skills, Job URL

**Frontend**: Click the "Download CSV" button in the dashboard header.

### `GET /export/pdf`
Download job listings as a formatted PDF report with summary statistics and job listings.

**Query Parameters** (optional filters):
- `city` (optional): Filter by city (e.g., "Casablanca")
- `role` (optional): Filter by role (e.g., "Data Scientist")
- `skill` (optional): Filter by detected skill (e.g., "React")

**Example**:
```bash
curl "http://127.0.0.1:8000/export/pdf?skill=Python" -o report.pdf
```

**Response**: PDF file containing:
- Report title and generation timestamp
- Summary statistics (total jobs, top city, top skill)
- Job listings table (first 50 jobs, with truncated fields for readability)
- Note: CSV export recommended for complete data

**Frontend**: Click the "Download PDF" button in the dashboard header.

**Requirements**:
- CSV export: Uses `pandas` (already in requirements.txt)
- PDF export: Requires `reportlab` (already in requirements.txt)

## 🔄 Data Pipeline

### Phase 1: Scraping (`scraper.py`)

- **Target Cities**: Casablanca, Rabat, Tanger, Morocco (catch-all)
- **Target Roles**: Data Scientist, Data Analyst, Data Engineer, Business Analyst, Ingénieur Data, Big Data, Business Intelligence
- **Sites**: Indeed, LinkedIn, Google, Bayt
- **Parameters**:
  - `results_wanted`: 40 per search
  - `hours_old`: 720 (30 days)
  - `linkedin_fetch_description`: True (for NLP analysis)

**Output**: `morocco_data_market.csv`

### Phase 2: Analysis (`analyze_skills.py`)

- **Skill Dictionary**: 60+ tech skills with regex patterns
- **Extraction Method**: Pattern matching on job descriptions
- **Multilingual Support**: Handles English and French job descriptions

**Output**: `processed_jobs_for_api.json`

### Phase 3: API & Automation (`main.py`)

- **Scheduler**: APScheduler runs pipeline every 6 hours
- **Data Loading**: Processed jobs synced to Supabase + in-memory cache refreshed from the DB
- **Endpoints**: RESTful API for frontend consumption

### Phase 4: Embedding Generation (`generate_embeddings.py`)

- **Model**: Uses `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)
- **Process**: Generates vector embeddings for all job descriptions
- **Storage**: Saves embeddings to Supabase `embedding` column
- **Batch Processing**: Processes jobs in batches of 32 for efficiency
- **Incremental**: Automatically skips jobs that already have embeddings

**Output**: Vector embeddings stored in Supabase for semantic search

### Phase 5: Frontend (`client/app/page.tsx`)

- **Polling**: Fetches fresh data every 60 seconds
- **Visualizations**: Bar charts (skills), pie charts (cities), line charts (historical trends)
- **Search**: Real-time filtering by company/role (keyword search)
- **AI Search**: Toggle button to enable semantic search with debounced queries
- **Export**: Download buttons for CSV and PDF reports in the dashboard header

## ⚙️ Configuration

### Scraper Settings (`scraper.py`)

```python
CITIES = ["Casablanca", "Rabat", "Tanger", "Morocco"]
ROLES = ["Data Scientist", "Data Analyst", ...]
results_wanted = 40      # Jobs per search
hours_old = 720          # 30 days lookback
time.sleep(5)           # Delay between requests
```

### Scheduler Settings (`main.py`)

```python
scheduler.add_job(run_pipeline, "interval", hours=6)
```

### Supabase Settings (`main.py`)

- `SUPABASE_URL`: Project URL (e.g., `https://cajemqbnvxmtqfsnnvjt.supabase.co`)
- `SUPABASE_KEY`: Service or anon key with insert/delete rights
- `SUPABASE_TABLE`: Defaults to `jobs`

**Table Schema**

| Column          | Type      | Notes                                           |
|-----------------|-----------|-------------------------------------------------|
| `id`            | bigint    | Identity primary key                            |
| `title`         | text      | Job title                                       |
| `company`       | text      | Employer name                                   |
| `location`      | text      | Raw location text                               |
| `searched_city` | text      | Normalized city used for filtering              |
| `searched_role` | text      | Search role keyword                             |
| `date_posted`   | text      | ISO date string (YYYY-MM-DD)                    |
| `job_url`       | text      | External link for the Apply button              |
| `extracted_skills` | jsonb  | Array of extracted skills                       |
| `embedding`     | vector(384) | Vector embedding for semantic search (optional) |
| `created_at`    | timestamptz | Defaults to `now()`                           |

> A unique constraint on `(title, company, searched_city)` prevents duplicates when upserting data.

> `sync_supabase_from_disk()` truncates and re-inserts all rows after each pipeline run.

### Notifications (Resend + subscriptions)

1. **Create the `subscriptions` table** (SQL editor → run):
   ```sql
   create table if not exists public.subscriptions (
     id uuid primary key default uuid_generate_v4(),
     email text not null,
     keyword text not null,
     created_at timestamptz not null default now()
   );
   create index if not exists subscriptions_email_idx on public.subscriptions (email);
   create index if not exists subscriptions_keyword_idx on public.subscriptions (keyword);
   ```
   > Grant insert/select rights to the same service key used by the API.

2. **Configure Resend**:
   ```bash
   export RESEND_API_KEY=re_********************************
   export RESEND_FROM_EMAIL="Morocco Jobs <jobs@yourdomain.com>"
   ```
   - The default sender falls back to `jobs@resend.dev` if `RESEND_FROM_EMAIL` is omitted.
   - Install the SDK (`pip3 install resend`) if you haven't already.

3. **How it works**:
   - When `run_pipeline()` ingests fresh jobs, it compares them to previously cached IDs.
   - Matching subscribers receive a digest (max 10 jobs) per keyword via Resend.

### Frontend Settings (`client/app/page.tsx`)

```typescript
const API_URL = "http://127.0.0.1:8000";
// Polling interval: 60000ms (60 seconds)
```

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'jobspy'"

**Solution**:
```bash
pip3 install -U python-jobspy
```

### "Network Error" in Frontend

**Solution**: Ensure the FastAPI backend is running:
```bash
uvicorn main:app --reload
```

### "Port 3000 is in use"

**Solution**: Kill existing Next.js processes:
```bash
pkill -f "next dev"
```

### Bayt Returns 403 Errors

**Status**: Expected. Bayt has anti-scraping measures. The scraper continues with other sites (Indeed, LinkedIn, Google).

### Hydration Warnings in Browser

**Status**: Harmless. Caused by browser extensions injecting attributes. Suppressed via `suppressHydrationWarning` in layout.

### Low Job Count

**Solutions**:
1. Increase `results_wanted` in `scraper.py` (currently 40)
2. Increase `hours_old` (currently 720 = 30 days)
3. Add more cities or roles to search

### Semantic Search Not Working

**Symptoms**: 
- "Semantic search is not available" error
- No results when using AI search toggle
- "Failed to load embedding model" error

**Solutions**:
1. **Install sentence-transformers**:
   ```bash
   pip3 install sentence-transformers
   ```

2. **Set up Supabase vector extension**:
   - Run `supabase_vector_setup.sql` in your Supabase SQL Editor
   - Verify the `embedding` column exists: `SELECT column_name FROM information_schema.columns WHERE table_name = 'jobs' AND column_name = 'embedding';`

3. **Generate embeddings**:
   ```bash
   python3 generate_embeddings.py
   ```
   - This will process all jobs and create embeddings
   - First run downloads the model (~90MB)

4. **Check if embeddings exist**:
   ```sql
   SELECT COUNT(*) FROM jobs WHERE embedding IS NOT NULL;
   ```
   - If count is 0, run `generate_embeddings.py` again

5. **Verify RPC function exists**:
   ```sql
   SELECT routine_name FROM information_schema.routines WHERE routine_name = 'search_jobs_semantic';
   ```
   - If missing, run `supabase_vector_setup.sql` again
   - **Important**: If you get "cannot change return type" error, make sure to run the DROP statements first

6. **Test with the test script**:
   ```bash
   python3 test_semantic_search.py
   ```
   - This will verify embeddings exist and test multiple queries
   - Helps diagnose issues with semantic search setup

## 🚧 Future Enhancements

- [x] **Database Integration**: JSON pipeline now syncs to Supabase (PostgreSQL + JSONB)
- [x] **AI-Powered Semantic Search**: Vector embeddings enable intelligent job search by meaning
- [x] **Email Alerts**: Users subscribe to keywords and get Resend-powered digests
- [ ] **Hybrid Search**: Combine keyword + semantic search for best results
- [ ] **Advanced Analytics**: Salary trends, experience level analysis
- [x] **Export Features**: PDF reports, CSV downloads (✅ Implemented)
- [ ] **Multi-language Support**: Arabic/French UI
- [ ] **Machine Learning**: Skill demand forecasting
- [ ] **Docker Deployment**: Containerized setup
- [ ] **CI/CD Pipeline**: Automated testing and deployment

## 📊 Current Statistics

- **Total Jobs Scraped**: 505+ unique job postings
- **Jobs with Embeddings**: 505 (100% coverage for semantic search)
- **Average Skills per Job**: 3.9
- **Top Skills**: Agile (167), Python (142), SQL (142)
- **Cities Covered**: Casablanca, Rabat, Tanger, Morocco-wide
- **Update Frequency**: Every 6 hours (automatic)
- **Semantic Search**: Fully operational with 384-dimensional vectors

## 📝 License

This project is for educational and portfolio purposes. Please respect the terms of service of job sites when scraping.

## 👤 Author

**Hafida Belayd**

Built as a full-stack data intelligence project demonstrating:
- Web scraping and data collection
- NLP and pattern matching
- **AI-powered semantic search** with vector embeddings
- RESTful API design with FastAPI
- Real-time data visualization
- Automated pipeline orchestration
- PostgreSQL with pgvector for vector similarity search

---

**Last Updated**: November 2025  
**Version**: 1.0
