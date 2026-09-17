"""Outcome demonstration tests for the NAC package.

These tests prove that the committed synthetic demonstration cases under
evaluation/cases/CT-PL-193/v09/ produce their documented engine outcomes
through the generic case loader and the unchanged deterministic engine.

This is evidence about engine mechanics, not clinical validity: a case that
produces MATCHED only demonstrates the mechanical outcome for that input.
"""

from __future__ import annotations

import json
from pathlib import Path

from cpg_tree.engine import RuleOutcome, evaluate_package
from cpg_tree.protocols.nac_v09 import build_nac_package
from cpg_tree.views.case_loader import load_case_text

CASES_DIR = (
    Path(__file__).resolve().parents[3] / "evaluation" / "cases" / "CT-PL-193" / "v09"
)

DOCUMENTED_CASES = {
    "nac_matched.json": RuleOutcome.MATCHED,
    "nac_not_matched.json": RuleOutcome.NOT_MATCHED,
    "nac_not_applicable.json": RuleOutcome.NOT_APPLICABLE,
    "nac_indeterminate.json": RuleOutcome.INDETERMINATE,
}


def _outcomes(case_name: str) -> list[RuleOutcome]:
    case_path = CASES_DIR / case_name
    assert case_path.is_file(), f"missing demonstration case {case_path}"
    package = build_nac_package()
    case = load_case_text(case_path.read_text(encoding="utf-8"), package.variables)
    result = evaluate_package(package, case)
    return [entry.outcome for entry in result.rule_results]


def test_every_documented_case_produces_its_outcome() -> None:
    for case_name, expected in DOCUMENTED_CASES.items():
        assert expected in _outcomes(case_name), (
            f"{case_name} does not produce the documented outcome {expected.value}"
        )


def test_nac_demonstrates_four_of_five_outcomes() -> None:
    demonstrated = {outcome for case_name in DOCUMENTED_CASES for outcome in _outcomes(case_name)}
    assert {RuleOutcome.MATCHED, RuleOutcome.NOT_MATCHED, RuleOutcome.NOT_APPLICABLE,
            RuleOutcome.INDETERMINATE} <= demonstrated


def test_nac_has_no_exception_rule_so_excepted_is_not_demonstrable() -> None:
    package = build_nac_package()
    assert all(not rule.exceptions for rule in package.rules.values())
    demonstrated = {outcome for case_name in DOCUMENTED_CASES for outcome in _outcomes(case_name)}
    assert RuleOutcome.EXCEPTED not in demonstrated


def test_nac_demo_cases_are_valid_json() -> None:
    for case_name in DOCUMENTED_CASES:
        json.loads((CASES_DIR / case_name).read_text(encoding="utf-8"))
