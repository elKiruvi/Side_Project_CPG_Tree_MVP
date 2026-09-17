"""End-to-end NAC chain test: raw PDF -> extraction -> knowledge package
-> validation -> engine evaluation -> test-case harness.

Skipped when the raw clinical PDF is not available locally (raw PDFs are
source data and are never committed to Git).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cpg_tree.engine import run_test_cases
from cpg_tree.extraction import extract_pdf
from cpg_tree.protocols.nac_v09 import DOCUMENT_ID, build_nac_package
from cpg_tree.validation import validate_package

RAW_DIR = Path(__file__).resolve().parents[3] / "data" / "01_raw"

pytestmark = pytest.mark.skipif(
    not any(RAW_DIR.glob("CT-PL-193*.pdf")),
    reason="the raw NAC PDF is not available locally",
)


def test_extraction_identity_matches_package_document() -> None:
    pdf_path = next(RAW_DIR.glob("CT-PL-193*.pdf"))
    result = extract_pdf(pdf_path, extracted_at="2026-09-17T00:00:00+00:00")
    assert result.document.document_id == DOCUMENT_ID


def test_full_nac_chain_validates_and_runs() -> None:
    package = build_nac_package()
    report = validate_package(package)
    assert report.error_count == 0
    assert report.warning_count == 0
    outcomes = run_test_cases(package)
    assert len(outcomes) == 30
    assert all(outcome.passed for outcome in outcomes)


def test_chain_is_repeatable() -> None:
    package = build_nac_package()
    first = run_test_cases(package)
    second = run_test_cases(package)
    assert first == second
