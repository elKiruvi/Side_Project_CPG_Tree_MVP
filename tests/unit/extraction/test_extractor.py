"""Tests for extract_pdf: page extraction, statuses, fragments, determinism."""

from __future__ import annotations

from pathlib import Path

import pytest
from unit.extraction.fixtures import make_minimal_pdf

from cpg_tree.extraction import ExtractionStatus, extract_pdf

FIXED_TIMESTAMP = "2026-09-17T00:00:00+00:00"
LONG_TEXT = "x" * 150
SINGLE_PAGE_TEXT = "Page one text"
EXPECTED_PAGES = 2
ZERO_CHARS = 0
ZERO_IMAGES = 0


@pytest.fixture
def two_page_pdf(tmp_path: Path) -> Path:
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(make_minimal_pdf([SINGLE_PAGE_TEXT, LONG_TEXT]))
    return pdf_path


def test_page_count_is_captured(two_page_pdf: Path) -> None:
    result = extract_pdf(two_page_pdf, extracted_at=FIXED_TIMESTAMP)
    assert result.record.page_count == EXPECTED_PAGES
    assert len(result.record.pages) == EXPECTED_PAGES


def test_page_numbers_are_consecutive(two_page_pdf: Path) -> None:
    result = extract_pdf(two_page_pdf, extracted_at=FIXED_TIMESTAMP)
    assert [page.page_number for page in result.record.pages] == [1, 2]


def test_extracted_text_is_preserved(two_page_pdf: Path) -> None:
    result = extract_pdf(two_page_pdf, extracted_at=FIXED_TIMESTAMP)
    assert result.record.pages[0].text == SINGLE_PAGE_TEXT
    assert result.record.pages[1].text == LONG_TEXT


def test_document_identity_is_content_addressed(two_page_pdf: Path) -> None:
    first = extract_pdf(two_page_pdf, extracted_at=FIXED_TIMESTAMP)
    second = extract_pdf(two_page_pdf, extracted_at=FIXED_TIMESTAMP)
    assert first.document.document_id == second.document.document_id
    assert first.document.sha256 == second.document.sha256
    assert first.document.document_id.startswith("doc-")


def test_no_text_pages_are_not_discarded(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(make_minimal_pdf(["", LONG_TEXT]))
    result = extract_pdf(pdf_path, extracted_at=FIXED_TIMESTAMP)
    assert result.record.page_count == EXPECTED_PAGES
    assert result.record.pages[0].status is ExtractionStatus.NO_TEXT
    assert result.record.pages[0].char_count == ZERO_CHARS
    assert len(result.fragments) == EXPECTED_PAGES


def test_sparse_threshold_boundary(tmp_path: Path) -> None:
    text = "tiny"
    at_threshold = tmp_path / "at.pdf"
    at_threshold.write_bytes(make_minimal_pdf([text]))
    above = tmp_path / "above.pdf"
    above.write_bytes(make_minimal_pdf([text]))
    result_at = extract_pdf(at_threshold, sparse_threshold=len(text), extracted_at=FIXED_TIMESTAMP)
    result_above = extract_pdf(above, sparse_threshold=len(text) - 1, extracted_at=FIXED_TIMESTAMP)
    assert result_at.record.pages[0].status is ExtractionStatus.SPARSE_TEXT
    assert result_above.record.pages[0].status is ExtractionStatus.OK


def test_default_sparse_threshold_marks_short_page(two_page_pdf: Path) -> None:
    result = extract_pdf(two_page_pdf, extracted_at=FIXED_TIMESTAMP)
    assert result.record.pages[0].status is ExtractionStatus.SPARSE_TEXT
    assert result.record.pages[1].status is ExtractionStatus.OK


def test_extraction_metadata_is_recorded(two_page_pdf: Path) -> None:
    result = extract_pdf(two_page_pdf, extracted_at=FIXED_TIMESTAMP)
    record = result.record
    assert record.tool == "pypdf"
    assert record.tool_version
    assert record.extracted_at == FIXED_TIMESTAMP
    assert record.document_id == result.document.document_id


def test_extracted_at_is_a_run_stamp_not_identity(two_page_pdf: Path) -> None:
    first = extract_pdf(two_page_pdf, extracted_at="2026-01-01T00:00:00+00:00")
    second = extract_pdf(two_page_pdf, extracted_at="2026-02-02T00:00:00+00:00")
    assert first.document == second.document
    assert first.record.extracted_at != second.record.extracted_at


def test_fragments_preserve_page_provenance(two_page_pdf: Path) -> None:
    result = extract_pdf(two_page_pdf, extracted_at=FIXED_TIMESTAMP)
    assert len(result.fragments) == EXPECTED_PAGES
    for index, fragment in enumerate(result.fragments, start=1):
        assert fragment.page == index
        assert fragment.document_id == result.document.document_id
        assert fragment.verbatim_text == result.record.pages[index - 1].text


def test_fragment_identifiers_are_deterministic(two_page_pdf: Path) -> None:
    first = extract_pdf(two_page_pdf, extracted_at=FIXED_TIMESTAMP)
    second = extract_pdf(two_page_pdf, extracted_at=FIXED_TIMESTAMP)
    assert [fragment.id for fragment in first.fragments] == [
        fragment.id for fragment in second.fragments
    ]


def test_section_candidate_recorded_on_fragment(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(make_minimal_pdf(["UPPERCASE HEADING"]))
    result = extract_pdf(pdf_path, extracted_at=FIXED_TIMESTAMP)
    assert result.fragments[0].section == "UPPERCASE HEADING"


def test_no_heading_leaves_section_none(two_page_pdf: Path) -> None:
    result = extract_pdf(two_page_pdf, extracted_at=FIXED_TIMESTAMP)
    assert result.fragments[0].section is None


def test_embedded_image_count_reported_for_synthetic_pdf(two_page_pdf: Path) -> None:
    result = extract_pdf(two_page_pdf, extracted_at=FIXED_TIMESTAMP)
    assert result.record.pages[0].embedded_image_count == ZERO_IMAGES


def test_run_is_deterministic(two_page_pdf: Path) -> None:
    first = extract_pdf(two_page_pdf, extracted_at=FIXED_TIMESTAMP)
    second = extract_pdf(two_page_pdf, extracted_at=FIXED_TIMESTAMP)
    assert first == second
