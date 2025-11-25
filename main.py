from contextlib import asynccontextmanager
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from supabase import Client, create_client  # type: ignore[import]

try:
    import resend  # type: ignore[import]
except ImportError:  # pragma: no cover - optional dependency
    resend = None

try:
    from sentence_transformers import SentenceTransformer  # type: ignore[import]
    SEMANTIC_SEARCH_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    SentenceTransformer = None
    SEMANTIC_SEARCH_AVAILABLE = False

SCRAPER_SCRIPT = "scraper.py"
ANALYZER_SCRIPT = "analyze_skills.py"
DATA_FILE = Path("processed_jobs_for_api.json")

try:
    load_dotenv()
except PermissionError as exc:  # pragma: no cover - env specific
    print(f"⚠️ Could not load .env file: {exc}. Continuing with existing environment.")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://cajemqbnvxmtqfsnnvjt.supabase.co")
SUPABASE_KEY = os.environ.get(
    "SUPABASE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNhamVtcWJudnhtdHFmc25udmp0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQwNzEzNTYsImV4cCI6MjA3OTY0NzM1Nn0.Tnpga0j1IFyEQF61PsAQdHVgWhqhHjg7PW0dfPAvlaE",
)
SUPABASE_TABLE = "jobs"
SUBSCRIPTIONS_TABLE = "subscriptions"

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
# Use onboarding@resend.dev for testing (Resend's verified test domain)
# For production, use your verified domain (e.g., jobs@yourdomain.com)
RESEND_FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "onboarding@resend.dev")
MAX_JOBS_PER_EMAIL = 10

JOBS_DATA = []
supabase_client: Client | None = None
LAST_JOB_IDS: set[Any] = set()
_embedding_model: Any = None  # Lazy-loaded sentence transformer model


class SubscriptionPayload(BaseModel):
    email: EmailStr
    keyword: str


def get_supabase_client() -> Client:
    """Instantiate or return a cached Supabase client."""
    global supabase_client
    if supabase_client is not None:
        return supabase_client

    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("Supabase credentials are missing. Set SUPABASE_URL and SUPABASE_KEY.")

    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as exc:
        raise RuntimeError(f"Unable to initialize Supabase client: {exc}") from exc
    return supabase_client


def chunked(items: list[dict[str, Any]], size: int = 500) -> Iterable[list[dict[str, Any]]]:
    """Yield list chunks of a given size."""
    for index in range(0, len(items), size):
        yield items[index : index + size]


def to_internal_job(record: dict[str, Any]) -> dict[str, Any]:
    """Normalize Supabase rows to the format expected by the API."""
    return {
        "id": record.get("id"),
        "title": record.get("title"),
        "company": record.get("company"),
        "location": record.get("location"),
        "searched_city": record.get("searched_city") or record.get("city"),
        "searched_role": record.get("searched_role"),
        "date_posted": record.get("date_posted"),
        "job_url": record.get("job_url"),
        "extracted_skills": record.get("extracted_skills") or record.get("skills") or [],
    }


def load_data_from_disk() -> list[dict[str, Any]]:
    """Load processed jobs directly from disk as a fallback."""
    if not DATA_FILE.exists():
        print(f"⚠️ Local data file {DATA_FILE} is missing; cannot serve cached jobs.")
        return []

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            jobs = json.load(file)
    except json.JSONDecodeError as exc:
        print(f"❌ Failed to parse {DATA_FILE}: {exc}")
        return []

    normalized_jobs = [to_internal_job(job) for job in jobs]
    print(f"📦 Loaded {len(normalized_jobs)} jobs from local cache.")
    return normalized_jobs


def sync_supabase_from_disk() -> None:
    """Push the processed JSON data set into Supabase."""
    if not DATA_FILE.exists():
        print("⚠️ No processed data file found; skipping Supabase sync.")
        return

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            jobs = json.load(file)
    except json.JSONDecodeError as exc:
        print(f"❌ Failed to parse {DATA_FILE}: {exc}")
        return

    payload: list[dict[str, Any]] = []
    for job in jobs:
        normalized_city = (job.get("searched_city") or job.get("location") or "").strip() or "Unknown"
        payload.append(
            {
                "title": job.get("title"),
                "company": job.get("company"),
                "location": job.get("location"),
                "date_posted": job.get("date_posted"),
                "job_url": job.get("job_url"),
                "searched_city": normalized_city,
                "searched_role": job.get("searched_role"),
                "extracted_skills": job.get("extracted_skills", []),
            }
        )

    if not payload:
        print("ℹ️ No jobs found in processed JSON; nothing to sync.")
        return

    try:
        client = get_supabase_client()
    except RuntimeError as exc:
        print(f"⚠️ Supabase is not configured: {exc}. Skipping remote sync.")
        return

    print(f"☁️ Upserting {len(payload)} processed jobs into Supabase...")
    for batch in chunked(payload):
        client.table(SUPABASE_TABLE).upsert(
            batch,
            on_conflict="title,company,searched_city",
        ).execute()
    print("✅ Supabase sync complete (history preserved).")


