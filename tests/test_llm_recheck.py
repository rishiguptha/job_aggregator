#!/usr/bin/env python3
"""
Test suite for the LLM classification module.

Tests prompt building, response parsing, graceful fallback, and skip logic.
All tests are synchronous with mocked aiohttp — no real HTTP calls.

Run:  uv run python tests/test_llm_recheck.py
"""

import sys
sys.path.insert(0, ".")

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

from src.filters.llm_recheck import (
    _build_prompt, _parse_response, _map_llm_level, llm_classify_jobs,
    _BATCH_SIZE, _is_anthropic, _build_headers, _build_payload,
    _build_url, _extract_content,
)

SAMPLE_JOBS = [
    {
        "title": "Data Engineer",
        "company": "acme-corp",
        "description": "Build data pipelines. 3+ years of experience preferred.",
        "_jd_excerpt": "Build data pipelines with Spark. 3+ years of experience preferred but not required.",
    },
    {
        "title": "Software Engineer",
        "company": "bigco",
        "description": "Join our team. Strong Python skills. Experience with AWS.",
    },
]


# ── Prompt Building ───────────────────────────────────────────────────────────

def test_build_prompt():
    prompt = _build_prompt(SAMPLE_JOBS)

    assert "--- Job 0 ---" in prompt, "Should label first job"
    assert "--- Job 1 ---" in prompt, "Should label second job"
    assert "Data Engineer" in prompt, "Should include title"
    assert "acme-corp" in prompt, "Should include company"
    assert "but not required" in prompt, "Should use _jd_excerpt when available"
    assert "Strong Python skills" in prompt, "Should fall back to description"
    return True


# ── Response Parsing ──────────────────────────────────────────────────────────

def test_parse_valid_json():
    raw = json.dumps([
        {"id": 0, "min_years": 0, "level": "New Grad", "suitable": True, "clearance": False, "phd": False},
        {"id": 1, "min_years": 3, "level": "3+ YoE", "suitable": False, "clearance": False, "phd": False},
    ])
    result = _parse_response(raw, 2)
    assert result is not None, "Should parse valid JSON"
    assert len(result) == 2
    assert result[0]["min_years"] == 0
    assert result[1]["level"] == "3+ YoE"
    return True


def test_parse_fenced_json():
    raw = '```json\n[{"id": 0, "min_years": 2, "level": "1-2 YoE", "suitable": true, "clearance": false, "phd": false}]\n```'
    result = _parse_response(raw, 1)
    assert result is not None, "Should parse markdown-fenced JSON"
    assert result[0]["min_years"] == 2
    return True


def test_parse_malformed_json():
    result = _parse_response("This is not JSON at all", 2)
    assert result is None, "Should return None for malformed JSON"
    return True


def test_parse_wrong_count():
    raw = json.dumps([{"id": 0, "min_years": 1, "level": "0-1 YoE", "suitable": True, "clearance": False, "phd": False}])
    result = _parse_response(raw, 2)
    assert result is None, "Should return None when count doesn't match"
    return True


def test_parse_not_a_list():
    raw = json.dumps({"id": 0, "suitable": True})
    result = _parse_response(raw, 1)
    assert result is None, "Should return None when response is not a list"
    return True


def test_parse_none_content():
    assert _parse_response(None, 1) is None, "Should return None for None input"
    assert _parse_response("", 1) is None, "Should return None for empty string"
    return True


# ── Level Mapping ─────────────────────────────────────────────────────────────

def test_map_llm_level():
    assert _map_llm_level("New Grad") == "🎓 New Grad"
    assert _map_llm_level("0-1 YoE") == "📗 0-1 YoE"
    assert _map_llm_level("1-2 YoE") == "📘 1-2 YoE"
    assert _map_llm_level("3+ YoE") == "🔶 3+ YoE"
    assert _map_llm_level("Not Specified") == "❓ Not Specified"
    assert _map_llm_level("  new grad  ") == "🎓 New Grad"
    assert _map_llm_level("garbage") == "❓ Not Specified"
    assert _map_llm_level(None) == "❓ Not Specified"
    assert _map_llm_level("") == "❓ Not Specified"
    return True


