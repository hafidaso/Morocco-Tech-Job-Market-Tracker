"""
Phase 1 Scraper: pulls Moroccan tech job postings and saves morocco_data_market.csv.

This script is invoked automatically by main.py's APScheduler task. You can still
run it manually (`python scraper.py`) when you need a fresh dataset on demand.
"""

from __future__ import annotations

import csv
import time
from pathlib import Path
from typing import List

import pandas as pd
from jobspy import scrape_jobs

OUTPUT_CSV = Path("morocco_data_market.csv")

CITIES: List[str] = ["Casablanca", "Rabat", "Tanger", "Morocco"]
ROLES: List[str] = [
    "Data Scientist",
    "Data Analyst",
    "Data Engineer",
    "Business Analyst",
    "Ingénieur Data",
    "Big Data",
    "Business Intelligence",
]
SITES = ["indeed", "linkedin", "google", "bayt"]


def main() -> None:
    all_jobs: List[pd.DataFrame] = []

    print(f"🚀 Starting High-Volume Scraper for: {', '.join(CITIES)}")
    print(f"🎯 Looking for roles: {', '.join(ROLES)}\n")

    for city in CITIES:
        for role in ROLES:
            print(f"🔎 Scraping: {role} in {city}...")
            try:
                jobs = scrape_jobs(
                    site_name=SITES,
                    search_term=role,
                    google_search_term=f"{role} jobs in {city} Morocco",
                    location=f"{city}, Morocco" if city != "Morocco" else "Morocco",
                    results_wanted=40,
                    hours_old=720,
                    country_indeed="Morocco",
                    linkedin_fetch_description=True,
                    verbose=0,
                )

                if not jobs.empty:
                    jobs["searched_city"] = city
                    jobs["searched_role"] = role
                    all_jobs.append(jobs)
                    print(f"   ✅ Found {len(jobs)} jobs.")
                else:
                    print("   ⚠️ No jobs found.")

                time.sleep(5)
            except Exception as exc:  # pragma: no cover - network dependent
                print(f"   ❌ Error: {exc}")

    if not all_jobs:
        print("\n😔 No jobs found. Check your internet connection or proxies.")
        return

    combined_jobs = pd.concat(all_jobs, ignore_index=True)
    combined_jobs.drop_duplicates(subset=["title", "company"], keep="first", inplace=True)
    print(f"\n🎉 Total Unique Jobs: {len(combined_jobs)}")

    combined_jobs.to_csv(
        OUTPUT_CSV,
        quoting=csv.QUOTE_NONNUMERIC,
        escapechar="\\",
        index=False,
    )
    print(f"💾 Data saved to '{OUTPUT_CSV}'")
    print("\nColumns captured:")
    print(combined_jobs.columns.tolist())


if __name__ == "__main__":
    main()

