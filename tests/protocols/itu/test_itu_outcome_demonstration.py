"""Outcome demonstration tests for the ITU package.

These tests prove that the committed synthetic demonstration cases under
evaluation/cases/CT-PL-197/v06/ produce their documented engine outcomes
through the generic case loader and the unchanged deterministic engine.

This is evidence about engine mechanics, not clinical validity: a case that
produces MATCHED only demonstrates the mechanical outcome for that input.
"""

from __future__ import annotations

import json
from pathlib import Path

from cpg_tree.engine import RuleOutcome, evaluate_package
from cpg_tree.protocols.itu_v06 import build_itu_package
from cpg_tree.views.case_loader import load_case_text

CASES_DIR = (
    Path(__file__).resolve().parents[3] / "evaluation" / "cases" / "CT-PL-197" / "v06"
)

DOCUMENTED_CASES = {
    "itu_matched.json": RuleOutcome.MATCHED,
    "itu_not_matched.json": RuleOutcome.NOT_MATCHED,
    "itu_not_applicable.json": RuleOutcome.NOT_APPLICABLE,
    "itu_indeterminate.json": RuleOutcome.INDETERMINATE,
    "itu_excepted.json": RuleOutcome.EXCEPTED,
}


def _outcomes(case_name: str) -> list[RuleOutcome]:
    case_path = CASES_DIR / case_name
    assert case_path.is_file(), f"missing demonstration case {case_path}"
    package = build_itu_package()
    case = load_case_text(case_path.read_text(encoding="utf-8"), package.variables)
    result = evaluate_package(package, case)
    return [entry.outcome for entry in result.rule_results]


def test_every_documented_case_produces_its_outcome() -> None:
    for case_name, expected in DOCUMENTED_CASES.items():
        assert expected in _outcomes(case_name), (
            f"{case_name} does not produce the documented outcome {expected.value}"
        )


def test_itu_demonstrates_all_five_outcomes() -> None:
    demonstrated = {outcome for case_name in DOCUMENTED_CASES for outcome in _outcomes(case_name)}
    assert demonstrated == {
        RuleOutcome.MATCHED,
        RuleOutcome.NOT_MATCHED,
        RuleOutcome.NOT_APPLICABLE,
        RuleOutcome.INDETERMINATE,
        RuleOutcome.EXCEPTED,
    }


def test_itu_demo_cases_are_valid_json() -> None:
    for case_name in DOCUMENTED_CASES:
        json.loads((CASES_DIR / case_name).read_text(encoding="utf-8"))
