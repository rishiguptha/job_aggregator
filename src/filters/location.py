import re
from src.config.settings import settings

# ── Non-US country / region indicators (lowercase) ──────────────────────────
_NON_US_PATTERNS = [
    # Regions
    "emea", "apac", "latam", "europe", "asia", "middle east",
    # Countries
    "afghanistan", "albania", "algeria", "argentina", "armenia", "australia",
    "austria", "azerbaijan", "bahrain", "bangladesh", "belarus", "belgium",
    "bolivia", "bosnia", "brazil", "brunei", "bulgaria", "cambodia", "cameroon",
    "canada", "chile", "china", "colombia", "costa rica", "croatia", "cuba",
    "cyprus", "czech republic", "czechia", "denmark", "dominican republic",
    "ecuador", "egypt", "el salvador", "estonia", "ethiopia", "finland",
    "france", "germany", "ghana", "greece", "guatemala",
    "honduras", "hong kong", "hungary", "iceland", "india", "indonesia",
    "iran", "iraq", "ireland", "israel", "italy", "jamaica", "japan",
    "jordan", "kazakhstan", "kenya", "korea", "kuwait", "latvia", "lebanon",
    "libya", "lithuania", "luxembourg", "malaysia", "malta", "mexico",
    "moldova", "mongolia", "morocco", "mozambique", "myanmar", "nairobi",
    "nepal", "netherlands", "new zealand", "nigeria", "norway", "oman",
    "pakistan", "panama", "paraguay", "peru", "philippines", "poland",
    "portugal", "qatar", "romania", "russia", "rwanda", "saudi arabia",
    "senegal", "serbia", "singapore", "slovakia", "slovenia", "south africa",
    "south korea", "spain", "sri lanka", "sudan", "sweden", "switzerland",
    "syria", "taiwan", "tanzania", "thailand", "tunisia", "turkey", "turkiye",
    "uganda", "ukraine", "united arab emirates", "uae", "united kingdom",
    "uruguay", "uzbekistan", "venezuela", "vietnam", "zambia", "zimbabwe",
    # Common non-US cities
    "london", "berlin", "paris", "toronto", "montreal", "vancouver",
    "sydney", "melbourne", "mumbai", "bengaluru", "bangalore", "hyderabad",
    "pune", "chennai", "kolkata", "delhi", "gurgaon", "noida", "ahmedabad",
    "coimbatore", "tokyo", "osaka", "seoul", "beijing", "shanghai",
    "shenzhen", "amsterdam", "rotterdam", "dublin", "edinburgh", "manchester",
    "munich", "hamburg", "frankfurt", "zurich", "geneva", "stockholm",
    "copenhagen", "oslo", "helsinki", "warsaw", "prague", "budapest",
    "vienna", "lisbon", "madrid", "barcelona", "milan", "rome",
    "brussels", "tel aviv", "dubai", "abu dhabi", "riyadh", "cairo",
    "lagos", "cape town", "johannesburg", "nairobi", "bogota", "lima",
    "santiago", "buenos aires", "são paulo", "sao paulo", "rio de janeiro",
    "mexico city", "guadalajara", "monterrey", "bangkok", "jakarta",
    "kuala lumpur", "manila", "ho chi minh", "hanoi", "singapore",
    "taipei", "kyiv", "kiev", "moscow", "saint petersburg",
    # Common non-US patterns
    "only within poland", "remote germany", "remote, united kingdom",
    # Non-US country codes (standalone 2-letter)
    "españa",
]

# ── US indicators ────────────────────────────────────────────────────────────
_US_STATES = [
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana", "maine",
    "maryland", "massachusetts", "michigan", "minnesota", "mississippi",
    "missouri", "montana", "nebraska", "nevada", "new hampshire",
    "new jersey", "new mexico", "new york", "north carolina", "north dakota",
    "ohio", "oklahoma", "oregon", "pennsylvania", "rhode island",
    "south carolina", "south dakota", "tennessee", "texas", "utah", "vermont",
    "virginia", "washington", "west virginia", "wisconsin", "wyoming",
    "district of columbia",
]

