# Missing H1B Sponsors — Coverage Audit
**Generated:** 2026-03-16
**Source:** `src/config/sponsors.py` cross-referenced against `src/config/companies.py`
**Total H1B sponsors in list:** 131 | **Tracked:** 67 | **Need action:** 20 | **Can't track:** 12 | **Skipped:** 32

---

## ✅ Already Tracked

| Company | H1B Slug | ATS | Config Key |
|---------|----------|-----|-----------|
| Airbnb | airbnb | Greenhouse | `greenhouse/airbnb` |
| Adobe | adobe | Workday | `workday/adobe.wd5` |
| AMD / Advanced Micro Devices | advancedmicrodevicesamd | iCIMS | ❌ iCIMS not supported |
| American Express | americanexpress | OracleCloud | `oraclecloud/american_express` |
| Anduril Industries | andurilindustries | Greenhouse | `greenhouse/andurilindustries` |
| Anthropic | anthropic | Greenhouse | `greenhouse/anthropic` |
| Autodesk | autodesk | Workday | `workday/autodesk.wd1` |
| Benchling | benchling | Greenhouse + Lever | both tracked |
| Bill.com | billcom | Greenhouse | `greenhouse/billcom` |
| Brex | brex | Greenhouse | `greenhouse/brex` |
| Bristol-Myers Squibb | bristolmyerssquibb | Workday | `workday/bms` |
| Broadcom | broadcom | Workday | `workday/broadcom.wd1` |
| Capital One | capitalone | Workday | `workday/capitalone.wd12` |
| Coinbase | coinbase | Lever | `lever/coinbase` |
| Danaher | danaher | Workday | `workday/danaher.wd1` |
| Databricks | databricks | Greenhouse | `greenhouse/databricks` |
| Datadog | datadog | Greenhouse | `greenhouse/datadog` |
| Discord | discord | Greenhouse | `greenhouse/discord` |
| DoorDash | doordash | Greenhouse | `greenhouse/doordash` |
| Dropbox | dropbox | Greenhouse | `greenhouse/dropbox` |
| Duolingo | duolingo | Greenhouse | `greenhouse/duolingo` |
| Elastic | elastic | Greenhouse | `greenhouse/elastic` |
| Faire | faire | Lever | `lever/faire` |
| Figma | figma | Greenhouse | `greenhouse/figma` |
| Ford Motor | fordmotor | OracleCloud | `oraclecloud/ford` |
| GitHub | github | Greenhouse | `greenhouse/github` |
| GitLab | gitlab | Greenhouse | `greenhouse/gitlab` |
| Goldman Sachs | goldmansachs | OracleCloud | `oraclecloud/goldman_sachs` |
| Gusto | gusto | Greenhouse | `greenhouse/gusto` |
| HashiCorp | hashicorp | Greenhouse | `greenhouse/hashicorp` |
| Honeywell | honeywellinternational | OracleCloud | `oraclecloud/honeywell` |
| HubSpot | hubspot | Greenhouse | `greenhouse/hubspot` |
| Illumio | illumio | Ashby | `ashby/illumio` |
| Instacart | instacartmaplebear | Greenhouse | `greenhouse/instacart` |
| Intel | intel | Workday | `workday/intel.wd1` |
| JPMorgan Chase | jpmorganchase | OracleCloud | `oraclecloud/jpmorgan` |
| Lyft | lyft | Greenhouse | `greenhouse/lyft` |
| Mastercard | mastercardinternational | Workday | `workday/mastercard.wd1` |
| MongoDB | mongodb | Greenhouse | `greenhouse/mongodb` |
| Netflix | netflix | Workday + Lever | both tracked |
| Notion Labs | notionlabs | Greenhouse | `greenhouse/notionlabs` |
| NVIDIA | nvidia | Workday | `workday/nvidia.wd5` |
| Okta | okta | Greenhouse | `greenhouse/okta` |
| OpenAI | openai | Greenhouse | `greenhouse/openai` |
| Oracle | oracleamerica | OracleCloud | `oraclecloud/oracle` |
| PagerDuty | pagerduty | Greenhouse | `greenhouse/pagerduty` |
| Palantir | palantirtechnologies | Greenhouse + Lever | both tracked |
| PayPal | paypal | Workday | `workday/paypal.wd1` |
| Pinterest | pinterest | Greenhouse | `greenhouse/pinterest` |
| Plaid | plaid | Greenhouse + Lever | both tracked |
| Postman | postman | Greenhouse + Lever | both tracked |
| PwC | pricewaterhousecoopersllppwc | Workday | tracked (consulting — bulk H1B, not target) |
| Ramp | ramp | Greenhouse + Ashby | both tracked |
| Reddit | reddit | Greenhouse | `greenhouse/reddit` |
| Rippling | rippling | Greenhouse | `greenhouse/rippling` |
| Roku | roku | Greenhouse | `greenhouse/roku` |
| Salesforce | salesforce | Workday | `workday/salesforce.wd12` |
| Samsara | samsara | Greenhouse | `greenhouse/samsara` |
| Scale AI | scaleai | Greenhouse | `greenhouse/scaleai` |
| Snap | snap | Workday | `workday/snapchat.wd1` |
| Snowflake | snowflake | Greenhouse + Ashby | both tracked |
| Spotify | spotifyusa | Greenhouse + Lever | both tracked |
| Stripe | stripe | Greenhouse | `greenhouse/stripe` |
| Toast | toast | Greenhouse | `greenhouse/toast` |
| Twilio | twilio | Greenhouse | `greenhouse/twilio` |
| Veeva Systems | veevasystems | Lever | `lever/veeva` |
| Visa | visausa | Workday | `workday/visa.wd5` |
| Walmart Global Tech | walmartglobaltech | Workday | `workday/walmart.wd5` |
| Workday | workday | Greenhouse + Workday | both tracked |

