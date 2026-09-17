"""Source document identity for the provenance chain."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

from cpg_tree.knowledge._validation import validate_identifier

_SHA256_PATTERN: Final = re.compile(r"^[0-9a-f]{64}$")
_MIN_SIZE: Final = 0


@dataclass(frozen=True, slots=True)
class SourceDocument:
    """Immutable identity of a raw source document.

    Identity is content-addressed: ``document_id`` derives from the SHA-256
    of the exact document bytes, so identical bytes always produce the same
    identity and any byte change produces a new one. The filename is recorded
    for human reference only; it is never part of the identity.
    """

    document_id: str
    filename: str
    sha256: str
    file_format: str = "pdf"
    byte_size: int | None = None

    def __post_init__(self) -> None:
        validate_identifier(self.document_id, "SourceDocument.document_id")
        if not self.filename:
            raise ValueError("SourceDocument.filename must not be empty")
        if _SHA256_PATTERN.fullmatch(self.sha256) is None:
            raise ValueError("SourceDocument.sha256 must be a 64-character hex digest")
        if self.byte_size is not None and self.byte_size < _MIN_SIZE:
            raise ValueError("SourceDocument.byte_size must not be negative")
