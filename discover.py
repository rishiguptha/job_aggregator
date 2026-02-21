import requests
import json
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

HEADERS = {"User-Agent": "CompanyDiscovery/1.0", "Accept": "application/json"}

KNOWN_COMPANIES = [
    # Big Tech
    "google", "meta", "amazon", "apple", "microsoft", "netflix",
    # AI/ML
    "openai", "anthropic", "deepmind", "cohere", "mistral", "huggingface",
    "stability-ai", "midjourney", "together-ai", "anyscale", "modal",
    "langchain", "pinecone", "weaviate", "qdrant", "chromadb", "mem0",
    # Data/Analytics
    "databricks", "snowflake", "datadog", "confluent", "fivetran",
    "dbt-labs", "airbyte", "dagster", "prefect", "astronomer",
    "monte-carlo-data", "atlan", "census", "hightouch", "rudderstack",
    # Cloud/Infra
    "cloudflare", "hashicorp", "vercel", "supabase", "neon",
    "planetscale", "railway", "fly", "render", "netlify",
    # Fintech
    "stripe", "plaid", "ramp", "brex", "mercury", "affirm",
    "chime", "robinhood", "coinbase", "ripple", "chainalysis",
    # B2B SaaS
    "notion", "airtable", "figma", "retool", "linear",
    "asana", "monday", "clickup", "miro", "loom",
    "hubspot", "intercom", "pagerduty", "sentry", "postman",
    # Security
    "snyk", "vanta", "wiz-inc", "lacework", "crowdstrike",
    # Health Tech
    "tempus", "flatiron-health", "nuna", "ro", "hinge-health",
    # E-commerce/Consumer
    "shopify", "instacart", "doordash", "lyft", "airbnb",
    "discord", "spotify", "reddit", "duolingo", "coursera",
    "dropbox", "twitch", "pinterest", "snap",
    # More startups
    "scale", "sourcegraph", "grafana", "posthog", "tinybird",
    "upstash", "turso", "resend", "clerk", "inngest",
    "trigger-dev", "val-town", "fal-ai", "elevenlabs",
    "runway", "livekit", "replit", "gitpod",
]

def probe_platform(platform: str, slug: str) -> dict | None:
    """Check if a company exists on a given platform."""
    urls = {
        "greenhouse": f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs",
        "lever": f"https://api.lever.co/v0/postings/{slug}?mode=json",
        "ashby": f"https://api.ashbyhq.com/posting-api/job-board/{slug}",
        "workable": f"https://apply.workable.com/api/v1/widget/accounts/{slug}",
    }
    url = urls.get(platform)
    if not url:
        return None

    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            if platform == "greenhouse":
                count = len(data.get("jobs", []))
            elif platform == "lever":
                count = len(data) if isinstance(data, list) else 0
            elif platform == "ashby":
                count = len(data.get("jobs", []))
            elif platform == "workable":
                count = len(data.get("jobs", []))
            else:
                count = 0

            if count > 0:
                return {"platform": platform, "slug": slug, "job_count": count}
    except Exception:
        pass
    return None

def discover_by_probing():
    """Probe all known companies against all platforms."""
    print("🔍 Probing known companies against all ATS platforms...")
    print(f"   Testing {len(KNOWN_COMPANIES)} companies × 4 platforms = {len(KNOWN_COMPANIES) * 4} checks\\n")

    results = {p: [] for p in ["greenhouse", "lever", "ashby", "workable"]}
    total_found = 0

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {}
        for platform in ["greenhouse", "lever", "ashby", "workable"]:
            for slug in KNOWN_COMPANIES:
                future = executor.submit(probe_platform, platform, slug)
                futures[future] = (platform, slug)

        for future in as_completed(futures):
            result = future.result()
            if result:
                results[result["platform"]].append(result)
                total_found += 1
                print(f"  ✅ {result['platform']}/{result['slug']}: {result['job_count']} jobs")

    print(f"\\n{'='*60}")
    print(f"Found {total_found} active company endpoints:\\n")

    for platform, found in results.items():
        if found:
            found.sort(key=lambda x: -x["job_count"])
            slugs = [f'"{r["slug"]}"' for r in found]
            print(f'  "{platform}": [{", ".join(slugs)}],')

    # Save to file
    output = {}
    for platform, found in results.items():
        output[platform] = [r["slug"] for r in sorted(found, key=lambda x: x["slug"])]

    with open("discovered_companies.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\\n💾 Saved to discovered_companies.json")

