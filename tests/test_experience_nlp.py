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
from src.filters.jd_parser import parse_jd_sections

# ── Test cases ───────────────────────────────────────────────────────────────
# (description, expected_passes, expected_min_exp, expected_level)

FLAT_TEXT_TESTS = [
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
        True, None, EXP_NEW_GRAD,
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
        True, 2, EXP_1_2,
    ),
    (
        "2 to 4 years of professional data engineering experience.",
        True, 2, EXP_1_2,
    ),
    (
        "1-2 years of relevant professional experience required.",
        True, 1, EXP_0_1,
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
        True, 1, EXP_0_1,
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

    # ── Preference signals in sentences (should PASS — skipped) ──────────
    (
        "Preferably 5+ years of software engineering experience.",
        True, None, EXP_NOT_SPECIFIED,
    ),
    (
        "5 years of experience in distributed systems is a plus.",
        True, None, EXP_NOT_SPECIFIED,
    ),
    (
        "Ideally 4-6 years of professional experience with cloud platforms.",
        True, None, EXP_NOT_SPECIFIED,
    ),
    (
        "Desired: 3 years of experience in backend development.",
        True, None, EXP_NOT_SPECIFIED,
    ),

    # ── OR-logic: conditional degree/experience (should take MIN) ────────
    (
        "Bachelor's degree with 3 years of experience or Master's degree with 1 year of experience in software engineering.",
        True, 1, EXP_0_1,
    ),
    (
        "Requires 5 years of experience or 2 years with a relevant graduate degree in data engineering.",
        True, 2, EXP_1_2,
    ),
]


# ── Section-aware tests ──────────────────────────────────────────────────────
# These test that "preferred" sections don't cause false rejections.

SECTION_TESTS = [
    # Required says 2, preferred says 5 → should pass (min=2 from required)
    {
        "name": "Required=2yr, Preferred=5yr",
        "text": (
            "Requirements\n"
            "2 years of experience in software engineering.\n"
            "Proficiency in Python and SQL.\n\n"
            "Preferred Qualifications\n"
            "5+ years of experience with distributed systems.\n"
            "Experience with Kubernetes."
        ),
        "expected": (True, 2, EXP_1_2),
    },
    # Required says 0, preferred says 3 → should pass
    {
        "name": "Required=new grad, Preferred=3yr",
        "text": (
            "Minimum Qualifications\n"
            "Bachelor's degree in Computer Science.\n"
            "No experience required.\n\n"
            "Nice to Have\n"
            "3+ years of experience with Spark and Kafka.\n"
        ),
        "expected": (True, 0, EXP_NEW_GRAD),
    },
    # Required says 1-2, preferred says 5 → should pass (min=1)
    {
        "name": "Required=1-2yr, Preferred=5yr",
        "text": (
            "What You Need\n"
            "1-2 years of relevant experience in data engineering.\n"
            "Strong SQL skills.\n\n"
            "Bonus\n"
            "5+ years of experience with cloud platforms.\n"
        ),
        "expected": (True, 1, EXP_0_1),
    },
    # No sections detected → unstructured fallback, 3+ should still fail
    {
        "name": "Unstructured, 3yr hard requirement",
        "text": "3+ years of experience in backend development required.",
        "expected": (False, 3, EXP_3_PLUS),
    },
    # About section mentions years (company context) + required section is clean
    {
        "name": "About=20yr company, Required=1yr",
        "text": (
            "About Us\n"
            "We have 20 years of experience in fintech.\n\n"
            "Requirements\n"
            "1 year of experience in software development.\n"
        ),
        "expected": (True, 1, EXP_0_1),
    },
]


def run_flat_tests():
    passed = 0
    failed = 0

    for i, (text, exp_passes, exp_min, exp_level) in enumerate(FLAT_TEXT_TESTS, 1):
        act_passes, act_min, act_level, _confidence = passes_experience_filter(text)

        pass_ok = act_passes == exp_passes
        min_ok = act_min == exp_min
        level_ok = act_level == exp_level
        all_ok = pass_ok and min_ok and level_ok

        if not all_ok:
            failed += 1
            short = text[:80].replace("\n", " ")
            print(f"\n  ❌ FAIL — Flat #{i}: {short}...")
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

    return passed, failed


def run_section_tests():
    passed = 0
    failed = 0

    for i, tc in enumerate(SECTION_TESTS, 1):
        text = tc["text"]
        sections = parse_jd_sections(text.lower())
        act_passes, act_min, act_level, _confidence = passes_experience_filter(
            text.lower(), sections=sections
        )
        exp_passes, exp_min, exp_level = tc["expected"]

        pass_ok = act_passes == exp_passes
        min_ok = act_min == exp_min
        level_ok = act_level == exp_level
        all_ok = pass_ok and min_ok and level_ok

        if not all_ok:
            failed += 1
            print(f"\n  ❌ FAIL — Section #{i}: {tc['name']}")
            if not pass_ok:
                print(f"    passes: expected={exp_passes}, got={act_passes}")
            if not min_ok:
                print(f"    min_exp: expected={exp_min}, got={act_min}")
            if not level_ok:
                print(f"    level: expected='{exp_level}', got='{act_level}'")
        else:
            passed += 1
            print(f"  ✅ Section: {tc['name']}  [{act_level}] min={act_min}")

    return passed, failed


def run_tests():
    print("── Flat Text Tests ──")
    fp, ff = run_flat_tests()

    print("\n── Section-Aware Tests ──")
    sp, sf = run_section_tests()

    total_p = fp + sp
    total_f = ff + sf
    total = total_p + total_f

    print(f"\n{'='*60}")
    print(f"Results: {total_p} passed, {total_f} failed out of {total}")

    if total_f:
        print("\n⚠️  Some tests failed — review before deploying!")
        sys.exit(1)
    else:
        print("\n🎉 All tests passed!")


if __name__ == "__main__":
    run_tests()
