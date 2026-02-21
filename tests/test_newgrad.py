import re
from src.config.settings import settings
from src.filters.title import matches_title
from src.filters.phd import passes_phd_filter

titles = [
    "Data Engineer",
    "Data Engineering Intern",
    "Senior Data Engineer",
    "Data Engineer, University Graduate",
    "Analytics Engineer (Entry Level)",
    "Data Engineer Co-op",
    "Junior Data Engineer"
]

print("--- Title Tests ---")
for t in titles:
    res = matches_title(t)
    print(f"[{'BLOCK' if not res else str(res).upper()}] {t}")

print("\n--- PhD Tests ---")
descs = [
    "Requires a PhD in Computer Science",
    "Master's degree or PhD preferred",
    "PhD optional, Master's required",
    "Must hold a Ph.D. or equivalent",
    "looking for a ph.d.",
    "BS in CS requires, PhD not required"
]
for d in descs:
    print(f"[{'PASS' if passes_phd_filter(d) else 'FAIL'}] {d}")

