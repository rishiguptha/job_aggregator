import re
from src.config.settings import settings

def matches_title(title: str) -> str | None:
    """Check if job title matches keywords. Returns match type or None."""
    t = title.lower()
    
    # Exclude upper-level and intern/co-op roles
    if re.search(settings.EXCLUDE_TITLE_PATTERN, t):
        return None
        
    match_type = None

    # Check plain-text primary keywords
    for kw in settings.TITLE_KEYWORDS:
        if kw in t:
            match_type = "primary"
            break

    # Check regex-based primary keywords (for abbreviations like SDE)
    if not match_type:
        for pattern in getattr(settings, "TITLE_KEYWORDS_REGEX", []):
            if re.search(pattern, t):
                match_type = "primary"
                break

    if not match_type:
        for kw in settings.BONUS_KEYWORDS:
            if kw in t:
                match_type = "bonus"
                break

    # Auto-prioritize entry level/new grad language in title
    if match_type == "bonus" and re.search(settings.NEW_GRAD_PATTERN, t):
        match_type = "primary"

    return match_type
