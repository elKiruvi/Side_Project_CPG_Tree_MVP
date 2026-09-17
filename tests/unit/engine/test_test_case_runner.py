"""Tests for the test-case harness built on the engine."""

from __future__ import annotations

from dataclasses import replace

import pytest

from cpg_tree.engine import (
    Case,
    EngineConfigurationError,
    RuleOutcome,
    evaluate_package,
    run_test_cases,
)
from cpg_tree.knowledge import (
    Condition,
    ConditionKind,
    DerivationState,
    LogicalExpression,
    LogicalOperator,
    Protocol,
    ProtocolVersion,
    Provenance,
    Rule,
    TestCase,
    TruthValue,
    Variable,
    VariableType,
)

# Prevent pytest from trying to collect the imported TestCase dataclass.
TestCase.__test__ = False  # type: ignore[misc]


def test_all_package_test_cases_pass(synthetic_package: ProtocolVersion) -> None:
    outcomes = run_test_cases(synthetic_package)
    assert [outcome.test_case_id for outcome in outcomes] == ["tc_full", "tc_missing"]
    assert all(outcome.passed for outcome in outcomes)


def test_matched_projects_to_true(synthetic_package: ProtocolVersion) -> None:
    outcome = run_test_cases(synthetic_package)[0]
    assert outcome.actual["rule_compare"] is TruthValue.TRUE
    assert outcome.expected["rule_compare"] is TruthValue.TRUE


def test_not_matched_projects_to_false(synthetic_package: ProtocolVersion) -> None:
    outcome = run_test_cases(synthetic_package)[0]
    assert outcome.actual["rule_or"] is TruthValue.FALSE


def test_indeterminate_projects_to_unknown(synthetic_package: ProtocolVersion) -> None:
    missing = run_test_cases(synthetic_package)[1]
    assert missing.test_case_id == "tc_missing"
    assert missing.actual["rule_flag"] is TruthValue.UNKNOWN
    assert missing.expected["rule_flag"] is TruthValue.UNKNOWN


def test_excepted_projects_to_false() -> None:
    package = ProtocolVersion(
        protocol=Protocol(id="TEST-PL-777", name="Except"),
        version="v01",
        variables={"flag_y": Variable(id="flag_y", label="Flag Y", type=VariableType.BOOLEAN)},
        rules={
            "rule_x": Rule(
                id="rule_x",
                condition=Condition(kind=ConditionKind.FLAG, variable_ref="flag_y", expected=True),
                action_refs=(),
                exceptions=(
                    LogicalExpression(
                        operator=LogicalOperator.NOT,
                        operands=(
                            Condition(
                                kind=ConditionKind.FLAG,
                                variable_ref="flag_y",
                                expected=False,
                            ),
                        ),
                    ),
                ),
                provenance=Provenance(derivation=DerivationState.SOURCE_STATED),
            )
        },
        test_cases={
            "tc_one": TestCase(
                id="tc_one",
                inputs={"flag_y": True},
                expected_results={"rule_x": TruthValue.FALSE},
            )
        },
    )
    evaluation = evaluate_package(package, Case.from_inputs({"flag_y": True}))
    assert evaluation.rule_results[0].outcome is RuleOutcome.EXCEPTED
    outcome = run_test_cases(package)[0]
    assert outcome.passed
    assert outcome.actual["rule_x"] is TruthValue.FALSE


def test_failing_expectation_reports_failure(synthetic_package: ProtocolVersion) -> None:
    wrong = TestCase(
        id="tc_full",
        inputs={"count_x": 101, "flag_y": True, "category_z": "alpha", "span_t": 48},
        expected_results={"rule_compare": TruthValue.FALSE},
    )
    package = replace(synthetic_package, test_cases={"tc_full": wrong})
    outcome = run_test_cases(package)[0]
    assert not outcome.passed
    assert outcome.expected["rule_compare"] is TruthValue.FALSE
    assert outcome.actual["rule_compare"] is TruthValue.TRUE


def test_run_test_cases_is_deterministic(synthetic_package: ProtocolVersion) -> None:
    first = run_test_cases(synthetic_package)
    second = run_test_cases(synthetic_package)
    assert first == second


def test_unknown_expected_rule_raises_configuration_error(
    synthetic_package: ProtocolVersion,
) -> None:
    bad = TestCase(
        id="tc_bad",
        inputs={},
        expected_results={"rule_ghost": TruthValue.TRUE},
    )
    package = replace(synthetic_package, test_cases={"tc_bad": bad})
    with pytest.raises(EngineConfigurationError, match="does not exist"):
        run_test_cases(package)


def test_only_listed_rules_are_asserted(synthetic_package: ProtocolVersion) -> None:
    sparse = TestCase(
        id="tc_sparse",
        inputs={"flag_y": True},
        expected_results={"rule_flag": TruthValue.TRUE},
    )
    package = replace(synthetic_package, test_cases={"tc_sparse": sparse})
    outcome = run_test_cases(package)[0]
    assert outcome.passed
    assert set(outcome.actual) == {"rule_flag"}
    assert set(outcome.expected) == {"rule_flag"}
