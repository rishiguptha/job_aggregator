import asyncio
import aiohttp
from src.config.settings import settings
from src.config.companies import COMPANY_SLUGS
from src.fetchers.greenhouse import fetch_greenhouse
from src.fetchers.lever import fetch_lever
from src.fetchers.ashby import fetch_ashby
from src.fetchers.workable import fetch_workable
from src.fetchers.oraclecloud import fetch_oraclecloud
from src.utils.logger import get_logger

log = get_logger(__name__)

FETCHERS = {
    "greenhouse": fetch_greenhouse,
    "lever": fetch_lever,
    "ashby": fetch_ashby,
    "workable": fetch_workable,
}

async def fetch_with_semaphore(semaphore, fetcher, platform, company, session):
    """Wrapper to limit concurrency with a semaphore."""
    async with semaphore:
        try:
            jobs = await fetcher(company, session)
            if jobs:
                company_name = company if isinstance(company, str) else company.get("name", "unknown")
                log.info(f"  ✅ {platform}/{company_name}: {len(jobs)} matching job(s)")
            return jobs
        except Exception as e:
            company_name = company if isinstance(company, str) else company.get("name", "unknown")
            log.debug(f"  ❌ {platform}/{company_name}: {e}")
            return []

async def fetch_all_jobs() -> list[dict]:
    """Fetch jobs from all platforms in parallel asynchronously."""
    all_jobs = []
    tasks = []

    semaphore = asyncio.Semaphore(settings.ASYNC_SEMAPHORE)
    conn = aiohttp.TCPConnector(limit=settings.ASYNC_SEMAPHORE)

    async with aiohttp.ClientSession(connector=conn) as session:
        for platform, companies in COMPANY_SLUGS.items():
            if platform == "oraclecloud":
                # Oracle Cloud uses dict-based configs and its own fetcher
                for company_config in companies:
                    tasks.append(fetch_with_semaphore(semaphore, fetch_oraclecloud, platform, company_config, session))
            else:
                fetcher = FETCHERS.get(platform)
                if not fetcher:
                    continue
                for company in companies:
                    tasks.append(fetch_with_semaphore(semaphore, fetcher, platform, company, session))
                
        log.info(f"Querying {len(tasks)} company endpoints across {len(COMPANY_SLUGS)} platforms concurrently...")

        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list) and result:
                all_jobs.extend(result)

    return all_jobs

