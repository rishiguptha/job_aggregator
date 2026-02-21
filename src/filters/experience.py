import re
from src.config.settings import settings

EXP_PATTERNS = [
    r'(\d+)\s*\+?\s*[-–to]*\s*(?:\d+\s*[-–]?\s*)?years?\s*(?:of\s+)?(?:(?:professional|relevant|related|hands-on|industry|proven|practical|work|software|data)\s+)?(?:experience|exp)',
    r'experience\s*[:;]\s*(\d+)\s*\+?\s*years?',
    r'(?:minimum|at\s+least|min\.?)\s*(\d+)\s*years?',
    r'(\d+)\s*\+?\s*years?\s+of\s+(?:professional|relevant|related|hands-on|industry|proven|practical|work|software|data)',
    r'(\d+)\s*\+?\s*yrs?\s*(?:of\s+)?(?:(?:professional|relevant|related|hands-on|industry|proven|practical|work|software|data)\s+)?(?:experience|exp)',
    r'(\d+)\s*\+?\s*years?\s+(?:working\s+)?(?:in|as\s+a?)\s+(?:\w+\s+){0,4}(?:data|analytics|software|engineer(?:ing)?|field|role|industry|capacity|environment)',
]

def extract_max_experience(text: str) -> int | None:
    """Extract max years of experience from text."""
    years_found = []
    for pattern in EXP_PATTERNS:
        for m in re.findall(pattern, text, re.IGNORECASE):
            try:
                years_found.append(int(m))
            except ValueError:
                continue
    return max(years_found) if years_found else None

def passes_experience_filter(description: str) -> tuple[bool, int | None]:
    """Returns (passes, max_exp_found)."""
    max_exp = extract_max_experience(description)
    if max_exp is None:
        return True, None
    return max_exp <= settings.MAX_EXPERIENCE_YEARS, max_exp
