"""Tests for package-level evaluation: determinism, purity, ordering."""

from __future__ import annotations

from dataclasses import replace

import pytest

from cpg_tree.engine import Case, EngineConfigurationError, RuleOutcome, evaluate_package
from cpg_tree.knowledge import (
    Condition,
    ConditionKind,
    DerivationState,
    Protocol,
    ProtocolVersion,
    dump_package,
)


def _full_case() -> Case:
    return Case.from_inputs({"count_x": 101, "flag_y": True, "category_z": "alpha", "span_t": 48})


def test_package_results_are_sorted_by_rule_id(synthetic_package: ProtocolVersion) -> None:
    result = evaluate_package(synthetic_package, _full_case())
    rule_ids = [rule_result.rule_id for rule_result in result.rule_results]
    assert rule_ids == sorted(rule_ids)
    assert rule_ids == sorted(synthetic_package.rules)


def test_package_evaluates_all_rules(synthetic_package: ProtocolVersion) -> None:
    result = evaluate_package(synthetic_package, _full_case())
    outcomes = {item.rule_id: item.outcome for item in result.rule_results}
    assert outcomes == {
        "rule_compare": RuleOutcome.MATCHED,
        "rule_flag": RuleOutcome.MATCHED,
        "rule_membership": RuleOutcome.MATCHED,
        "rule_temporal": RuleOutcome.MATCHED,
        "rule_composite": RuleOutcome.MATCHED,
        "rule_or": RuleOutcome.NOT_MATCHED,
        "rule_zero": RuleOutcome.NOT_MATCHED,
        "rule_unresolved": RuleOutcome.MATCHED,
    }


def test_repeated_evaluation_is_equal(synthetic_package: ProtocolVersion) -> None:
    case = _full_case()
    first = evaluate_package(synthetic_package, case)
    second = evaluate_package(synthetic_package, case)
    assert first == second
    assert first.rule_results == second.rule_results


def test_package_evaluation_does_not_mutate_package(synthetic_package: ProtocolVersion) -> None:
    before = dump_package(synthetic_package)
    evaluate_package(synthetic_package, _full_case())
    after = dump_package(synthetic_package)
    assert before == after


def test_package_evaluation_does_not_mutate_case(synthetic_package: ProtocolVersion) -> None:
    case = _full_case()
    evaluate_package(synthetic_package, case)
    assert case.values["count_x"].value == 101
    assert case.values["flag_y"].value is True
    assert set(case.values) == {"count_x", "flag_y", "category_z", "span_t"}


def test_unknown_action_ref_raises_configuration_error(synthetic_package: ProtocolVersion) -> None:
    rule = replace(synthetic_package.rules["rule_flag"], action_refs=("missing_act",))
    package = replace(synthetic_package, rules={**synthetic_package.rules, "rule_flag": rule})
    with pytest.raises(EngineConfigurationError, match="does not resolve"):
        evaluate_package(package, _full_case())


def test_unknown_variable_ref_raises_configuration_error(synthetic_package: ProtocolVersion) -> None:
    condition = Condition(kind=ConditionKind.FLAG, variable_ref="missing_v", expected=True)
    rule = replace(synthetic_package.rules["rule_flag"], condition=condition)
    package = replace(synthetic_package, rules={**synthetic_package.rules, "rule_flag": rule})
    with pytest.raises(EngineConfigurationError, match="does not resolve"):
        evaluate_package(package, _full_case())


def test_empty_package_yields_empty_results() -> None:
    package = ProtocolVersion(protocol=Protocol(id="TEST-PL-000", name="Empty"), version="v01")
    result = evaluate_package(package, Case.from_inputs({}))
    assert result.protocol_id == "TEST-PL-000"
    assert result.version == "v01"
    assert result.rule_results == ()


def test_zero_action_rule_matches_through_package(synthetic_package: ProtocolVersion) -> None:
    result = evaluate_package(synthetic_package, _full_case())
    zero = next(item for item in result.rule_results if item.rule_id == "rule_zero")
    assert zero.outcome is RuleOutcome.NOT_MATCHED
    assert zero.action_refs == ()


def test_result_carries_protocol_identity(synthetic_package: ProtocolVersion) -> None:
    result = evaluate_package(synthetic_package, _full_case())
    assert result.protocol_id == "TEST-PL-999"
    assert result.version == "v01"


def test_unresolved_rule_derivation_survives_package_evaluation(
    synthetic_package: ProtocolVersion,
) -> None:
    result = evaluate_package(synthetic_package, _full_case())
    unresolved = next(item for item in result.rule_results if item.rule_id == "rule_unresolved")
    assert unresolved.outcome is RuleOutcome.MATCHED
    assert unresolved.provenance.derivation is DerivationState.UNRESOLVED


def test_rule_provenance_reaches_evaluation_result(synthetic_package: ProtocolVersion) -> None:
    result = evaluate_package(synthetic_package, _full_case())
    compare = next(item for item in result.rule_results if item.rule_id == "rule_compare")
    assert compare.provenance is synthetic_package.rules["rule_compare"].provenance
