"""End-to-end chain test: synthetic PDF -> extraction -> knowledge package
-> validation -> engine evaluation -> test-case runner.

No clinical content is involved: the synthetic PDF carries generic text and
the package uses only generic model classes.
"""

from __future__ import annotations

from pathlib import Path

from unit.extraction.fixtures import make_minimal_pdf

from cpg_tree.engine import run_test_cases
from cpg_tree.extraction import ExtractionResult, extract_pdf
from cpg_tree.knowledge import (
    Action,
    ActionType,
    Condition,
    ConditionKind,
    DerivationState,
    Protocol,
    ProtocolVersion,
    Provenance,
    Rule,
    TestCase,
    TruthValue,
    Variable,
    VariableType,
)
from cpg_tree.validation import validate_package

FIXED_TIMESTAMP = "2026-09-17T00:00:00+00:00"

# Prevent pytest from trying to collect the imported TestCase dataclass.
TestCase.__test__ = False  # type: ignore[misc]


def _package_from_result(result: ExtractionResult) -> ProtocolVersion:
    return ProtocolVersion(
        protocol=Protocol(id="TEST-PL-900", name="Chain Protocol"),
        version="v01",
        documents={result.document.document_id: result.document},
        fragments={fragment.id: fragment for fragment in result.fragments},
        variables={"flag_y": Variable(id="flag_y", label="Flag Y", type=VariableType.BOOLEAN)},
        actions={"act_decide": Action(id="act_decide", type=ActionType.DECISION)},
        rules={
            "rule_x": Rule(
                id="rule_x",
                condition=Condition(kind=ConditionKind.FLAG, variable_ref="flag_y", expected=True),
                action_refs=("act_decide",),
                provenance=Provenance(
                    derivation=DerivationState.SOURCE_STATED,
                    fragment_refs=(result.fragments[0].id,),
                ),
            )
        },
        test_cases={
            "tc_true": TestCase(
                id="tc_true",
                inputs={"flag_y": True},
                expected_results={"rule_x": TruthValue.TRUE},
            ),
            "tc_false": TestCase(
                id="tc_false",
                inputs={"flag_y": False},
                expected_results={"rule_x": TruthValue.FALSE},
            ),
            "tc_missing": TestCase(
                id="tc_missing",
                inputs={"flag_y": None},
                expected_results={"rule_x": TruthValue.UNKNOWN},
            ),
        },
    )


def _extract(tmp_path: Path) -> ExtractionResult:
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(make_minimal_pdf(["CRITERION TEXT", "SECOND PAGE TEXT"]))
    return extract_pdf(pdf_path, extracted_at=FIXED_TIMESTAMP)


def test_full_chain_extracts_validates_and_evaluates(tmp_path: Path) -> None:
    result = _extract(tmp_path)
    package = _package_from_result(result)
    report = validate_package(package)
    assert report.is_valid()
    assert report.findings == ()
    outcomes = run_test_cases(package)
    assert all(outcome.passed for outcome in outcomes)


def test_chain_is_repeatable(tmp_path: Path) -> None:
    result = _extract(tmp_path)
    package = _package_from_result(result)
    first = run_test_cases(package)
    second = run_test_cases(package)
    assert first == second
