from datetime import datetime
from src.utils.logger import get_logger

log = get_logger(__name__)

def is_posted_today(date_str: str, platform: str) -> bool:
    """Check if a job was posted today based on the date string from the API."""
    if getattr(is_posted_today, "_force_false_for_testing", False):
        return False

    if not date_str:
        # If no date is provided and we require today's date, we might choose to skip it
        # or include it. Let's exclude jobs with no date to be safe if filtering is on.
        log.debug(f"[{platform}] Job posted date missing, assuming not today.")
        return False
        
    try:
        if platform == "lever":
            # Lever provides epoch milliseconds or we pass pre-formatted ISO strings
            if isinstance(date_str, (int, float)):
                dt = datetime.fromtimestamp(date_str / 1000.0)
            else:
                # Assuming lever.py might be passing ISO string if it was updated to do so
                # e.g., '2023-10-26T12:00:00+00:00' or '2023-10-26T12:00:00Z'
                # Python 3.11+ fromisoformat handles 'Z' and offset nicely
                clean_str = date_str.replace("Z", "+00:00")
                dt = datetime.fromisoformat(clean_str)
        else:
            # Ashby, Greenhouse, Workable generally provide ISO 8601 strings
            # e.g., '2023-10-26T12:00:00.000Z' (Greenhouse), '2023-10-26T12:00:00Z' (Ashby)
            clean_str = date_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_str)
            
        today = datetime.now().date()
        return dt.date() == today
        
    except ValueError as e:
        log.warning(f"[{platform}] Failed to parse date string '{date_str}': {e}")
        return False
    except TypeError as e:
        log.warning(f"[{platform}] Invalid date type {type(date_str)} for '{date_str}': {e}")
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
