import aiohttp
import re
import html
from src.filters.title import matches_title
from src.filters.experience import passes_experience_filter
from src.filters.clearance import passes_clearance_filter
from src.filters.phd import passes_phd_filter
from src.utils.logger import get_logger

log = get_logger(__name__)

HEADERS = {
    "User-Agent": "JobAlertBot/2.0 (Personal job search automation)",
    "Accept": "application/json",
}

async def fetch_ashby(company: str, session: aiohttp.ClientSession) -> list[dict]:
    """Fetch jobs from Ashby public API asynchronously."""
    url = f"https://api.ashbyhq.com/posting-api/job-board/{company}"
    try:
        async with session.get(url, headers=HEADERS, timeout=15) as resp:
            if resp.status == 404:
                return []
            resp.raise_for_status()
            data = await resp.json()

        jobs = []
        for job in data.get("jobs", []):
            title = job.get("title", "")
            match_type = matches_title(title)
            if not match_type:
                continue

            desc_plain = job.get("descriptionPlain", "") or ""
            desc_html = job.get("descriptionHtml", "") or ""
            # Prioritize HTML description if available, otherwise use plain text
            description_content = desc_html if desc_html else desc_plain
            description = html.unescape(description_content)
            clean_desc = re.sub(r'<[^>]+>', ' ', description).lower()
            passes, min_exp, exp_level = passes_experience_filter(clean_desc)
            passes_clearance = passes_clearance_filter(clean_desc)
            passes_phd = passes_phd_filter(clean_desc)

            # Location format can be a string or object
            loc_data = job.get("location", "Unknown")
            if isinstance(loc_data, dict):
                location = loc_data.get("name", "Unknown")
            else:
                location = str(loc_data)

            # Extract posted date
            posted_at = job.get("publishedAt", "")
            
            from src.config.settings import settings
            from src.filters.date import is_posted_today, is_posted_yesterday, is_posted_current_year
            if settings.FETCH_ONLY_TODAY and not (is_posted_today(posted_at, "ashby") or is_posted_yesterday(posted_at, "ashby")):
                continue
            if not settings.FETCH_ONLY_TODAY and not is_posted_current_year(posted_at, "ashby"):
                continue

            jobs.append({
                "title": title,
                "company": company,
                "platform": "ashby",
                "url": job.get("jobUrl", f"https://jobs.ashbyhq.com/{company}/{job.get('id','')}"),
                "location": location,
                "description": clean_desc[:500],
                "experience": min_exp,
                "passes_filter": passes,
                "exp_level": exp_level,
                "passes_clearance": passes_clearance,
                "passes_phd": passes_phd,
                "match_type": match_type,
                "posted_at": posted_at,
            })
        return jobs
    except Exception as e:
        log.debug(f"Ashby/{company}: {e}")
        return []
