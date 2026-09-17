"""Tests for intermediate artifact writing."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from unit.extraction.fixtures import make_minimal_pdf

from cpg_tree.extraction import extract_pdf, write_artifacts

FIXED_TIMESTAMP = "2026-09-17T00:00:00+00:00"
EXPECTED_PAGES = 2


@pytest.fixture
def extracted(tmp_path: Path):
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(make_minimal_pdf(["Page one text", "UPPERCASE HEADING"]))
    return extract_pdf(pdf_path, extracted_at=FIXED_TIMESTAMP)


def test_artifacts_written_with_expected_layout(extracted, tmp_path: Path) -> None:
    target = tmp_path / "artifacts"
    written = write_artifacts(extracted, target)
    paths = {path.relative_to(target) for path in written}
    assert Path("source_document.yaml") in paths
    assert Path("fragments.yaml") in paths
    assert Path("report.txt") in paths
    assert Path("pages/page_001.txt") in paths
    assert Path("pages/page_002.txt") in paths


def test_source_document_yaml_content(extracted, tmp_path: Path) -> None:
    target = tmp_path / "artifacts"
    write_artifacts(extracted, target)
    data = yaml.safe_load((target / "source_document.yaml").read_text(encoding="utf-8"))
    assert data["document"]["document_id"] == extracted.document.document_id
    assert data["document"]["sha256"] == extracted.document.sha256
    assert data["extraction"]["tool"] == "pypdf"
    assert data["extraction"]["page_count"] == EXPECTED_PAGES
    pages = data["extraction"]["pages"]
    assert [page["page_number"] for page in pages] == [1, 2]
    assert pages[0]["status"] == "SPARSE_TEXT"


def test_page_text_files_preserve_verbatim_text(extracted, tmp_path: Path) -> None:
    target = tmp_path / "artifacts"
    write_artifacts(extracted, target)
    assert (target / "pages/page_001.txt").read_text(encoding="utf-8") == "Page one text"
    assert (target / "pages/page_002.txt").read_text(encoding="utf-8") == "UPPERCASE HEADING"


def test_fragments_yaml_content(extracted, tmp_path: Path) -> None:
    target = tmp_path / "artifacts"
    write_artifacts(extracted, target)
    fragments = yaml.safe_load((target / "fragments.yaml").read_text(encoding="utf-8"))
    assert len(fragments) == EXPECTED_PAGES
    assert fragments[0]["page"] == 1
    assert fragments[1]["section"] == "UPPERCASE HEADING"
    assert fragments[1]["verbatim_text"] == "UPPERCASE HEADING"


def test_report_mentions_status_vocabulary(extracted, tmp_path: Path) -> None:
    target = tmp_path / "artifacts"
    write_artifacts(extracted, target)
    report = (target / "report.txt").read_text(encoding="utf-8")
    assert extracted.document.document_id in report
    assert "NO_TEXT" in report


def test_artifacts_are_byte_identical_for_same_input(extracted, tmp_path: Path) -> None:
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    write_artifacts(extracted, first_dir)
    write_artifacts(extracted, second_dir)
    for first in sorted(first_dir.rglob("*")):
        if first.is_file():
            second = second_dir / first.relative_to(first_dir)
            assert first.read_bytes() == second.read_bytes()
