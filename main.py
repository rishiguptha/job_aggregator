import argparse
import resource
import time
from datetime import datetime

soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
resource.setrlimit(resource.RLIMIT_NOFILE, (min(hard, 4096), hard))
from src.config.settings import settings
from src.config.companies import COMPANY_SLUGS
from src.config.constants import PLATFORM_ICONS
from src.fetchers.manager import fetch_all_jobs
from src.state.dedup import load_seen_jobs, save_seen_jobs, job_id
from src.notifications.email import send_email
from src.filters.llm_recheck import llm_classify_jobs
from src.utils.logger import get_logger

log = get_logger(__name__)

import asyncio
import aiohttp

async def run_pipeline():
    t_start = time.perf_counter()
    log.info("=" * 60)
    log.info(f"Job Alert v2 — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    log.info(f"Tracking {sum(len(v) for v in COMPANY_SLUGS.values())} companies "
             f"across {len(COMPANY_SLUGS)} platforms")

    seen = load_seen_jobs()
    all_jobs = await fetch_all_jobs()
    t_fetch = time.perf_counter()
    log.info(f"Found {len(all_jobs)} title-matched jobs across all platforms")

    new_jobs = []
    unclassified_jobs = []
    borderline_jobs = []
    filtered_exp = 0
    filtered_loc = 0
    filtered_clearance = 0
    filtered_phd = 0
    for job in all_jobs:
        jid = job_id(job)
        if jid in seen:
            continue
        seen.add(jid)

        from src.filters.location import passes_location_filter
        if not passes_location_filter(job["location"]):
            filtered_loc += 1
            log.info(f"  🚫 Filtered (Loc): {job['title']} @ {job['company']} "
                     f"({job['location']})")
            continue

        if not job.get("passes_clearance", True):
            filtered_clearance += 1
            log.info(f"  🚫 Filtered (Clearance/Citizenship): {job['title']} @ {job['company']}")
            continue

        if not job.get("passes_phd", True):
            filtered_phd += 1
            log.info(f"  🚫 Filtered (PhD Required): {job['title']} @ {job['company']}")
            continue

        if job["passes_filter"]:
            if job.get("exp_level") == "❓ Not Specified":
                unclassified_jobs.append(job)
            else:
                new_jobs.append(job)
        else:
            confidence = job.get("confidence", 1.0)
            if confidence < settings.LLM_CONFIDENCE_THRESHOLD:
                borderline_jobs.append(job)
                log.info(f"  🔍 Borderline (conf={confidence:.2f}): {job['title']} @ {job['company']} "
                         f"({job.get('exp_level', '?')} — requires {job['experience']}+ yrs)")
            else:
                filtered_exp += 1
                log.info(f"  🚫 Filtered (Exp): {job['title']} @ {job['company']} "
                         f"({job.get('exp_level', '?')} — requires {job['experience']}+ yrs)")

    t_filter = time.perf_counter()

    # LLM classification: enrich unclassified + recover borderline
    llm_enriched = 0
    llm_recovered = 0
    llm_filtered = 0
    llm_batch = unclassified_jobs + borderline_jobs
    if llm_batch and settings.LLM_API_KEY:
        log.info(f"Sending {len(llm_batch)} jobs to LLM "
                 f"({len(unclassified_jobs)} unclassified + {len(borderline_jobs)} borderline)...")
        async with aiohttp.ClientSession() as llm_session:
            llm_batch = await llm_classify_jobs(llm_batch, llm_session)

        for job in llm_batch:
            has_llm = "llm_level" in job
            if has_llm and (job.get("llm_clearance") or job.get("llm_phd")):
                filtered_exp += 1
                flag = "clearance" if job.get("llm_clearance") else "PhD"
                log.info(f"  🚫 LLM filtered ({flag}): {job['title']} @ {job['company']}")
                continue
            if has_llm and not job.get("llm_suitable"):
                filtered_exp += 1
                llm_filtered += 1
                log.info(f"  🚫 LLM filtered (Exp): {job['title']} @ {job['company']} "
                         f"({job.get('llm_level', '?')} — {job.get('llm_min_years', '?')}+ yrs)")
                continue

            # LLM says suitable (or LLM failed, fall back to regex)
            if has_llm:
                job["exp_level"] = job["llm_level"] + " (LLM)"
                if job["llm_min_years"] is not None:
                    job["experience"] = job["llm_min_years"]
                if job in unclassified_jobs:
                    llm_enriched += 1
                else:
                    llm_recovered += 1
            new_jobs.append(job)

        log.info(f"LLM results: {llm_enriched} enriched, {llm_recovered} recovered, {llm_filtered} filtered out")
    else:
        new_jobs.extend(unclassified_jobs)
        filtered_exp += len(borderline_jobs)

    t_llm = time.perf_counter()

    log.info(f"Passed: {len(new_jobs)} | Exp: {filtered_exp} | Loc: {filtered_loc} "
             f"| Clearance: {filtered_clearance} | PhD: {filtered_phd}"
             + (f" | LLM: +{llm_recovered} -{llm_filtered} ~{llm_enriched}" if llm_batch and settings.LLM_API_KEY else ""))
    new_jobs.sort(key=lambda j: (0 if j["match_type"] == "primary" else 1, j["company"]))

    if new_jobs:
        send_email(new_jobs)
    else:
        log.info("No new jobs this cycle.")

    save_seen_jobs(seen)
    t_end = time.perf_counter()

    log.info(
        f"⏱ Timing: fetch={t_fetch - t_start:.1f}s | "
        f"filter={t_filter - t_fetch:.1f}s | "
        f"llm={t_llm - t_filter:.1f}s | "
        f"email+save={t_end - t_llm:.1f}s | "
        f"total={t_end - t_start:.1f}s"
    )
    log.info("Pipeline complete.\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-ATS Data Engineer Job Alerts v2")
    parser.add_argument("--once", action="store_true", help="Run once (for cron)")
    parser.add_argument("--test-email", action="store_true", help="Send test email")
    parser.add_argument("--dry-run", action="store_true", help="Fetch & show jobs, no email")
    parser.add_argument("--stats", action="store_true", help="Show company counts per platform")
    parser.add_argument("--today", action="store_true", help="Only fetch jobs posted today (skip yesterday)")
    args = parser.parse_args()

    if args.today:
        settings.TODAY_ONLY = True

    if args.stats:
        for platform, companies in COMPANY_SLUGS.items():
            print(f"  {PLATFORM_ICONS.get(platform, '📋')} {platform}: {len(companies)} companies")
        print(f"  Total: {sum(len(v) for v in COMPANY_SLUGS.values())} companies")

    elif args.test_email:
        send_email([{
            "title": "Data Engineer (Test)",
            "company": "test-company",
            "platform": "greenhouse",
            "url": "https://boards.greenhouse.io/test",
            "location": "Remote",
            "description": "Test alert to verify email delivery.",
            "experience": 1,
            "passes_filter": True,
            "match_type": "primary",
            "posted_at": "",
        }])

    elif args.dry_run:
        from src.filters.location import passes_location_filter
        all_jobs = asyncio.run(fetch_all_jobs())
        passed = [j for j in all_jobs if j["passes_filter"] and passes_location_filter(j["location"]) and j.get("passes_clearance", True) and j.get("passes_phd", True)]
        print(f"\n{'='*60}")
        print(f"Found {len(all_jobs)} matching jobs | {len(passed)} pass exp/loc/clearance/phd filters\n")
        for j in passed:
            icon = PLATFORM_ICONS.get(j["platform"], "")
            exp = f"{j['experience']} yrs" if j["experience"] else "n/a"
            exp_level = j.get("exp_level", "❓")
            posted = f" | Posted: {j['posted_at'][:10]}" if j.get("posted_at") else ""
            print(f"  {icon} [{j['platform']}/{j['company']}] {j['title']}")
            print(f"     📍 {j['location']} | Exp: {exp} | {exp_level}{posted}")
            print(f"     🔗 {j['url']}\n")

    elif args.once:
        asyncio.run(run_pipeline())

    else:
        import schedule
        log.info(f"🚀 Daemon mode — every {settings.CHECK_INTERVAL_MINUTES} min")
        
        def job():
            asyncio.run(run_pipeline())
            
        job()
        schedule.every(settings.CHECK_INTERVAL_MINUTES).minutes.do(job)
        while True:
            schedule.run_pending()
            time.sleep(30)
