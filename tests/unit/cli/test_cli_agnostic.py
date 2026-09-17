"""The CLI layer must remain protocol-agnostic and structurally independent."""

from __future__ import annotations

from pathlib import Path

CLI_FILES = (
    Path(__file__).resolve().parents[3] / "src" / "cpg_tree" / "cli.py",
    Path(__file__).resolve().parents[3] / "src" / "cpg_tree" / "__main__.py",
)

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
)


def test_cli_source_contains_no_protocol_specific_strings() -> None:
    for source_file in CLI_FILES:
        content = source_file.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_SOURCE_STRINGS:
            assert forbidden not in content, f"{source_file} contains {forbidden!r}"


def test_cli_never_imports_the_protocol_packages() -> None:
    for source_file in CLI_FILES:
        content = source_file.read_text(encoding="utf-8")
        assert "cpg_tree.protocols" not in content, (
            f"{source_file} imports the protocol knowledge packages"
        )


def test_cli_never_imports_condition_evaluation_internals() -> None:
    for source_file in CLI_FILES:
        content = source_file.read_text(encoding="utf-8")
        assert "evaluate_operand" not in content, (
            f"{source_file} calls the engine's condition evaluator"
        )
        assert "cpg_tree.engine.conditions" not in content, (
            f"{source_file} imports the engine's condition evaluator"
        )
