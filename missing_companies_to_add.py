# ── New companies discovered 2026-03-16 ──────────────────────────────────────
# Source: H1B sponsor cross-reference + SimplifyJobs/New-Grad-Positions + YC batches
# All slugs validated live against ATS APIs before inclusion.
# Job counts are point-in-time snapshots from 2026-03-16.

# ─────────────────────────────────────────────────────────────────────────────
# HOW TO USE: Copy each list's contents into the corresponding section of
# src/config/companies.py
# ─────────────────────────────────────────────────────────────────────────────

# ── GREENHOUSE ────────────────────────────────────────────────────────────────
DISCOVERED_GREENHOUSE = [
    # ── H1B Sponsors (confirmed active, not previously tracked) ──────────────
    "cloudflare",          # Cloudflare — 563 jobs — H1B sponsor: Yes
    "robinhood",           # Robinhood Markets — 142 jobs — H1B sponsor: Yes
    "flexport",            # Flexport — 164 jobs — H1B sponsor: Yes
    "janestreet",          # Jane Street — 230 jobs — H1B sponsor: Yes
    "c3iot",               # C3.ai — 26 jobs — H1B sponsor: Yes  ⚠️ slug is c3iot NOT c3ai
    "wehrtyou",            # Hudson River Trading — 71 jobs — H1B sponsor: Yes  ⚠️ slug is wehrtyou
    "lucidmotors",         # Lucid Motors — 240 jobs — H1B sponsor: Yes

    # ── AI / ML / Data Infra ─────────────────────────────────────────────────
    "appliedintuition",    # Applied Intuition — 218 jobs — AI autonomous vehicles
    "fireworksai",         # Fireworks AI — 23 jobs — LLM inference platform (YC)
    "gleanwork",           # Glean — 192 jobs — AI enterprise search  ⚠️ slug is gleanwork
    "figureai",            # Figure AI — 94 jobs — AI humanoid robotics
    "humeai",              # Hume AI — 8 jobs — Emotional AI / voice
    "earlytalentcerebras", # Cerebras Systems (Early Talent Board) — 5 jobs — AI chips
                           #   Note: separate from lever/cerebras-systems (senior roles)

    # ── Developer Tools / Infrastructure ─────────────────────────────────────
    "canonical",           # Canonical — 276 jobs — Linux/Ubuntu/Cloud (Kubernetes, Juju)
    "warp",                # Warp — 6 jobs — AI-native terminal (dev tools)

    # ── Security / Enterprise Tech ────────────────────────────────────────────
    "axon",                # Axon — 467 jobs — AI public safety tech (Taser, body cams)
    "verkada",             # Verkada — 317 jobs — Physical security cloud platform
    "appian",              # Appian — 151 jobs — Low-code automation platform

    # ── FinTech / Marketplaces ────────────────────────────────────────────────
    "imc",                 # IMC Trading — 149 jobs — Quant trading (strong SWE pipeline)

    # ── Media / Entertainment Tech ────────────────────────────────────────────
    "twitch",              # Twitch (Amazon) — 64 jobs — Streaming/gaming infrastructure
]


# ── LEVER ─────────────────────────────────────────────────────────────────────
DISCOVERED_LEVER = [
    # ── H1B Sponsors ──────────────────────────────────────────────────────────
    "atlassian",           # Atlassian — 0 jobs as of 2026-03 (post-layoff freeze)
                           #   Slug valid; add now to catch when hiring resumes
    "canva",               # Canva — active roles — H1B sponsor: Yes (canvaus in H1B list)
]


# ── ASHBY ─────────────────────────────────────────────────────────────────────
DISCOVERED_ASHBY = [
    # ── AI / ML / Data ───────────────────────────────────────────────────────
    "gigaml",              # Giga AI (GigaML) — 60 jobs — AI training infrastructure
    "genmo",               # Genmo — 5 jobs — AI video generation (YC S22)
    "n1",                  # N1 — 14 jobs — AI data platform
    "continue",            # Continue.dev — 3 jobs — OSS AI code assistant (Sequoia-backed)
    "uncountable",         # Uncountable — 27 jobs — AI R&D platform (chemistry / materials)
    "eventualcomputing",   # Eventual Computing — 6 jobs — Distributed systems / Rust

    # ── Security / Data ───────────────────────────────────────────────────────
    "persona",             # Persona — 33 jobs — Identity verification / fraud (Series C)
    "sentilink",           # SentiLink — 36 jobs — Synthetic fraud detection / fintech
    "sentra",              # Sentra — 4 jobs — Cloud data security

    # ── Crypto / Blockchain Data ──────────────────────────────────────────────
    "allium",              # Allium — 16 jobs — Blockchain data analytics (DE / data infra)
]


