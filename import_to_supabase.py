#!/usr/bin/env python3
"""
Standalone script to import processed_jobs_for_api.json into Supabase.
Run this once to populate your Supabase database with all your job data.
"""
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
try:
    load_dotenv()
except Exception as e:
    print(f"⚠️ Could not load .env file: {e}. Continuing with existing environment.")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://cajemqbnvxmtqfsnnvjt.supabase.co")
# Try service_role key first (bypasses RLS), fall back to anon key
SUPABASE_KEY = os.environ.get(
    "SUPABASE_SERVICE_ROLE_KEY",
    os.environ.get(
        "SUPABASE_KEY",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNhamVtcWJudnhtdHFmc25udmp0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQwNzEzNTYsImV4cCI6MjA3OTY0NzM1Nn0.Tnpga0j1IFyEQF61PsAQdHVgWhqhHjg7PW0dfPAvlaE",
    ),
)
DATA_FILE = Path("processed_jobs_for_api.json")
BATCH_SIZE = 500  # Supabase has limits on batch size


def chunked(items: list[dict[str, Any]], size: int = BATCH_SIZE):
    """Yield list chunks of a given size."""
    for index in range(0, len(items), size):
        yield items[index : index + size]


def main():
    """Import JSON data into Supabase."""
    if not DATA_FILE.exists():
        print(f"❌ Error: {DATA_FILE} not found!")
        print("   Make sure you've run analyze_skills.py first to generate the processed data.")
        return

    print(f"📂 Loading data from {DATA_FILE}...")
    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            jobs = json.load(file)
    except json.JSONDecodeError as exc:
        print(f"❌ Failed to parse {DATA_FILE}: {exc}")
        return

    print(f"📊 Found {len(jobs)} jobs to import.")

    # Connect to Supabase
    print("🔌 Connecting to Supabase...")
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as exc:
        print(f"❌ Failed to connect to Supabase: {exc}")
        return

    # Prepare payload
    print("🔄 Preparing data for import...")
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

    # Import in batches
    print(f"☁️ Uploading {len(payload)} jobs to Supabase in batches of {BATCH_SIZE}...")
    total_imported = 0
    for batch_num, batch in enumerate(chunked(payload, BATCH_SIZE), 1):
        try:
            result = client.table("jobs").upsert(
                batch,
                on_conflict="title,company,searched_city",
            ).execute()
            total_imported += len(batch)
            print(f"   ✅ Batch {batch_num}: {len(batch)} jobs uploaded ({total_imported}/{len(payload)})")
        except Exception as exc:
            error_msg = str(exc)
            print(f"   ❌ Batch {batch_num} failed: {error_msg}")
            if "row-level security" in error_msg.lower() or "42501" in error_msg:
                print("\n   ⚠️  RLS (Row Level Security) is blocking inserts!")
                print("   📝 To fix this, run this SQL in Supabase SQL Editor:")
                print("   ")
                print("   -- Option 1: Disable RLS (simplest for public data)")
                print("   ALTER TABLE public.jobs DISABLE ROW LEVEL SECURITY;")
                print("   ")
                print("   -- Option 2: Allow public inserts (more secure)")
                print("   CREATE POLICY \"Allow public inserts\" ON public.jobs")
                print("   FOR INSERT WITH CHECK (true);")
                print("   ")
                print("   -- Option 3: Use service_role key (bypasses RLS)")
                print("   -- Add SUPABASE_SERVICE_ROLE_KEY to your .env file")
                print("   -- Get it from: Supabase Dashboard > Settings > API > service_role key")
                return
            continue

    if total_imported == 0:
        print(f"\n❌ Import failed! No jobs were imported.")
        print("   Check the error messages above for details.")
    else:
        print(f"\n🎉 Import complete! {total_imported} jobs imported into Supabase.")
        print("   You can now restart your backend server and it will load data from Supabase.")


if __name__ == "__main__":
    main()

