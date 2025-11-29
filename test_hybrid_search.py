#!/usr/bin/env python3
"""Test script for Hybrid Search and More Like This features."""

import requests
from typing import Optional

API_URL = "http://127.0.0.1:8000"


def test_hybrid_search(query: str, city: Optional[str] = None, skill: Optional[str] = None):
    """Test hybrid search: semantic search + filters."""
    print(f"\n{'='*60}")
    print(f"🔍 Hybrid Search: '{query}'")
    if city:
        print(f"   📍 City: {city}")
    if skill:
        print(f"   🔧 Skill: {skill}")
    print(f"{'='*60}")
    
    params = {
        "query": query,
        "limit": 5,
        "threshold": 0.2,
    }
    if city:
        params["city"] = city
    if skill:
        params["skill"] = skill
    
    try:
        response = requests.get(f"{API_URL}/jobs/search/hybrid", params=params)
        response.raise_for_status()
        data = response.json()
        
        print(f"\n✅ Found {data['total']} jobs")
        print(f"   Query: {data['query']}")
        print(f"   Filters: {data['filters']}")
        
        for i, job in enumerate(data['data'][:5], 1):
            similarity = job.get('similarity', 0)
            skills = ', '.join(job.get('extracted_skills', [])[:3])
            print(f"\n{i}. {job.get('title', 'N/A')} @ {job.get('company', 'N/A')}")
            print(f"   📍 {job.get('searched_city', 'Unknown')}")
            print(f"   🔧 Skills: {skills}")
            print(f"   📊 Similarity: {similarity:.2%}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Details: {e.response.text}")


def test_similar_jobs(job_id: int):
    """Test 'More Like This' feature."""
    print(f"\n{'='*60}")
    print(f"🔗 Finding jobs similar to Job #{job_id}")
    print(f"{'='*60}")
    
    try:
        # First, get the source job details
        response = requests.get(f"{API_URL}/jobs", params={"limit": 1000})
        response.raise_for_status()
        jobs_data = response.json()
        
        source_job = None
        for job in jobs_data['data']:
            if job.get('id') == job_id:
                source_job = job
                break
        
        if source_job:
            print(f"\n📌 Source Job:")
            print(f"   {source_job.get('title', 'N/A')} @ {source_job.get('company', 'N/A')}")
            print(f"   📍 {source_job.get('searched_city', 'Unknown')}")
            skills = ', '.join(source_job.get('extracted_skills', [])[:5])
            print(f"   🔧 Skills: {skills}")
        
        # Now find similar jobs
        response = requests.get(f"{API_URL}/jobs/{job_id}/similar", params={"limit": 5, "threshold": 0.2})
        response.raise_for_status()
        data = response.json()
        
        print(f"\n✅ Found {data['total']} similar jobs")
        
        for i, job in enumerate(data['data'], 1):
            similarity = job.get('similarity', 0)
            skills = ', '.join(job.get('extracted_skills', [])[:3])
            print(f"\n{i}. {job.get('title', 'N/A')} @ {job.get('company', 'N/A')}")
            print(f"   📍 {job.get('searched_city', 'Unknown')}")
            print(f"   🔧 Skills: {skills}")
            print(f"   📊 Similarity: {similarity:.2%}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Details: {e.response.text}")


def get_sample_job_id():
    """Get a sample job ID that has an embedding."""
    try:
        response = requests.get(f"{API_URL}/jobs", params={"limit": 10})
        response.raise_for_status()
        data = response.json()
        
        if data['data']:
            return data['data'][0].get('id')
    except Exception as e:
        print(f"⚠️ Could not fetch sample job: {e}")
    return None


if __name__ == "__main__":
    print("🚀 Testing Hybrid Search & More Like This Features")
    print("="*60)
    
    # Test 1: Hybrid search with city filter
    test_hybrid_search("Machine Learning", city="Casablanca")
    
    # Test 2: Hybrid search with skill filter
    test_hybrid_search("Data Science", skill="Python")
    
    # Test 3: Hybrid search with both filters
    test_hybrid_search("Backend Development", city="Rabat", skill="Java")
    
    # Test 4: More Like This feature
    job_id = get_sample_job_id()
    if job_id:
        test_similar_jobs(job_id)
    else:
        print("\n⚠️ Could not test 'More Like This' - no jobs found")
    
    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("\n💡 Tips:")
    print("   - Make sure you've run supabase_hybrid_search_setup.sql in Supabase")
    print("   - Make sure generate_embeddings.py has been run")
    print("   - Adjust threshold (0.1-0.5) to control result strictness")

