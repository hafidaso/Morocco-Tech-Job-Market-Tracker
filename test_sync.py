#!/usr/bin/env python3
"""Test script to verify Supabase sync works after fixing RLS."""

from main import sync_supabase_from_disk, load_data, JOBS_DATA

print("🔄 Testing Supabase sync after RLS fix...")
print("=" * 50)

try:
    # Try to sync
    sync_supabase_from_disk()
    print("\n✅ Sync completed successfully!")
    
    # Reload data from Supabase
    load_data()
    print(f"📊 Total jobs in API: {len(JOBS_DATA)}")
    
    if JOBS_DATA:
        print(f"📝 Sample job: {JOBS_DATA[0].get('title', 'N/A')} @ {JOBS_DATA[0].get('company', 'N/A')}")
        print("\n✅ All systems working! Your data is synced to Supabase.")
    else:
        print("⚠️  No jobs found in database. Make sure data was synced.")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\n🔧 Troubleshooting:")
    print("1. Make sure you ran the SQL script in Supabase SQL Editor")
    print("2. Check that RLS is disabled: Run 'SELECT tablename, rowsecurity FROM pg_tables WHERE tablename = 'jobs';'")
    print("3. Verify your SUPABASE_KEY in main.py or .env file")

