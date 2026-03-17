"""
Security clearance / US citizenship filter — sentence-level negation.

Splits text into sentences and checks each for clearance terms.  Only rejects
when the term is affirmed (no negation word in the same sentence).  This
correctly handles phrases like "does not require security clearance" and
"no US citizenship required" that the old lookbehind regex missed.
"""

import re
from src.config.settings import settings
from src.filters.jd_parser import split_sentences

CLEARANCE_TERMS = re.compile(
    r"\b(top secret|ts/?sci|polygraph|security clearance|active clearance|"
    r"top-secret|clearance required|"
    r"us citizenship(?:\s+required)?|u\.s\.?\s*citizen(?:ship)?)\b",
    re.IGNORECASE,
)

NEGATION_IN_SENTENCE = re.compile(
    r"\b(not|no|don't|doesn't|do not|does not|without|"
    r"never|isn't|is not|aren't|are not|won't|will not|"
    r"not required|not needed|not necessary)\b",
    re.IGNORECASE,
)


def passes_clearance_filter(text: str) -> bool:
    """
    Return False if text requires security clearance or explicit US citizenship.

    Uses sentence-level analysis: a clearance term is only treated as a hard
    requirement when the surrounding sentence does NOT contain a negation.
    Falls back to full-text analysis when abbreviations (e.g. "U.S.") cause
    terms to split across sentence boundaries.
    """
    if not settings.EXCLUDE_CLEARANCE_PATTERN:
        return True

    if not text or not text.strip():
        return True

    if not CLEARANCE_TERMS.search(text):
        return True

    sentences = split_sentences(text)
    for sent in sentences:
        if CLEARANCE_TERMS.search(sent):
            if NEGATION_IN_SENTENCE.search(sent):
                continue
            return False

    # Clearance term exists in full text but wasn't captured in any single
    # sentence (e.g. "U.S. Citizen" split on the abbreviation period).
    # Fall back: if negation words exist anywhere nearby, allow it.
    if NEGATION_IN_SENTENCE.search(text):
        return True

    return False
