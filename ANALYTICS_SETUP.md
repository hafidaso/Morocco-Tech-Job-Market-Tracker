# Trend Forecasting & Analytics - Setup Guide

This guide explains how to use the **Trend Forecasting** and **City vs Tech Stack Heatmap** features for market intelligence and predictive analytics.

## What's New?

### 1. Trend Forecasting
Predict future skill demand using linear regression and moving averages.

**What it does:**
- Analyzes historical job data by month
- Uses simple linear regression to calculate trend slope
- Predicts next month's demand
- Identifies growing, declining, or stable trends
- Provides actionable career recommendations

**Example Results:**
- "Python demand is **growing strongly** (+31% predicted growth)"
- "PHP demand is **declining** (-15% predicted change)"
- "React demand is **stable** with consistent opportunities"

### 2. City vs Tech Stack Heatmap
Visual matrix showing which technologies are popular in which cities.

**What it reveals:**
- Regional differences in tech preferences
- Dominant skills per city
- Technology distribution patterns
- Where to focus job search by skill

**Example Insights:**
- "Python dominates Casablanca (45% of jobs)"
- "PHP/Symfony is stronger in Rabat"
- "Machine Learning is concentrated in Casablanca"

---

## 🚀 Usage

### Option 1: Python Script (Detailed Analysis)

```bash
# Run the comprehensive analysis script
python3 forecast_trends.py
```

**Output:**
- Trend forecasts for top 10 skills
- Detailed recommendations
- City-Tech heatmap matrix
- Insights about dominant skills per city
- Saves results to `analytics_snapshot.json`

### Option 2: API Endpoints (Real-time)

Start the API and query endpoints:

```bash
uvicorn main:app --reload
```

---

## 📡 API Endpoints

### 1. Skill Trend Forecasting

**Endpoint:** `GET /analytics/forecast`

**Parameters:**
- `skill` (optional): Specific skill to forecast (e.g., "Python", "React")
- `top` (optional, default: 10): Number of top skills to analyze (1-20)

**Example Requests:**

```bash
# Forecast top 10 skills
curl "http://127.0.0.1:8000/analytics/forecast"

# Forecast specific skill
curl "http://127.0.0.1:8000/analytics/forecast?skill=Python"

# Forecast top 15 skills
curl "http://127.0.0.1:8000/analytics/forecast?top=15"
```

**Response:**
```json
{
  "forecasts": [
    {
      "skill": "Python",
      "status": "success",
      "trend": "growing",
      "trend_strength": "strong",
      "slope": 7.5,
      "current_month_count": 127,
      "recent_average": 45.7,
      "predicted_next_month": 60,
      "predicted_change_pct": 31.4,
      "historical_data": {
        "months": ["2025-09", "2025-10", "2025-11"],
        "counts": [20, 34, 127]
      },
      "recommendations": [
        "✅ High demand - Consider learning or improving this skill",
        "🔥 Strong growth - Hot skill in the market"
      ]
    }
  ],
  "total_skills_analyzed": 10
}
```

### 2. City-Tech Heatmap

**Endpoint:** `GET /analytics/heatmap`

**Parameters:**
- `top_skills` (optional, default: 15): Number of top skills to include (5-30)

**Example Requests:**

```bash
# Get heatmap with top 15 skills
curl "http://127.0.0.1:8000/analytics/heatmap"

# Get heatmap with top 20 skills
curl "http://127.0.0.1:8000/analytics/heatmap?top_skills=20"
```

**Response:**
```json
{
  "cities": ["Casablanca", "Rabat", "Tanger", "Morocco"],
  "skills": ["Python", "SQL", "Java", "React", "..."],
  "matrix": [
    {
      "city": "Casablanca",
      "total_jobs": 200,
      "skills": {
        "Python": 90,
        "SQL": 75,
        "Java": 45,
        "React": 30
      }
    }
  ],
  "insights": [
    {
      "city": "Casablanca",
      "dominant_skill": "Python",
      "count": 90,
      "percentage": 45.0,
      "total_jobs": 200,
      "message": "Python is dominant in Casablanca (45.0% of jobs)"
    }
  ],
  "metadata": {
    "total_jobs": 650,
    "total_cities": 4,
    "total_skills_analyzed": 15
  }
}
```

---

## 📊 Understanding the Results

### Trend Analysis

**Trend Types:**
- **Growing**: Demand is increasing (slope > 1)
- **Declining**: Demand is decreasing (slope < -1)
- **Stable**: Demand is relatively constant (-1 ≤ slope ≤ 1)

**Trend Strength:**
- **Strong**: Rapid change (|slope| > 5)
- **Moderate**: Steady change (1 < |slope| ≤ 5)
- **Stable**: Minimal change

**Key Metrics:**
- **Slope**: Rate of change (jobs per month)
- **Predicted Change %**: Expected percentage change next month
- **Recent Average**: Average of last 3 months
- **Moving Average**: Smoothed prediction using last 3 months

### Heatmap Insights

**Matrix Values:**
- Each cell shows job count for that skill in that city
- Higher numbers = more jobs requiring that skill
- Zeros indicate no jobs found with that skill

**Dominant Skill:**
- The most common skill in each city
- Shows percentage of city's total jobs
- Reveals regional specializations

