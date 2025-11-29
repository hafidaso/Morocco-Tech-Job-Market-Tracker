#!/usr/bin/env python3
"""
Trend Forecasting and Analytics Module
Analyzes historical job data to predict future trends and generate insights.
"""

import json
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import numpy as np
from pathlib import Path

DATA_FILE = Path("processed_jobs_for_api.json")
SKILLS_SNAPSHOT = Path("skills_snapshot.json")


def load_jobs_data() -> List[Dict]:
    """Load processed jobs data."""
    if not DATA_FILE.exists():
        print(f"❌ Data file {DATA_FILE} not found.")
        return []
    
    with DATA_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def calculate_monthly_skill_counts(jobs: List[Dict]) -> Dict[str, Dict[str, int]]:
    """
    Calculate skill counts per month.
    Returns: {skill: {month: count}}
    """
    monthly_counts = defaultdict(lambda: defaultdict(int))
    
    for job in jobs:
        date_str = job.get("date_posted")
        skills = job.get("extracted_skills", [])
        
        if not date_str or not skills:
            continue
        
        try:
            date_obj = datetime.fromisoformat(date_str)
            month_key = date_obj.strftime("%Y-%m")
            
            for skill in skills:
                monthly_counts[skill][month_key] += 1
        except (ValueError, TypeError):
            continue
    
    return dict(monthly_counts)


def simple_linear_regression(x: List[float], y: List[float]) -> Tuple[float, float]:
    """
    Calculate linear regression: y = mx + b
    Returns: (slope, intercept)
    """
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


def calculate_moving_average(values: List[float], window: int = 3) -> float:
    """Calculate simple moving average."""
    if len(values) < window:
        return np.mean(values) if values else 0
    
    return np.mean(values[-window:])


def forecast_skill_trend(skill: str, monthly_data: Dict[str, int], months_ahead: int = 1) -> Dict:
    """
    Forecast skill demand using linear regression and moving average.
    
    Args:
        skill: Skill name
        monthly_data: {month: count} dictionary
        months_ahead: Number of months to forecast ahead
    
    Returns:
        Dictionary with forecast results
    """
    if len(monthly_data) < 2:
        return {
            "skill": skill,
            "status": "insufficient_data",
            "message": "Need at least 2 months of data",
        }
    
    # Sort months chronologically
    sorted_months = sorted(monthly_data.keys())
    counts = [monthly_data[month] for month in sorted_months]
    
    # Create numeric x values (0, 1, 2, ...)
    x = list(range(len(sorted_months)))
    y = counts
    
    # Linear regression
    slope, intercept = simple_linear_regression(x, y)
    
    # Predict next month(s)
    next_x = len(x)
    predictions = []
    for i in range(months_ahead):
        predicted_value = slope * (next_x + i) + intercept
        predictions.append(max(0, round(predicted_value)))  # Can't have negative jobs
    
    # Moving average (last 3 months)
    ma_prediction = calculate_moving_average(counts, window=3)
    
    # Calculate trend
    if slope > 1:
        trend = "growing"
        trend_strength = "strong" if slope > 5 else "moderate"
    elif slope < -1:
        trend = "declining"
        trend_strength = "strong" if slope < -5 else "moderate"
    else:
        trend = "stable"
        trend_strength = "stable"
    
    # Calculate percentage change
    recent_avg = np.mean(counts[-3:]) if len(counts) >= 3 else counts[-1]
    if recent_avg > 0:
        pct_change = ((predictions[0] - recent_avg) / recent_avg) * 100
    else:
        pct_change = 0
    
    return {
        "skill": skill,
        "status": "success",
        "trend": trend,
        "trend_strength": trend_strength,
        "slope": round(slope, 2),
        "current_month_count": counts[-1],
        "recent_average": round(recent_avg, 1),
        "predicted_next_month": predictions[0],
        "predicted_change_pct": round(pct_change, 1),
        "moving_average_prediction": round(ma_prediction),
        "historical_data": {
            "months": sorted_months,
            "counts": counts,
        },
        "recommendations": get_recommendations(trend, trend_strength, pct_change),
    }


def get_recommendations(trend: str, strength: str, pct_change: float) -> List[str]:
    """Generate actionable recommendations based on trend."""
    recommendations = []
    
    if trend == "growing":
        recommendations.append(f"✅ High demand - Consider learning or improving this skill")
        if strength == "strong":
            recommendations.append(f"🔥 Strong growth ({pct_change:+.1f}%) - Hot skill in the market")
        recommendations.append("💼 Good for career development and job opportunities")
    elif trend == "declining":
        recommendations.append(f"⚠️ Declining demand - May want to focus on other skills")
        if strength == "strong":
            recommendations.append(f"📉 Strong decline ({pct_change:+.1f}%) - Consider pivoting")
        recommendations.append("🔄 Look for complementary or emerging skills")
    else:
        recommendations.append("📊 Stable demand - Consistent opportunities available")
        recommendations.append("💡 Maintain proficiency in this skill")
    
    return recommendations


