"""Extraction-layer data model: per-run metadata and page summaries.

This module holds pipeline artifacts, not canonical clinical knowledge. Status
values are machine-readable facts about text extraction only; they never claim
anything about clinical content.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from cpg_tree.knowledge._validation import validate_identifier, validate_iso_date
from cpg_tree.knowledge.documents import SourceDocument
from cpg_tree.knowledge.provenance import SourceFragment

_FIRST_PAGE: Final = 1
_MIN_COUNT: Final = 0
_MIN_THRESHOLD: Final = 1


class ExtractionStatus(StrEnum):
    """Machine-readable text-extraction status of a single page."""

    OK = "OK"
    SPARSE_TEXT = "SPARSE_TEXT"
    NO_TEXT = "NO_TEXT"
    EXTRACTION_ERROR = "EXTRACTION_ERROR"


@dataclass(frozen=True, slots=True)
class PageExtraction:
    """Extracted text and factual inspection data for one page.

    ``embedded_image_count`` counts embedded image XObjects found in the page
    resources; ``None`` means the resources were not inspectable. It is a
    factual PDF inspection result, never an interpretation of image content.
    """

    page_number: int
    text: str
    embedded_image_count: int | None
    status: ExtractionStatus

    @property
    def char_count(self) -> int:
        return len(self.text)

    def __post_init__(self) -> None:
        if self.page_number < _FIRST_PAGE:
            raise ValueError("PageExtraction.page_number must be positive")
        if self.embedded_image_count is not None and self.embedded_image_count < _MIN_COUNT:
            raise ValueError("PageExtraction.embedded_image_count must not be negative")
        if self.status is ExtractionStatus.NO_TEXT and self.char_count != _MIN_COUNT:
            raise ValueError("NO_TEXT status requires empty page text")
        if self.char_count == _MIN_COUNT and self.status not in (
            ExtractionStatus.NO_TEXT,
            ExtractionStatus.EXTRACTION_ERROR,
        ):
            raise ValueError("empty page text requires NO_TEXT or EXTRACTION_ERROR status")


@dataclass(frozen=True, slots=True)
class ExtractionRecord:
    """Per-run extraction metadata for one source document.

    Reproducibility contract: identical document bytes plus identical tool,
    version, and configuration produce an identical record except for
    ``extracted_at``, which is a labeled run stamp and never content identity.
    """

    document_id: str
    tool: str
    tool_version: str
    page_count: int
    sparse_threshold: int
    pages: tuple[PageExtraction, ...]
    extracted_at: str | None = None

    def __post_init__(self) -> None:
        validate_identifier(self.document_id, "ExtractionRecord.document_id")
        if not self.tool:
            raise ValueError("ExtractionRecord.tool must not be empty")
        if not self.tool_version:
            raise ValueError("ExtractionRecord.tool_version must not be empty")
        if self.sparse_threshold < _MIN_THRESHOLD:
            raise ValueError("ExtractionRecord.sparse_threshold must be positive")
        if self.extracted_at is not None:
            validate_iso_date(self.extracted_at, "ExtractionRecord.extracted_at")
        if self.page_count != len(self.pages):
            raise ValueError("ExtractionRecord.page_count must equal the number of pages")
        for index, page in enumerate(self.pages, start=_FIRST_PAGE):
            if page.page_number != index:
                raise ValueError("page numbers must be consecutive starting at 1")


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    """Complete output of an extraction run: identity, record, and fragments.

    Fragments are page-level: one SourceFragment per page, ordered by page
    number, each preserving its page and the verbatim extracted page text.
    """

    document: SourceDocument
    record: ExtractionRecord
    fragments: tuple[SourceFragment, ...]

    def __post_init__(self) -> None:
        if self.record.document_id != self.document.document_id:
            raise ValueError("ExtractionResult document and record ids must match")
        if len(self.fragments) != self.record.page_count:
            raise ValueError("ExtractionResult must have one fragment per page")
        for index, fragment in enumerate(self.fragments):
            page_number = index + _FIRST_PAGE
            if fragment.page != page_number:
                raise ValueError("fragments must be ordered by page number")
            if fragment.document_id != self.document.document_id:
                raise ValueError("fragment document_id must match the source document")
            if fragment.verbatim_text != self.record.pages[index].text:
                raise ValueError("fragment verbatim_text must equal the page text")
