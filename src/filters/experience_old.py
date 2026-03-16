import re
from src.config.settings import settings

WORD_TO_NUM = {
    'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
    'eleven': 11, 'twelve': 12
}

def parse_years(match_str: str) -> int | None:
    match_str = match_str.lower().strip()
    if match_str in WORD_TO_NUM:
        return WORD_TO_NUM[match_str]
    try:
        return int(match_str)
    except ValueError:
        return None

# We capture the number group so we can extract it precisely
# If there are ranges like "2-4", we parse the right side separately.
EXP_PATTERNS = [
    r'experience\s*[:;]\s*([a-z]+|\d+)\s*\+?\s*years?',
    r'(?:minimum|at\s+least|min\.?)\s*([a-z]+|\d+)\s*(?:\(\d+\)\s*)?\+?\s*years?',
    r'([a-z]+|\d+)\s*(?:\(\d+\)\s*)?\+?\s*years?\s+of\s+(?:professional|relevant|related|hands-on|industry|proven|practical|work|software|data)',
    r'([a-z]+|\d+)\s*(?:\(\d+\)\s*)?\+?\s*yrs?\s*(?:of\s+)?(?:(?:professional|relevant|related|hands-on|industry|proven|practical|work|software|data)\s+)?(?:experience|exp)',
    r'([a-z]+|\d+)\s*(?:\(\d+\)\s*)?\+?\s*years?\s+(?:working\s+)?(?:in|on|with|as\s+a?)\s+(?:\w+\s+){0,4}(?:data|analytics|software|engineer(?:ing)?|field|role|industry|capacity|environment|ingestion|pipeline|development|cloud|machine\s+learning|ml|ai)',
    r'([a-z]+|\d+)\s*(?:\(\d+\)\s*)?\+?\s*years?\s+of\s+\w+',  # Generic: "3+ years of <anything>"
    r'([a-z]+|\d+)\s*(?:\(\d+\)\s*)?\+?\s*[-–to]*\s*(?:\d+\s*[-–]?\s*)?years?\s*(?:of\s+)?(?:(?:professional|relevant|related|hands-on|industry|proven|practical|work|software|data)\s+)?(?:experience|exp)'
]

def extract_max_experience(text: str) -> int | None:
    """Extract max years of experience from text, handling words and ranges."""
    years_found = []
    text = text.lower()
    
    # 1. Clean up "five (5)" formats by keeping only the digit
    text = re.sub(r'(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*\(\s*(\d+)\s*\)', r'\1', text)
    
    # 2. Handle ranges like "2-4", "2 to 4", "2 and 4". We capture the MAX side of the range.
    range_pattern = r'(?:[a-z]+|\d+)\s*(?:-|to|or|and|-)\s*([a-z]+|\d+)\s*\+?\s*years?'
    for m in re.findall(range_pattern, text):
        val = parse_years(m)
        if val is not None:
            years_found.append(val)
            
    # 3. Use normal patterns for singular matches like "5+ years of experience"
    for pattern in EXP_PATTERNS:
        for m in re.findall(pattern, text):
            val = parse_years(m)
            if val is not None:
                years_found.append(val)
                
    return max(years_found) if years_found else None

def passes_experience_filter(description: str) -> tuple[bool, int | None]:
    """Returns (passes, max_exp_found)."""
    max_exp = extract_max_experience(description)
    if max_exp is None:
        return True, None
    return max_exp <= settings.MAX_EXPERIENCE_YEARS, max_exp
