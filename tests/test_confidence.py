#!/usr/bin/env python3
"""
Test suite for confidence scoring in the experience filter.

Run:  uv run python tests/test_confidence.py
"""

import sys
sys.path.insert(0, ".")

from src.filters.experience import passes_experience_filter
from src.filters.jd_parser import parse_jd_sections

# ── Test cases ───────────────────────────────────────────────────────────────
# (description, sections_text_or_None, min_conf, max_conf, label)
#
# min_conf/max_conf define the acceptable confidence range.

CONFIDENCE_TESTS = [
    # ── HIGH confidence (>0.7) ────────────────────────────────────────────

    # Clear "Required" section + unambiguous experience number
    {
        "name": "Structured JD: Required=2yr",
        "text": (
            "Requirements\n"
            "2 years of experience in software engineering.\n"
            "Proficiency in Python and SQL.\n\n"
            "Preferred Qualifications\n"
            "5+ years of experience with distributed systems.\n"
        ),
        "use_sections": True,
        "min_conf": 0.70,
        "max_conf": 1.0,
    },
    # Explicit negation is a strong, clear signal
    {
        "name": "Explicit negation: no experience required",
        "text": "No experience required. This is an entry-level role.",
        "use_sections": False,
        "min_conf": 0.55,
        "max_conf": 1.0,
    },
    # Required section + negation
    {
        "name": "Structured + negation",
        "text": (
            "Minimum Qualifications\n"
            "Bachelor's degree in Computer Science.\n"
            "No experience required.\n"
        ),
        "use_sections": True,
        "min_conf": 0.70,
        "max_conf": 1.0,
    },

    # ── MEDIUM confidence (0.4–0.7) ──────────────────────────────────────

    # No sections but clear experience number
    {
        "name": "Flat text: clear 2yr requirement",
        "text": "2 years of experience in data engineering required.",
        "use_sections": False,
        "min_conf": 0.40,
        "max_conf": 0.70,
    },
    # Sections found but no experience numbers at all
    {
        "name": "Structured JD but no experience numbers",
        "text": (
            "Requirements\n"
            "Bachelor's degree in Computer Science.\n"
            "Strong problem-solving skills.\n\n"
            "Preferred Qualifications\n"
            "Experience with Kubernetes.\n"
        ),
        "use_sections": True,
        "min_conf": 0.40,
        "max_conf": 0.75,
    },
    # No experience words at all → we don't know the requirement, low confidence
    {
        "name": "No experience words at all",
        "text": "Build data pipelines with Spark and Kafka. Strong SQL skills.",
        "use_sections": False,
        "min_conf": 0.20,
        "max_conf": 0.35,
    },

    # ── LOW confidence (<0.4) ────────────────────────────────────────────

    # No sections + preference signals near experience numbers
    {
        "name": "Flat + preference ambiguity only",
        "text": "Preferably 5+ years of software engineering experience.",
        "use_sections": False,
        "min_conf": 0.0,
        "max_conf": 0.40,
    },

    # ── EDGE CASES ───────────────────────────────────────────────────────

    # Empty description
    {
        "name": "Empty description",
        "text": "",
        "use_sections": False,
        "min_conf": 0.65,
        "max_conf": 0.75,
    },
    # Whitespace only
    {
        "name": "Whitespace only",
        "text": "   ",
        "use_sections": False,
        "min_conf": 0.65,
        "max_conf": 0.75,
    },
]


def run_confidence_tests():
    passed = 0
    failed = 0

    for i, tc in enumerate(CONFIDENCE_TESTS, 1):
        text = tc["text"]
        sections = None
        if tc["use_sections"] and text.strip():
            sections = parse_jd_sections(text.lower())

        _passes, _min_exp, _level, confidence = passes_experience_filter(
            text.lower() if text.strip() else text, sections=sections
        )

        in_range = tc["min_conf"] <= confidence <= tc["max_conf"]

        if not in_range:
            failed += 1
            print(f"\n  ❌ FAIL — #{i}: {tc['name']}")
            print(f"    confidence: {confidence:.2f} (expected {tc['min_conf']:.2f}–{tc['max_conf']:.2f})")
            print(f"    result: passes={_passes}, min_exp={_min_exp}, level={_level}")
        else:
            passed += 1
            print(f"  ✅ conf={confidence:.2f}  {tc['name']}")

    return passed, failed


def run_tests():
    print("── Confidence Scoring Tests ──")
    cp, cf = run_confidence_tests()

    total_p = cp
    total_f = cf
    total = total_p + total_f

    print(f"\n{'='*60}")
    print(f"Results: {total_p} passed, {total_f} failed out of {total}")

    if total_f:
        print("\n⚠️  Some tests failed — review before deploying!")
        sys.exit(1)
    else:
        print("\n🎉 All confidence tests passed!")


if __name__ == "__main__":
    run_tests()
