import aiohttp
from src.config.settings import settings
from src.filters.title import matches_title
from src.filters.experience import passes_experience_filter
from src.filters.clearance import passes_clearance_filter
from src.filters.phd import passes_phd_filter
from src.filters.jd_parser import clean_html, parse_jd_sections
from src.filters.date import is_posted_today, is_posted_current_year
from src.utils.logger import get_logger

log = get_logger(__name__)

HEADERS = {
    "User-Agent": "JobAlertBot/2.0 (Personal job search automation)",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

SEARCH_KEYWORDS = [
    "data engineer",
    "software engineer",
    "software development engineer",
    "ai engineer",
    "machine learning engineer",
    "analytics engineer",
]


async def fetch_workday(company_config: dict, session: aiohttp.ClientSession) -> list[dict]:
    """
    Fetch jobs from Workday career sites.

    company_config should be a dict with:
        - name: display name (e.g., "nvidia")
        - instance: Workday instance (e.g., "nvidia.wd5")
        - site: career site path (e.g., "NVIDIAExternalCareerSite")
    """
    name = company_config["name"]
    instance = company_config["instance"]
    site = company_config["site"]
    company_slug = instance.split(".")[0]

    base_url = f"https://{instance}.myworkdayjobs.com"
    api_url = f"{base_url}/wday/cxs/{company_slug}/{site}/jobs"

    seen_ids = set()
    all_jobs = []

    for keyword in SEARCH_KEYWORDS:
        try:
            payload = {
                "appliedFacets": {},
                "limit": 20,
                "offset": 0,
                "searchText": keyword,
            }

            async with session.post(api_url, json=payload, headers=HEADERS,
                                    timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status in (404, 422):
                    continue
                resp.raise_for_status()
                data = await resp.json()

            postings = data.get("jobPostings", [])

            for job in postings:
                external_path = job.get("externalPath", "")
                if external_path in seen_ids:
                    continue
                seen_ids.add(external_path)

                title = job.get("title", "")
                match_type = matches_title(title)
                if not match_type:
                    continue

                location = job.get("locationsText", "") or ""
                posted_on = job.get("postedOn", "")

                if settings.FETCH_ONLY_TODAY:
                    if posted_on not in ("Posted Today", "Posted Yesterday"):
                        continue

                job_url = f"{base_url}/en-US/{site}{external_path}"

                detail_url = f"https://{instance}.myworkdayjobs.com/wday/cxs/{company_slug}/{site}{external_path}"
                description = ""
                try:
                    async with session.get(detail_url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=10)) as d_resp:
                        if d_resp.status == 200:
                            detail_data = await d_resp.json()
                            job_info = detail_data.get("jobPostingInfo", {})
                            description = job_info.get("jobDescription", "")
                            if not location.strip():
                                location = job_info.get("location", "") or "Unknown"
                except Exception as e:
                    log.debug(f"Workday detail fetch error ({name}): {e}")

                clean_text = clean_html(description).lower() if description else ""
                sections = parse_jd_sections(clean_text) if clean_text else None
                passes_exp, min_exp, exp_level = passes_experience_filter(clean_text, sections=sections) if clean_text else (True, None, "❓ Not Specified")
                passes_cl = passes_clearance_filter(clean_text) if clean_text else True
                passes_p = passes_phd_filter(clean_text) if clean_text else True

                all_jobs.append({
                    "title": title,
                    "company": name,
                    "platform": "workday",
                    "url": job_url,
                    "location": location,
                    "description": clean_text[:500],
                    "experience": min_exp,
                    "passes_filter": passes_exp,
                    "exp_level": exp_level,
                    "passes_clearance": passes_cl,
                    "passes_phd": passes_p,
                    "match_type": match_type,
                    "posted_at": posted_on,
                })

        except Exception as e:
            log.debug(f"Workday/{name} (keyword={keyword}): {e}")
            continue

    return all_jobs