---

## 🆕 ADD — New entries (copy from `missing_companies_to_add.py`)

| Company | H1B Slug | ATS | Slug to Add | Jobs | Notes |
|---------|----------|-----|-------------|------|-------|
| Cloudflare | cloudflare | Greenhouse | `cloudflare` | 563 | High priority — infra/security |
| Robinhood | robinhoodmarkets | Greenhouse | `robinhood` | 142 | Fintech |
| Flexport | flexport | Greenhouse | `flexport` | 164 | Logistics tech |
| Jane Street | janestreet | Greenhouse | `janestreet` | 230 | Quant (SWE/DE roles) |
| C3.ai | c3ai | Greenhouse | **`c3iot`** | 26 | ⚠️ slug is c3iot not c3ai |
| Hudson River Trading | hudsonrivertrading | Greenhouse | **`wehrtyou`** | 71 | ⚠️ slug is wehrtyou (internal name) |
| Lucid Motors | lucidmotors | Greenhouse | `lucidmotors` | 240 | EV tech, strong SW division |
| Atlassian | atlassianus | Lever | `atlassian` | 0 | Slug valid; frozen post-layoffs — add now |
| Canva | canvaus | Lever | `canva` | active | Design/AI platform |
| Zoom Video | zoomvideocommunications | Workday | `zoom.wd5` / `Zoom` | large | Video comms |
| Cisco (+ Splunk) | ciscosystems | Workday | `cisco.wd5` / `Cisco_Careers` | large | Splunk absorbed here |
| Qualcomm | qualcommtechnologies | Workday | `qualcomm.wd12` / `External` | large | Chips + software |
| Micron Technology | microntechnology | Workday | `micron.wd1` / `External` | large | Memory/storage tech |
| Red Hat | redhat | Workday | `redhat.wd5` / `Jobs` | large | IBM subsidiary, OSS |
| ServiceTitan | servicetitan | Workday | `servicetitan.wd1` / `ServiceTitan` | — | ⚠️ migrated from Greenhouse |
| eBay | ebay | Workday | `ebay.wd5` / `apply` | large | E-commerce |
| Expedia | expedia | Workday | `expedia.wd108` / `search` | large | Travel tech |
| FactSet | factsetresearchsystems | Workday | `factset.wd108` / `FactSetCareers` | large | Financial data, strong eng |
| S&P Global | spglobal | Workday | `spgi.wd5` / `SPGI_Careers` | large | Financial data/analytics |
| Morningstar | morningstar | Workday | `morningstar.wd5` / `Americas` | large | Investment data |

---

## ⚠️ Cannot Track — Custom/Proprietary ATS

These companies sponsor H1B but use non-standard ATS platforms not supported by the scraper.