---

## 💻 Use Cases

### For Job Seekers

1. **Career Planning:**
   ```bash
   # Check if your skill is in demand
   curl "http://127.0.0.1:8000/analytics/forecast?skill=React"
   ```
   - If growing → Good time to enter market
   - If declining → Consider complementary skills

2. **City Selection:**
   ```bash
   # See where your skills are most in demand
   curl "http://127.0.0.1:8000/analytics/heatmap"
   ```
   - Target cities where your skills dominate
   - Avoid cities with low demand

3. **Skill Development:**
   - Focus on **growing** skills for future-proofing
   - Learn skills that are dominant in your target city

### For Recruiters

1. **Talent Availability:**
   - Identify cities with strong tech talent pools
   - Understand which skills are oversaturated vs scarce

2. **Salary Negotiation:**
   - Growing trends → Expect higher salaries
   - Declining trends → More negotiation leverage

3. **Hiring Strategy:**
   - Target cities where specific skills are abundant
   - Plan training programs for declining skills

### For Training Centers

1. **Course Planning:**
   - Offer courses on **growing** technologies
   - Phase out courses on **declining** technologies

2. **Regional Focus:**
   - Tailor courses to city-specific demands
   - Partner with companies in cities needing specific skills

---

## 📈 Example Insights

### From Real Data (Morocco Tech Market)

**Growing Skills:**
- **Python** (+31% predicted) - Very hot in Casablanca
- **Machine Learning** (+45% predicted) - Emerging field
- **Power BI** (+127% predicted) - Business analytics boom
- **AWS** (+31% predicted) - Cloud adoption increasing

**Stable Skills:**
- **SQL** - Consistent demand across all cities
- **Git** - Essential skill, always needed
- **Docker** - Standard DevOps tool

**Regional Patterns:**
- **Casablanca**: Python, Java, Machine Learning dominant
- **Rabat**: More balanced, strong in business intelligence
- **Tanger**: Emerging market with diverse needs
- **Morocco-wide**: Remote positions, varied requirements

---

## 🛠️ Technical Details

### Forecasting Algorithm

1. **Data Preparation:**
   - Group jobs by month and skill
   - Create time series for each skill

2. **Linear Regression:**
   ```
   y = mx + b
   where:
   - y = predicted job count
   - m = slope (trend)
   - x = month index
   - b = intercept
   ```

3. **Moving Average:**
   ```
   MA = average(last 3 months)
   ```

4. **Trend Classification:**
   - slope > 5: Strong growth
   - 1 < slope ≤ 5: Moderate growth
   - -1 ≤ slope ≤ 1: Stable
   - -5 ≤ slope < -1: Moderate decline
   - slope < -5: Strong decline

### Heatmap Generation

1. Count skills per city
2. Select top N skills by total count
3. Build matrix: cities × skills
4. Calculate percentages for insights
5. Identify dominant skill per city

---

## 🐛 Troubleshooting

### "Insufficient data" Error

**Cause:** Less than 2 months of historical data

**Solution:**
- Run scraper multiple times over several weeks
- Historical data accumulates automatically

### Unexpected Trends

**Why predictions might seem off:**
- Small sample size (< 100 jobs total)
- Seasonal variations (hiring cycles)
- Recent market changes
- Data quality issues

**Best practices:**
- Look at trends over 3+ months
- Consider moving average (more stable)
- Compare with industry knowledge

### Empty Heatmap Cells

**Normal reasons:**
- Skill truly not used in that city
- Very small sample size
- Regional specialization

---

## 📚 Integration Examples

### Frontend Dashboard

```typescript
// Fetch forecast data
const fetchForecast = async () => {
  const response = await axios.get('/analytics/forecast?top=10');
  const forecasts = response.data.forecasts;
  
  // Display growing skills
  const growing = forecasts.filter(f => f.trend === 'growing');
  setGrowingSkills(growing);
};

// Fetch heatmap
const fetchHeatmap = async () => {
  const response = await axios.get('/analytics/heatmap');
  setHeatmapData(response.data);
};
```

### Email Reports

```python
# Generate weekly trend report
import requests

response = requests.get('http://localhost:8000/analytics/forecast')
forecasts = response.json()['forecasts']

# Send to subscribers
for skill in forecasts:
    if skill['trend'] == 'growing' and skill['trend_strength'] == 'strong':
        send_email(f"🔥 Hot Skill Alert: {skill['skill']} is growing!")
```

---

## 🎯 Roadmap

Future enhancements:
- [ ] ARIMA forecasting for better accuracy
- [ ] Confidence intervals for predictions
- [ ] Salary trend predictions
- [ ] Company-specific trends
- [ ] Experience level analysis
- [ ] Interactive heatmap visualization
- [ ] Export to Excel/PDF
- [ ] Historical snapshots comparison

---

## 📝 Files Reference

- **forecast_trends.py** - Standalone analysis script
- **main.py** - API endpoints (`/analytics/forecast`, `/analytics/heatmap`)
- **analytics_snapshot.json** - Saved analysis results (generated by script)

---

**Need Help?** 
- Run `python3 forecast_trends.py` for detailed output
- Check API docs: http://127.0.0.1:8000/docs
- Review historical data in `processed_jobs_for_api.json`