def generate_city_tech_heatmap(jobs: List[Dict]) -> Dict:
    """
    Generate a city vs technology heatmap matrix.
    
    Returns:
        Dictionary with cities, skills, and matrix data
    """
    city_skill_counts = defaultdict(lambda: defaultdict(int))
    
    # Count skills per city
    for job in jobs:
        city = job.get("searched_city", "Unknown")
        skills = job.get("extracted_skills", [])
        
        if city and skills:
            for skill in skills:
                city_skill_counts[city][skill] += 1
    
    # Get top cities and skills
    all_cities = sorted(city_skill_counts.keys())
    
    # Get top 15 most common skills across all cities
    skill_totals = defaultdict(int)
    for city_data in city_skill_counts.values():
        for skill, count in city_data.items():
            skill_totals[skill] += count
    
    top_skills = sorted(skill_totals.items(), key=lambda x: x[1], reverse=True)[:15]
    top_skill_names = [skill for skill, _ in top_skills]
    
    # Build matrix
    matrix = []
    for city in all_cities:
        row = {
            "city": city,
            "total_jobs": sum(city_skill_counts[city].values()),
            "skills": {},
        }
        
        for skill in top_skill_names:
            count = city_skill_counts[city].get(skill, 0)
            row["skills"][skill] = count
        
        matrix.append(row)
    
    # Calculate percentages and dominance
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
        })
    
    return {
        "cities": all_cities,
        "skills": top_skill_names,
        "matrix": matrix,
        "insights": insights,
        "metadata": {
            "total_jobs": len(jobs),
            "total_cities": len(all_cities),
            "total_skills_analyzed": len(top_skill_names),
        },
    }


def save_snapshot(data: Dict, filename: str = "analytics_snapshot.json"):
    """Save analytics snapshot to file."""
    output_path = Path(filename)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"💾 Saved analytics snapshot to {filename}")


def main():
    """Run trend forecasting and heatmap analysis."""
    print("🔮 Morocco Tech Job Market - Trend Forecasting & Analytics")
    print("=" * 70)
    
    # Load data
    print("\n📂 Loading job data...")
    jobs = load_jobs_data()
    if not jobs:
        print("❌ No data available. Run scraper.py and analyze_skills.py first.")
        return
    
    print(f"✅ Loaded {len(jobs)} jobs")
    
    # Calculate monthly skill counts
    print("\n📊 Calculating historical trends...")
    monthly_data = calculate_monthly_skill_counts(jobs)
    
    # Get top skills to forecast
    skill_totals = defaultdict(int)
    for skill, months in monthly_data.items():
        skill_totals[skill] = sum(months.values())
    
    top_skills = sorted(skill_totals.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Forecast trends for top skills
    print("\n🔮 TREND FORECASTING (Top 10 Skills)")
    print("-" * 70)
    
    forecasts = []
    for skill, total_count in top_skills:
        forecast = forecast_skill_trend(skill, monthly_data[skill])
        if forecast["status"] == "success":
            forecasts.append(forecast)
            
            print(f"\n📈 {skill} (Total: {total_count} jobs)")
            print(f"   Trend: {forecast['trend'].upper()} ({forecast['trend_strength']})")
            print(f"   Current month: {forecast['current_month_count']} jobs")
            print(f"   Predicted next month: {forecast['predicted_next_month']} jobs "
                  f"({forecast['predicted_change_pct']:+.1f}%)")
            print(f"   Moving Average: {forecast['moving_average_prediction']}")
            
            for rec in forecast['recommendations']:
                print(f"   {rec}")
    
    # Generate city-tech heatmap
    print("\n\n🗺️  CITY vs TECH STACK HEATMAP")
    print("-" * 70)
    
    heatmap = generate_city_tech_heatmap(jobs)
    
    print(f"\n📊 Matrix: {len(heatmap['cities'])} cities × {len(heatmap['skills'])} skills")
    print(f"   Total jobs analyzed: {heatmap['metadata']['total_jobs']}")
    
    print("\n🎯 Top Skills by City:")
    for insight in sorted(heatmap['insights'], key=lambda x: x['total_jobs'], reverse=True):
        print(f"\n   {insight['city']}: {insight['total_jobs']} jobs")
        print(f"   → Dominant skill: {insight['dominant_skill']} "
              f"({insight['count']} jobs, {insight['percentage']}% of city total)")
    
    # Show detailed matrix
    print("\n\n📋 DETAILED MATRIX (Top 5 Skills per City)")
    print("-" * 70)
    
    for row in heatmap['matrix']:
        city = row['city']
        skills_data = row['skills']
        top_5 = sorted(skills_data.items(), key=lambda x: x[1], reverse=True)[:5]
        
        print(f"\n{city}:")
        for skill, count in top_5:
            if count > 0:
                bar = "█" * min(count // 2, 30)
                print(f"  {skill:.<25} {count:>3} {bar}")
    
    # Save results
    analytics_data = {
        "generated_at": datetime.now().isoformat(),
        "forecasts": forecasts,
        "heatmap": heatmap,
    }
    
    save_snapshot(analytics_data)
    
    print("\n" + "=" * 70)
    print("✅ Analysis complete!")
    print("\n💡 Use these insights for:")
    print("   • Career planning and skill development")
    print("   • Understanding regional tech market differences")
    print("   • Identifying emerging vs declining technologies")
    print("   • Strategic job search targeting")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

