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
    TITLE_KEYWORDS = ["data engineer", "data engineering", "software development engineer", "software engineer", "software developer", "ai engineer"]
    TITLE_KEYWORDS_REGEX = [r'\bsde\b']  # Short abbreviations needing word-boundary matching
    BONUS_KEYWORDS = ["analytics engineer", "etl engineer", "pipeline engineer", "ml engineer", "machine learning engineer"]
    EXCLUDE_TITLE_PATTERN = r'\b(senior|staff|manager|principal|lead|director|vp|head|president|sr|intern|internship|co-op|coop|ii|iii|iv|v|vi|2|3|4|5|6|mid|mid-level)\b'
    EXCLUDE_CLEARANCE_PATTERN = r'(?<!no\s)(?<!not\s)(?<!without\s)\b(top secret|ts/?sci|polygraph|security clearance|active clearance|top-secret|clearance required|us citizenship(?: required)?|u\.s\. citizen(?:ship)?)\b'
    EXCLUDE_PHD_PATTERN = r'\b(ph\.?d\.?)\b(?!\s+(?:not\s+required|optional|preferred|or\s+equivalent|or\s+master))'
    NEW_GRAD_PATTERN = r'\b(new grad(?:uate)?|recent grad(?:uate)?|university grad(?:uate)?|early career|entry level|entry-level)\b'


    # Filters
    MAX_EXPERIENCE_YEARS = 2
    FILTER_LOCATION_US = True
    FETCH_ONLY_TODAY = True

    # H1B Sponsorship
    H1B_SPONSORS = H1B_SPONSORS

    # App Config
    CHECK_INTERVAL_MINUTES = 60
    SEEN_JOBS_FILE = BASE_DIR / "seen_jobs_v2.json"
    MAX_WORKERS = 40
    ASYNC_SEMAPHORE = 100

settings = Settings()
