"""The views layer must remain protocol-agnostic and structurally independent."""

from __future__ import annotations

from pathlib import Path

VIEWS_PACKAGE = Path(__file__).resolve().parents[3] / "src" / "cpg_tree" / "views"

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


def test_views_source_contains_no_protocol_specific_strings() -> None:
    for source_file in VIEWS_PACKAGE.rglob("*.py"):
        content = source_file.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_SOURCE_STRINGS:
            assert forbidden not in content, f"{source_file} contains {forbidden!r}"


def test_views_never_import_the_protocol_packages() -> None:
    for source_file in VIEWS_PACKAGE.rglob("*.py"):
        content = source_file.read_text(encoding="utf-8")
        assert "cpg_tree.protocols" not in content, (
            f"{source_file} imports the protocol knowledge packages"
        )


def test_views_never_reimplement_condition_evaluation() -> None:
    for source_file in VIEWS_PACKAGE.rglob("*.py"):
        content = source_file.read_text(encoding="utf-8")
        assert "evaluate_operand" not in content, (
            f"{source_file} calls the engine's condition evaluator"
        )
        assert "evaluate_condition" not in content, (
            f"{source_file} calls the engine's condition evaluator"
        )
        assert "cpg_tree.engine.conditions" not in content, (
            f"{source_file} imports the engine's condition evaluator"
        )
