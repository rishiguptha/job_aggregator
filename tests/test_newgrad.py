#!/usr/bin/env python3
"""
Test suite for title matching and PhD filter.

Run:  uv run python tests/test_newgrad.py
"""

import sys
sys.path.insert(0, ".")

from src.filters.title import matches_title
from src.filters.phd import passes_phd_filter


def run_title_tests():
    titles = [
        ("Data Engineer", "primary"),
        ("Data Engineering Intern", None),
        ("Senior Data Engineer", None),
        ("Data Engineer, University Graduate", "primary"),
        ("Analytics Engineer (Entry Level)", "primary"),
        ("Data Engineer Co-op", None),
        ("Junior Data Engineer", "primary"),
        ("Software Engineer", "primary"),
        ("Backend Engineer", "primary"),
        ("Full Stack Developer", "primary"),
        ("Platform Engineer", "bonus"),
        ("Cloud Engineer", "bonus"),
        ("ML Engineer", "bonus"),
        ("Staff Software Engineer", None),
        ("Software Engineer II", None),
        ("Senior Backend Developer", None),
    ]

    passed = 0
    failed = 0

    print("── Title Tests ──")
    for title, expected in titles:
        result = matches_title(title)
        ok = result == expected
        if not ok:
            failed += 1
            print(f"  ❌ Expected {expected}, got {result} for: {title}")
        else:
            passed += 1
            label = str(result).upper() if result else "BLOCK"
            print(f"  ✅ [{label:7s}] {title}")

    return passed, failed


def run_phd_tests():
    tests = [
        # ── Should FAIL (PhD hard requirement) ───────────────────────────
        ("Requires a PhD in Computer Science", False),
        ("Must hold a Ph.D. or equivalent", False),
        ("looking for a ph.d.", False),
        ("PhD required for this position", False),

        # ── Should PASS (PhD optional / softened) ────────────────────────
        ("Master's degree or PhD preferred", True),
        ("PhD optional, Master's required", True),
        ("BS in CS required, PhD not required", True),
        ("PhD preferred but not required", True),
        ("PhD is a plus but not necessary", True),

        # ── Should PASS (multi-degree list — PhD is one option) ──────────
        ("PhD or Master's degree required", True),
        ("Bachelor's, Master's, or PhD in CS", True),
        ("MS or PhD in a related field", True),
        ("PhD/MS in Computer Science preferred", True),
        ("BS/MS/PhD in Engineering", True),

        # ── Should PASS (no PhD terms) ───────────────────────────────────
        ("Master's degree in Computer Science", True),
        ("BS in CS required", True),
        ("Great opportunity for engineers", True),
        ("", True),
    ]

    passed = 0
    failed = 0

    print("\n── PhD Tests ──")
    for text, expected in tests:
        result = passes_phd_filter(text)
        ok = result == expected
        if not ok:
            failed += 1
            print(f"  ❌ Expected {'pass' if expected else 'fail'}, got {'pass' if result else 'fail'} for: {text}")
        else:
            passed += 1
            action = "allow" if expected else "block"
            print(f"  ✅ [{action:5s}] {text[:70]}")

    return passed, failed


def run_tests():
    tp, tf = run_title_tests()
    pp, pf = run_phd_tests()

    total_p = tp + pp
    total_f = tf + pf
    total = total_p + total_f

    print(f"\n{'='*60}")
    print(f"Results: {total_p} passed, {total_f} failed out of {total}")

    if total_f:
        print("\n⚠️  Some tests failed!")
        sys.exit(1)
    else:
        print("\n🎉 All title + PhD tests passed!")


if __name__ == "__main__":
    run_tests()
