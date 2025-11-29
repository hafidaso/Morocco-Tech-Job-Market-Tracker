from contextlib import asynccontextmanager
import io
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
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
from supabase import Client, create_client  # type: ignore[import]
import pandas as pd
import numpy as np

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    REPORTLAB_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    REPORTLAB_AVAILABLE = False

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

JOBS_DATA = []
supabase_client: Client | None = None
LAST_JOB_IDS: set[Any] = set()
_embedding_model: Any = None  # Lazy-loaded sentence transformer model


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
            print(f"📧 {len(new_jobs)} new jobs detected.")
        else:
            print("ℹ️ No brand-new jobs since last run.")
        print("🎉 AUTO-UPDATE FINISHED: API is serving fresh data.\n")
    except subprocess.CalledProcessError as exc:
        print(f"❌ Error during auto-update (exit code {exc.returncode}): {exc}")
    except Exception as exc:  # pragma: no cover - defensive path
        print(f"❌ Unexpected error during auto-update: {exc}")


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


@app.get("/jobs/search/hybrid")
def hybrid_search(
    query: str = Query(..., description="Search query (e.g., 'Machine Learning', 'Web Development')"),
    city: str | None = Query(None, description="Filter by city (e.g., 'Casablanca')"),
    role: str | None = Query(None, description="Filter by role (e.g., 'Data Scientist')"),
    skill: str | None = Query(None, description="Filter by skill (e.g., 'Python')"),
    limit: int = Query(20, ge=1, le=50, description="Maximum number of results"),
    threshold: float = Query(0.3, ge=0.0, le=1.0, description="Similarity threshold (0.0-1.0)"),
):
    """
    Hybrid search: Combine semantic search with exact filters.
    
    This endpoint allows you to search by meaning AND filter by specific criteria:
    - Search for "AI" (semantic) AND filter by city="Casablanca" (exact match)
    - Search for "Backend" (semantic) AND filter by skill="Python" (exact match)
    
    Example: Find AI-related jobs in Casablanca that require Python
    - query="AI", city="Casablanca", skill="Python"
    
    Returns jobs that match BOTH the semantic search AND all provided filters.
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

    # Call the Supabase RPC function for hybrid search
    try:
        response = client.rpc(
            "search_jobs_hybrid",
            {
                "query_embedding": query_embedding,
                "match_threshold": float(threshold),
                "match_count": int(limit),
                "filter_city": city,
                "filter_role": role,
                "filter_skill": skill,
            },
        ).execute()

        results = response.data or []
        
        # Convert to internal job format
        jobs = [to_internal_job(row) for row in results]
        
        return {
            "query": query,
            "filters": {
                "city": city,
                "role": role,
                "skill": skill,
            },
            "total": len(jobs),
            "data": jobs,
            "threshold": threshold,
        }
    except Exception as exc:
        error_msg = str(exc)
        print(f"❌ Hybrid search error: {error_msg}")
        raise HTTPException(
            status_code=500,
            detail=f"Hybrid search failed: {error_msg}. Make sure the hybrid search function exists in Supabase.",
        ) from exc


@app.get("/jobs/{job_id}/similar")
def find_similar_jobs(
    job_id: int,
    limit: int = Query(5, ge=1, le=20, description="Maximum number of similar jobs"),
    threshold: float = Query(0.3, ge=0.0, le=1.0, description="Similarity threshold (0.0-1.0)"),
):
    """
    Find jobs similar to a specific job (More Like This feature).
    
    This endpoint finds jobs that are semantically similar to the given job.
    Useful for showing "Related Jobs" or "You may also like" sections.
    
    Example: GET /jobs/123/similar?limit=5
    Returns the 5 most similar jobs to job #123.
    
    How it works:
    - Uses the embedding of the source job to find nearest neighbors
    - Excludes the source job itself from results
    - Orders by similarity (highest first)
    """
    if not SEMANTIC_SEARCH_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Semantic search is not available. Install sentence-transformers: pip install sentence-transformers",
        )

    try:
        client = get_supabase_client()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}") from exc

    # Call the Supabase RPC function to find similar jobs
    try:
        response = client.rpc(
            "find_similar_jobs",
            {
                "source_job_id": int(job_id),
                "match_threshold": float(threshold),
                "match_count": int(limit),
            },
        ).execute()

        results = response.data or []
        
        if not results:
            # Try to check if the source job exists
            job_check = client.table(SUPABASE_TABLE).select("id, title, embedding").eq("id", job_id).execute()
            if not job_check.data:
                raise HTTPException(status_code=404, detail=f"Job #{job_id} not found")
            if not job_check.data[0].get("embedding"):
                raise HTTPException(
                    status_code=404,
                    detail=f"Job #{job_id} does not have an embedding. Run generate_embeddings.py first.",
                )
        
        # Convert to internal job format
        jobs = [to_internal_job(row) for row in results]
        
        return {
            "source_job_id": job_id,
            "total": len(jobs),
            "data": jobs,
            "threshold": threshold,
        }
    except HTTPException:
        raise
    except Exception as exc:
        error_msg = str(exc)
        print(f"❌ Similar jobs search error: {error_msg}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to find similar jobs: {error_msg}. Make sure the find_similar_jobs function exists in Supabase.",
        ) from exc


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


@app.get("/export/csv")
def export_csv(
    city: str | None = Query(None, description="Filter by city"),
    role: str | None = Query(None, description="Filter by role"),
    skill: str | None = Query(None, description="Filter by skill"),
):
    """Export jobs data as CSV file."""
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

    # Prepare data for DataFrame
    export_data = []
    for job in filtered_jobs:
        export_data.append({
            "Title": job.get("title", ""),
            "Company": job.get("company", ""),
            "Location": job.get("location", ""),
            "City": job.get("searched_city", ""),
            "Role": job.get("searched_role", ""),
            "Date Posted": job.get("date_posted", ""),
            "Skills": ", ".join(job.get("extracted_skills", [])),
            "Job URL": job.get("job_url", ""),
        })

    df = pd.DataFrame(export_data)
    
    # Create CSV in memory
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"morocco_tech_jobs_{timestamp}.csv"
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/export/pdf")
def export_pdf(
    city: str | None = Query(None, description="Filter by city"),
    role: str | None = Query(None, description="Filter by role"),
    skill: str | None = Query(None, description="Filter by skill"),
):
    """Export jobs data as PDF report."""
    if not REPORTLAB_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="PDF export is not available. Install reportlab: pip install reportlab",
        )

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

    # Create PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=colors.HexColor("#6366f1"),
        spaceAfter=30,
        alignment=1,  # Center
    )
    story.append(Paragraph("Morocco Tech Job Market Report", title_style))
    story.append(Spacer(1, 0.2*inch))

    # Report metadata
    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    meta_style = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#64748b"),
        alignment=1,
    )
    story.append(Paragraph(f"Generated on {timestamp}", meta_style))
    story.append(Paragraph(f"Total Jobs: {len(filtered_jobs)}", meta_style))
    story.append(Spacer(1, 0.3*inch))

    # Summary statistics
    if filtered_jobs:
        all_skills = [skill for job in filtered_jobs for skill in job.get("extracted_skills", [])]
        top_skills = Counter(all_skills).most_common(5)
        cities = Counter([job.get("searched_city", "Unknown") for job in filtered_jobs])
        
        summary_data = [
            ["Metric", "Value"],
            ["Total Jobs", str(len(filtered_jobs))],
            ["Top City", cities.most_common(1)[0][0] if cities else "N/A"],
            ["Top Skill", top_skills[0][0] if top_skills else "N/A"],
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 12),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#334155")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#1e293b"), colors.HexColor("#0f172a")]),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.4*inch))

    # Jobs table (limit to first 50 for PDF)
    jobs_to_export = filtered_jobs[:50]
    if jobs_to_export:
        story.append(Paragraph("Job Listings", styles["Heading2"]))
        story.append(Spacer(1, 0.2*inch))

        # Prepare table data
        table_data = [["Title", "Company", "City", "Skills", "Date"]]
        for job in jobs_to_export:
            title = (job.get("title") or "N/A")[:40]  # Truncate long titles
            company = (job.get("company") or "N/A")[:25]
            city = (job.get("searched_city") or job.get("location") or "Unknown")[:20]
            skills = ", ".join(job.get("extracted_skills", [])[:3])[:30]  # First 3 skills
            date_posted = job.get("date_posted", "N/A")[:10]  # Just date part
            table_data.append([title, company, city, skills, date_posted])

        # Create table
        jobs_table = Table(table_data, colWidths=[2*inch, 1.5*inch, 1*inch, 2*inch, 1*inch], repeatRows=1)
        jobs_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#334155")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#1e293b"), colors.HexColor("#0f172a")]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(jobs_table)

        if len(filtered_jobs) > 50:
            story.append(Spacer(1, 0.2*inch))
            note_style = ParagraphStyle(
                "Note",
                parent=styles["Normal"],
                fontSize=9,
                textColor=colors.HexColor("#94a3b8"),
                fontStyle="italic",
            )
            story.append(Paragraph(f"Note: Showing first 50 of {len(filtered_jobs)} jobs. Export CSV for complete data.", note_style))

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"morocco_tech_jobs_{timestamp}.pdf"
    
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/analytics/forecast")
def get_skill_forecasts(
    skill: str | None = Query(None, description="Specific skill to forecast (optional)"),
    top: int = Query(10, ge=1, le=20, description="Number of top skills to forecast"),
):
    """
    Forecast skill demand trends using linear regression.
    
    Analyzes historical data to predict whether skill demand is growing or declining.
    Uses simple linear regression and moving averages for predictions.
    
    Query params:
    - skill: Focus on a specific skill (e.g., "Python", "React")
    - top: Number of top skills to analyze (default: 10)
    
    Returns trend analysis with:
    - Current state, predicted next month, percentage change
    - Trend direction (growing/declining/stable)
    - Actionable recommendations
    """
    def calculate_monthly_skill_counts(jobs: list[dict]) -> dict[str, dict[str, int]]:
        monthly_counts = defaultdict(lambda: defaultdict(int))
        for job in jobs:
            date_str = job.get("date_posted")
            skills = job.get("extracted_skills", [])
            if not date_str or not skills:
                continue
            try:
                date_obj = datetime.fromisoformat(date_str)
                month_key = date_obj.strftime("%Y-%m")
                for s in skills:
                    monthly_counts[s][month_key] += 1
            except (ValueError, TypeError):
                continue
        return dict(monthly_counts)
    
    def simple_linear_regression(x: list[float], y: list[float]) -> tuple[float, float]:
        n = len(x)
        if n < 2:
            return 0, 0
        x_mean = np.mean(x)
        y_mean = np.mean(y)
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        if denominator == 0:
            return 0, y_mean
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        return slope, intercept
    
    def forecast_skill(skill_name: str, monthly_data: dict[str, int]) -> dict:
        if len(monthly_data) < 2:
            return {"skill": skill_name, "status": "insufficient_data"}
        
        sorted_months = sorted(monthly_data.keys())
        counts = [monthly_data[month] for month in sorted_months]
        x = list(range(len(sorted_months)))
        slope, intercept = simple_linear_regression(x, counts)
        
        predicted_value = slope * len(x) + intercept
        predicted_next = max(0, round(predicted_value))
        
        if slope > 1:
            trend = "growing"
            trend_strength = "strong" if slope > 5 else "moderate"
        elif slope < -1:
            trend = "declining"
            trend_strength = "strong" if slope < -5 else "moderate"
        else:
            trend = "stable"
            trend_strength = "stable"
        
        recent_avg = np.mean(counts[-3:]) if len(counts) >= 3 else counts[-1]
        pct_change = ((predicted_next - recent_avg) / recent_avg * 100) if recent_avg > 0 else 0
        
        recommendations = []
        if trend == "growing":
            recommendations.append("✅ High demand - Consider learning or improving this skill")
            if trend_strength == "strong":
                recommendations.append(f"🔥 Strong growth - Hot skill in the market")
        elif trend == "declining":
            recommendations.append("⚠️ Declining demand - May want to focus on other skills")
        else:
            recommendations.append("📊 Stable demand - Consistent opportunities available")
        
        return {
            "skill": skill_name,
            "status": "success",
            "trend": trend,
            "trend_strength": trend_strength,
            "slope": round(slope, 2),
            "current_month_count": counts[-1],
            "recent_average": round(recent_avg, 1),
            "predicted_next_month": predicted_next,
            "predicted_change_pct": round(pct_change, 1),
            "historical_data": {"months": sorted_months, "counts": counts},
            "recommendations": recommendations,
        }
    
    # Calculate monthly trends
    monthly_data = calculate_monthly_skill_counts(JOBS_DATA)
    
    if skill:
        # Forecast specific skill
        if skill not in monthly_data:
            raise HTTPException(status_code=404, detail=f"Skill '{skill}' not found in data")
        forecast = forecast_skill(skill, monthly_data[skill])
        return {"forecasts": [forecast]}
    
    # Forecast top skills
    skill_totals = {s: sum(months.values()) for s, months in monthly_data.items()}
    top_skills = sorted(skill_totals.items(), key=lambda x: x[1], reverse=True)[:top]
    
    forecasts = []
    for skill_name, _ in top_skills:
        forecast = forecast_skill(skill_name, monthly_data[skill_name])
        if forecast["status"] == "success":
            forecasts.append(forecast)
    
    return {
        "forecasts": forecasts,
        "total_skills_analyzed": len(forecasts),
    }


@app.get("/analytics/heatmap")
def get_city_tech_heatmap(
    top_skills: int = Query(15, ge=5, le=30, description="Number of top skills to include"),
):
    """
    Generate City vs Technology heatmap matrix.
    
    Shows which technologies are popular in which cities.
    Reveals regional differences in tech stack preferences.
    
    Returns:
    - Matrix: Cities × Skills with job counts
    - Insights: Dominant skill per city
    - Metadata: Total jobs, cities, skills analyzed
    
    Example insights:
    - "Python is dominant in Casablanca (45% of jobs)"
    - "PHP/Symfony is popular in Rabat"
    - "React is evenly distributed across cities"
    """
    city_skill_counts = defaultdict(lambda: defaultdict(int))
    
    # Count skills per city
    for job in JOBS_DATA:
        city = job.get("searched_city", "Unknown")
        skills = job.get("extracted_skills", [])
        if city and skills:
            for skill in skills:
                city_skill_counts[city][skill] += 1
    
    all_cities = sorted(city_skill_counts.keys())
    
    # Get top skills across all cities
    skill_totals = defaultdict(int)
    for city_data in city_skill_counts.values():
        for skill, count in city_data.items():
            skill_totals[skill] += count
    
    top_skill_list = sorted(skill_totals.items(), key=lambda x: x[1], reverse=True)[:top_skills]
    top_skill_names = [skill for skill, _ in top_skill_list]
    
    # Build matrix
    matrix = []
    for city in all_cities:
        row = {
            "city": city,
            "total_jobs": sum(city_skill_counts[city].values()),
            "skills": {skill: city_skill_counts[city].get(skill, 0) for skill in top_skill_names},
        }
        matrix.append(row)
    
    # Calculate insights (dominant skill per city)
    insights = []
    for city in all_cities:
        city_data = city_skill_counts[city]
        if not city_data:
            continue
        
        total = sum(city_data.values())
        top_skill_in_city = max(city_data.items(), key=lambda x: x[1])
        skill_name, skill_count = top_skill_in_city
        percentage = (skill_count / total) * 100
        
        insights.append({
            "city": city,
            "dominant_skill": skill_name,
            "count": skill_count,
            "percentage": round(percentage, 1),
            "total_jobs": total,
            "message": f"{skill_name} is dominant in {city} ({percentage:.1f}% of jobs)",
        })
    
    return {
        "cities": all_cities,
        "skills": top_skill_names,
        "matrix": matrix,
        "insights": sorted(insights, key=lambda x: x["total_jobs"], reverse=True),
        "metadata": {
            "total_jobs": len(JOBS_DATA),
            "total_cities": len(all_cities),
            "total_skills_analyzed": len(top_skill_names),
        },
    }


