"""The extraction layer must remain protocol-agnostic."""

from __future__ import annotations

from pathlib import Path

from unit.extraction.fixtures import make_minimal_pdf

from cpg_tree.extraction import extract_pdf

FIXED_TIMESTAMP = "2026-09-17T00:00:00+00:00"

EXTRACTION_PACKAGE = Path(__file__).resolve().parents[3] / "src" / "cpg_tree" / "extraction"

FORBIDDEN_SOURCE_STRINGS = (
    "CT-PL-193",
    "CT-PL-197",
    "neumonía",
    "neumonia",
    "pielonefritis",
    "bacteriuria",
    "community-acquired",
    "urinary tract",
)


def test_different_documents_flow_through_the_same_pipeline(
    tmp_path: Path,
) -> None:
    first_pdf = tmp_path / "first.pdf"
    second_pdf = tmp_path / "second.pdf"
    first_pdf.write_bytes(make_minimal_pdf(["first document text"]))
    second_pdf.write_bytes(make_minimal_pdf(["second document text"]))
    first = extract_pdf(first_pdf, extracted_at=FIXED_TIMESTAMP)
    second = extract_pdf(second_pdf, extracted_at=FIXED_TIMESTAMP)
    assert first.record.tool == second.record.tool
    assert first.document.document_id != second.document.document_id
    assert first.fragments[0].verbatim_text == "first document text"
    assert second.fragments[0].verbatim_text == "second document text"


def test_extraction_source_contains_no_protocol_specific_strings() -> None:
    for source_file in EXTRACTION_PACKAGE.rglob("*.py"):
        content = source_file.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_SOURCE_STRINGS:
            assert forbidden not in content, f"{source_file} contains {forbidden!r}"
