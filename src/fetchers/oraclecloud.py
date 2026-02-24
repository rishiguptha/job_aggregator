import aiohttp
import re
import html
from src.config.settings import settings
from src.filters.title import matches_title
from src.filters.experience import passes_experience_filter
from src.filters.clearance import passes_clearance_filter
from src.filters.phd import passes_phd_filter
from src.filters.date import is_posted_today, is_posted_yesterday, is_posted_current_year
from src.utils.logger import get_logger

log = get_logger(__name__)

HEADERS = {
    "User-Agent": "JobAlertBot/2.0 (Personal job search automation)",
    "Accept": "application/json",
}

# Search keywords to query the Oracle API with (API does server-side keyword search)
SEARCH_KEYWORDS = [
    "data engineer",
    "software engineer",
    "software development engineer",
    "ai engineer",
    "machine learning engineer",
    "analytics engineer",
]

async def fetch_oraclecloud(company_config: dict, session: aiohttp.ClientSession) -> list[dict]:
    """
    Fetch jobs from Oracle Cloud HCM Candidate Experience API.
    
    company_config should be a dict with:
        - name: company display name
        - subdomain + region: Oracle Cloud endpoint (e.g., subdomain="eeho", region="us2")
          OR
        - domain: custom career domain that proxies to Oracle Cloud (e.g., "careers.autozone.com")
        - site: career site number (default: "CX_1")
    """
    name = company_config["name"]
    site = company_config.get("site", "CX_1")

    # Support both direct Oracle Cloud URLs and custom proxied domains
    if "domain" in company_config:
        domain = company_config["domain"]
        base_url = f"https://{domain}/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
        job_base_url = f"https://{domain}/hcmUI/CandidateExperience/en/sites/{site}/job"
    else:
        subdomain = company_config["subdomain"]
        region = company_config["region"]
        base_url = f"https://{subdomain}.fa.{region}.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
        job_base_url = f"https://{subdomain}.fa.{region}.oraclecloud.com/hcmUI/CandidateExperience/en/sites/{site}/job"
    seen_ids = set()
    all_jobs = []

    for keyword in SEARCH_KEYWORDS:
        try:
            # Build URL manually to avoid double-encoding in finder param
            finder = f"findReqs;siteNumber={site},keyword={keyword},locationId=,locationLevel=,workplaceTypeCode=,unitId="
            url = f"{base_url}?onlyData=true&expand=requisitionList.secondaryLocations&finder={finder}&limit=25&offset=0"

            async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status == 404:
                    continue
                resp.raise_for_status()
                data = await resp.json()

            items = data.get("items", [])
            if not items:
                continue

            requisitions = items[0].get("requisitionList", [])

            for job in requisitions:
                job_id = job.get("Id", "")
                if job_id in seen_ids:
                    continue
                seen_ids.add(job_id)

                title = job.get("Title", "")
                match_type = matches_title(title)
                if not match_type:
                    continue

                # Build description from available fields
                desc_parts = []
                for field in ["ShortDescriptionStr", "ExternalQualificationsStr", "ExternalResponsibilitiesStr"]:
                    val = job.get(field)
                    if val:
                        desc_parts.append(val)
                description = " ".join(desc_parts)
                description = html.unescape(description)
                clean_desc = re.sub(r'<[^>]+>', ' ', description).lower()

                passes, max_exp = passes_experience_filter(clean_desc)
                passes_clearance = passes_clearance_filter(clean_desc)
                passes_phd = passes_phd_filter(clean_desc)

                location = job.get("PrimaryLocation", "Unknown")
                posted_at = job.get("PostedDate", "")

                # Date filtering
                if settings.FETCH_ONLY_TODAY and not (is_posted_today(posted_at, "oraclecloud") or is_posted_yesterday(posted_at, "oraclecloud")):
                    continue
                if not settings.FETCH_ONLY_TODAY and not is_posted_current_year(posted_at, "oraclecloud"):
                    continue

                job_url = f"{job_base_url}/{job_id}"

                all_jobs.append({
                    "title": title,
                    "company": name,
                    "platform": "oraclecloud",
                    "url": job_url,
                    "location": location,
                    "description": clean_desc[:500],
                    "experience": max_exp,
                    "passes_filter": passes,
                    "passes_clearance": passes_clearance,
                    "passes_phd": passes_phd,
                    "match_type": match_type,
                    "posted_at": posted_at,
                })

        except Exception as e:
            log.debug(f"OracleCloud/{name} (keyword={keyword}): {e}")
            continue

    return all_jobs