def load_data() -> None:
    """Refresh the in-memory cache from Supabase, falling back to disk when needed."""
    global JOBS_DATA, LAST_JOB_IDS

    try:
        client = get_supabase_client()
    except RuntimeError as exc:
        print(f"⚠️ Supabase unavailable: {exc}. Using local cached data.")
        JOBS_DATA = load_data_from_disk()
    else:
        try:
            response = client.table(SUPABASE_TABLE).select("*").order("date_posted", desc=True).execute()
            JOBS_DATA = [to_internal_job(row) for row in response.data or []]
            print(f"✅ Data fetched from Supabase! Total jobs: {len(JOBS_DATA)}")
            if not JOBS_DATA:
                print("ℹ️ Supabase returned no rows; falling back to local cache.")
                JOBS_DATA = load_data_from_disk()
        except Exception as exc:
            print(f"❌ Failed to load data from Supabase: {exc}")
            JOBS_DATA = load_data_from_disk()

    LAST_JOB_IDS = {
        job["id"]
        for job in JOBS_DATA
        if isinstance(job.get("id"), (int, str)) and job.get("id") not in (None, "")
    }


def run_pipeline() -> None:
    """Trigger scraping + NLP analysis and reload the dataset."""
    previous_ids = LAST_JOB_IDS.copy()
    print("\n🔄 AUTO-UPDATE STARTED: Scraping new jobs...")
    try:
        subprocess.run([sys.executable, SCRAPER_SCRIPT], check=True)
        print("   ✅ Scraping complete.")

        subprocess.run([sys.executable, ANALYZER_SCRIPT], check=True)
        print("   ✅ Analysis complete.")

        sync_supabase_from_disk()
        load_data()
        new_jobs = [
            job
            for job in JOBS_DATA
            if (job_id := job.get("id")) not in previous_ids and job_id not in (None, "")
        ]
        if new_jobs:
            print(f"📧 {len(new_jobs)} new jobs detected; checking subscriber alerts...")
            try:
                notify_subscribers(new_jobs)
            except Exception as exc:  # pragma: no cover - defensive path
                print(f"❌ Failed to notify subscribers: {exc}")
        else:
            print("ℹ️ No brand-new jobs since last run. Skipping email notifications.")
        print("🎉 AUTO-UPDATE FINISHED: API is serving fresh data.\n")
    except subprocess.CalledProcessError as exc:
        print(f"❌ Error during auto-update (exit code {exc.returncode}): {exc}")
    except Exception as exc:  # pragma: no cover - defensive path
        print(f"❌ Unexpected error during auto-update: {exc}")


def fetch_subscriptions() -> list[dict[str, Any]]:
    """Fetch all active keyword subscriptions."""
    try:
        client = get_supabase_client()
        response = client.table(SUBSCRIPTIONS_TABLE).select("*").execute()
        return response.data or []
    except Exception as exc:
        print(f"⚠️ Could not load subscriptions: {exc}")
        return []


def job_matches_keyword(job: dict[str, Any], keyword: str) -> bool:
    """Return True if the job looks relevant for the keyword."""
    if not keyword:
        return False

    keyword_lower = keyword.lower()
    text_fields = [
        job.get("title") or "",
        job.get("company") or "",
        job.get("searched_role") or "",
    ]
    if any(keyword_lower in field.lower() for field in text_fields if field):
        return True

    skills = job.get("extracted_skills") or []
    return any(keyword_lower in str(skill).lower() for skill in skills)


