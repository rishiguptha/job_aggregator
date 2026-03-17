from datetime import datetime
from src.config.settings import settings
from src.utils.logger import get_logger

log = get_logger(__name__)


def passes_date_filter(date_str: str, platform: str) -> bool:
    """Single entry point for date filtering used by all fetchers."""
    if not settings.FETCH_ONLY_TODAY:
        return is_posted_current_year(date_str, platform)
    if is_posted_today(date_str, platform):
        return True
    if not settings.TODAY_ONLY and is_posted_yesterday(date_str, platform):
        return True
    return False

def is_posted_today(date_str: str, platform: str) -> bool:
    """Check if a job was posted today based on the date string from the API."""
    if getattr(is_posted_today, "_force_false_for_testing", False):
        return False

    if not date_str:
        log.debug(f"[{platform}] Job posted date missing, assuming not today.")
        return False
        
    try:
        if platform == "lever":
            if isinstance(date_str, (int, float)):
                dt = datetime.fromtimestamp(date_str / 1000.0)
            else:
                clean_str = date_str.replace("Z", "+00:00")
                dt = datetime.fromisoformat(clean_str)
        else:
            clean_str = date_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_str)
            
        today = datetime.now().date()
        return dt.date() == today
        
    except (ValueError, TypeError) as e:
        log.warning(f"[{platform}] Failed to parse date string '{date_str}': {e}")
        return False

def is_posted_yesterday(date_str: str, platform: str) -> bool:
    """Check if a job was posted yesterday based on the date string from the API."""
    if not date_str:
        return False
        
    try:
        if platform == "lever":
            if isinstance(date_str, (int, float)):
                dt = datetime.fromtimestamp(date_str / 1000.0)
            else:
                clean_str = date_str.replace("Z", "+00:00")
                dt = datetime.fromisoformat(clean_str)
        else:
            clean_str = date_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_str)
            
        from datetime import timedelta
        yesterday = datetime.now().date() - timedelta(days=1)
        return dt.date() == yesterday
        
    except (ValueError, TypeError) as e:
        return False

def is_posted_current_year(date_str: str, platform: str) -> bool:
    """Check if a job was posted in the current year."""
    if not date_str:
        return False

    try:
        if platform == "lever":
            if isinstance(date_str, (int, float)):
                dt = datetime.fromtimestamp(date_str / 1000.0)
            else:
                clean_str = date_str.replace("Z", "+00:00")
                dt = datetime.fromisoformat(clean_str)
        else:
            clean_str = date_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_str)

        return dt.year == datetime.now().year

    except (ValueError, TypeError) as e:
        log.debug(f"[{platform}] Could not parse date '{date_str}' for year check: {e}")
        return False
