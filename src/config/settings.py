import os
from pathlib import Path

# Base working directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings:
    # Email Config
    SENDER_EMAIL = os.getenv("JOB_ALERT_SENDER_EMAIL", "rishiguptha.mankala@gmail.com")
    SENDER_PASSWORD = os.getenv("JOB_ALERT_SENDER_PASSWORD", "ekiyognydkdvxned")
    RECIPIENT_EMAIL = os.getenv("JOB_ALERT_RECIPIENT_EMAIL", "rishiguptha.mankala@gmail.com")

    # Job Keywords
    TITLE_KEYWORDS = ["data engineer", "data engineering"]
    BONUS_KEYWORDS = ["analytics engineer", "etl engineer", "pipeline engineer"]
    EXCLUDE_TITLE_PATTERN = r'\b(senior|staff|manager|principal|lead|director|vp|head|president|sr|intern|internship|co-op|coop)\b'
    EXCLUDE_CLEARANCE_PATTERN = r'(?<!no\s)(?<!not\s)(?<!without\s)\b(top secret|ts/?sci|polygraph|security clearance|active clearance|top-secret|clearance required|us citizenship(?: required)?|u\.s\. citizen(?:ship)?)\b'
    EXCLUDE_PHD_PATTERN = r'\b(ph\.?d\.?)\b(?!\s+(?:not\s+required|optional|preferred|or\s+equivalent|or\s+master))'
    NEW_GRAD_PATTERN = r'\b(new grad(?:uate)?|recent grad(?:uate)?|university grad(?:uate)?|early career|entry level|entry-level)\b'


    # Filters
    MAX_EXPERIENCE_YEARS = 2
    FILTER_LOCATION_US = True
    FETCH_ONLY_TODAY = True

    # App Config
    CHECK_INTERVAL_MINUTES = 60
    SEEN_JOBS_FILE = BASE_DIR / "seen_jobs_v2.json"
    MAX_WORKERS = 40
    ASYNC_SEMAPHORE = 100

settings = Settings()
