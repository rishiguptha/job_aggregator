# Multi-ATS Job Aggregator

A high-performance, asynchronous Python tool built to monitor **6,400+** public company job boards across **6 ATS platforms** (Greenhouse, Lever, Ashby, Workable, OracleCloud, Workday). It automatically tracks, validates, and emails you newly posted roles — before they hit LinkedIn.

By querying unauthenticated public ATS endpoints directly, this aggregator bypasses the standard 24-48 hour delay of 3rd-party job boards, giving you a massive early-access advantage, especially for highly competitive or New Grad roles.

## Features

- **Massive Scale & Speed:** Uses `aiohttp` and `asyncio` to concurrently query thousands of endpoints in a non-blocking way, reducing execution time from minutes to seconds.
- **6 ATS Platforms:** Greenhouse (4,540), Lever (1,001), Ashby (833), Workable (13), OracleCloud (30), Workday (39).
- **Smart Filtering Engine:** Employs rule-based regex parsing on HTML job descriptions to filter out roles you don't want:
  - **Title Checks:** Includes/excludes specific job title keywords with primary and bonus match tiers.
  - **Experience Caps:** Excludes roles requesting more than `MAX_EXPERIENCE_YEARS` (e.g., skips "5+ years required").
  - **Security Clearance:** Filters out jobs strictly requiring TS/SCI or active US government clearances.
  - **PhD Filters:** Excludes roles strictly requesting a Ph.D.
  - **Location Filters:** US-only filtering with comprehensive state/city/keyword matching.
  - **Date Filters:** Only fetches roles posted *today* or *yesterday*.
- **H1B Sponsor Tagging:** Cross-references ~190 known H1B sponsors and tags them in the email.
- **Dual Email Backend:** Supports Gmail SMTP (port 465) and Resend REST API (port 443) for environments with blocked SMTP ports.
- **Deduplication:** Maintains local state via a `seen_jobs_v2.json` file so you are never emailed the same role twice.
- **New Grad Detection:** Auto-promotes "entry level" / "new graduate" bonus matches to primary priority.

## Project Structure

```text
job_aggregator/
├── main.py                    # Core entry point and CLI wrapper
├── discover.py                # ATS company slug discovery tool
├── .env                       # Environment variables (email config)
├── src/
│   ├── config/
│   │   ├── companies.py       # 6,400+ tracked ATS company slugs
│   │   ├── settings.py        # Global configurations & regex patterns
│   │   ├── constants.py       # UI / Icon constants
│   │   └── sponsors.py        # H1B sponsor company list
│   ├── fetchers/
│   │   ├── manager.py         # Async execution controller using concurrent semaphores
│   │   ├── greenhouse.py      # Greenhouse API parser
│   │   ├── lever.py           # Lever API parser
│   │   ├── ashby.py           # Ashby API parser
│   │   ├── workable.py        # Workable widget API parser
│   │   ├── oraclecloud.py     # Oracle Cloud HCM parser
│   │   └── workday.py         # Workday career sites parser
│   ├── filters/
│   │   ├── title.py           # Role matching logic (primary + bonus tiers)
│   │   ├── experience.py      # 0-x years experience analyzer
│   │   ├── clearance.py       # Clearance / citizenship filter
│   │   ├── phd.py             # Education filter
│   │   ├── location.py        # US location filter
│   │   └── date.py            # Posted today/yesterday datetime utility
│   ├── state/
│   │   └── dedup.py           # Deduplication IO cache (MD5 of URL)
│   └── notifications/
│       └── email.py           # SMTP + Resend REST API email delivery
└── seen_jobs_v2.json          # Deduplication ledger (auto-generated)
```

## Setup & Installation

**1. Clone the repository**
```bash
git clone <repository_url>
cd job_aggregator
```

**2. Install dependencies**
```bash
uv sync
```

**3. Configure `.env`**

Create a `.env` file in the project root:

```dotenv
# ── Email Recipients (comma-separated for multiple) ──────────
JOB_ALERT_RECIPIENT_EMAIL="you@gmail.com"

# ── Email Backend ─────────────────────────────────────────────
# "smtp"   → Gmail SMTP on port 465 (local dev / GitHub Actions)
# "resend" → Resend REST API on port 443 (DigitalOcean / blocked SMTP)
EMAIL_BACKEND="smtp"

# ── SMTP Settings (when EMAIL_BACKEND=smtp) ───────────────────
JOB_ALERT_SENDER_EMAIL="you@gmail.com"
JOB_ALERT_SENDER_PASSWORD="your-gmail-app-password"

# ── Resend Settings (when EMAIL_BACKEND=resend) ──────────────
RESEND_API_KEY=""
# Set SENDER_EMAIL to a verified Resend domain address, e.g.:
# JOB_ALERT_SENDER_EMAIL="alerts@yourdomain.com"
```

> **Gmail App Password:** Go to [Google Account → Security → App Passwords](https://myaccount.google.com/apppasswords) to generate one.
>
> **Resend (for DigitalOcean):** Sign up at [resend.com](https://resend.com), verify your domain, and get a free API key (100 emails/day free).

**4. (Optional) Customize search parameters** in `src/config/settings.py`:
- `TITLE_KEYWORDS` / `BONUS_KEYWORDS` — which roles to match
- `MAX_EXPERIENCE_YEARS` — experience cap (default: 2)
- `FILTER_LOCATION_US` — US-only filtering (default: True)
- `FETCH_ONLY_TODAY` — only today's/yesterday's postings (default: True)

## Usage

```bash
# Dry run — fetch & display jobs, no email, no cache update
uv run main.py --dry-run

# Run once — full pipeline, send email, update dedup cache
uv run main.py --once

# Daemon mode — run continuously every CHECK_INTERVAL_MINUTES
uv run main.py

# Test email delivery
uv run main.py --test-email

# Show company stats per platform
uv run main.py --stats
```

## Deployment (DigitalOcean Droplet)

```bash
# SSH into your Droplet
ssh root@<droplet-ip>

# Install dependencies
apt update && apt install -y python3.11 python3.11-venv git
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Clone and setup
cd /opt
git clone <repo-url> job_aggregator
cd job_aggregator
uv sync

# Create .env with Resend backend (SMTP is blocked on DO)
cat > .env << 'EOF'
EMAIL_BACKEND="resend"
RESEND_API_KEY="re_xxxxxxxxxxxx"
JOB_ALERT_SENDER_EMAIL="alerts@yourdomain.com"
JOB_ALERT_RECIPIENT_EMAIL="you@gmail.com"
EOF

# Test
uv run main.py --test-email

# Schedule via cron (every hour at :37)
crontab -e
# Add: 37 * * * * cd /opt/job_aggregator && /root/.local/bin/uv run main.py --once >> /opt/job_aggregator/logs/cron.log 2>&1
```

## Discover New Companies

```bash
# Probe known companies against all ATS platforms
uv run discover.py --method api

# Show community-maintained company lists
uv run discover.py --method github

# Show how to manually find slugs
uv run discover.py --method manual
```
