import aiohttp
from src.config.settings import settings
from src.filters.title import matches_title
from src.filters.experience import passes_experience_filter
from src.filters.clearance import passes_clearance_filter
from src.filters.phd import passes_phd_filter
from src.filters.jd_parser import clean_html, parse_jd_sections
from src.filters.date import passes_date_filter
from src.utils.logger import get_logger

log = get_logger(__name__)

HEADERS = {
    "User-Agent": "JobAlertBot/2.0 (Personal job search automation)",
    "Accept": "application/json",
}

SEARCH_KEYWORDS = [
    "data engineer",
    "software engineer",
    "software development engineer",
    "ai engineer",
    "machine learning engineer",
    "analytics engineer",
]


async def fetch_smartrecruiters(company: str, session: aiohttp.ClientSession) -> list[dict]:
    """
    Fetch jobs from SmartRecruiters public Posting API.

    company is the company identifier from the career site URL
    (e.g., "ServiceNow" from https://careers.smartrecruiters.com/ServiceNow).
    """
    base_url = f"https://api.smartrecruiters.com/v1/companies/{company}/postings"

    seen_ids = set()
    all_jobs = []

    for keyword in SEARCH_KEYWORDS:
        try:
            url = f"{base_url}?q={keyword}&limit=100&offset=0"

            async with session.get(url, headers=HEADERS,
                                   timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status == 404:
                    continue
                resp.raise_for_status()
                data = await resp.json()

            postings = data.get("content", [])

            for posting in postings:
                posting_id = posting.get("id", "")
                if posting_id in seen_ids:
                    continue
                seen_ids.add(posting_id)

                title = posting.get("name", "")
                match_type = matches_title(title)
                if not match_type:
                    continue

                posted_at = posting.get("releasedDate", "")

                if not passes_date_filter(posted_at, "smartrecruiters"):
                    continue

                location_obj = posting.get("location", {})
                location = location_obj.get("fullLocation", "") or location_obj.get("city", "Unknown")

                posting_url = posting.get("ref", f"{base_url}/{posting_id}")
                job_page_url = f"https://jobs.smartrecruiters.com/{company}/{posting_id}"

                description = ""
                try:
                    async with session.get(posting_url, headers=HEADERS,
                                           timeout=aiohttp.ClientTimeout(total=10)) as d_resp:
                        if d_resp.status == 200:
                            detail = await d_resp.json()
                            sections = detail.get("jobAd", {}).get("sections", {})
                            parts = []
                            for key in ("jobDescription", "qualifications", "additionalInformation"):
                                section = sections.get(key, {})
                                text = section.get("text", "")
                                if text:
                                    parts.append(text)
                            description = " ".join(parts)
                except Exception as e:
                    log.debug(f"SmartRecruiters detail fetch error ({company}/{posting_id}): {e}")

                clean_text = clean_html(description).lower() if description else ""
                sections = parse_jd_sections(clean_text) if clean_text else None
                passes_exp, min_exp, exp_level, confidence = passes_experience_filter(clean_text, sections=sections) if clean_text else (True, None, "❓ Not Specified", 1.0)
                passes_cl = passes_clearance_filter(clean_text) if clean_text else True
                passes_p = passes_phd_filter(clean_text) if clean_text else True

                job_dict = {
                    "title": title,
                    "company": company,
                    "platform": "smartrecruiters",
                    "url": job_page_url,
                    "location": location,
                    "description": clean_text[:500],
                    "experience": min_exp,
                    "passes_filter": passes_exp,
                    "exp_level": exp_level,
                    "passes_clearance": passes_cl,
                    "passes_phd": passes_p,
                    "match_type": match_type,
                    "posted_at": posted_at,
                    "confidence": confidence,
                }
                if (confidence < 0.4 or exp_level == "❓ Not Specified") and clean_text:
                    req = (sections.get("required", "") if sections else "") or clean_text
                    job_dict["_jd_excerpt"] = req[:2000]
                all_jobs.append(job_dict)

        except Exception as e:
            log.debug(f"SmartRecruiters/{company} (keyword={keyword}): {e}")
            continue

    return all_jobs
