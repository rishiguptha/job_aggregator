import aiohttp
import re
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
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
    "Accept": "application/rss+xml, application/xml, text/xml",
}

SEARCH_KEYWORDS = [
    "data engineer",
    "software engineer",
    "software development engineer",
    "ai engineer",
    "machine learning engineer",
    "analytics engineer",
]


def _rfc2822_to_iso(date_str: str) -> str:
    """Convert RFC 2822 date (from RSS pubDate) to ISO 8601 for the date filter."""
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.isoformat()
    except Exception:
        return date_str


async def fetch_successfactors(company_config: dict, session: aiohttp.ClientSession) -> list[dict]:
    """
    Fetch jobs from SAP SuccessFactors career sites via public RSS feed.

    company_config should be a dict with:
        - name: company display name (e.g., "sap")
        - domain: career site domain (e.g., "jobs.sap.com")
    """
    name = company_config["name"]
    domain = company_config["domain"]

    seen_urls = set()
    all_jobs = []

    for keyword in SEARCH_KEYWORDS:
        try:
            url = f"https://{domain}/services/rss/job/?locale=en_US&keywords=({keyword})"

            async with session.get(url, headers=HEADERS,
                                   timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status == 404:
                    continue
                resp.raise_for_status()
                text = await resp.text()

            root = ET.fromstring(text)
            channel = root.find("channel")
            if channel is None:
                continue

            for item in channel.findall("item"):
                title_el = item.find("title")
                link_el = item.find("link")
                pub_el = item.find("pubDate")
                desc_el = item.find("description")

                title = title_el.text.strip() if title_el is not None and title_el.text else ""
                job_url = link_el.text.strip() if link_el is not None and link_el.text else ""

                if not title or not job_url:
                    continue
                if job_url in seen_urls:
                    continue
                seen_urls.add(job_url)

                # Strip parenthetical location suffix before title matching—
                # SuccessFactors titles look like "Data Engineer (City, State, Country, 12345)"
                # and postal codes/numbers would trigger the exclude pattern.
                loc_match = re.search(r'\(([^)]+)\)\s*$', title)
                location = loc_match.group(1) if loc_match else "Unknown"
                clean_title = title[:loc_match.start()].strip() if loc_match else title

                match_type = matches_title(clean_title)
                if not match_type:
                    continue

                raw_date = pub_el.text.strip() if pub_el is not None and pub_el.text else ""
                posted_at = _rfc2822_to_iso(raw_date)

                if not passes_date_filter(posted_at, "successfactors"):
                    continue

                description_html = desc_el.text if desc_el is not None and desc_el.text else ""
                clean_text = clean_html(description_html).lower() if description_html else ""
                sections = parse_jd_sections(clean_text) if clean_text else None

                passes_exp, min_exp, exp_level, confidence = passes_experience_filter(clean_text, sections=sections) if clean_text else (True, None, "❓ Not Specified", 1.0)
                passes_cl = passes_clearance_filter(clean_text) if clean_text else True
                passes_p = passes_phd_filter(clean_text) if clean_text else True

                job_dict = {
                    "title": title,
                    "company": name,
                    "platform": "successfactors",
                    "url": job_url,
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
                if clean_text:
                    job_dict["_jd_excerpt"] = clean_text[:2000]
                all_jobs.append(job_dict)

        except ET.ParseError as e:
            log.debug(f"SuccessFactors/{name} RSS parse error (keyword={keyword}): {e}")
            continue
        except Exception as e:
            log.debug(f"SuccessFactors/{name} (keyword={keyword}): {e}")
            continue

    return all_jobs