# ── Classify Function (async, mocked) ────────────────────────────────────────

def test_skip_no_api_key():
    jobs = [{"title": "Test", "passes_filter": False}]
    with patch("src.filters.llm_recheck.settings") as mock_settings:
        mock_settings.LLM_API_KEY = ""
        mock_settings.LLM_BASE_URL = "https://api.example.com/v1"
        result = asyncio.run(llm_classify_jobs(jobs, MagicMock()))
    assert result == jobs, "Should return original jobs when no API key"
    assert "llm_level" not in result[0], "Should not add LLM fields"
    return True


def test_skip_empty_jobs():
    with patch("src.filters.llm_recheck.settings") as mock_settings:
        mock_settings.LLM_API_KEY = "sk-test"
        mock_settings.LLM_BASE_URL = "https://api.example.com/v1"
        result = asyncio.run(llm_classify_jobs([], MagicMock()))
    assert result == [], "Should return empty list"
    return True


def test_successful_classify():
    llm_response = {
        "choices": [{
            "message": {
                "content": json.dumps([
                    {"id": 0, "min_years": 0, "level": "New Grad", "suitable": True, "clearance": False, "phd": False},
                    {"id": 1, "min_years": 5, "level": "3+ YoE", "suitable": False, "clearance": True, "phd": False},
                ])
            }
        }]
    }

    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json = AsyncMock(return_value=llm_response)
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_resp)

    jobs = [
        {"title": "Data Engineer", "company": "acme", "description": "test1"},
        {"title": "SWE", "company": "bigco", "description": "test2"},
    ]

    with patch("src.filters.llm_recheck.settings") as mock_settings:
        mock_settings.LLM_API_KEY = "sk-test"
        mock_settings.LLM_BASE_URL = "https://api.example.com/v1"
        mock_settings.LLM_MODEL = "test-model"
        mock_settings.LLM_TIMEOUT = 15
        result = asyncio.run(llm_classify_jobs(jobs, mock_session))

    assert result[0].get("llm_suitable") is True, "First job should be suitable"
    assert result[0].get("llm_min_years") == 0, "First job should be 0 years"
    assert result[0].get("llm_level") == "🎓 New Grad", "First job should be New Grad"
    assert result[1].get("llm_suitable") is False, "Second job should not be suitable"
    assert result[1].get("llm_clearance") is True, "Second job should flag clearance"
    assert result[1].get("llm_min_years") == 5, "Second job should be 5 years"
    return True


def test_fallback_on_error():
    mock_resp = AsyncMock()
    mock_resp.raise_for_status = MagicMock(side_effect=Exception("HTTP 500"))
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_resp)

    jobs = [{"title": "Test", "company": "co", "description": "desc"}]

    with patch("src.filters.llm_recheck.settings") as mock_settings:
        mock_settings.LLM_API_KEY = "sk-test"
        mock_settings.LLM_BASE_URL = "https://api.example.com/v1"
        mock_settings.LLM_MODEL = "test-model"
        mock_settings.LLM_TIMEOUT = 15
        result = asyncio.run(llm_classify_jobs(jobs, mock_session))

    assert "llm_level" not in result[0], "Should not add LLM fields on error"
    return True


# ── Batching ──────────────────────────────────────────────────────────────────

def _make_mock_response(chunk_size: int):
    """Build a mock aiohttp context manager that returns a valid LLM response."""
    resp_data = {
        "choices": [{
            "message": {
                "content": json.dumps([
                    {"id": i, "min_years": 0, "level": "New Grad",
                     "suitable": True, "clearance": False, "phd": False}
                    for i in range(chunk_size)
                ])
            }
        }]
    }
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json = AsyncMock(return_value=resp_data)
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)
    return mock_resp


