import json
import hashlib
import re
from pathlib import Path
from src.config.settings import settings

def load_seen_jobs() -> set:
    path = Path(settings.SEEN_JOBS_FILE)
    if path.exists():
        try:
            with open(path) as f:
                return set(json.load(f))
        except (json.JSONDecodeError, ValueError):
            return set()
    return set()

def save_seen_jobs(seen: set):
    with open(settings.SEEN_JOBS_FILE, "w") as f:
        json.dump(list(seen), f)

def job_id(job: dict) -> str:
    return hashlib.md5(job["url"].encode()).hexdigest()


# ── Repost Detection ──────────────────────────────────────────────────────────

def _repost_key(job: dict) -> str:
    """Stable key based on normalized title + company (URL-independent)."""
    title = re.sub(r'\W+', '', job.get("title", "").lower())
    company = re.sub(r'\W+', '', job.get("company", "").lower())
    return hashlib.md5(f"{title}|{company}".encode()).hexdigest()

def load_repost_index() -> dict:
    """Load {repost_key: first_seen_date_str} mapping from disk."""
    path = Path(settings.REPOST_FILE)
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            return {}
    return {}

def save_repost_index(index: dict):
    with open(settings.REPOST_FILE, "w") as f:
        json.dump(index, f)

def is_repost(job: dict, repost_index: dict, today_str: str) -> bool:
    """Return True if this title+company was seen on a PREVIOUS day (not today)."""
    key = _repost_key(job)
    if key not in repost_index:
        return False
    return repost_index[key] != today_str  # same day = not a repost

def record_in_repost_index(job: dict, repost_index: dict, date_str: str):
    """Record title+company as seen (only if not already tracked)."""
    key = _repost_key(job)
    if key not in repost_index:
        repost_index[key] = date_str
