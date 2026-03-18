# 💼 Internship Tracker — WSU Edition

An automated internship search tool built specifically for **Wright State University** students. It logs into Handshake via SSO, scrapes job listings based on configurable keywords and locations, stores results in CSV, and displays everything in an interactive **Streamlit dashboard** — saving 30+ minutes per manual search session.

---

## 📌 Table of Contents

- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Running the Project](#running-the-project)
- [Dashboard Guide](#dashboard-guide)
- [Analytics & Time Savings](#analytics--time-savings)
- [API / Functions Reference](#api--functions-reference)
- [Data Output Format](#data-output-format)
- [Security Notice](#security-notice)

---

## Features

- 🔐 **Automated SSO login** — handles Wright State University's multi-step Handshake authentication
- 🔍 **Keyword & location search** — configurable major, location, and page-depth scraping
- 📋 **Full job detail extraction** — title, company, location, and description per listing
- 💾 **Auto-deduplication** — merges new results into a master `internships.csv`, removing duplicates by URL
- 🤖 **Headless mode** — run silently in the background via `scheduler.py`
- 📊 **Streamlit dashboard** — 3-tab UI for searching, browsing, and analytics
- ⏱️ **Time savings tracking** — logs every action and calculates hours saved vs. manual searching
- 📁 **JSON search config** — define multiple saved searches in `search_config.json`
- 📝 **Doctest-compatible** — helper functions include full doctest coverage

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  dashboard.py                        │
│           (Streamlit UI — 3 tabs)                   │
│   Search Jobs │ Job Listings │ Analytics            │
└────────────────────────┬────────────────────────────┘
                         │ imports
           ┌─────────────▼────────────┐
           │    internship_tracker.py │  ◄── Main library
           │    InternshipTracker     │
           │    class + helpers       │
           └──────────┬───────────────┘
                      │ Selenium
           ┌──────────▼───────────────┐
           │     Handshake (WSU SSO)  │
           │  app.joinhandshake.com   │
           └──────────────────────────┘
                      │
           ┌──────────▼───────────────┐
           │  internships.csv         │  ◄── Master data file
           │  internships_YYYYMMDD_   │  ◄── Timestamped snapshots
           │  usage_log.json          │  ◄── Analytics data
           └──────────────────────────┘
                      ▲
           ┌──────────┴───────────────┐
           │     scheduler.py         │  ◄── Automated batch runner
           │     AutomatedTracker     │       (headless, config-driven)
           └──────────────────────────┘
```

---

## Project Structure

```
academic_project_internships_tracker/
│
├── internship_tracker.py       # Core library — InternshipTracker class + doctests
├── handshake_scraper.py        # Lightweight alternative scraper (simplified)
├── dashboard.py                # Streamlit web dashboard (3 tabs)
├── scheduler.py                # Headless automated runner with scheduling logic
│
├── search_config.json          # Define saved searches (major, location, pages)
├── requirements.txt            # Python dependencies
│
├── internships.csv             # Master deduplicated job database (auto-generated)
├── internships_YYYYMMDD_*.csv  # Timestamped snapshots per scrape session
├── internship_tracker.log      # Detailed run logs
├── usage_log.json              # Action history for analytics dashboard
│
└── .env                        # WSU credentials (create this — see setup)
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Browser Automation | [Selenium](https://selenium-python.readthedocs.io/) + WebDriver Manager |
| HTML Parsing | [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) |
| Data Processing | [Pandas](https://pandas.pydata.org/) |
| Dashboard | [Streamlit](https://streamlit.io/) |
| Charts | [Plotly Express](https://plotly.com/python/plotly-express/) |
| Scheduling | [schedule](https://schedule.readthedocs.io/) |
| Auth / Config | [python-dotenv](https://pypi.org/project/python-dotenv/) |
| Language | Python 3.8+ |

---

## Getting Started

### Prerequisites

- Python 3.8+
- Google Chrome installed
- A Wright State University Handshake account

### 1. Clone the repository

```bash
git clone https://github.com/bishalth28/academic_project_internships_tracker.git
cd academic_project_internships_tracker
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> ChromeDriver is managed automatically by `webdriver-manager` — no manual install needed.

### 4. Create your `.env` file

```bash
# Create .env in the project root
WRIGHT_STATE_EMAIL=yourname@wright.edu
WRIGHT_STATE_USERNAME=w00xxxxxx
WRIGHT_STATE_PASSWORD=your_campus_password
```

> ⚠️ Never commit this file. It is (and should be) listed in `.gitignore`.

---

## Configuration

Edit `search_config.json` to define your saved searches:

```json
{
  "searches": [
    {
      "major": "Computer Science",
      "location": "Remote",
      "max_pages": 2
    },
    {
      "major": "Software Engineering",
      "location": "Ohio",
      "max_pages": 2
    }
  ],
  "max_jobs_per_search": 10,
  "output_format": "csv"
}
```

| Field | Description | Default |
|-------|-------------|---------|
| `major` | Keyword or field of study to search | `"Computer Science"` |
| `location` | City, state, or "Remote" | `"Remote"` |
| `max_pages` | How many Handshake result pages to scrape | `2` |
| `max_jobs_per_search` | Max number of jobs to scrape full details for | `10` |
| `output_format` | Output file format | `"csv"` |

---

## Running the Project

### Option 1 — Interactive Mode (manual input)

```bash
python internship_tracker.py
```

Prompts for keywords and location, then runs a single search.

### Option 2 — Streamlit Dashboard (recommended)

```bash
streamlit run dashboard.py
```

Opens at **http://localhost:8501** — full UI for searching, browsing results, and viewing analytics.

### Option 3 — Automated / Headless Scheduler

```bash
python scheduler.py
```

Runs all searches defined in `search_config.json` silently in headless Chrome. Ideal for cron jobs or scheduled automation:

```bash
# Example: run every day at 8am (Linux/Mac cron)
0 8 * * * cd /path/to/project && python scheduler.py
```

### Option 4 — Run Doctests

```bash
python -m doctest -v internship_tracker.py
```

---

## Dashboard Guide

The Streamlit dashboard has **three tabs**:

### 🔍 Tab 1 — Search Jobs
- Enter keywords, location, and number of pages
- Set a job detail limit (5–50)
- Click **Start Scraping** — a live progress bar and log stream shows scraping activity in real time
- Results are saved automatically to `internships.csv`

### 💼 Tab 2 — Job Listings
- Filter by company, location, or title keyword
- Summary metrics: total jobs, unique companies, locations
- Bar charts for top companies and locations
- Expandable job cards with description preview and a direct **View Job** link
- Download filtered results as CSV

### 📊 Tab 3 — Analytics
- Session count, total time saved, and efficiency percentage
- Time comparison chart: Manual vs. Automated vs. Saved
- Daily usage line chart
- Action breakdown pie chart
- Recent activity log table (last 20 actions)

---

## Analytics & Time Savings

The tracker measures efficiency automatically:

| Metric | Value |
|--------|-------|
| Manual search time / session | 37.5 minutes |
| Automated search time / session | 5 minutes |
| Time saved / session | **32.5 minutes** |
| Efficiency | **87%** |

Every action (init, login, search, save, close) is appended to `usage_log.json` and aggregated in the dashboard.

---

## API / Functions Reference

### Helper Functions (`internship_tracker.py`)

#### `clean_text(text: str) → str`
Strips extra whitespace and newlines. Returns `"N/A"` for empty/None input.

```python
>>> clean_text("  Software   Engineer  ")
'Software Engineer'
>>> clean_text(None)
'N/A'
```

#### `validate_url(url: str) → bool`
Returns `True` if the URL belongs to the `joinhandshake.com` domain.

```python
>>> validate_url("https://app.joinhandshake.com/job-search/12345")
True
>>> validate_url("https://google.com")
False
```

---

### `InternshipTracker` Class

#### `__init__(email, username, password, headless=False)`
Initializes the tracker, loading credentials from arguments or `.env` fallback.

#### `setup_driver()`
Installs and configures ChromeDriver with anti-detection user agent. Supports headless mode.

#### `login() → bool`
Performs the full Wright State SSO flow:
1. Navigate to Handshake login
2. Select Wright State University
3. Enter email → trigger SSO redirect
4. Enter campus username + password
5. Returns `True` on success, `False` on failure

#### `search_jobs(major, location, max_pages) → List[str]`
Searches Handshake and returns a list of unique job posting URLs. Uses JS injection for robust URL extraction and auto-scrolls to trigger lazy-loaded content.

#### `scrape_job_details(job_url) → Dict`
Navigates to a job URL and extracts: title, company, location, description, source, and scrape timestamp.

#### `save_to_file(jobs, filename, format)`
Saves results to a timestamped CSV file and merges with the master `internships.csv`, deduplicating by URL.

#### `log_usage(action, details)`
Appends a timestamped entry to `usage_log.json` for dashboard analytics.

#### `close()`
Quits the browser and resets session state.

---

## Data Output Format

Each row in `internships.csv` contains:

| Column | Description |
|--------|-------------|
| `url` | Unique Handshake job URL |
| `date_scraped` | Timestamp when the record was scraped |
| `source` | Always `"Handshake"` |
| `title` | Job title |
| `company` | Company / employer name |
| `location` | Job location or "Remote" |
| `description` | First 500 characters of the job description |

---

## Security Notice

> ⚠️ Your campus credentials are sensitive. Follow these rules:

**Always use `.env`** — never hardcode credentials in source files:
```bash
WRIGHT_STATE_EMAIL=yourname@wright.edu
WRIGHT_STATE_USERNAME=w00xxxxxx
WRIGHT_STATE_PASSWORD=your_campus_password
```

**Verify `.gitignore` includes:**
```
.env
*.log
usage_log.json
internships*.csv
last_run.txt
```

**Do not share** `usage_log.json` or log files publicly — they contain timestamps of when you logged in.

---

## Contributing

Ideas to extend the project:

- Add email/SMS notifications when new matching jobs appear
- Expand to additional job platforms (LinkedIn, Indeed, Glassdoor)
- Add application status tracking (Applied / Interview / Offer)
- Build a cron-based daily auto-run with Dockerfile
- Add NLP-based job relevance scoring using `scikit-learn`

---


*Built as an academic automation project for Wright State University — saving students 30+ minutes per search session.*
