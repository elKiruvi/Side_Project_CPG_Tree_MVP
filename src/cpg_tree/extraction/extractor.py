"""Deterministic PDF extraction: fingerprinting, page text, fragment inventory."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import Final

import pypdf
from pypdf import PdfReader
from pypdf._page import PageObject
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject

from cpg_tree.extraction.model import (
    ExtractionRecord,
    ExtractionResult,
    ExtractionStatus,
    PageExtraction,
)
from cpg_tree.extraction.sectioning import detect_section
from cpg_tree.knowledge import SourceDocument, SourceFragment

_SHA256_PATTERN: Final = re.compile(r"^[0-9a-f]{64}$")
_SHA256_PREFIX_LENGTH: Final = 16
_DOCUMENT_ID_PREFIX: Final = "doc-"
_DEFAULT_SPARSE_THRESHOLD: Final = 100
_NO_CHARS: Final = 0


def fingerprint_bytes(data: bytes) -> str:
    """Return the SHA-256 hex digest of the exact bytes."""
    return hashlib.sha256(data).hexdigest()


def document_id_from_sha256(sha256_hex: str) -> str:
    """Derive a deterministic, content-addressed document id from a digest."""
    if _SHA256_PATTERN.fullmatch(sha256_hex) is None:
        raise ValueError("expected a 64-character lowercase hex SHA-256 digest")
    return f"{_DOCUMENT_ID_PREFIX}{sha256_hex[:_SHA256_PREFIX_LENGTH]}"


def count_embedded_images(page: PageObject) -> int | None:
    """Count image XObjects in the page resources; None if not inspectable.

    This is a structural PDF inspection: it counts ``/Subtype /Image`` XObjects
    without opening or interpreting their content.
    """
    count = 0
    try:
        resources = page["/Resources"]
        if resources is None:
            return count
        xobjects = resources.get("/XObject")
        if xobjects is None:
            return count
        if isinstance(xobjects, DictionaryObject):
            entries: list[object] = list(xobjects.values())
        elif isinstance(xobjects, ArrayObject):
            entries = list(xobjects)
        else:
            entries = [xobjects]
        for entry in entries:
            candidate = entry.get_object() if isinstance(entry, IndirectObject) else entry
            if (
                isinstance(candidate, DictionaryObject)
                and str(candidate.get("/Subtype")) == "/Image"
            ):
                count += 1
    except Exception:
        return None
    return count


def extract_pdf(
    path: str | Path,
    *,
    sparse_threshold: int = _DEFAULT_SPARSE_THRESHOLD,
    extracted_at: str | None = None,
) -> ExtractionResult:
    """Extract a source PDF into a reproducible ExtractionResult.

    The same implementation processes any PDF: identity derives from content
    bytes only, so no protocol- or document-specific knowledge is involved.
    Pages with no extractable text are preserved, never discarded.
    """
    pdf_path = Path(path)
    data = pdf_path.read_bytes()
    sha256 = fingerprint_bytes(data)
    document_id = document_id_from_sha256(sha256)
    reader = PdfReader(BytesIO(data))
    pages = tuple(
        _extract_page(page, page_number, sparse_threshold)
        for page_number, page in enumerate(reader.pages, start=1)
    )
    record = ExtractionRecord(
        document_id=document_id,
        tool="pypdf",
        tool_version=pypdf.__version__,
        extracted_at=extracted_at if extracted_at is not None else _now_iso(),
        page_count=len(pages),
        sparse_threshold=sparse_threshold,
        pages=pages,
    )
    fragments = tuple(
        SourceFragment(
            id=f"{document_id}-p{page.page_number:03d}",
            document_id=document_id,
            page=page.page_number,
            section=detect_section(page.text),
            verbatim_text=page.text,
        )
        for page in pages
    )
    return ExtractionResult(
        document=SourceDocument(
            document_id=document_id,
            filename=pdf_path.name,
            sha256=sha256,
            file_format="pdf",
            byte_size=len(data),
        ),
        record=record,
        fragments=fragments,
    )


def _extract_page(
    page: PageObject,
    page_number: int,
    sparse_threshold: int,
) -> PageExtraction:
    try:
        text = page.extract_text() or ""
        status = _status_for(len(text), sparse_threshold)
    except Exception:
        text = ""
        status = ExtractionStatus.EXTRACTION_ERROR
    return PageExtraction(
        page_number=page_number,
        text=text,
        embedded_image_count=count_embedded_images(page),
        status=status,
    )


def _status_for(char_count: int, sparse_threshold: int) -> ExtractionStatus:
    if char_count == _NO_CHARS:
        return ExtractionStatus.NO_TEXT
    if char_count <= sparse_threshold:
        return ExtractionStatus.SPARSE_TEXT
    return ExtractionStatus.OK


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()
