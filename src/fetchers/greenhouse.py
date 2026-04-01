import aiohttp
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

async def fetch_greenhouse(company: str, session: aiohttp.ClientSession) -> list[dict]:
    """Fetch jobs from Greenhouse public API asynchronously."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true"
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

            content = job.get("content", "")
            clean_content = clean_html(content).lower()
            sections = parse_jd_sections(clean_content)
            passes, min_exp, exp_level, confidence = passes_experience_filter(clean_content, sections=sections)
            passes_clearance = passes_clearance_filter(clean_content)
            passes_phd = passes_phd_filter(clean_content)

            posted_at = job.get("first_published_at") or job.get("updated_at", "")

            from src.config.settings import settings
            from src.filters.date import passes_date_filter
            if not passes_date_filter(posted_at, "greenhouse"):
                continue

            job_dict = {
                "title": title,
                "company": company,
                "platform": "greenhouse",
                "url": f"https://boards.greenhouse.io/{company}/jobs/{job.get('id', '')}",
                "location": job.get("location", {}).get("name", "Unknown"),
                "description": clean_content[:500],
                "experience": min_exp,
                "passes_filter": passes,
                "exp_level": exp_level,
                "passes_clearance": passes_clearance,
                "passes_phd": passes_phd,
                "match_type": match_type,
                "posted_at": posted_at,
                "confidence": confidence,
            }
            job_dict["_jd_excerpt"] = clean_content[:2000]
            jobs.append(job_dict)
        return jobs
    except Exception as e:
        log.debug(f"Greenhouse/{company}: {e}")
        return []
