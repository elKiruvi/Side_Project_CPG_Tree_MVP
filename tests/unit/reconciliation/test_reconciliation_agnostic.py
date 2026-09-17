"""The reconciliation layer must remain protocol-agnostic and structural."""

from __future__ import annotations

from pathlib import Path

RECONCILIATION_PACKAGE = Path(__file__).resolve().parents[3] / "src" / "cpg_tree" / "reconciliation"

FORBIDDEN_SOURCE_STRINGS = (
    "CT-PL-193",
    "CT-PL-197",
    "neumonía",
    "neumonia",
    "pielonefritis",
    "bacteriuria",
    "community-acquired",
    "urinary tract",
    "pregnancy",
    "embarazo",
    "antibiotic",
    "CURB",
    "NAC",
    "ITU",
)


def test_reconciliation_source_contains_no_protocol_specific_strings() -> None:
    for source_file in RECONCILIATION_PACKAGE.rglob("*.py"):
        content = source_file.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_SOURCE_STRINGS:
            assert forbidden not in content, f"{source_file} contains {forbidden!r}"


def test_reconciliation_never_imports_protocol_packages() -> None:
    for source_file in RECONCILIATION_PACKAGE.rglob("*.py"):
        content = source_file.read_text(encoding="utf-8")
        assert "cpg_tree.protocols" not in content, (
            f"{source_file} imports the protocol knowledge packages"
        )


def test_reconciliation_never_imports_the_engine() -> None:
    for source_file in RECONCILIATION_PACKAGE.rglob("*.py"):
        content = source_file.read_text(encoding="utf-8")
        assert "cpg_tree.engine" not in content, f"{source_file} imports the evaluation engine"
