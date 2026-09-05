"""Masks likely personal identifiers before any text reaches the LLM.

The product's real PII boundary is architectural (Decision 2 in the README:
no student accounts, no student data collected at all). This module is a
second, narrower layer: teachers sometimes paste content — a topic
description, a pasted paragraph from a document — that incidentally
contains an email, phone number, or roll number. Catch the cheap, common
cases with regex; don't try to catch names or addresses here.
"""

import re

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE_RE = re.compile(r"(?:\+91[\s-]?)?\b[6-9]\d{9}\b")
_ROLL_NUMBER_RE = re.compile(r"\broll\s*(?:no\.?|number)?\s*[:#-]?\s*\d+\b", re.IGNORECASE)

_PATTERNS = {
    "email": _EMAIL_RE,
    "phone": _PHONE_RE,
    "roll_number": _ROLL_NUMBER_RE,
}


def scrub_pii(text: str) -> tuple[str, list[str]]:
    """Returns (cleaned_text, list of PII categories found and masked)."""
    hits: list[str] = []
    cleaned = text
    for label, pattern in _PATTERNS.items():
        if pattern.search(cleaned):
            hits.append(label)
            cleaned = pattern.sub(f"[REDACTED_{label.upper()}]", cleaned)
    return cleaned, hits
