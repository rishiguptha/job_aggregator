import re
from src.config.settings import settings

def passes_phd_filter(text: str) -> bool:
    """Return False if text requires a PhD, True otherwise."""
    if not settings.EXCLUDE_PHD_PATTERN:
        return True
    
    # Check for PhD requirement
    if re.search(settings.EXCLUDE_PHD_PATTERN, text, re.IGNORECASE):
        # We also want to check for masters if PhD is found. If they say "Masters or PhD", we might want to keep it?
        # Actually our regex has a lookahead `(?!\s+(?:not\s+required|optional|preferred|or\s+equivalent|or\s+master))`
        # So we can just trust the regex.
        return False
        
    return True
