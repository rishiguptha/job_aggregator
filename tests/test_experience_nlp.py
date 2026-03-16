#!/usr/bin/env python3
"""
Test suite for the smart experience filter.

Run:  uv run python tests/test_experience_nlp.py
"""

import sys
sys.path.insert(0, ".")

from src.filters.experience import (
    passes_experience_filter,
    EXP_NEW_GRAD, EXP_0_1, EXP_1_2, EXP_3_PLUS, EXP_NOT_SPECIFIED,
)

# ── Test cases ───────────────────────────────────────────────────────────────
# (description, expected_passes, expected_min_exp, expected_level)

TESTS = [
    # ── New Grad / Entry Level (should PASS) ─────────────────────────────
    (
        "This is a new graduate role. No prior experience required.",
        True, 0, EXP_NEW_GRAD,
    ),
    (
        "Entry level software engineer position. Looking for recent graduates.",
        True, None, EXP_NEW_GRAD,
    ),
    (
        "Early career opportunity. 0-1 year of experience preferred.",
        True, None, EXP_NEW_GRAD,  # "0-1 year" triggers NEW_GRAD_SIGNALS fast path
    ),

    # ── 0-1 Years (should PASS) ─────────────────────────────────────────
    (
        "Requires 1 year of experience in software development.",
        True, 1, EXP_0_1,
    ),
    (
        "Minimum one year of experience with Python or Java.",
        True, 1, EXP_0_1,
    ),

    # ── 1-2 Years (should PASS with MAX_EXPERIENCE_YEARS=2) ─────────────
    (
        "2 years of experience in data engineering or related field.",
        True, 2, EXP_1_2,
    ),
    (
        "Requires two years of hands-on experience with cloud platforms.",
        True, 2, EXP_1_2,
    ),

    # ── RANGE: min of range used for filtering ──────────────────────────
    (
        "2-4 years of experience in software engineering.",
        True, 2, EXP_1_2,   # min=2 ≤ MAX(2) → passes
    ),
    (
        "2 to 4 years of professional data engineering experience.",
        True, 2, EXP_1_2,
    ),
    (
        "1-2 years of relevant professional experience required.",
        True, 1, EXP_0_1,   # min=1
    ),

    # ── 3+ Years (should FAIL) ──────────────────────────────────────────
    (
        "3+ years of experience in backend development.",
        False, 3, EXP_3_PLUS,
    ),
    (
        "Minimum 5 years of experience in machine learning.",
        False, 5, EXP_3_PLUS,
    ),
    (
        "Requires three to five years of relevant experience.",
        False, 3, EXP_3_PLUS,
    ),
    (
        "5-7 years of software development experience required.",
        False, 5, EXP_3_PLUS,
    ),

    # ── Company context should be IGNORED ────────────────────────────────
    (
        "We have 15 years of experience building enterprise software. Looking for a junior engineer to join the team.",
        True, None, EXP_NOT_SPECIFIED,
    ),
    (
        "Our company has over 20 years of experience in fintech. This is an entry level position.",
        True, None, EXP_NEW_GRAD,
    ),
    (
        "Founded in 2005, we have 20 years of experience. Ideal candidate has 1-2 years of relevant experience.",
        True, 1, EXP_0_1,  # ignores 20 (company context), uses 1 (requirement min)
    ),

    # ── No experience mentioned (should PASS) ────────────────────────────
    (
        "Software engineer to build APIs using Python and FastAPI. Strong problem-solving skills. BS in CS preferred.",
        True, None, EXP_NOT_SPECIFIED,
    ),
    (
        "Join our team to build data pipelines with Spark and Kafka.",
        True, None, EXP_NOT_SPECIFIED,
    ),

    # ── Multiple mentions → strictest wins ───────────────────────────────
    (
        "3+ years of experience with Python. 1+ year of experience with AWS.",
        False, 3, EXP_3_PLUS,
    ),
    (
        "1 year of experience with SQL. 2 years of data engineering experience.",
        True, 2, EXP_1_2,
    ),

    # ── "experience" in non-requirement context ──────────────────────────
    (
        "Great opportunity to gain experience in a fast-paced environment.",
        True, None, EXP_NOT_SPECIFIED,
    ),

    # ── Written numbers ──────────────────────────────────────────────────
    (
        "Minimum three years of professional software development experience.",
        False, 3, EXP_3_PLUS,
    ),
    (
        "Two years of experience in data pipelines and ETL.",
        True, 2, EXP_1_2,
    ),

    # ── Empty / None ─────────────────────────────────────────────────────
    (
        "",
        True, None, EXP_NOT_SPECIFIED,
    ),
    (
        "   ",
        True, None, EXP_NOT_SPECIFIED,
    ),
]


def run_tests():
    passed = 0
    failed = 0

    for i, (text, exp_passes, exp_min, exp_level) in enumerate(TESTS, 1):
        act_passes, act_min, act_level = passes_experience_filter(text)

        pass_ok = act_passes == exp_passes
        min_ok = act_min == exp_min
        level_ok = act_level == exp_level
        all_ok = pass_ok and min_ok and level_ok

        if not all_ok:
            failed += 1
            short = text[:80].replace("\n", " ")
            print(f"\n  ❌ FAIL — Test #{i}: {short}...")
            if not pass_ok:
                print(f"    passes: expected={exp_passes}, got={act_passes}")
            if not min_ok:
                print(f"    min_exp: expected={exp_min}, got={act_min}")
            if not level_ok:
                print(f"    level: expected='{exp_level}', got='{act_level}'")
        else:
            passed += 1
            short = text[:55].replace("\n", " ")
            print(f"  ✅ [{act_level:16s}] min={str(act_min):>4s}  {short}...")

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed out of {len(TESTS)}")

    if failed:
        print("\n⚠️  Some tests failed — review before deploying!")
        sys.exit(1)
    else:
        print("\n🎉 All tests passed!")


if __name__ == "__main__":
    run_tests()
