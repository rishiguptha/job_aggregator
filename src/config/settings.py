import os
from pathlib import Path
from dotenv import load_dotenv

# Base working directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

from src.config.sponsors import H1B_SPONSORS

class Settings:
    # Email Config
    SENDER_EMAIL = os.getenv("JOB_ALERT_SENDER_EMAIL", "")
    SENDER_PASSWORD = os.getenv("JOB_ALERT_SENDER_PASSWORD", "")
    _recipients_str = os.getenv("JOB_ALERT_RECIPIENT_EMAIL", "")
    RECIPIENT_EMAILS = [email.strip() for email in _recipients_str.split(",") if email.strip()]

    # Email Backend: "smtp" (default, works locally/GitHub Actions) or "resend" (works on DO)
    EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "smtp")
    RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
    # Job Keywords

    TITLE_KEYWORDS = [
        # Core DE titles
        "data engineer", "data engineering",
        "analytics engineer",
        "etl developer", "etl engineer",
        "data platform engineer",
        "data pipeline engineer",
        "cloud data engineer",
        "data warehouse engineer",
        "ml data engineer",
        # SWE titles
        "software development engineer", "software engineer", "software developer",
        "backend engineer", "backend developer",
        # AI / ML titles (primary — ranked #3)
        "ai engineer", "ml engineer", "machine learning engineer",
        "ai/ml engineer", "applied ml engineer", "applied ai engineer",
    ]

    TITLE_KEYWORDS_REGEX = [
        r'\bsde\b',
        r'\bswe\b',       # "SWE New Grad", "New Grad SWE"
        r'\bde\b',        # "DE I", "DE II" job posts
        r'\betl\b',       # standalone ETL posts
        r'\bmle\b',       # "MLE" abbreviation for ML Engineer
    ]

    BONUS_KEYWORDS = [
        # Fullstack/frontend — bonus; auto-promoted to primary if title has new-grad/entry-level language
        "fullstack engineer", "full stack engineer", "full-stack engineer",
        "fullstack developer", "full stack developer", "full-stack developer",
        "frontend engineer", "front end engineer", "front-end engineer",
        "frontend developer", "front end developer", "front-end developer",
        # Analytics / platform / infra — lowest priority bonus
        "platform engineer",
        "infrastructure engineer",
        "data infrastructure engineer",
        "data integration engineer",
        "data operations engineer",
        "data catalog engineer",
    ]

    EXCLUDE_TITLE_PATTERN = r'\b(senior|staff|manager|principal|lead|director|vp|head|president|sr|intern|internship|co-op|coop|ii|iii|iv|v|vi|2|3|4|5|6|mid|mid-level)\b'

    EXCLUDE_CLEARANCE_PATTERN = r'(?<!no\s)(?<!not\s)(?<!without\s)\b(top secret|ts/?sci|polygraph|security clearance|active clearance|top-secret|clearance required|us citizenship(?: required)?|u\.s\. citizen(?:ship)?)\b'

    EXCLUDE_PHD_PATTERN = r'\b(ph\.?d\.?)\b(?!\s+(?:not\s+required|optional|preferred|or\s+equivalent|or\s+master))'

    NEW_GRAD_PATTERN = r'\b(new grad(?:uate)?|recent grad(?:uate)?|university grad(?:uate)?|early career|entry level|entry-level|associate engineer|engineer i)\b'

    # Filters
    MAX_EXPERIENCE_YEARS = 2
    FILTER_LOCATION_US = True   # filter to US-only (remote/hybrid/onsite within US)
    FETCH_ONLY_TODAY = True
    TODAY_ONLY = False  # strict today-only mode (no yesterday), toggled by --today CLI flag

    # H1B Sponsorship
    H1B_SPONSORS = H1B_SPONSORS

    # LLM Recheck (optional — omit API key to disable)
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_MODEL = os.getenv("LLM_MODEL", "")
    LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "30"))
    LLM_CONFIDENCE_THRESHOLD = float(os.getenv("LLM_CONFIDENCE_THRESHOLD", "0.4"))

    # App Config
    CHECK_INTERVAL_MINUTES = 60
    SEEN_JOBS_FILE = BASE_DIR / "seen_jobs_v2.json"
    REPOST_FILE = BASE_DIR / "seen_jobs_repost.json"
    MAX_WORKERS = 40
    ASYNC_SEMAPHORE = 100

settings = Settings()
