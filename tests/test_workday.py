import asyncio
import aiohttp
import json

async def test_workday_detail():
    instance = "nvidia.wd5"
    company_slug = "nvidia"
    site = "NVIDIAExternalCareerSite"
    external_path = "/job/US-CA-Santa-Clara/Senior-Data-Engineer_JR1985160" # example path, we might need a real one

    api_url = f"https://{instance}.myworkdayjobs.com/wday/cxs/{company_slug}/{site}{external_path}"
    
    headers = {
        "User-Agent": "JobAlertBot/2.0",
        "Accept": "application/json",
    }
    
    async with aiohttp.ClientSession() as session:
        # First, search to get a valid external_path
        search_url = f"https://{instance}.myworkdayjobs.com/wday/cxs/{company_slug}/{site}/jobs"
        async with session.post(search_url, json={"appliedFacets":{},"limit":1,"offset":0,"searchText":"data engineer"}, headers=headers) as r:
            data = await r.json()
            if not data.get("jobPostings"):
                print("No jobs found")
                return
            external_path = data["jobPostings"][0]["externalPath"]
            print(f"Found path: {external_path}")
            
        # Now fetch detail
        detail_url = f"https://{instance}.myworkdayjobs.com/wday/cxs/{company_slug}/{site}{external_path}"
        async with session.get(detail_url, headers=headers) as r:
            print(f"Detail status: {r.status}")
            if r.status == 200:
                detail_data = await r.json()
                print("Keys:", detail_data.keys())
                print("Job Description:", detail_data.get("jobPostingInfo", {}).get("jobDescription", "")[:200])
            else:
                print(await r.text())

asyncio.run(test_workday_detail())
