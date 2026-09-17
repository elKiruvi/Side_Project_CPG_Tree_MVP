# ruff: noqa: TRY004
"""Test-case harness built on top of the deterministic engine.

``run_test_cases`` is testing tooling, not part of the runtime engine: the
core evaluator never depends on ``TestCase``. It projects ``RuleOutcome`` onto
``TruthValue`` to compare against ``TestCase.expected_results``:

- MATCHED -> TRUE
- NOT_MATCHED, NOT_APPLICABLE, EXCEPTED -> FALSE
- INDETERMINATE -> UNKNOWN

Known limitation of this projection: EXCEPTED and NOT_APPLICABLE collapse
into FALSE because ``TestCase.expected_results`` only supports TruthValue.
The full outcome remains available on each ``RuleEvaluation``.

TRY004 is disabled for this module on purpose: harness configuration errors
raise ValueError subclasses by API contract, and the test suite asserts them
explicitly.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from cpg_tree.engine.case import Case
from cpg_tree.engine.errors import EngineConfigurationError
from cpg_tree.engine.rules import RuleOutcome, evaluate_package
from cpg_tree.knowledge.enums import TruthValue
from cpg_tree.knowledge.protocol import ProtocolVersion

_OUTCOME_PROJECTION: dict[RuleOutcome, TruthValue] = {
    RuleOutcome.MATCHED: TruthValue.TRUE,
    RuleOutcome.NOT_MATCHED: TruthValue.FALSE,
    RuleOutcome.NOT_APPLICABLE: TruthValue.FALSE,
    RuleOutcome.EXCEPTED: TruthValue.FALSE,
    RuleOutcome.INDETERMINATE: TruthValue.UNKNOWN,
}


@dataclass(frozen=True, slots=True)
class TestCaseOutcome:
    """Result of running one TestCase against the engine.

    Only rules listed in ``expected_results`` are asserted. ``expected`` and
    ``actual`` are exposed read-only for deterministic reporting.
    """

    test_case_id: str
    passed: bool
    expected: Mapping[str, TruthValue]
    actual: Mapping[str, TruthValue]

    def __post_init__(self) -> None:
        object.__setattr__(self, "expected", MappingProxyType(dict(self.expected)))
        object.__setattr__(self, "actual", MappingProxyType(dict(self.actual)))


def run_test_cases(version: ProtocolVersion) -> tuple[TestCaseOutcome, ...]:
    """Evaluate every TestCase of a package and compare with its expectations.

    Deterministic: test cases are processed in id order and rule results are
    already ordered by rule id. A TestCase whose ``expected_results`` names a
    rule that is not in the package raises ``EngineConfigurationError``.
    """
    outcomes: list[TestCaseOutcome] = []
    for test_case_id in sorted(version.test_cases):
        test_case = version.test_cases[test_case_id]
        case = Case.from_inputs(test_case.inputs)
        evaluation = evaluate_package(version, case)
        actual_by_rule = {
            result.rule_id: _OUTCOME_PROJECTION[result.outcome]
            for result in evaluation.rule_results
        }
        expected: dict[str, TruthValue] = {}
        actual: dict[str, TruthValue] = {}
        for rule_id in sorted(test_case.expected_results):
            if rule_id not in actual_by_rule:
                raise EngineConfigurationError(
                    f"test case {test_case_id!r} expects rule {rule_id!r} that does "
                    "not exist in the package"
                )
            expected[rule_id] = test_case.expected_results[rule_id]
            actual[rule_id] = actual_by_rule[rule_id]
        passed = all(actual[rule_id] is expected[rule_id] for rule_id in expected)
        outcomes.append(
            TestCaseOutcome(
                test_case_id=test_case.id,
                passed=passed,
                expected=expected,
                actual=actual,
            )
        )
    return tuple(outcomes)


__all__ = ["TestCaseOutcome", "run_test_cases"]
