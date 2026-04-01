"""
JD (Job Description) parser — stdlib only, zero dependencies.

Provides:
  1. clean_html()        — HTMLParser-based HTML→text with block boundaries
  2. split_sentences()   — regex sentence splitter (shared across filters)
  3. parse_jd_sections() — classify JD text into required/preferred/about/other
"""

import re
from html.parser import HTMLParser


# ── HTML Cleaner ──────────────────────────────────────────────────────────────

_BLOCK_TAGS = frozenset({
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "div", "li", "ul", "ol", "br",
    "tr", "td", "th", "table",
    "section", "article", "header", "footer",
    "blockquote", "dt", "dd", "hr",
})

_SKIP_TAGS = frozenset({"script", "style"})


class _HTMLTextExtractor(HTMLParser):
    """Extract text from HTML, inserting newlines at block-level boundaries."""

    def __init__(self):
        super().__init__()
        self._parts: list[str] = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        tag_l = tag.lower()
        if tag_l in _SKIP_TAGS:
            self._skip = True
        elif tag_l in _BLOCK_TAGS:
            self._parts.append("\n")

    def handle_endtag(self, tag):
        tag_l = tag.lower()
        if tag_l in _SKIP_TAGS:
            self._skip = False
        elif tag_l in _BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data):
        if not self._skip:
            self._parts.append(data)

    def get_text(self) -> str:
        return "".join(self._parts)


def clean_html(raw_html: str) -> str:
    """Convert HTML to plain text, preserving block-level boundaries as newlines."""
    import html as html_mod

    text = html_mod.unescape(raw_html)
    extractor = _HTMLTextExtractor()
    extractor.feed(text)
    result = extractor.get_text()
    result = re.sub(r"\n{3,}", "\n\n", result)
    result = re.sub(r"[ \t]+", " ", result)
    return result.strip()


# ── Sentence Splitter ─────────────────────────────────────────────────────────

_SENT_SPLIT = re.compile(
    r"(?<=[.!?])"
    r"(?<!\b[A-Za-z]\.)"   # don't split after single-letter abbreviation (U. S.)
    r"\s+(?=[A-Za-z])"
    r"|[\n\r]+|\s{2,}|[•·■▪►]"
)


def split_sentences(text: str) -> list[str]:
    """Split text into rough sentences. Good enough for JD parsing."""
    raw = _SENT_SPLIT.split(text)
    return [s.strip() for s in raw if s and len(s.strip()) > 10]


# ── Section Parser ────────────────────────────────────────────────────────────

REQUIRED_HEADERS = re.compile(
    r"(?:minimum|required|must.?have|basic|what you.?(?:ll )?need|"
    r"you (?:should )?have|qualifications?|requirements?|"
    r"what we.?re looking for|who you are|about you|"
    r"skills?\s*(?:and |& )?(?:qualifications?|requirements?)|essential)",
    re.IGNORECASE,
)

PREFERRED_HEADERS = re.compile(
    r"(?:preferred|nice to have|bonus|ideally|desired|"
    r"plus|additional|not required|what.?s nice|"
    r"it.?s a plus|extra credit|you might also|good to have)",
    re.IGNORECASE,
)

ABOUT_HEADERS = re.compile(
    r"(?:about (?:us|the company|the team|the role)|"
    r"who we are|our (?:mission|culture|story)|"
    r"company (?:overview|description)|what we do|the opportunity|"
    r"overview|job (?:description|summary))",
    re.IGNORECASE,
)

RESPONSIBILITY_HEADERS = re.compile(
    r"(?:responsibilities|what you.?ll do|your (?:role|impact)|"
    r"key (?:responsibilities|duties)|day to day|in this role)",
    re.IGNORECASE,
)

SECTION_REQUIRED = "required"
SECTION_PREFERRED = "preferred"
SECTION_ABOUT = "about"
SECTION_RESPONSIBILITIES = "responsibilities"
SECTION_UNSTRUCTURED = "unstructured"

_MAX_HEADER_LEN = 60


def _classify_header(line: str) -> str | None:
    """Return section type if `line` looks like a JD section header, else None."""
    stripped = line.strip().rstrip(":")
    if not stripped or len(stripped) > _MAX_HEADER_LEN:
        return None
    # Check PREFERRED / ABOUT / RESPONSIBILITIES before REQUIRED because
    # generic terms like "qualifications" appear in both "preferred qualifications"
    # and "minimum qualifications"; checking narrow patterns first avoids
    # misclassifying "preferred qualifications" as a required section.
    if PREFERRED_HEADERS.search(stripped):
        return SECTION_PREFERRED
    if ABOUT_HEADERS.search(stripped):
        return SECTION_ABOUT
    if RESPONSIBILITY_HEADERS.search(stripped):
        return SECTION_RESPONSIBILITIES
    if REQUIRED_HEADERS.search(stripped):
        return SECTION_REQUIRED
    return None


def parse_jd_sections(clean_text: str) -> dict[str, str]:
    """
    Split a cleaned JD into classified sections.

    Iterates line-by-line; when a line matches a known header pattern all
    subsequent lines are assigned to that section until the next header.
    Works on both original-case and lowercased text.

    Returns a dict with keys: required, preferred, about, responsibilities,
    unstructured.  When no clear headers are detected the entire text goes
    into 'unstructured'.
    """
    buckets: dict[str, list[str]] = {
        SECTION_REQUIRED: [],
        SECTION_PREFERRED: [],
        SECTION_ABOUT: [],
        SECTION_RESPONSIBILITIES: [],
        SECTION_UNSTRUCTURED: [],
    }

    current = SECTION_UNSTRUCTURED
    classified_any = False

    for line in clean_text.split("\n"):
        section_type = _classify_header(line)
        if section_type is not None:
            current = section_type
            classified_any = True
            continue
        buckets[current].append(line)

    result = {k: "\n".join(v).strip() for k, v in buckets.items()}

    if not classified_any:
        result[SECTION_UNSTRUCTURED] = clean_text

    return result
