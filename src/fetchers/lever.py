import aiohttp
from datetime import datetime, timezone
from src.filters.title import matches_title
from src.filters.experience import passes_experience_filter
from src.filters.clearance import passes_clearance_filter
from src.filters.phd import passes_phd_filter
from src.filters.jd_parser import clean_html, parse_jd_sections
from src.utils.logger import get_logger

log = get_logger(__name__)

HEADERS = {
    "User-Agent": "JobAlertBot/2.0 (Personal job search automation)",
    "Accept": "application/json",
}

async def fetch_lever(company: str, session: aiohttp.ClientSession) -> list[dict]:
    """Fetch jobs from Lever public API asynchronously."""
    url = f"https://api.lever.co/v0/postings/{company}?mode=json"
    try:
        async with session.get(url, headers=HEADERS, timeout=15) as resp:
            if resp.status == 404:
                return []
            resp.raise_for_status()
            data = await resp.json()
        if not isinstance(data, list):
            return []

        jobs = []
        for job in data:
            title = job.get("text", "")
            match_type = matches_title(title)
            if not match_type:
                continue

            desc = job.get("descriptionPlain", "") or job.get("description", "")
            additional = job.get("additionalPlain", "") or job.get("additional", "")
            full_text = f"{desc} {additional}"
            clean_text = clean_html(full_text).lower()
            sections = parse_jd_sections(clean_text)
            passes, min_exp, exp_level, confidence = passes_experience_filter(clean_text, sections=sections)
            passes_clearance = passes_clearance_filter(clean_text)
            passes_phd = passes_phd_filter(clean_text)

            location = job.get("categories", {}).get("location", "Unknown")

            posted_at = ""
            created_at_ms = job.get("createdAt")
            if created_at_ms:
                try:
                    dt = datetime.fromtimestamp(created_at_ms / 1000.0, tz=timezone.utc)
                    posted_at = dt.isoformat()
                except (ValueError, TypeError):
                    pass

            from src.config.settings import settings
            from src.filters.date import passes_date_filter
            if not passes_date_filter(posted_at, "lever"):
                continue

            job_dict = {
                "title": title,
                "company": company,
                "platform": "lever",
                "url": job.get("hostedUrl", f"https://jobs.lever.co/{company}/{job.get('id','')}"),
                "location": location,
                "description": clean_text[:500],
                "experience": min_exp,
                "passes_filter": passes,
                "exp_level": exp_level,
                "passes_clearance": passes_clearance,
                "passes_phd": passes_phd,
                "match_type": match_type,
                "posted_at": posted_at,
                "confidence": confidence,
            }
            if confidence < 0.4 or exp_level == "❓ Not Specified":
                req = (sections.get("required", "") if sections else "") or clean_text
                job_dict["_jd_excerpt"] = req[:2000]
            jobs.append(job_dict)
        return jobs
    except Exception as e:
        log.debug(f"Lever/{company}: {e}")
        return []
