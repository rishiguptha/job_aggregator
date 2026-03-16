#!/usr/bin/env python3
"""
Migration script: Regex experience filter → Smart sentence-based filter.

Run from project root:
    python migrate_experience_nlp.py

What it does:
  1. Patches all 6 fetchers to handle (passes, min_exp, exp_level) 3-value return
  2. Patches email.py to show experience level badge tags
  3. Patches main.py log lines + dry-run output
  4. No new dependencies — pure Python stdlib

After running:
    uv run python tests/test_experience_nlp.py   # verify
    uv run main.py --dry-run                      # live test
"""

from pathlib import Path

ROOT = Path(__file__).parent

# ─────────────────────────────────────────────────────────────────────────────
# 1. Patch fetchers: 2-value unpack → 3-value unpack + add exp_level to dict
# ─────────────────────────────────────────────────────────────────────────────

FETCHER_FILES = [
    "src/fetchers/greenhouse.py",
    "src/fetchers/lever.py",
    "src/fetchers/ashby.py",
    "src/fetchers/workable.py",
    "src/fetchers/oraclecloud.py",
]

for fpath in FETCHER_FILES:
    p = ROOT / fpath
    if not p.exists():
        print(f"  ⚠️  Skipped (not found): {fpath}")
        continue

    text = p.read_text()
    original = text

    # passes, max_exp = ... → passes, min_exp, exp_level = ...
    text = text.replace(
        "passes, max_exp = passes_experience_filter(",
        "passes, min_exp, exp_level = passes_experience_filter("
    )

    # "experience": max_exp → "experience": min_exp
    text = text.replace(
        '"experience": max_exp,',
        '"experience": min_exp,'
    )

    # Add exp_level to the job dict
    if '"exp_level": exp_level,' not in text:
        text = text.replace(
            '"passes_filter": passes,',
            '"passes_filter": passes,\n                "exp_level": exp_level,'
        )

    if text != original:
        p.write_text(text)
        print(f"  ✅ Patched: {fpath}")
    else:
        print(f"  ℹ️  No changes needed: {fpath}")


# ── Workday fetcher (different variable names) ───────────────────────────────
wd_path = ROOT / "src/fetchers/workday.py"
if wd_path.exists():
    text = wd_path.read_text()
    original = text

    text = text.replace(
        "passes_exp, max_exp = passes_experience_filter(clean_text) if clean_text else (True, None)",
        'passes_exp, min_exp, exp_level = passes_experience_filter(clean_text) if clean_text else (True, None, "❓ Not Specified")'
    )

    text = text.replace(
        '"experience": max_exp,',
        '"experience": min_exp,'
    )

    if '"exp_level": exp_level,' not in text:
        text = text.replace(
            '"passes_filter": passes_exp,',
            '"passes_filter": passes_exp,\n                    "exp_level": exp_level,'
        )

    if text != original:
        wd_path.write_text(text)
        print(f"  ✅ Patched: src/fetchers/workday.py")
    else:
        print(f"  ℹ️  No changes needed: src/fetchers/workday.py")


# ─────────────────────────────────────────────────────────────────────────────
# 2. Patch email.py: add exp_level badge next to experience line
# ─────────────────────────────────────────────────────────────────────────────

email_path = ROOT / "src/notifications/email.py"
if email_path.exists():
    text = email_path.read_text()
    original = text

    old_exp_line = 'exp_text = f"{job[\'experience\']} yrs" if job["experience"] else "Not specified (likely entry-level)"'
    new_exp_line = (
        'exp_text = f"{job[\'experience\']} yrs" if job["experience"] else "Not specified"\n'
        '        exp_level = job.get("exp_level", "❓ Not Specified")\n'
        '        exp_level_colors = {\n'
        '            "🎓 New Grad": ("#e8f5e9", "#2e7d32"),\n'
        '            "📗 0-1 YoE": ("#e8f5e9", "#2e7d32"),\n'
        '            "📘 1-2 YoE": ("#e3f2fd", "#1565c0"),\n'
        '            "🔶 3+ YoE": ("#fff3e0", "#e65100"),\n'
        '            "❓ Not Specified": ("#f5f5f5", "#616161"),\n'
        '        }\n'
        '        exp_bg, exp_fg = exp_level_colors.get(exp_level, ("#f5f5f5", "#616161"))'
    )
    text = text.replace(old_exp_line, new_exp_line)

    old_display = '<p style="color:#777; margin:4px 0; font-size:13px;">📋 Experience: {exp_text}</p>'
    new_display = (
        '<p style="color:#777; margin:4px 0; font-size:13px;">'
        '📋 Experience: {exp_text} '
        '<span style="font-size:11px; padding:2px 6px; border-radius:10px; '
        'background:{exp_bg}; color:{exp_fg}; margin-left:6px;">{exp_level}</span>'
        '</p>'
    )
    text = text.replace(old_display, new_display)

    if text != original:
        email_path.write_text(text)
        print(f"  ✅ Patched: src/notifications/email.py")
    else:
        print(f"  ℹ️  No changes needed: src/notifications/email.py")


# ─────────────────────────────────────────────────────────────────────────────
# 3. Patch main.py: update log + dry-run to show exp_level
# ─────────────────────────────────────────────────────────────────────────────

main_path = ROOT / "main.py"
if main_path.exists():
    text = main_path.read_text()
    original = text

    # Update filtered log line
    old_log = (
        'log.info(f"  🚫 Filtered (Exp): {job[\'title\']} @ {job[\'company\']} "\n'
        '                     f"(requires {job[\'experience\']}+ yrs)")'
    )
    new_log = (
        'log.info(f"  🚫 Filtered (Exp): {job[\'title\']} @ {job[\'company\']} "\n'
        '                     f"({job.get(\'exp_level\', \'?\')} — requires {job[\'experience\']}+ yrs)")'
    )
    text = text.replace(old_log, new_log)

    # Update dry-run display to show exp_level
    old_dry = 'exp = f"{j[\'experience\']} yrs" if j["experience"] else "n/a"'
    new_dry = 'exp = f"{j[\'experience\']} yrs" if j["experience"] else "n/a"\n            exp_level = j.get("exp_level", "❓")'
    text = text.replace(old_dry, new_dry)

    old_dry_print = 'print(f"     📍 {j[\'location\']} | Exp: {exp}{posted}")'
    new_dry_print = 'print(f"     📍 {j[\'location\']} | Exp: {exp} | {exp_level}{posted}")'
    text = text.replace(old_dry_print, new_dry_print)

    if text != original:
        main_path.write_text(text)
        print(f"  ✅ Patched: main.py")
    else:
        print(f"  ℹ️  No changes needed: main.py")


# ─────────────────────────────────────────────────────────────────────────────
# 4. Summary
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("Migration complete! No new dependencies needed.")
print("=" * 60)
print("""
Next steps:
  1. Replace src/filters/experience.py with the new version
     (should already be in place if you copied it)

  2. Run tests:
       uv run python tests/test_experience_nlp.py

  3. Dry run to verify:
       uv run main.py --dry-run

  4. Check email output:
       uv run main.py --test-email
""")
