"""Tests for rule evaluation: outcomes, short-circuit paths, and contracts."""

from __future__ import annotations

from dataclasses import replace

import pytest

from cpg_tree.engine import (
    Case,
    EngineConfigurationError,
    EngineInputError,
    RuleOutcome,
    evaluate_rule,
)
from cpg_tree.knowledge import (
    ComparisonOperator,
    Condition,
    ConditionKind,
    DerivationState,
    LogicalExpression,
    Provenance,
    Rule,
    TruthValue,
    ValidationStatus,
    Variable,
    VariableType,
)

T = TruthValue.TRUE
F = TruthValue.FALSE
U = TruthValue.UNKNOWN

FLAG_TRUE = Condition(kind=ConditionKind.FLAG, variable_ref="flag_y", expected=True)
FLAG_FALSE = Condition(kind=ConditionKind.FLAG, variable_ref="flag_y", expected=False)


def _rule(
    condition: Condition | LogicalExpression = FLAG_TRUE,
    *,
    action_refs: tuple[str, ...] = ("act_decide",),
    applies_to: Condition | LogicalExpression | None = None,
    exceptions: tuple[Condition | LogicalExpression, ...] = (),
    derivation: DerivationState = DerivationState.SOURCE_STATED,
) -> Rule:
    return Rule(
        id="rule_x",
        condition=condition,
        action_refs=action_refs,
        provenance=Provenance(derivation=derivation),
        applies_to=applies_to,
        exceptions=exceptions,
    )


def test_matched_rule_carries_declared_action_refs() -> None:
    result = evaluate_rule(_rule(), Case.from_inputs({"flag_y": True}))
    assert result.outcome is RuleOutcome.MATCHED
    assert result.action_refs == ("act_decide",)
    assert result.condition_result is T
    assert result.applies_to_result is None
    assert result.exception_results == ()


def test_zero_action_rule_matches_with_empty_refs() -> None:
    result = evaluate_rule(_rule(action_refs=()), Case.from_inputs({"flag_y": True}))
    assert result.outcome is RuleOutcome.MATCHED
    assert result.action_refs == ()


def test_not_matched_when_condition_false() -> None:
    result = evaluate_rule(_rule(), Case.from_inputs({"flag_y": False}))
    assert result.outcome is RuleOutcome.NOT_MATCHED
    assert result.condition_result is F
    assert result.exception_results == ()
    assert result.action_refs == ()


def test_indeterminate_when_condition_unknown() -> None:
    result = evaluate_rule(_rule(), Case.from_inputs({"flag_y": None}))
    assert result.outcome is RuleOutcome.INDETERMINATE
    assert result.condition_result is U
    assert result.exception_results == ()
    assert result.action_refs == ()


def test_applies_to_true_proceeds() -> None:
    result = evaluate_rule(
        _rule(applies_to=FLAG_TRUE),
        Case.from_inputs({"flag_y": True}),
    )
    assert result.outcome is RuleOutcome.MATCHED
    assert result.applies_to_result is T


def test_applies_to_false_is_not_applicable() -> None:
    result = evaluate_rule(
        _rule(applies_to=FLAG_TRUE),
        Case.from_inputs({"flag_y": False}),
    )
    assert result.outcome is RuleOutcome.NOT_APPLICABLE
    assert result.applies_to_result is F
    assert result.condition_result is U
    assert result.exception_results == ()
    assert result.action_refs == ()


def test_applies_to_unknown_is_indeterminate() -> None:
    result = evaluate_rule(
        _rule(applies_to=FLAG_TRUE),
        Case.from_inputs({"flag_y": None}),
    )
    assert result.outcome is RuleOutcome.INDETERMINATE
    assert result.applies_to_result is U
    assert result.condition_result is U
    assert result.exception_results == ()


def test_absent_applies_to_yields_none_result() -> None:
    result = evaluate_rule(_rule(), Case.from_inputs({"flag_y": True}))
    assert result.applies_to_result is None


def test_exceptions_all_false_match() -> None:
    result = evaluate_rule(
        _rule(exceptions=(FLAG_FALSE,)),
        Case.from_inputs({"flag_y": True}),
    )
    assert result.outcome is RuleOutcome.MATCHED
    assert result.exception_results == (F,)


def test_exception_true_suppresses_rule() -> None:
    result = evaluate_rule(
        _rule(exceptions=(FLAG_TRUE,)),
        Case.from_inputs({"flag_y": True}),
    )
    assert result.outcome is RuleOutcome.EXCEPTED
    assert result.exception_results == (T,)
    assert result.action_refs == ()


def test_exception_unknown_is_indeterminate() -> None:
    exception = Condition(kind=ConditionKind.FLAG, variable_ref="flag_b", expected=True)
    result = evaluate_rule(
        _rule(exceptions=(exception,)),
        Case.from_inputs({"flag_y": True, "flag_b": None}),
    )
    assert result.outcome is RuleOutcome.INDETERMINATE
    assert result.exception_results == (U,)
    assert result.action_refs == ()


def test_exceptions_not_evaluated_when_condition_false() -> None:
    exception = Condition(kind=ConditionKind.FLAG, variable_ref="missing_v", expected=True)
    result = evaluate_rule(
        _rule(exceptions=(exception,)),
        Case.from_inputs({"flag_y": False}),
    )
    assert result.outcome is RuleOutcome.NOT_MATCHED
    assert result.exception_results == ()


def test_validation_status_never_gates_evaluation() -> None:
    for status in ValidationStatus:
        rule = replace(_rule(), validation_status=status)
        result = evaluate_rule(rule, Case.from_inputs({"flag_y": True}))
        assert result.outcome is RuleOutcome.MATCHED
        assert result.validation_status is status


def test_provenance_is_carried_verbatim() -> None:
    rule = _rule(derivation=DerivationState.EXTRACTED)
    result = evaluate_rule(rule, Case.from_inputs({"flag_y": True}))
    assert result.provenance is rule.provenance
    assert result.provenance.derivation is DerivationState.EXTRACTED


def test_unresolved_rule_is_mechanically_evaluated_without_validation_claim() -> None:
    rule = _rule(derivation=DerivationState.UNRESOLVED)
    result = evaluate_rule(rule, Case.from_inputs({"flag_y": True}))
    assert result.outcome is RuleOutcome.MATCHED
    assert result.provenance.derivation is DerivationState.UNRESOLVED
    assert result.validation_status is ValidationStatus.DRAFT


def test_incompatible_input_raises_engine_input_error() -> None:
    condition = Condition(
        kind=ConditionKind.COMPARISON,
        variable_ref="count_x",
        operator=ComparisonOperator.GT,
        operand=10,
    )
    rule = _rule(condition=condition)
    with pytest.raises(EngineInputError, match="numeric"):
        evaluate_rule(rule, Case.from_inputs({"count_x": "high"}))  # type: ignore[dict-item]


def test_unknown_variable_reference_raises_configuration_error() -> None:
    variables = {"flag_y": Variable(id="flag_y", label="Y", type=VariableType.BOOLEAN)}
    with pytest.raises(EngineConfigurationError, match="does not resolve"):
        evaluate_rule(
            _rule(), Case.from_inputs({"flag_y": True}), variables={"other": variables["flag_y"]}
        )


def test_provenance_not_used_as_condition() -> None:
    no_source = _rule(derivation=DerivationState.UNRESOLVED, applies_to=FLAG_FALSE)
    result = evaluate_rule(no_source, Case.from_inputs({"flag_y": True}))
    assert result.outcome is RuleOutcome.NOT_APPLICABLE
    assert result.provenance.derivation is DerivationState.UNRESOLVED
