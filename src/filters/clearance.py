import re
from src.config.settings import settings

def passes_clearance_filter(text: str) -> bool:
    """Return False if text requires security clearance or explicit US Citizenship, True otherwise."""
    if not settings.EXCLUDE_CLEARANCE_PATTERN:
        return True
    
    if re.search(settings.EXCLUDE_CLEARANCE_PATTERN, text, re.IGNORECASE):
        return False
    return True