def test_batching_splits_large_input():
    n_jobs = _BATCH_SIZE * 2 + 1
    jobs = [{"title": f"Job {i}", "company": f"co{i}", "description": f"desc{i}"}
            for i in range(n_jobs)]

    chunk_sizes = [_BATCH_SIZE, _BATCH_SIZE, 1]
    responses = [_make_mock_response(s) for s in chunk_sizes]

    mock_session = MagicMock()
    mock_session.post = MagicMock(side_effect=responses)

    with patch("src.filters.llm_recheck.settings") as mock_settings:
        mock_settings.LLM_API_KEY = "sk-test"
        mock_settings.LLM_BASE_URL = "https://api.example.com/v1"
        mock_settings.LLM_MODEL = "test-model"
        mock_settings.LLM_TIMEOUT = 30
        result = asyncio.run(llm_classify_jobs(jobs, mock_session))

    assert mock_session.post.call_count == 3, (
        f"Should make 3 API calls for {n_jobs} jobs, got {mock_session.post.call_count}")
    classified = sum(1 for j in result if "llm_level" in j)
    assert classified == n_jobs, f"All {n_jobs} jobs should be classified, got {classified}"
    return True


def test_partial_batch_failure():
    n_jobs = _BATCH_SIZE * 2 + 1
    jobs = [{"title": f"Job {i}", "company": f"co{i}", "description": f"desc{i}"}
            for i in range(n_jobs)]

    timeout_resp = MagicMock()
    timeout_resp.__aenter__ = AsyncMock(side_effect=asyncio.TimeoutError())
    timeout_resp.__aexit__ = AsyncMock(return_value=False)

    responses = [
        _make_mock_response(_BATCH_SIZE),  # chunk 0: succeeds
        timeout_resp,                       # chunk 1: times out
        _make_mock_response(1),             # chunk 2: succeeds
    ]

    mock_session = MagicMock()
    mock_session.post = MagicMock(side_effect=responses)

    with patch("src.filters.llm_recheck.settings") as mock_settings:
        mock_settings.LLM_API_KEY = "sk-test"
        mock_settings.LLM_BASE_URL = "https://api.example.com/v1"
        mock_settings.LLM_MODEL = "test-model"
        mock_settings.LLM_TIMEOUT = 30
        result = asyncio.run(llm_classify_jobs(jobs, mock_session))

    for i in range(_BATCH_SIZE):
        assert "llm_level" in result[i], f"Job {i} (chunk 0) should have LLM fields"

    for i in range(_BATCH_SIZE, _BATCH_SIZE * 2):
        assert "llm_level" not in result[i], f"Job {i} (chunk 1, timed out) should NOT have LLM fields"

    assert "llm_level" in result[-1], "Last job (chunk 2) should have LLM fields"
    return True


# ── Provider Detection ────────────────────────────────────────────────────────

def test_anthropic_detection():
    assert _is_anthropic("https://api.anthropic.com/v1") is True
    assert _is_anthropic("https://openrouter.ai/api/v1") is False
    assert _is_anthropic("https://api.openai.com/v1") is False
    return True


def test_anthropic_headers_and_url():
    h = _build_headers("sk-ant-test", anthropic=True)
    assert h["x-api-key"] == "sk-ant-test"
    assert "Authorization" not in h

    h2 = _build_headers("sk-or-test", anthropic=False)
    assert "Bearer sk-or-test" in h2["Authorization"]
    assert "x-api-key" not in h2

    assert _build_url("https://api.anthropic.com/v1", True).endswith("/messages")
    assert _build_url("https://openrouter.ai/api/v1", False).endswith("/chat/completions")
    return True


def test_anthropic_payload_format():
    p = _build_payload("claude-haiku", "test prompt", 5, anthropic=True)
    assert "system" in p, "Anthropic payload should have top-level system field"
    assert p["messages"][0]["role"] == "user"
    assert len(p["messages"]) == 1

    p2 = _build_payload("gpt-4", "test prompt", 5, anthropic=False)
    assert "system" not in p2
    assert p2["messages"][0]["role"] == "system"
    assert p2["messages"][1]["role"] == "user"
    return True


