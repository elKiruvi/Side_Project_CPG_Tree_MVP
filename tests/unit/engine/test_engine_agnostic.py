"""The engine layer must remain protocol-agnostic and structurally independent."""

from __future__ import annotations

from pathlib import Path

from cpg_tree.engine import Case, RuleOutcome, evaluate_package
from cpg_tree.knowledge import ProtocolVersion

ENGINE_PACKAGE = Path(__file__).resolve().parents[3] / "src" / "cpg_tree" / "engine"

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


def test_engine_source_contains_no_protocol_specific_strings() -> None:
    for source_file in ENGINE_PACKAGE.rglob("*.py"):
        content = source_file.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_SOURCE_STRINGS:
            assert forbidden not in content, f"{source_file} contains {forbidden!r}"


def test_engine_never_imports_the_validation_layer() -> None:
    for source_file in ENGINE_PACKAGE.rglob("*.py"):
        content = source_file.read_text(encoding="utf-8")
        assert "cpg_tree.validation" not in content, f"{source_file} imports the validation layer"


def test_third_protocol_evaluates_with_generic_engine(
    synthetic_package: ProtocolVersion,
) -> None:
    case = Case.from_inputs({"count_x": 101, "flag_y": True, "category_z": "alpha", "span_t": 48})
    result = evaluate_package(synthetic_package, case)
    assert result.protocol_id == "TEST-PL-999"
    assert result.version == "v01"
    outcomes = {item.rule_id: item.outcome for item in result.rule_results}
    assert outcomes["rule_compare"] is RuleOutcome.MATCHED
    assert outcomes["rule_composite"] is RuleOutcome.MATCHED
    assert outcomes["rule_temporal"] is RuleOutcome.MATCHED
