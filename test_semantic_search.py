#!/usr/bin/env python3
"""
Test script to verify semantic search is working correctly.
"""
import os
from dotenv import load_dotenv
from supabase import create_client
from sentence_transformers import SentenceTransformer

try:
    load_dotenv()
except Exception as e:
    print(f"⚠️ Could not load .env file: {e}")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://cajemqbnvxmtqfsnnvjt.supabase.co")
SUPABASE_KEY = os.environ.get(
    "SUPABASE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNhamVtcWJudnhtdHFmc25udmp0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQwNzEzNTYsImV4cCI6MjA3OTY0NzM1Nn0.Tnpga0j1IFyEQF61PsAQdHVgWhqhHjg7PW0dfPAvlaE",
)

def main():
    print("🔍 Testing Semantic Search Setup\n")
    
    # Connect to Supabase
    print("1. Connecting to Supabase...")
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("   ✅ Connected\n")
    except Exception as exc:
        print(f"   ❌ Failed: {exc}\n")
        return
    
    # Check if embeddings exist
    print("2. Checking for embeddings in database...")
    try:
        response = client.table("jobs").select("id, title, embedding").not_.is_("embedding", "null").limit(5).execute()
        jobs_with_embeddings = response.data or []
        print(f"   Found {len(jobs_with_embeddings)} jobs with embeddings (sample)")
        if jobs_with_embeddings:
            print(f"   Sample job: {jobs_with_embeddings[0].get('title', 'N/A')}")
        print()
    except Exception as exc:
        print(f"   ❌ Failed: {exc}\n")
        return
    
    # Count total jobs with embeddings
    try:
        response = client.table("jobs").select("id", count="exact").not_.is_("embedding", "null").execute()
        total_with_embeddings = response.count or 0
        print(f"3. Total jobs with embeddings: {total_with_embeddings}\n")
    except Exception as exc:
        print(f"   ⚠️ Could not count: {exc}\n")
        total_with_embeddings = 0
    
    if total_with_embeddings == 0:
        print("❌ No embeddings found! Run generate_embeddings.py first.\n")
        return
    
    # Load model and generate test embedding
    print("4. Loading embedding model...")
    try:
        model = SentenceTransformer("all-MiniLM-L6-v2")
        print("   ✅ Model loaded\n")
    except Exception as exc:
        print(f"   ❌ Failed: {exc}\n")
        return
    
    # Test queries
    test_queries = [
        "Python",
        "Machine Learning",
        "Data Science",
        "React",
        "SQL"
    ]
    
    print("5. Testing semantic search with different queries:\n")
    for query in test_queries:
        try:
            # Generate embedding
            query_embedding = model.encode(query, convert_to_numpy=True).tolist()
            
            # Call RPC
            response = client.rpc(
                "search_jobs_semantic",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": 0.1,  # Very low threshold for testing
                    "match_count": 5,
                },
            ).execute()
            
            results = response.data or []
            print(f"   Query: '{query}' → Found {len(results)} results")
            if results:
                print(f"      Top match: {results[0].get('title', 'N/A')} (similarity: {results[0].get('similarity', 'N/A'):.3f})")
            else:
                print(f"      ⚠️ No results (try lowering threshold or check embeddings)")
        except Exception as exc:
            print(f"   ❌ Query '{query}' failed: {exc}")
        print()
    
    print("✅ Test complete!")

if __name__ == "__main__":
    main()

