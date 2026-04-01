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

            desc_html = job.get("descriptionHtml", "") or ""
            desc_plain = job.get("descriptionPlain", "") or ""
            description_content = desc_html if desc_html else desc_plain
            clean_desc = clean_html(description_content).lower()
            sections = parse_jd_sections(clean_desc)
            passes, min_exp, exp_level, confidence = passes_experience_filter(clean_desc, sections=sections)
            passes_clearance = passes_clearance_filter(clean_desc)
            passes_phd = passes_phd_filter(clean_desc)

            loc_data = job.get("location", "Unknown")
            if isinstance(loc_data, dict):
                location = loc_data.get("name", "Unknown")
            else:
                location = str(loc_data)

            posted_at = job.get("publishedAt", "")

            from src.config.settings import settings
            from src.filters.date import passes_date_filter
            if not passes_date_filter(posted_at, "ashby"):
                continue

            job_dict = {
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
                "confidence": confidence,
            }
            job_dict["_jd_excerpt"] = clean_desc[:2000]
            jobs.append(job_dict)
        return jobs
    except Exception as e:
        log.debug(f"Ashby/{company}: {e}")
        return []
