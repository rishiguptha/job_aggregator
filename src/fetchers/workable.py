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

async def fetch_workable(company: str, session: aiohttp.ClientSession) -> list[dict]:
    """Fetch jobs from Workable public widget API asynchronously."""
    url = f"https://apply.workable.com/api/v1/widget/accounts/{company}"
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

            shortcode = job.get("shortcode", "")
            description = ""
            if shortcode:
                try:
                    detail_url = f"https://apply.workable.com/api/v1/widget/accounts/{company}/jobs/{shortcode}"
                    async with session.get(detail_url, headers=HEADERS, timeout=10) as detail_resp:
                        if detail_resp.ok:
                            detail = await detail_resp.json()
                            description = detail.get("description", "")
                            description = html.unescape(description)
                            description = re.sub(r'<[^>]+>', ' ', description).lower()
                except Exception:
                    pass

            passes, max_exp = passes_experience_filter(description)
            passes_clearance = passes_clearance_filter(description)
            passes_phd = passes_phd_filter(description)
            location = job.get("city", "") or job.get("country", "Unknown")

            posted_at = job.get("published_on", "")
            
            from src.config.settings import settings
            from src.filters.date import is_posted_today, is_posted_yesterday, is_posted_current_year
            if settings.FETCH_ONLY_TODAY and not (is_posted_today(posted_at, "workable") or is_posted_yesterday(posted_at, "workable")):
                continue
            if not settings.FETCH_ONLY_TODAY and not is_posted_current_year(posted_at, "workable"):
                continue

            jobs.append({
                "title": title,
                "company": company,
                "platform": "workable",
                "url": job.get("url", f"https://apply.workable.com/{company}/j/{shortcode}/"),
                "location": location,
                "description": description[:500],
                "experience": max_exp,
                "passes_filter": passes,
                "passes_clearance": passes_clearance,
                "passes_phd": passes_phd,
                "match_type": match_type,
                "posted_at": posted_at,
            })
        return jobs
    except Exception as e:
        log.debug(f"Workable/{company}: {e}")
        return []
