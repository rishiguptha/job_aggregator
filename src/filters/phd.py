"""
PhD requirement filter — sentence-level negation + multi-degree handling.

Splits text into sentences and checks each for PhD terms.  Only rejects when
PhD is a hard, standalone requirement.  Correctly handles:
  - "PhD or Master's degree" → pass (multi-degree list)
  - "Bachelor's, Master's, or PhD" → pass (multi-degree list)
  - "PhD preferred but not required" → pass (softener)
  - "PhD required" → fail
"""

import re
from src.config.settings import settings
from src.filters.jd_parser import split_sentences

PHD_TERMS = re.compile(r"\b(ph\.?d\.?)\b", re.IGNORECASE)

PHD_SOFTENERS = re.compile(
    r"\b(not required|optional|preferred|"
    r"nice to have|is a plus|is a bonus|desired|a bonus)\b",
    re.IGNORECASE,
)

MULTI_DEGREE = re.compile(
    r"(?:"
    r"\b(?:bachelor|master|bs|ms|ba|ma|b\.s|m\.s)\b.*\bor\b.*\bph\.?d"
    r"|"
    r"\bph\.?d\.?\s*(?:,\s*|\s+or\s+|\s*/\s*)\s*(?:master|ms|m\.s|bachelor|bs|b\.s)\b"
    r"|"
    r"\b(?:bachelor|master|bs|ms|ba|ma|b\.s|m\.s)\b.*(?:,|/)\s*\bph\.?d"
    r")",
    re.IGNORECASE,
)

NEGATION_IN_SENTENCE = re.compile(
    r"\b(not|no|don't|doesn't|do not|does not|without|"
    r"never|isn't|is not|not required|not needed|not necessary)\b",
    re.IGNORECASE,
)


def passes_phd_filter(text: str) -> bool:
    """
    Return False if text strictly requires a PhD, True otherwise.

    Handles multi-degree lists (PhD is one of several accepted degrees),
    softeners (preferred/optional), and sentence-level negation.
    """
    if not settings.EXCLUDE_PHD_PATTERN:
        return True

    if not text or not text.strip():
        return True

    sentences = split_sentences(text)
    for sent in sentences:
        if not PHD_TERMS.search(sent):
            continue

        if MULTI_DEGREE.search(sent):
            continue

        if PHD_SOFTENERS.search(sent):
            continue

        if NEGATION_IN_SENTENCE.search(sent):
            continue

        return False

    return True
