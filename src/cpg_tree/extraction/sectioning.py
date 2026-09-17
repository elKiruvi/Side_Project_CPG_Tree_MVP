"""Deterministic, content-agnostic section-heading detection.

This is an extraction heuristic only. A detected heading is a "section
candidate from page text": it must not be read as semantic section membership
or inferred clinical structure. When no candidate is found, the section stays
``None`` rather than guessing.
"""

from __future__ import annotations

import re
from typing import Final

_HEADING_MAX_LENGTH: Final = 100
_HAS_LETTER: Final = re.compile(r"[^\W\d_]", re.UNICODE)


def detect_section(page_text: str) -> str | None:
    """Return the first uppercase-line candidate on the page, or None.

    A line is a candidate when it contains at least one letter, contains no
    lowercase letters, and is at most ``_HEADING_MAX_LENGTH`` characters long.
    Trailing punctuation is stripped for readability; the verdict remains a
    detection of an uppercase line, nothing more.
    """
    for raw_line in page_text.splitlines():
        line = raw_line.strip()
        if not line or len(line) > _HEADING_MAX_LENGTH:
            continue
        if _HAS_LETTER.search(line) is None:
            continue
        if any(character.islower() for character in line):
            continue
        cleaned = line.rstrip(":.- ")
        return cleaned or line
    return None