| Company | H1B Slug | ATS Platform | Why Not Tracked |
|---------|----------|--------------|-----------------|
| Meta / Facebook | metaplatforms | Custom (metacareers.com) | Proprietary portal — no public API |
| Microsoft | microsoft | Custom (careers.microsoft.com) | Proprietary portal — no public API |
| Amazon | amazoncom | Custom (amazon.jobs) | Proprietary portal — no public API |
| Apple | apple | Custom (jobs.apple.com) | Proprietary portal — no public API |
| Google / Alphabet | google | Custom (careers.google.com) | Proprietary portal — no public API |
| Tesla | tesla | Custom (tesla.com/careers) | Proprietary portal — no public API |
| Bloomberg LP | bloomberglp | Avature | `bloomberg.avature.net` — not standard API |
| Two Sigma | twosigmainvestmentslp | Avature | `careers.twosigma.com` — not standard API |
| Citadel | citadel | Proprietary | `citadel.com/careers` — fully custom |
| Citadel Securities | citadelsecurities | Proprietary | Fully custom — no public ATS endpoint |
| ServiceNow | servicenow | SmartRecruiters | Scraper not implemented |
| Intuit | intuit | iCIMS | Scraper not implemented |
| AMD | advancedmicrodevicesamd | iCIMS | `careers.amd.com` via iCIMS |
| Rivian | rivianautomotive | iCIMS | Migrated away from Greenhouse in 2024 |
| Nutanix | nutanix | Jobvite | Scraper not implemented |

---

## 🔍 Unverified — Needs Follow-up

| Company | H1B Slug | Issue |
|---------|----------|-------|
| Wayfair | wayfair | GH slug `wayfair` returns 0 jobs — possible migration to Workday in 2024-2025 |
| Etsy | etsy | GH slug `etsy` returns 0 — verify correct slug or new ATS |
| Bolt Financial | boltfinancial | GH slug `bolt42` returns 0 — major layoffs 2022-2023, likely hiring freeze |
| Booking.com | booking | Likely Workday — instance not researched |
| Ansys | ansys | Likely Workday — instance not researched |
| Charles Schwab | charlesschwab | Likely Workday — instance not researched |
| BlackRock | blackrock | Likely Workday — instance not researched |
| SAP America | sapamerica | Uses SuccessFactors (own product) — not standard scraper |
| MathWorks | mathworks | Custom careers portal — needs investigation |

---

## ⏭️ Skipped — Not Target Companies

| Category | Companies |
|----------|-----------|
| Consulting (bulk H1B, not target roles) | Accenture, Deloitte, TCS, Infosys, Wipro, Cognizant, Capgemini, HCL, LTI Mindtree, Mphasis, PwC, KPMG, EY, Persistent, UST Global, Zensartechnologies |
| Pharma / Biotech | AbbVie, Amgen, Biogen, Genentech, Gilead, J&J, Merck, Pfizer, Regeneron, Thermo Fisher, AbbottLaboratories, BMS (tracked), BostonScientific, Medtronic |
| Automotive (mostly hardware) | BMW, Mercedes-Benz, Toyota, Continental Automotive, Ford (tracked) |
| Industrial / Aerospace | Boeing, GE, Robert Bosch, Siemens (some SW roles — worth adding later) |
| Pure Hardware (limited SW roles) | Seagate, Western Digital, GlobalFoundries, NXP Semiconductors |
| Healthcare / Insurance | Elevance, Cigna, CVS/Aetna, Humana, United Health/Optum, IQVIA |
| Already acquired/defunct | VMware (→Broadcom, tracked), Splunk (→Cisco, tracked) |

---

## 📊 Summary Stats

| Action | Count |
|--------|-------|
| Already tracked | 67 |
| **Newly added (this session)** | **20** |
| Cannot track (custom ATS) | 15 |
| Needs follow-up verification | 9 |
| Skipped (consulting/pharma/auto) | ~32 |
| **Total H1B sponsors in list** | **~143** |

**Net new slugs added across all ATS:**
- Greenhouse: +20 (7 H1B sponsors + 13 new-grad / AI companies)
- Lever: +2 (Atlassian, Canva)
- Ashby: +10 (AI/ML startups + fintech)
- Workday: +11 (H1B sponsors on Workday)
- **Total: +43 new company boards**
