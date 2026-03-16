"""
Smart experience requirement extraction — zero external dependencies.

Uses regex sentence splitting + contextual analysis. No spaCy, no NLTK.
Memory footprint: ~0 MB extra (pure Python stdlib).

Improvements over the old regex filter:
  1. Sentence segmentation → avoids cross-sentence false matches
  2. Context filtering → skips "we have 10 years as a company" sentences
  3. Range-aware → "2-4 years" uses min (2) for filtering, not max (4)
  4. Word numbers → handles "three to five years"
  5. Negation-aware → "no experience required" → New Grad
  6. Experience level tagging for email badges
"""

import re
from src.config.settings import settings


# ── Constants ────────────────────────────────────────────────────────────────

WORD_TO_NUM = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12,
}

# Sentence is about the COMPANY's history, not a job requirement
COMPANY_CONTEXT_PHRASES = [
    "we have", "we've been", "we've had", "our team has", "our company",
    "the company has", "firm has", "organization has", "been in business",
    "founded", "established", "serving clients", "serving customers",
    "industry leader", "track record", "we are a",
]

# JD explicitly says no experience needed
NEGATION_PATTERNS = [
    "no experience required", "no prior experience", "no experience necessary",
    "no experience needed", "experience not required", "experience not necessary",
    "0 years of experience", "zero years of experience",
    "without prior experience", "no professional experience required",
    "no work experience required",
]

# New grad / entry-level signals
NEW_GRAD_SIGNALS = [
    "new grad", "new graduate", "recent grad", "recent graduate",
    "university grad", "college grad", "entry level", "entry-level",
    "early career", "early-career", "fresh graduate", "just graduated",
    "0-1 year", "0 to 1 year", "less than 1 year", "less than one year",
    "no prior experience", "no experience required",
    "bootcamp grad", "career starter", "launching your career",
]

# Experience level tags (used in email badges)
EXP_NEW_GRAD      = "🎓 New Grad"
EXP_0_1           = "📗 0-1 YoE"
EXP_1_2           = "📘 1-2 YoE"
EXP_3_PLUS        = "🔶 3+ YoE"
EXP_NOT_SPECIFIED = "❓ Not Specified"


# ── Sentence Splitter ────────────────────────────────────────────────────────

_SENT_SPLIT = re.compile(r'(?<=[.!?])\s+(?=[A-Z])|[\n\r]+|\s{2,}|[•·■▪►]')


def _split_sentences(text: str) -> list[str]:
    """Split text into rough sentences. Good enough for JD parsing."""
    raw = _SENT_SPLIT.split(text)
    return [s.strip() for s in raw if s and len(s.strip()) > 10]


# ── Number Parser ────────────────────────────────────────────────────────────

def _parse_number(text: str) -> float | None:
    """Parse a number from a string (digit or written word)."""
    t = text.strip().lower().rstrip("+")
    if t in WORD_TO_NUM:
        return float(WORD_TO_NUM[t])
    t = re.sub(r'[()]', '', t).strip()
    try:
        return float(t)
    except ValueError:
        return None


# ── Experience Extraction Pattern ────────────────────────────────────────────

_NUM_WORD = (
    r'(?:\d+|zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)'
)

_EXP_PATTERN = re.compile(
    r'(?:(?:minimum|at\s+least|min\.?|requires?|requiring)\s+)?'
    r'(' + _NUM_WORD + r')'             # group 1: first number
    r'\s*\+?'
    r'(?:\s*\(\d+\)\s*)?'              # optional "(5)" after word
    r'(?:\s*'
    r'([-–—]|to|or)\s*'               # group 2: range separator
    r'(' + _NUM_WORD + r')'             # group 3: second number
    r'\s*\+?'
    r')?'
    r'\s*(?:years?|yrs?)\b',
    re.IGNORECASE,
)

# Context words that make a year-mention about job requirements
_EXP_CONTEXT = re.compile(
    r'\b(?:experience|professional|relevant|related|hands-on|industry|'
    r'proven|practical|work\s+experience|software|data|engineering|'
    r'development|cloud|machine\s+learning|ml|ai|backend|frontend|'
    r'full\s*stack|devops|working|in\s+a\s+role|in\s+the\s+field)\b',
    re.IGNORECASE,
)


# ── Core Logic ───────────────────────────────────────────────────────────────

def _is_company_context(sent: str) -> bool:
    return any(phrase in sent for phrase in COMPANY_CONTEXT_PHRASES)


def _extract_from_sentence(sent: str) -> list[tuple[float, float]]:
    """Extract (min_years, max_years) tuples from a sentence."""
    results = []
    for match in _EXP_PATTERN.finditer(sent):
        first = _parse_number(match.group(1))
        if first is None or first > 20:
            continue
        second_str = match.group(3)
        if match.group(2) and second_str:
            second = _parse_number(second_str)
            if second is not None and second > first:
                results.append((first, second))
            else:
                results.append((first, first))
        else:
            results.append((first, first))
    return results


def _classify_level(min_years: float | None, text_lower: str) -> str:
    if any(sig in text_lower for sig in NEW_GRAD_SIGNALS):
        return EXP_NEW_GRAD
    if any(pat in text_lower for pat in NEGATION_PATTERNS):
        return EXP_NEW_GRAD
    if min_years is None:
        return EXP_NOT_SPECIFIED
    if min_years < 1:
        return EXP_NEW_GRAD
    if min_years <= 1:
        return EXP_0_1
    if min_years <= 2:
        return EXP_1_2
    return EXP_3_PLUS


# ── Public API ───────────────────────────────────────────────────────────────

def passes_experience_filter(description: str) -> tuple[bool, int | None, str]:
    """
    Analyze job description for experience requirements.

    Returns:
        (passes_filter, min_years_required, experience_level_tag)

    Logic:
      - Ranges: "2-4 years" uses MIN (2) for filtering (generous)
      - Multiple mentions: takes MAX across all (strictest requirement)
      - Company-context sentences are ignored
      - Only counts year-mentions near experience-related words
    """
    if not description or not description.strip():
        return True, None, EXP_NOT_SPECIFIED

    text_lower = description.lower()

    # Fast path: no year-related words at all
    if not any(kw in text_lower for kw in ("experience", "years", "year", "yr", "yrs")):
        level = EXP_NEW_GRAD if any(s in text_lower for s in NEW_GRAD_SIGNALS) else EXP_NOT_SPECIFIED
        return True, None, level

    # Fast path: explicit negation
    if any(pat in text_lower for pat in NEGATION_PATTERNS):
        return True, 0, EXP_NEW_GRAD

    # Sentence-level extraction
    sentences = _split_sentences(description)
    all_ranges: list[tuple[float, float]] = []

    for sent in sentences:
        sent_lower = sent.lower()

        # Skip if no year words
        if not any(kw in sent_lower for kw in ("year", "years", "yr", "yrs")):
            continue

        # Skip company-context
        if _is_company_context(sent_lower):
            continue

        ranges = _extract_from_sentence(sent_lower)

        # Only count if sentence has experience-related context
        if ranges and (_EXP_CONTEXT.search(sent_lower) or "experience" in sent_lower):
            all_ranges.extend(ranges)

    # No experience numbers found
    if not all_ranges:
        level = EXP_NEW_GRAD if any(s in text_lower for s in NEW_GRAD_SIGNALS) else EXP_NOT_SPECIFIED
        return True, None, level

    # min of each range (generous), max across all mentions (strictest)
    min_required = max(r[0] for r in all_ranges)

    level = _classify_level(min_required, text_lower)
    passes = min_required <= settings.MAX_EXPERIENCE_YEARS

    return passes, int(min_required), level