def test_extract_content_both_formats():
    openai_data = {"choices": [{"message": {"content": "hello"}}]}
    assert _extract_content(openai_data, anthropic=False) == "hello"

    anthropic_data = {"content": [{"type": "text", "text": "hello"}]}
    assert _extract_content(anthropic_data, anthropic=True) == "hello"

    assert _extract_content({}, anthropic=False) is None
    assert _extract_content({"content": []}, anthropic=True) is None
    return True


def test_successful_classify_anthropic():
    """Full classify flow using Anthropic response format."""
    anthropic_response = {
        "content": [{
            "type": "text",
            "text": json.dumps([
                {"id": 0, "min_years": 0, "level": "New Grad", "suitable": True, "clearance": False, "phd": False},
                {"id": 1, "min_years": 5, "level": "3+ YoE", "suitable": False, "clearance": False, "phd": False},
            ])
        }]
    }

    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json = AsyncMock(return_value=anthropic_response)
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_resp)

    jobs = [
        {"title": "Data Engineer", "company": "acme", "description": "test1"},
        {"title": "SWE", "company": "bigco", "description": "test2"},
    ]

    with patch("src.filters.llm_recheck.settings") as mock_settings:
        mock_settings.LLM_API_KEY = "sk-ant-test"
        mock_settings.LLM_BASE_URL = "https://api.anthropic.com/v1"
        mock_settings.LLM_MODEL = "claude-haiku-4-5-20250901"
        mock_settings.LLM_TIMEOUT = 30
        result = asyncio.run(llm_classify_jobs(jobs, mock_session))

    assert result[0].get("llm_suitable") is True
    assert result[0].get("llm_level") == "🎓 New Grad"
    assert result[1].get("llm_suitable") is False
    assert result[1].get("llm_min_years") == 5

    call_kwargs = mock_session.post.call_args
    assert "/messages" in str(call_kwargs), "Should use /messages endpoint for Anthropic"
    return True


# ── Runner ────────────────────────────────────────────────────────────────────

ALL_TESTS = [
    ("build_prompt", test_build_prompt),
    ("parse_valid_json", test_parse_valid_json),
    ("parse_fenced_json", test_parse_fenced_json),
    ("parse_malformed_json", test_parse_malformed_json),
    ("parse_wrong_count", test_parse_wrong_count),
    ("parse_not_a_list", test_parse_not_a_list),
    ("parse_none_content", test_parse_none_content),
    ("map_llm_level", test_map_llm_level),
    ("skip_no_api_key", test_skip_no_api_key),
    ("skip_empty_jobs", test_skip_empty_jobs),
    ("successful_classify", test_successful_classify),
    ("fallback_on_error", test_fallback_on_error),
    ("batching_splits_large_input", test_batching_splits_large_input),
    ("partial_batch_failure", test_partial_batch_failure),
    ("anthropic_detection", test_anthropic_detection),
    ("anthropic_headers_and_url", test_anthropic_headers_and_url),
    ("anthropic_payload_format", test_anthropic_payload_format),
    ("extract_content_both_formats", test_extract_content_both_formats),
    ("successful_classify_anthropic", test_successful_classify_anthropic),
]


def run_tests():
    print("── LLM Classification Tests ──")
    passed = 0
    failed = 0

    for name, fn in ALL_TESTS:
        try:
            fn()
            passed += 1
            print(f"  ✅ {name}")
        except Exception as e:
            failed += 1
            print(f"\n  ❌ FAIL — {name}: {e}")

    total = passed + failed
    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed out of {total}")

    if failed:
        print("\n⚠️  Some tests failed — review before deploying!")
        sys.exit(1)
    else:
        print("\n🎉 All LLM classification tests passed!")


if __name__ == "__main__":
    run_tests()