def filter_jobs_by_keyword(keyword: str, jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Pick the subset of jobs that match a given keyword."""
    trimmed = keyword.strip()
    if not trimmed:
        return []
    matched = [job for job in jobs if job_matches_keyword(job, trimmed)]
    return matched[:MAX_JOBS_PER_EMAIL]


def build_email_html(keyword: str, jobs: list[dict[str, Any]]) -> str:
    """Prepare a compact HTML digest for the subscriber."""
    items = []
    for job in jobs:
        title = job.get("title", "New role")
        company = job.get("company", "Unknown company")
        city = job.get("searched_city") or "Morocco"
        date_posted = job.get("date_posted") or "Recently"
        skills = ", ".join(job.get("extracted_skills") or []) or "Skills TBD"
        items.append(
            f"<li><strong>{title}</strong> @ {company} — {city} "
            f"<br/><small>Posted: {date_posted} • Skills: {skills}</small></li>"
        )

    jobs_list_html = "".join(items)
    return (
        f"<h2>🔥 Fresh {keyword.title()} opportunities</h2>"
        f"<p>We just found {len(jobs)} new postings that mention “{keyword}”.</p>"
        f"<ol>{jobs_list_html}</ol>"
        "<p style='margin-top:16px;'>You are receiving this alert because you subscribed on Morocco Tech Monitor.</p>"
    )


def send_email_via_resend(email: str, keyword: str, jobs: list[dict[str, Any]]) -> None:
    """Send an alert email using Resend."""
    if not RESEND_API_KEY:
        print("⚠️ RESEND_API_KEY is not configured. Skipping email delivery.")
        return
    if resend is None:
        print("⚠️ Resend SDK is missing. Run `pip install resend` to enable alerts.")
        return

    resend.api_key = RESEND_API_KEY
    subject = f"{len(jobs)} new {keyword.title()} role{'s' if len(jobs) > 1 else ''} in Morocco"
    payload = {
        "from": RESEND_FROM_EMAIL,
        "to": [email],
        "subject": subject,
        "html": build_email_html(keyword, jobs),
    }
    try:
        resend.Emails.send(payload)  # type: ignore[attr-defined]
        print(f"✅ Alert sent to {email} for keyword '{keyword}'.")
    except Exception as exc:  # pragma: no cover - network dependent
        print(f"❌ Failed to send Resend email to {email}: {exc}")


def notify_subscribers(new_jobs: list[dict[str, Any]]) -> None:
    """Notify subscribers whose keywords match the new jobs."""
    if not new_jobs:
        return

    subscriptions = fetch_subscriptions()
    if not subscriptions:
        print("ℹ️ No subscribers found. Skipping email notifications.")
        return

    notifications_sent = 0
    for subscription in subscriptions:
        email = (subscription.get("email") or "").strip()
        keyword = (subscription.get("keyword") or "").strip()
        if not email or not keyword:
            continue

        relevant_jobs = filter_jobs_by_keyword(keyword, new_jobs)
        if not relevant_jobs:
            continue

        send_email_via_resend(email, keyword, relevant_jobs)
        notifications_sent += 1

    if notifications_sent:
        print(f"📨 Completed {notifications_sent} subscriber notification(s).")
    else:
        print("ℹ️ No subscribers matched the new postings.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_data()

    scheduler = BackgroundScheduler()
    scheduler.add_job(run_pipeline, "interval", hours=6)
    scheduler.start()
    print("⏰ Scheduler started: Will scrape every 6 hours.")

    try:
        yield
    finally:
        scheduler.shutdown()


app = FastAPI(
    title="Morocco Tech Job Tracker",
    description="API for tracking Data & Tech jobs in Casablanca, Rabat, Tanger",
    version="1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"status": "Live", "jobs_count": len(JOBS_DATA)}


@app.get("/jobs")
def get_jobs(
    city: str | None = Query(None, description="Filter by city (e.g., Casablanca)"),
    role: str | None = Query(None, description="Filter by role (e.g., Data Scientist)"),
    skill: str | None = Query(None, description="Filter by skill (e.g., React)"),
    limit: int = 20,
):
    filtered_jobs = JOBS_DATA
    if city:
        filtered_jobs = [j for j in filtered_jobs if (j.get("searched_city") or "").lower() == city.lower()]
    if role:
        filtered_jobs = [
            j
            for j in filtered_jobs
            if role.lower() in (j.get("searched_role") or j.get("title", "")).lower()
        ]
    if skill:
        filtered_jobs = [
            j
            for j in filtered_jobs
            if any(skill.lower() == s.lower() for s in j.get("extracted_skills", []))
        ]

    return {"total": len(filtered_jobs), "data": filtered_jobs[:limit]}


def get_embedding_model():
    """Lazy-load the sentence transformer model for semantic search."""
    global _embedding_model
    if _embedding_model is None and SEMANTIC_SEARCH_AVAILABLE:
        try:
            _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception as exc:
            print(f"⚠️ Failed to load embedding model: {exc}")
            return None
    return _embedding_model


@app.get("/jobs/search")
def semantic_search(
    query: str = Query(..., description="Search query (e.g., 'Machine Learning', 'Web Development')"),
    limit: int = Query(20, ge=1, le=50, description="Maximum number of results"),
    threshold: float = Query(0.3, ge=0.0, le=1.0, description="Similarity threshold (0.0-1.0)"),
):
    """
    Semantic search for jobs using vector embeddings.
    
    This endpoint uses AI embeddings to find jobs by meaning, not just keywords.
    Example: Searching "AI" will find jobs mentioning "Machine Learning", "LLM", "Artificial Intelligence", etc.
    
    Returns jobs ordered by semantic similarity to the query.
    """
    if not SEMANTIC_SEARCH_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Semantic search is not available. Install sentence-transformers: pip install sentence-transformers",
        )

    model = get_embedding_model()
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Failed to load embedding model. Check server logs.",
        )

    try:
        client = get_supabase_client()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}") from exc

    # Generate embedding for the search query
    try:
        query_embedding = model.encode(query, convert_to_numpy=True).tolist()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate query embedding: {exc}") from exc

    # Call the Supabase RPC function for semantic search
    try:
        response = client.rpc(
            "search_jobs_semantic",
            {
                "query_embedding": query_embedding,
                "match_threshold": float(threshold),
                "match_count": int(limit),
            },
        ).execute()

        results = response.data or []
        
        # Convert to internal job format
        jobs = [to_internal_job(row) for row in results]
        
        return {
            "query": query,
            "total": len(jobs),
            "data": jobs,
            "threshold": threshold,
        }
    except Exception as exc:
        error_msg = str(exc)
        print(f"❌ Semantic search error: {error_msg}")
        raise HTTPException(
            status_code=500,
            detail=f"Semantic search failed: {error_msg}. Make sure pgvector is enabled, the RPC function exists, and embeddings are generated.",
        ) from exc


@app.post("/subscribe")
def create_subscription(payload: SubscriptionPayload):
    """Persist a new keyword subscription."""
    keyword = payload.keyword.strip()
    if not keyword:
        raise HTTPException(status_code=400, detail="Keyword is required.")

    normalized_keyword = keyword.lower()

    try:
        client = get_supabase_client()
        existing = (
            client.table(SUBSCRIPTIONS_TABLE)
            .select("id")
            .eq("email", payload.email)
            .eq("keyword", normalized_keyword)
            .execute()
        )
        if existing.data:
            return {"status": "ok", "message": "You are already subscribed to that keyword."}

        client.table(SUBSCRIPTIONS_TABLE).insert(
            [
                {
                    "email": payload.email,
                    "keyword": normalized_keyword,
                }
            ]
        ).execute()

        return {
            "status": "ok",
            "message": f"Subscription saved. We'll email new '{keyword}' roles automatically.",
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save subscription: {exc}") from exc


@app.get("/trends/skills")
def get_top_skills():
    all_skills = [skill for job in JOBS_DATA for skill in job.get("extracted_skills", [])]
    counts = Counter(all_skills).most_common(10)
    return [{"name": skill, "value": count} for skill, count in counts]


@app.get("/trends/cities")
def get_job_distribution():
    cities = [job.get("searched_city", "Unknown") for job in JOBS_DATA]
    counts = Counter(cities)
    return [{"name": city, "value": count} for city, count in counts.items()]


@app.get("/trends/history")
def get_skill_history(
    skill: str | None = Query(None, description="Specific skill to trend (defaults to top 5 skills)"),
    top: int = Query(5, ge=1, le=10, description="Number of skills when no filter provided"),
):
    if not JOBS_DATA:
        raise HTTPException(status_code=404, detail="No job data is available yet.")

    monthly_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    skill_totals = Counter()

    for job in JOBS_DATA:
        date_str = job.get("date_posted")
        skill_list = job.get("extracted_skills") or []
        if not date_str or not skill_list:
            continue

        try:
            date_obj = datetime.fromisoformat(date_str)
        except ValueError:
            continue

        month_key = date_obj.strftime("%Y-%m")
        current_skills = skill_list if not skill else [s for s in skill_list if s.lower() == skill.lower()]

        for entry in current_skills:
            monthly_counts[month_key][entry] += 1
            skill_totals[entry] += 1

    if skill:
        tracked_skills = [skill]
    else:
        tracked_skills = [name for name, _ in skill_totals.most_common(top)]

    months = sorted(monthly_counts.keys())
    history = []
    for month in months:
        row = {"month": month}
        for tracked in tracked_skills:
            row[tracked] = monthly_counts[month].get(tracked, 0)
        history.append(row)

    return {"skills": tracked_skills, "data": history}

