"""Integration tests running the generic pipeline over the real source PDFs.

These tests skip when the raw PDFs are not present locally: the clinical PDFs
are source data and are never committed to Git.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cpg_tree.extraction import ExtractionStatus, extract_pdf

RAW_DIR = Path(__file__).resolve().parents[3] / "data" / "01_raw"

NAC_PAGE_COUNT = 7
ITU_PAGE_COUNT = 5

NAC_IMAGE_COUNTS = (1, 1, 0, 0, 0, 1, 0)
ITU_IMAGE_COUNTS = (1, 0, 0, 0, 0)
MIN_REAL_PDFS = 2


def _raw_pdfs() -> list[Path]:
    return sorted(RAW_DIR.glob("CT-PL-19*.pdf"))


pytestmark = pytest.mark.skipif(
    len(_raw_pdfs()) < MIN_REAL_PDFS, reason="real source PDFs are not available locally"
)


def _result_for(path: Path):
    return extract_pdf(path, extracted_at="2026-09-17T00:00:00+00:00")


@pytest.mark.parametrize(
    ("name_token", "expected_page_count"),
    [("NAC", NAC_PAGE_COUNT), ("ITU", ITU_PAGE_COUNT)],
)
def test_real_pdf_page_counts(name_token: str, expected_page_count: int) -> None:
    pdf_path = next(path for path in _raw_pdfs() if name_token in path.name)
    result = _result_for(pdf_path)
    assert result.record.page_count == expected_page_count
    assert len(result.fragments) == expected_page_count


@pytest.mark.parametrize("name_token", ["NAC", "ITU"])
def test_every_real_page_extracts_text(name_token: str) -> None:
    pdf_path = next(path for path in _raw_pdfs() if name_token in path.name)
    result = _result_for(pdf_path)
    for page in result.record.pages:
        assert page.char_count > 0
        assert page.status is ExtractionStatus.OK
        assert page.embedded_image_count is not None


@pytest.mark.parametrize("name_token", ["NAC", "ITU"])
def test_fragments_preserve_page_provenance(name_token: str) -> None:
    pdf_path = next(path for path in _raw_pdfs() if name_token in path.name)
    result = _result_for(pdf_path)
    for index, fragment in enumerate(result.fragments, start=1):
        assert fragment.page == index
        assert fragment.document_id == result.document.document_id
        assert fragment.verbatim_text == result.record.pages[index - 1].text


def test_nac_embedded_image_counts() -> None:
    pdf_path = next(path for path in _raw_pdfs() if "NAC" in path.name)
    result = _result_for(pdf_path)
    counts = tuple(page.embedded_image_count for page in result.record.pages)
    assert counts == NAC_IMAGE_COUNTS


def test_itu_embedded_image_counts() -> None:
    pdf_path = next(path for path in _raw_pdfs() if "ITU" in path.name)
    result = _result_for(pdf_path)
    counts = tuple(page.embedded_image_count for page in result.record.pages)
    assert counts == ITU_IMAGE_COUNTS


def test_nac_treatment_section_header_is_extracted() -> None:
    pdf_path = next(path for path in _raw_pdfs() if "NAC" in path.name)
    result = _result_for(pdf_path)
    page_4_text = result.record.pages[3].text
    assert "TRATAMIENTO ANTIBIÓTICO EMPÍRICO" in page_4_text


def test_real_pdf_identity_matches_known_sha256() -> None:
    nac_path = next(path for path in _raw_pdfs() if "NAC" in path.name)
    itu_path = next(path for path in _raw_pdfs() if "ITU" in path.name)
    nac_result = _result_for(nac_path)
    itu_result = _result_for(itu_path)
    assert nac_result.document.sha256.startswith("3a165475")
    assert itu_result.document.sha256.startswith("800af94b")
    assert nac_result.document.document_id == "doc-3a1654757801b7b6"
    assert itu_result.document.document_id == "doc-800af94bc0654138"
