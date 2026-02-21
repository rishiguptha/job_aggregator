# Multi-ATS Data Engineer Job Aggregator

A high-performance, asynchronous Python tool built to monitor over 6,300+ public company job boards (Greenhouse, Lever, Ashby, and Workable). It automatically tracks, validates, and emails you newly posted Data Engineering (and optional related) roles.

By querying the unauthenticated public ATS endpoints directly, this aggregator bypasses the standard 24-48 hour delay of 3rd-party job boards like LinkedIn, giving you a massive early-access advantage, especially for highly competitive or New Grad roles.

## Features

- **Massive Scale & Speed:** Uses `aiohttp` and `asyncio` to concurrently query thousands of endpoints in a non-blocking way, reducing execution time from minutes to seconds.
- **Smart Filtering Engine:** Employs rule-based regex parsing on HTML job descriptions to filter out roles you don't want:
  - **Title Checks:** Includes/excludes specific job title keywords.
  - **Experience Caps:** Excludes roles requesting more than `MAX_EXPERIENCE_YEARS` (e.g., skips "5+ years required").
  - **Security Clearance:** Filters out jobs strictly requiring TS/SCI or active US government clearances.
  - **PhD Filters:** Excludes roles strictly requesting a Ph.D.
  - **Date Filters:** Only fetches roles posted *today*.
- **Email Delivery:** Automatically sends formatted daily batches of matching jobs to your inbox.
- **Deduplication:** Maintains local state via a `seen_jobs_v2.json` file so you are never emailed the same role twice.

## Project Structure

```text
job_aggregator/
├── main.py                    # Core entry node and CLI wrapper
├── src/
│   ├── config/
│   │   ├── companies.py       # 6300+ tracked ATS company slugs
│   │   ├── settings.py        # Global configurations & regex patterns
│   │   └── constants.py       # UI / Icon constants
│   ├── fetchers/
│   │   ├── manager.py         # Async execution controller using concurrent semaphores
│   │   ├── greenhouse.py      # Greenhouse API parser
│   │   ├── lever.py           # Lever API parser
│   │   ├── ashby.py           # Ashby API parser
│   │   └── workable.py        # Workable widget API parser
│   ├── filters/
│   │   ├── title.py           # Role matching logic
│   │   ├── experience.py      # 0-x years experience analyzer
│   │   ├── clearance.py       # Clearance / citizenship bounds
│   │   ├── phd.py             # Education bounds
│   │   ├── location.py        # Geolocator bounds
│   │   └── date.py            # 'Posted Today' datetime utility
│   ├── state/
│   │   └── dedup.py           # Deduplication IO cache
│   └── notifications/
│       └── email.py           # SMTP TLS delivery system
└── seen_jobs_v2.json          # Cached UUID deduplication ledger (auto-generated)
```

## Setup & Installation

**1. Clone the repository**
```bash
git clone <repository_url>
cd job_aggregator
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```
*(Key dependencies: `aiohttp`, `requests`, `schedule`)*

**3. Configure Settings**
Open `src/config/settings.py` to modify your parameters:
- **Email Alerts:** Add your SMTP `SENDER_EMAIL` and `SENDER_PASSWORD` alongside your `RECIPIENT_EMAIL`. (It is highly recommended to use an App Password for Gmail).
- **Settings:** Adjust `MAX_EXPERIENCE_YEARS` or your core search parameters like `TITLE_KEYWORDS`.

## Usage

The application uses `argparse` and has a few different operational modes:

**Dry-Run (Test Execution)**
Runs the asynchronous fetchers and prints matching roles to the terminal without modifying the local cache or sending an email.
```bash
python main.py --dry-run
```

**Run Once**
Executes the data pipeline exactly one time, emails the results, updates the tracker, and exits. Perfect for piping into a scheduled cron job.
```bash
python main.py --once
```

**Daemon Mode (Continuous Execution)**
Runs continuously in the foreground, triggering the aggregator every `CHECK_INTERVAL_MINUTES` as defined in `settings.py`.
```bash
python main.py
```

**Test Email Setup**
Verifies your SMTP functionality by pushing a mock email payload.
```bash
python main.py --test-email
```

**View Company Stats**
Prints a breakdown of how many active ATS platforms and domains are currently being tracked.
```bash
python main.py --stats
```
