import json
import hashlib
from pathlib import Path
from src.config.settings import settings

def load_seen_jobs() -> set:
    path = Path(settings.SEEN_JOBS_FILE)
    if path.exists():
        with open(path) as f:
            return set(json.load(f))
    return set()

def save_seen_jobs(seen: set):
    with open(settings.SEEN_JOBS_FILE, "w") as f:
        json.dump(list(seen), f)

def job_id(job: dict) -> str:
    return hashlib.md5(job["url"].encode()).hexdigest()
