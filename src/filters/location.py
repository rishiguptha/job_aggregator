from src.config.settings import settings

def passes_location_filter(location: str) -> bool:
    """
    Check if a job location is within the United States.
    If location filtering is disabled, always returns True.
    """
    if not getattr(settings, "FILTER_LOCATION_US", False):
        return True
        
    loc = location.lower()
    
    # Common global/non-US indicators
    exclude_keywords = [
        "uk", "london", "europe", "emea", "apac", "latam",
        "india", "bengaluru", "bangalore", "canada", "toronto",
        "australia", "sydney", "germany", "berlin", "france", "paris"
    ]
    
    if any(ex in loc for ex in exclude_keywords):
        return False
        
    # US indicators
    us_keywords = [
        "us", "usa", "united states", "america", "remote - us",
        "new york", "ny", "san francisco", "sf", "california", "ca",
        "seattle", "wa", "boston", "ma", "austin", "tx", "chicago", "il"
    ]
    
    # If it exactly says "remote", we usually assume it might encompass US 
    if "remote" in loc and len(loc) < 15:
        return True
        
    if any(inc in loc for inc in us_keywords):
        return True
        
    # Default to False if we are strictly filtering for US and couldn't match
    return False
