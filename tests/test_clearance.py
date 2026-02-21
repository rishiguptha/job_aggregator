from src.filters.clearance import passes_clearance_filter

tests = [
    ("We need a data engineer with Top Secret clearance", False),
    ("Requires active TS/SCI with polygraph", False),
    ("Requires US citizenship", False),
    ("U.S. Citizen required", False),
    ("Secret clearance required", False), # Wait, "secret" by itself is not in regex unless it says "clearance required"
    ("No clearance required", True), # "clearance required" is in the text, so this will fail! Let's check!
    ("We are a top secret company", False),
    ("Data Engineer role", True)
]

for text, expected in tests:
    result = passes_clearance_filter(text)
    print(f"[{'PASS' if result == expected else 'FAIL'}] Expected {expected}, got {result} for: {text}")