# Two-letter state abbreviations — matched with word boundaries
_US_STATE_ABBREVS = [
    "al", "ak", "az", "ar", "ca", "co", "ct", "de", "fl", "ga",
    "hi", "id", "il", "in", "ia", "ks", "ky", "la", "me", "md",
    "ma", "mi", "mn", "ms", "mo", "mt", "ne", "nv", "nh", "nj",
    "nm", "ny", "nc", "nd", "oh", "ok", "or", "pa", "ri", "sc",
    "sd", "tn", "tx", "ut", "vt", "va", "wa", "wv", "wi", "wy", "dc",
]

_US_CITIES = [
    "new york", "los angeles", "chicago", "houston", "phoenix", "philadelphia",
    "san antonio", "san diego", "dallas", "san jose", "austin", "jacksonville",
    "fort worth", "columbus", "charlotte", "indianapolis", "san francisco",
    "seattle", "denver", "nashville", "oklahoma city", "el paso", "boston",
    "portland", "las vegas", "memphis", "louisville", "baltimore", "milwaukee",
    "albuquerque", "tucson", "fresno", "mesa", "sacramento", "atlanta",
    "kansas city", "omaha", "raleigh", "miami", "minneapolis", "cleveland",
    "tampa", "st. louis", "pittsburgh", "cincinnati", "orlando", "irvine",
    "aurora", "arlington", "detroit", "salt lake city", "bellevue",
    "sunnyvale", "mountain view", "palo alto", "redmond", "cupertino",
    "menlo park", "santa clara", "jersey city", "hoboken", "brooklyn",
    "manhattan", "san mateo", "burlingame", "redwood city", "lehi",
    "provo", "scottsdale", "tempe", "boulder", "ann arbor", "durham",
    "reston", "mclean", "tysons", "herndon", "plano", "irving",
    "richmond", "columbia",
]

_US_KEYWORDS = [
    "united states", "usa",
    "remote - us", "remote, us", "remote - usa", "remote - united states",
    "remote, usa", "remote (us)", "remote (usa)", "us remote", "usa remote",
    "us-remote", "usa-remote",
]

# Build a word-boundary regex for 2-letter state abbrevs to avoid false matches
_STATE_ABBREV_PATTERN = re.compile(
    r'(?:^|[\s,;/|(])'
    r'(' + '|'.join(re.escape(abbr) for abbr in _US_STATE_ABBREVS) + r')'
    r'(?:$|[\s,;/|)])',
    re.IGNORECASE,
)


def passes_location_filter(location: str) -> bool:
    """
    Check if a job location is within the United States.
    If location filtering is disabled, always returns True.
    """
    if not getattr(settings, "FILTER_LOCATION_US", False):
        return True

    if not location or location.strip().lower() in ("unknown", ""):
        # No location info — reject by default (likely non-US)
        return False

    loc = location.lower().strip()

    # ── 1. Reject if location contains a known non-US indicator ──────────
    for pattern in _NON_US_PATTERNS:
        if pattern in loc:
            return False

    # ── 2. Accept if location explicitly mentions US ─────────────────────
    for kw in _US_KEYWORDS:
        if kw in loc:
            return True

    # Accept full US state names
    for state in _US_STATES:
        if state in loc:
            return True

    # Accept known US cities
    for city in _US_CITIES:
        if city in loc:
            return True

    # Accept 2-letter state abbreviations (word-boundary safe)
    if _STATE_ABBREV_PATTERN.search(loc):
        return True

    # ── 3. Generic "Remote" without country qualifier → assume US ────────
    if "remote" in loc:
        return True

    # ── 4. Default: reject unknown locations when filtering is on ────────
    return False