# ── WORKDAY ──────────────────────────────────────────────────────────────────
# These are new H1B-sponsoring companies to add to the "workday" list in
# src/config/companies.py alongside the existing entries.
# Format matches the existing workday entries.

DISCOVERED_WORKDAY = [
    # ── Big Tech / Communications ────────────────────────────────────────────
    {"name": "zoom",         "instance": "zoom.wd5",          "site": "Zoom"},
    {"name": "cisco",        "instance": "cisco.wd5",         "site": "Cisco_Careers"},
    # Note: cisco.wd5/Cisco_Careers includes all Splunk roles post-2024 acquisition

    # ── Semiconductors ────────────────────────────────────────────────────────
    {"name": "qualcomm",     "instance": "qualcomm.wd12",     "site": "External"},
    {"name": "micron",       "instance": "micron.wd1",        "site": "External"},

    # ── Enterprise / Cloud ────────────────────────────────────────────────────
    {"name": "redhat",       "instance": "redhat.wd5",        "site": "Jobs"},
    {"name": "servicetitan", "instance": "servicetitan.wd1",  "site": "ServiceTitan"},
    # Note: ServiceTitan migrated from Greenhouse to Workday in 2024

    # ── E-Commerce / Travel ───────────────────────────────────────────────────
    {"name": "ebay",         "instance": "ebay.wd5",          "site": "apply"},
    {"name": "expedia",      "instance": "expedia.wd108",     "site": "search"},

    # ── Financial Data ────────────────────────────────────────────────────────
    {"name": "factset",      "instance": "factset.wd108",     "site": "FactSetCareers"},
    {"name": "spglobal",     "instance": "spgi.wd5",          "site": "SPGI_Careers"},
    {"name": "morningstar",  "instance": "morningstar.wd5",   "site": "Americas"},
]


# ── NOT ADDED — Notable omissions & reasons ──────────────────────────────────
NOT_ADDED = {
    # Custom/proprietary ATS (not API-accessible):
    "metaplatforms":    "metacareers.com — custom ATS",
    "microsoft":        "careers.microsoft.com — custom ATS",
    "amazoncom":        "amazon.jobs — custom ATS",
    "apple":            "jobs.apple.com — custom ATS",
    "google":           "careers.google.com — custom ATS",
    "tesla":            "tesla.com/careers — custom ATS",
    "bloomberglp":      "bloomberg.avature.net — Avature (no public API)",
    "twosigma":         "careers.twosigma.com — Avature (no public API)",
    "citadel":          "citadel.com/careers — proprietary (no public API)",
    "citadelsecurities":"citadelsecurities.com/careers — proprietary",

    # Non-standard ATS (SmartRecruiters / iCIMS / Jobvite — scraper not implemented):
    "servicenow":       "SmartRecruiters — scraper not implemented",
    "intuit":           "iCIMS — scraper not implemented",
    "rivianautomotive": "iCIMS — migrated away from Greenhouse in 2024",
    "advancedmicrodevices": "iCIMS (careers.amd.com) — scraper not implemented",
    "nutanix":          "Jobvite — scraper not implemented",

    # 0 active jobs (slug valid but currently inactive):
    "bolt42":           "Bolt Financial on Greenhouse — 0 jobs (hiring freeze post-layoffs)",
    "wayfair":          "Greenhouse slug shows 0 — possible migration to Workday, needs re-check",
    "etsy":             "Greenhouse — 0 jobs returned; may have migrated ATS",

    # Consulting / skip per criteria:
    "accenturellp":     "Already tracked + skip (consulting bulk H1B filer)",
    "deloitte":         "Skip (consulting)",
    "infosys":          "Skip (consulting)",
    "wipro":            "Skip (consulting)",
    "cognizant":        "Skip (consulting)",
    "tcs":              "Skip (consulting)",
    "capgemini":        "Skip (consulting)",
}
