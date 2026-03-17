#!/usr/bin/env python3
"""
Test suite for the security clearance filter.

Run:  uv run python tests/test_clearance.py
"""

import sys
sys.path.insert(0, ".")

from src.filters.clearance import passes_clearance_filter

TESTS = [
    # ── Should FAIL (clearance required) ──────────────────────────────────
    ("We need a data engineer with Top Secret clearance", False),
    ("Requires active TS/SCI with polygraph", False),
    ("Requires US citizenship", False),
    ("U.S. Citizen required", False),
    ("Active security clearance required for this position", False),
    ("Must have top-secret clearance", False),
    ("Candidates must hold an active security clearance", False),
    ("US citizenship required for this role", False),
    ("This position requires a Top Secret clearance", False),

    # ── Should PASS (negated / not required) ──────────────────────────────
    ("No clearance required", True),
    ("No security clearance required for this role", True),
    ("This position does not require security clearance", True),
    ("Security clearance is NOT required", True),
    ("No US citizenship required", True),
    ("U.S. citizenship is not required for this position", True),
    ("This role doesn't require any security clearance", True),
    ("Clearance is not needed for this position", True),

    # ── Should PASS (no clearance terms at all) ──────────────────────────
    ("Data Engineer role", True),
    ("Build data pipelines with Python and Spark", True),
    ("Great opportunity for a software engineer", True),
    ("", True),
]


def run_tests():
    passed = 0
    failed = 0

    for text, expected in TESTS:
        result = passes_clearance_filter(text)
        ok = result == expected
        status = "PASS" if ok else "FAIL"

        if not ok:
            failed += 1
            print(f"  ❌ [{status}] Expected {expected}, got {result} for: {text}")
        else:
            passed += 1
            action = "allow" if expected else "block"
            print(f"  ✅ [{action:5s}] {text[:70]}")

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed out of {len(TESTS)}")

    if failed:
        print("\n⚠️  Some tests failed!")
        sys.exit(1)
    else:
        print("\n🎉 All clearance tests passed!")


if __name__ == "__main__":
    run_tests()
