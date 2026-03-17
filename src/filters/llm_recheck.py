"""
LLM classification for jobs — extracts experience, classifies level, validates fit.

Two use cases batched into a single API call:
  1. "Not Specified" jobs that passed regex but lack experience data → enrich
  2. Borderline jobs that failed regex with low confidence → recover or confirm

Provider-agnostic: auto-detects Anthropic (api.anthropic.com) vs OpenAI-compatible
(OpenRouter, OpenAI, Together, etc.) from LLM_BASE_URL.

Fully optional: returns jobs unchanged when no API key is configured or the
call fails for any reason (timeout, HTTP error, malformed response).
"""

import asyncio
import json
import re

import aiohttp

from src.config.settings import settings
from src.utils.logger import get_logger

log = get_logger(__name__)

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*\n?(.*?)\n?\s*```", re.DOTALL)

SYSTEM_PROMPT = (
    "You analyze job listings for a candidate with 0-2 years of experience.\n"
    "For each numbered job, extract and return:\n"
    "1. min_years: the MINIMUM years of experience required (integer, 0 if none/new grad, null if truly unspecified)\n"
    "2. level: classify as exactly one of: \"New Grad\", \"0-1 YoE\", \"1-2 YoE\", \"3+ YoE\", \"Not Specified\"\n"
    "   - Use the MINIMUM requirement, not preferred/bonus\n"
    "   - \"3+ YoE\" means the hard minimum is 3 or more years\n"
    "3. suitable: is this realistically suitable for someone with 0-2 YoE? (true/false)\n"
    "4. clearance: does it require security clearance or US citizenship? (true/false)\n"
    "5. phd: does it strictly require a PhD (not just preferred)? (true/false)\n"
    "6. title_flag: true if the title is misleading — e.g. title says entry-level but JD is clearly senior/staff/lead/manager, "
    "or title omits seniority but JD demands 5+ years, architecture ownership, or team leadership. false otherwise.\n\n"
    "Return ONLY a compact JSON array (no newlines, no indentation), one object per job:\n"
    '[{"id":0,"min_years":2,"level":"1-2 YoE","suitable":true,"clearance":false,"phd":false,"title_flag":false},...]\n'
    "No explanation, no markdown fences, no pretty-printing. Just one line of JSON."
)

LLM_LEVEL_MAP = {
    "new grad": "🎓 New Grad",
    "0-1 yoe": "📗 0-1 YoE",
    "1-2 yoe": "📘 1-2 YoE",
    "3+ yoe": "🔶 3+ YoE",
    "not specified": "❓ Not Specified",
}


def _is_anthropic(base_url: str) -> bool:
    return "anthropic.com" in base_url


def _build_prompt(jobs: list[dict]) -> str:
    parts = []
    for i, job in enumerate(jobs):
        excerpt = job.get("_jd_excerpt") or job.get("description", "")
        parts.append(
            f"--- Job {i} ---\n"
            f"Title: {job.get('title', 'Unknown')}\n"
            f"Company: {job.get('company', 'Unknown')}\n"
            f"Description:\n{excerpt}\n"
        )
    return "\n".join(parts)


def _build_url(base: str, anthropic: bool) -> str:
    if anthropic:
        return f"{base}/messages"
    return f"{base}/chat/completions"


def _build_headers(api_key: str, anthropic: bool) -> dict:
    if anthropic:
        return {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _build_payload(model: str, prompt: str, chunk_size: int, anthropic: bool) -> dict:
    max_tokens = 8192
    if anthropic:
        return {
            "model": model,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": max_tokens,
        }
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "max_tokens": max_tokens,
    }


def _extract_content(data: dict, anthropic: bool) -> str | None:
    if anthropic:
        blocks = data.get("content", [])
        return blocks[0].get("text") if blocks else None
    choices = data.get("choices", [])
    if choices:
        return choices[0].get("message", {}).get("content")
    return None


def _parse_response(text: str, count: int) -> list[dict] | None:
    """Parse the LLM response into a list of verdict dicts.

    Handles raw JSON arrays and markdown-fenced JSON.  Returns None if
    parsing fails or the result is obviously wrong.
    """
    if not text:
        return None
    cleaned = text.strip()

    fence = _JSON_FENCE_RE.search(cleaned)
    if fence:
        cleaned = fence.group(1).strip()

    try:
        results = json.loads(cleaned)
    except json.JSONDecodeError:
        return None

    if not isinstance(results, list):
        return None

    if len(results) != count:
        return None

    return results


_BATCH_SIZE = 8
_MAX_CONCURRENT = 2
_MAX_RETRIES = 2
_RETRY_BASE_DELAY = 3.0


def _map_llm_level(raw: str | None) -> str:
    """Map LLM level string to our emoji-tagged format."""
    if not raw:
        return "❓ Not Specified"
    return LLM_LEVEL_MAP.get(raw.lower().strip(), "❓ Not Specified")


async def _classify_chunk(
    chunk: list[dict],
    chunk_idx: int,
    session: aiohttp.ClientSession,
    url: str,
    headers: dict,
    model: str,
    timeout: aiohttp.ClientTimeout,
    semaphore: asyncio.Semaphore,
    anthropic: bool,
) -> None:
    """Classify a single chunk of jobs via one LLM API call.

    Mutates job dicts in-place on success; leaves them unchanged on failure
    so the caller can fall back to the regex verdict for that chunk.
    Retries on 429 (rate-limit) with exponential backoff.
    """
    prompt = _build_prompt(chunk)
    payload = _build_payload(model, prompt, len(chunk), anthropic)

    for attempt in range(_MAX_RETRIES + 1):
        try:
            async with semaphore:
                async with session.post(
                    url, json=payload, headers=headers, timeout=timeout,
                ) as resp:
                    if resp.status == 429 and attempt < _MAX_RETRIES:
                        delay = _RETRY_BASE_DELAY * (2 ** attempt)
                        log.info(f"LLM chunk {chunk_idx}: rate-limited, retrying in {delay:.0f}s (attempt {attempt + 1}/{_MAX_RETRIES})")
                        await asyncio.sleep(delay)
                        continue
                    resp.raise_for_status()
                    data = await resp.json()

            content = _extract_content(data, anthropic)
            finish = (data.get("choices") or [{}])[0].get("finish_reason", "?")
            log.debug(f"LLM chunk {chunk_idx}: finish={finish}, len={len(content) if content else 0}")
            results = _parse_response(content, len(chunk))

            if results is None:
                log.warning(f"LLM chunk {chunk_idx}: could not parse response "
                            f"(preview: {(content or '')[:200]!r})")
                return

            for r in results:
                idx = r.get("id")
                if isinstance(idx, int) and 0 <= idx < len(chunk):
                    min_yrs = r.get("min_years")
                    chunk[idx]["llm_min_years"] = int(min_yrs) if min_yrs is not None else None
                    chunk[idx]["llm_level"] = _map_llm_level(r.get("level", "Not Specified"))
                    chunk[idx]["llm_suitable"] = bool(r.get("suitable", False))
                    chunk[idx]["llm_clearance"] = bool(r.get("clearance", False))
                    chunk[idx]["llm_phd"] = bool(r.get("phd", False))
                    chunk[idx]["llm_title_flag"] = bool(r.get("title_flag", False))
            return

        except asyncio.TimeoutError:
            log.warning(f"LLM chunk {chunk_idx}: timed out after {timeout.total}s")
            return
        except Exception as e:
            log.warning(f"LLM chunk {chunk_idx}: failed ({e})")
            return


async def llm_classify_jobs(
    jobs: list[dict],
    session: aiohttp.ClientSession,
) -> list[dict]:
    """Send jobs to an LLM for experience extraction and classification.

    Splits large batches into chunks of _BATCH_SIZE and runs them
    concurrently (limited by _MAX_CONCURRENT).  Each chunk has independent
    error handling — one chunk failing does not affect the others.

    Auto-detects Anthropic vs OpenAI-compatible API from LLM_BASE_URL.

    Adds to each job dict (when the LLM responds successfully):
      - llm_min_years: int | None
      - llm_level: str (emoji-tagged experience level)
      - llm_suitable: bool
      - llm_clearance: bool
      - llm_phd: bool

    On any failure the affected jobs are returned unchanged so the
    caller can fall back to the regex verdict.
    """
    if not settings.LLM_API_KEY or not settings.LLM_BASE_URL or not jobs:
        return jobs

    model = settings.LLM_MODEL or "gpt-3.5-turbo"
    base = settings.LLM_BASE_URL.rstrip("/")
    anthropic = _is_anthropic(base)
    url = _build_url(base, anthropic)
    headers = _build_headers(settings.LLM_API_KEY, anthropic)
    timeout = aiohttp.ClientTimeout(total=settings.LLM_TIMEOUT)
    semaphore = asyncio.Semaphore(_MAX_CONCURRENT)

    chunks = [jobs[i:i + _BATCH_SIZE] for i in range(0, len(jobs), _BATCH_SIZE)]

    if len(chunks) > 1:
        log.info(f"Splitting {len(jobs)} jobs into {len(chunks)} batches of ~{_BATCH_SIZE}")

    await asyncio.gather(*[
        _classify_chunk(chunk, i, session, url, headers, model, timeout, semaphore, anthropic)
        for i, chunk in enumerate(chunks)
    ])

    classified = sum(1 for j in jobs if "llm_level" in j)
    suitable = sum(1 for j in jobs if j.get("llm_suitable"))
    log.info(f"LLM classify: {classified}/{len(jobs)} jobs evaluated, {suitable} suitable for 0-2 YoE")
    return jobs