GITHUB_SOURCES = [
    {
        "name": "job-board-aggregator (4000+ companies)",
        "url": "https://github.com/Feashliaa/job-board-aggregator",
        "data_dir": "https://raw.githubusercontent.com/Feashliaa/job-board-aggregator/main/data/",
    },
    {
        "name": "job-board-scraper (Greenhouse+Lever+Ashby+Rippling)",
        "url": "https://github.com/adgramigna/job-board-scraper",
    },
    {
        "name": "jobber (Ashby, Greenhouse, Lever, BambooHR)",
        "url": "https://github.com/plibither8/jobber",
    },
    {
        "name": "wrkmatch (Greenhouse, Lever, Ashby, Workable, Recruitee)",
        "url": "https://github.com/daviderubio/wrkmatch",
    },
]

def show_github_sources():
    """Show community-maintained company lists."""
    print("📂 Community-maintained company lists on GitHub:\n")
    for src in GITHUB_SOURCES:
        print(f"  📦 {src['name']}")
        print(f"     {src['url']}\n")

    print("How to use these:")
    print("  1. Clone the repo with the largest list (job-board-aggregator)")
    print("  2. Look in their data/ directory for company slug lists")
    print("  3. Copy the slugs into COMPANY_SLUGS in src/config/companies.py\n")
    print("  Or use their scrapers directly — they already handle the iteration!")

def show_manual_guide():
    """Show how to manually find company slugs."""
    print("""
📋 How to Find Company Slugs Manually
======================================

Each ATS platform uses a slug (company identifier) in their URL:

┌─────────────┬───────────────────────────────────────────────┬──────────┐
│ Platform    │ Career Page URL Pattern                       │ Slug     │
├─────────────┼───────────────────────────────────────────────┼──────────┤
│ Greenhouse  │ boards.greenhouse.io/{slug}                   │ openai   │
│ Lever       │ jobs.lever.co/{slug}                          │ netflix  │
│ Ashby       │ jobs.ashbyhq.com/{slug}                       │ linear   │
│ Workable    │ apply.workable.com/{slug}                     │ deepl    │
└─────────────┴───────────────────────────────────────────────┴──────────┘

🔍 Quick Discovery Methods:

1. Google search (find specific companies):
   "data engineer" site:boards.greenhouse.io
   "data engineer" site:jobs.lever.co
   "data engineer" site:jobs.ashbyhq.com
   "data engineer" site:apply.workable.com

2. From the URL, extract the slug:
   https://boards.greenhouse.io/databricks/jobs/12345
                                 ^^^^^^^^^
                                 This is the slug: "databricks"

3. Check a company's careers page — look for redirects to:
   boards.greenhouse.io, jobs.lever.co, etc.

4. Use builtwith.com or wappalyzer to detect which ATS a company uses.

5. Check these curated lists:
   - github.com/Feashliaa/job-board-aggregator (4000+ companies)
   - github.com/adgramigna/job-board-scraper
   - fantastic.jobs (shows companies per ATS)

💡 Pro tip: Many companies use different slugs than their name.
   Example: Pinterest on Greenhouse = "pinterestcareers" not "pinterest"
   Always verify by visiting the URL before adding.
""")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Discover company slugs for ATS platforms")
    parser.add_argument("--method", choices=["api", "github", "manual", "all"],
                        default="all", help="Discovery method")
    args = parser.parse_args()

    if args.method in ("api", "all"):
        discover_by_probing()
        print()

    if args.method in ("github", "all"):
        show_github_sources()
        print()

    if args.method in ("manual", "all"):
        show_manual_guide()
