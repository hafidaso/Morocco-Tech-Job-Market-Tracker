from contextlib import asynccontextmanager
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

SCRAPER_SCRIPT = "scraper.py"
ANALYZER_SCRIPT = "analyze_skills.py"
DATA_FILE = Path("processed_jobs_for_api.json")

JOBS_DATA = []


def load_data() -> None:
    """Refresh the in-memory cache from disk."""
    global JOBS_DATA
    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            JOBS_DATA = json.load(file)
        print(f"✅ Data reloaded! Total jobs: {len(JOBS_DATA)}")
    except FileNotFoundError:
        print("⚠️ Data file not found yet. Waiting for first scrape.")
        JOBS_DATA = []
    except json.JSONDecodeError as exc:
        print(f"❌ Failed to parse {DATA_FILE}: {exc}")
        JOBS_DATA = []


def run_pipeline() -> None:
    """Trigger scraping + NLP analysis and reload the dataset."""
    print("\n🔄 AUTO-UPDATE STARTED: Scraping new jobs...")
    try:
        subprocess.run([sys.executable, SCRAPER_SCRIPT], check=True)
        print("   ✅ Scraping complete.")

        subprocess.run([sys.executable, ANALYZER_SCRIPT], check=True)
        print("   ✅ Analysis complete.")

        load_data()
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
    limit: int = 20,
):
    filtered_jobs = JOBS_DATA
    if city:
        filtered_jobs = [j for j in filtered_jobs if j.get("searched_city", "").lower() == city.lower()]
    if role:
        filtered_jobs = [j for j in filtered_jobs if role.lower() in j.get("searched_role", "").lower()]

    return {"total": len(filtered_jobs), "data": filtered_jobs[:limit]}


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

