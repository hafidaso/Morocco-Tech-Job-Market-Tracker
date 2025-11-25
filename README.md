# 🇲🇦 Morocco Tech Job Market Tracker

A full-stack data intelligence platform that scrapes, analyzes, and visualizes tech job market trends across Morocco. Built with Python, FastAPI, Next.js, and real-time automation.

![Status](https://img.shields.io/badge/status-active-success)
![Python](https://img.shields.io/badge/python-3.13-blue)
![Next.js](https://img.shields.io/badge/next.js-16.0.3-black)
![FastAPI](https://img.shields.io/badge/fastapi-0.121.3-green)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Data Pipeline](#data-pipeline)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Future Enhancements](#future-enhancements)
```
## 🎯 Overview

This project transforms raw job postings into actionable market intelligence. It automatically:

1. **Scrapes** job listings from Indeed, LinkedIn, Google, and Bayt across major Moroccan cities
2. **Extracts** technical skills using NLP and regex pattern matching
3. **Analyzes** trends to identify in-demand technologies
4. **Visualizes** insights through an interactive dashboard

**Current Dataset**: 454+ unique job postings with skill extraction and trend analysis.

## ✨ Features

- 🔄 **Automated Scraping**: Runs every 6 hours via APScheduler (configurable)
- 🧠 **NLP Skill Extraction**: Regex-based pattern matching for 60+ tech skills
- 📊 **Real-time Dashboard**: Live charts showing top skills, city distribution, and job listings
- 🔍 **Search & Filter**: Find jobs by company, role, or city
- 🌐 **RESTful API**: FastAPI backend with automatic documentation
- 📱 **Responsive UI**: Dark mode dashboard built with Next.js and Tailwind CSS
- 🔁 **Auto-refresh**: Frontend polls API every 60 seconds for fresh data

## 🏗️ Architecture

```
┌─────────────────┐
│   Job Sites     │ (Indeed, LinkedIn, Google, Bayt)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   scraper.py    │ → morocco_data_market.csv
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ analyze_skills.py│ → processed_jobs_for_api.json
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    main.py      │ (FastAPI + APScheduler)
│  (Backend API)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Next.js App    │ (React Dashboard)
│   (Frontend)    │
└─────────────────┘
```

## 🛠️ Tech Stack

### Backend
- **Python 3.13**: Core language
- **FastAPI**: REST API framework
- **APScheduler**: Background job automation
- **pandas**: Data manipulation
- **python-jobspy**: Web scraping library
- **uvicorn**: ASGI server

### Frontend
- **Next.js 16**: React framework with SSR
- **TypeScript**: Type safety
- **Tailwind CSS**: Styling
- **Recharts**: Data visualization
- **Axios**: HTTP client
- **Lucide React**: Icons

## 📁 Project Structure

```
Job Market Trends Tracker/
├── scraper.py                 # Phase 1: Web scraping script
├── analyze_skills.py          # Phase 2: NLP skill extraction
├── main.py                    # Phase 3: FastAPI + automation
├── morocco_data_market.csv    # Raw scraped data
├── processed_jobs_for_api.json # Analyzed data for API
│
├── client/                    # Next.js frontend
│   ├── app/
│   │   ├── page.tsx          # Main dashboard component
│   │   ├── layout.tsx        # Root layout
│   │   └── globals.css       # Global styles
│   ├── package.json
│   └── next.config.ts
│
└── README.md                  # This file
```

## 🚀 Installation

### Prerequisites

- Python 3.13+
- Node.js 18+
- npm or yarn

### Backend Setup

1. **Clone or navigate to the project directory**:
   ```bash
   cd "Job Market Trends Tracker"
   ```

2. **Install Python dependencies**:
   ```bash
   pip3 install fastapi uvicorn apscheduler pandas python-jobspy
   ```

3. **Verify installation**:
   ```bash
   python3 --version
   python3 -c "import fastapi; print('FastAPI installed')"
   ```

### Frontend Setup

1. **Navigate to client directory**:
   ```bash
   cd client
   ```

2. **Install Node dependencies**:
   ```bash
   npm install
   ```

3. **Verify installation**:
   ```bash
   npm run dev
   # Should start on http://localhost:3000
   ```

## 💻 Usage

### Running the Full Stack

#### Terminal 1: Start Backend API
```bash
cd "Job Market Trends Tracker"
uvicorn main:app --reload
```

The API will be available at:
- **API**: http://127.0.0.1:8000
- **Docs**: http://127.0.0.1:8000/docs (Swagger UI)

#### Terminal 2: Start Frontend
```bash
cd client
npm run dev
```

The dashboard will be available at:
- **Dashboard**: http://localhost:3000

### Manual Pipeline Execution

If you want to run the scraping and analysis manually:

```bash
# Step 1: Scrape jobs
python3 scraper.py

# Step 2: Extract skills
python3 analyze_skills.py

# Step 3: Restart API to reload data
# (Ctrl+C the uvicorn process, then restart)
uvicorn main:app --reload
```

### Automation

The backend automatically runs the pipeline every **6 hours** via APScheduler. To change the interval, edit `main.py`:

```python
# For testing (1 minute - use with caution!)
scheduler.add_job(run_pipeline, "interval", minutes=1)

# Production (6 hours - recommended)
scheduler.add_job(run_pipeline, "interval", hours=6)
```

⚠️ **Warning**: Scraping too frequently (every minute) can result in IP bans. Use intervals of 4-12 hours for production.

## 📡 API Endpoints

### `GET /`
Health check and job count.

**Response**:
```json
{
  "status": "Live",
  "jobs_count": 454
}
```

### `GET /jobs`
Get job listings with optional filters.

**Query Parameters**:
- `city` (optional): Filter by city (e.g., "Casablanca")
- `role` (optional): Filter by role (e.g., "Data Scientist")
- `limit` (optional, default: 20): Maximum results to return

**Example**:
```bash
curl "http://127.0.0.1:8000/jobs?city=Casablanca&limit=10"
```

**Response**:
```json
{
  "total": 150,
  "data": [
    {
      "title": "Data Scientist",
      "company": "TechCorp",
      "location": "Casablanca, Morocco",
      "searched_city": "Casablanca",
      "searched_role": "Data Scientist",
      "job_url": "https://...",
      "extracted_skills": ["Python", "SQL", "Machine Learning"]
    }
  ]
}
```

### `GET /trends/skills`
Get top 10 most in-demand skills.

**Response**:
```json
[
  {"name": "Python", "value": 142},
  {"name": "SQL", "value": 142},
  {"name": "Machine Learning", "value": 102}
]
```

### `GET /trends/cities`
Get job distribution by city.

**Response**:
```json
[
  {"name": "Casablanca", "value": 200},
  {"name": "Rabat", "value": 150},
  {"name": "Morocco", "value": 104}
]
```

## 🔄 Data Pipeline

### Phase 1: Scraping (`scraper.py`)

- **Target Cities**: Casablanca, Rabat, Tanger, Morocco (catch-all)
- **Target Roles**: Data Scientist, Data Analyst, Data Engineer, Business Analyst, Ingénieur Data, Big Data, Business Intelligence
- **Sites**: Indeed, LinkedIn, Google, Bayt
- **Parameters**:
  - `results_wanted`: 40 per search
  - `hours_old`: 720 (30 days)
  - `linkedin_fetch_description`: True (for NLP analysis)

**Output**: `morocco_data_market.csv`

### Phase 2: Analysis (`analyze_skills.py`)

- **Skill Dictionary**: 60+ tech skills with regex patterns
- **Extraction Method**: Pattern matching on job descriptions
- **Multilingual Support**: Handles English and French job descriptions

**Output**: `processed_jobs_for_api.json`

### Phase 3: API & Automation (`main.py`)

- **Scheduler**: APScheduler runs pipeline every 6 hours
- **Data Loading**: In-memory cache refreshed after each scrape
- **Endpoints**: RESTful API for frontend consumption

### Phase 4: Frontend (`client/app/page.tsx`)

- **Polling**: Fetches fresh data every 60 seconds
- **Visualizations**: Bar charts (skills), pie charts (cities)
- **Search**: Real-time filtering by company/role

## ⚙️ Configuration

### Scraper Settings (`scraper.py`)

```python
CITIES = ["Casablanca", "Rabat", "Tanger", "Morocco"]
ROLES = ["Data Scientist", "Data Analyst", ...]
results_wanted = 40      # Jobs per search
hours_old = 720          # 30 days lookback
time.sleep(5)           # Delay between requests
```

### Scheduler Settings (`main.py`)

```python
scheduler.add_job(run_pipeline, "interval", hours=6)
```

### Frontend Settings (`client/app/page.tsx`)

```typescript
const API_URL = "http://127.0.0.1:8000";
// Polling interval: 60000ms (60 seconds)
```

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'jobspy'"

**Solution**:
```bash
pip3 install -U python-jobspy
```

### "Network Error" in Frontend

**Solution**: Ensure the FastAPI backend is running:
```bash
uvicorn main:app --reload
```

### "Port 3000 is in use"

**Solution**: Kill existing Next.js processes:
```bash
pkill -f "next dev"
```

### Bayt Returns 403 Errors

**Status**: Expected. Bayt has anti-scraping measures. The scraper continues with other sites (Indeed, LinkedIn, Google).

### Hydration Warnings in Browser

**Status**: Harmless. Caused by browser extensions injecting attributes. Suppressed via `suppressHydrationWarning` in layout.

### Low Job Count

**Solutions**:
1. Increase `results_wanted` in `scraper.py` (currently 40)
2. Increase `hours_old` (currently 720 = 30 days)
3. Add more cities or roles to search

## 🚧 Future Enhancements

- [ ] **Database Integration**: Replace JSON files with PostgreSQL/MongoDB
- [ ] **Authentication**: User accounts and saved searches
- [ ] **Email Alerts**: Notify users of new jobs matching criteria
- [ ] **Advanced Analytics**: Salary trends, experience level analysis
- [ ] **Export Features**: PDF reports, CSV downloads
- [ ] **Multi-language Support**: Arabic/French UI
- [ ] **Machine Learning**: Skill demand forecasting
- [ ] **Docker Deployment**: Containerized setup
- [ ] **CI/CD Pipeline**: Automated testing and deployment

## 📊 Current Statistics

- **Total Jobs Scraped**: 454+
- **Average Skills per Job**: 3.9
- **Top Skills**: Agile (167), Python (142), SQL (142)
- **Cities Covered**: Casablanca, Rabat, Tanger, Morocco-wide
- **Update Frequency**: Every 6 hours (automatic)

## 📝 License

This project is for educational and portfolio purposes. Please respect the terms of service of job sites when scraping.

## 👤 Author

**Hafida Belayd**

Built as a full-stack data intelligence project demonstrating:
- Web scraping and data collection
- NLP and pattern matching
- RESTful API design
- Real-time data visualization
- Automated pipeline orchestration

---

**Last Updated**: November 2025  
**Version**: 1.0

>>>>>>> 8fbeb4e (Initial commit: Morocco Tech Job Tracker)
