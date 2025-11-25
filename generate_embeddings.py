#!/usr/bin/env python3
"""
Generate vector embeddings for job descriptions using sentence-transformers.
This enables semantic search - finding jobs by meaning, not just keywords.

Usage:
    python3 generate_embeddings.py

Requirements:
    pip install sentence-transformers supabase
"""
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from supabase import create_client

try:
    load_dotenv()
except Exception as e:
    print(f"⚠️ Could not load .env file: {e}. Continuing with existing environment.")

# Use a lightweight, fast model that works well for job descriptions
# all-MiniLM-L6-v2: 384 dimensions, fast, good quality
MODEL_NAME = "all-MiniLM-L6-v2"
BATCH_SIZE = 32  # Process jobs in batches for efficiency

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://cajemqbnvxmtqfsnnvjt.supabase.co")
SUPABASE_KEY = os.environ.get(
    "SUPABASE_SERVICE_ROLE_KEY",
    os.environ.get(
        "SUPABASE_KEY",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNhamVtcWJudnhtdHFmc25udmp0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQwNzEzNTYsImV4cCI6MjA3OTY0NzM1Nn0.Tnpga0j1IFyEQF61PsAQdHVgWhqhHjg7PW0dfPAvlaE",
    ),
)


def build_searchable_text(job: dict[str, Any]) -> str:
    """Combine job fields into a searchable text string."""
    parts = []
    
    if title := job.get("title"):
        parts.append(title)
    if company := job.get("company"):
        parts.append(f"at {company}")
    if role := job.get("searched_role"):
        parts.append(role)
    if skills := job.get("extracted_skills"):
        if isinstance(skills, list):
            parts.extend(skills)
        elif isinstance(skills, str):
            parts.append(skills)
    
    return " ".join(parts)


def main():
    """Generate embeddings for all jobs and store in Supabase."""
    print("🤖 Loading sentence transformer model...")
    try:
        model = SentenceTransformer(MODEL_NAME)
        print(f"✅ Model loaded: {MODEL_NAME} (384 dimensions)")
    except Exception as exc:
        print(f"❌ Failed to load model: {exc}")
        print("   Install with: pip install sentence-transformers")
        return

    print("\n🔌 Connecting to Supabase...")
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as exc:
        print(f"❌ Failed to connect to Supabase: {exc}")
        return

    print("📊 Fetching jobs from Supabase...")
    try:
        response = client.table("jobs").select("id,title,company,searched_role,extracted_skills").execute()
        jobs = response.data or []
        print(f"   Found {len(jobs)} jobs")
    except Exception as exc:
        print(f"❌ Failed to fetch jobs: {exc}")
        return

    if not jobs:
        print("⚠️ No jobs found in Supabase. Run import_to_supabase.py first.")
        return

    # Filter jobs that don't have embeddings yet
    print("\n🔍 Checking which jobs need embeddings...")
    jobs_with_embeddings = set()
    try:
        response = client.table("jobs").select("id").not_.is_("embedding", "null").execute()
        jobs_with_embeddings = {job["id"] for job in (response.data or [])}
        print(f"   {len(jobs_with_embeddings)} jobs already have embeddings")
    except Exception as exc:
        print(f"   ⚠️ Could not check existing embeddings: {exc}")
        print("   Will generate embeddings for all jobs")

    jobs_to_process = [job for job in jobs if job.get("id") not in jobs_with_embeddings]
    print(f"   {len(jobs_to_process)} jobs need embeddings")

    if not jobs_to_process:
        print("\n✅ All jobs already have embeddings!")
        return

    print(f"\n🧮 Generating embeddings in batches of {BATCH_SIZE}...")
    total_processed = 0

    for i in range(0, len(jobs_to_process), BATCH_SIZE):
        batch = jobs_to_process[i : i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (len(jobs_to_process) + BATCH_SIZE - 1) // BATCH_SIZE

        # Build searchable text for each job
        texts = [build_searchable_text(job) for job in batch]

        # Generate embeddings
        try:
            embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
            print(f"   ✅ Batch {batch_num}/{total_batches}: Generated {len(embeddings)} embeddings")

            # Update Supabase with embeddings
            updates = []
            for job, embedding in zip(batch, embeddings):
                updates.append({
                    "id": job["id"],
                    "embedding": embedding.tolist(),  # Convert numpy array to list
                })

            # Update in smaller chunks to avoid payload size limits
            chunk_size = 10
            for chunk_start in range(0, len(updates), chunk_size):
                chunk = updates[chunk_start : chunk_start + chunk_size]
                try:
                    client.table("jobs").upsert(chunk).execute()
                except Exception as exc:
                    print(f"      ⚠️ Failed to update chunk: {exc}")
                    continue

            total_processed += len(batch)
            print(f"      💾 Saved {len(updates)} embeddings to Supabase ({total_processed}/{len(jobs_to_process)})")

        except Exception as exc:
            print(f"   ❌ Batch {batch_num} failed: {exc}")
            continue

    print(f"\n🎉 Embedding generation complete!")
    print(f"   Processed: {total_processed}/{len(jobs_to_process)} jobs")
    print(f"\n✨ Semantic search is now enabled!")
    print("   Try searching for 'AI' and it will find 'Machine Learning', 'LLM', etc.")


if __name__ == "__main__":
    main()

