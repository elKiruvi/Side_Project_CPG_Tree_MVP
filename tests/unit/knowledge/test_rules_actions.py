"""Tests for Rule and Action construction and structural invariants."""

from __future__ import annotations

import pytest

from cpg_tree.knowledge import (
    Action,
    ActionType,
    ComparisonOperator,
    Condition,
    ConditionKind,
    DerivationState,
    LogicalExpression,
    LogicalOperator,
    Provenance,
    Rule,
    ValidationStatus,
    Variable,
)

OPERAND_HIGH = 100


def _provenance() -> Provenance:
    return Provenance(derivation=DerivationState.SOURCE_STATED, fragment_refs=("frag_1",))


def _condition(variable_ref: str = "count_x") -> Condition:
    return Condition(
        kind=ConditionKind.COMPARISON,
        variable_ref=variable_ref,
        operator=ComparisonOperator.GT,
        operand=OPERAND_HIGH,
    )


def test_rule_construction(numeric_variable: Variable) -> None:
    rule = Rule(
        id="rule_x",
        condition=_condition(numeric_variable.id),
        action_refs=("act_decide",),
        provenance=_provenance(),
    )
    assert rule.id == "rule_x"
    assert rule.action_refs == ("act_decide",)
    assert rule.validation_status is ValidationStatus.DRAFT
    assert rule.applies_to is None
    assert rule.exceptions == ()


def test_rule_with_applicability_and_exceptions(
    numeric_variable: Variable,
    flag_variable: Variable,
) -> None:
    rule = Rule(
        id="rule_x",
        condition=_condition(numeric_variable.id),
        action_refs=("act_decide",),
        provenance=_provenance(),
        applies_to=Condition(
            kind=ConditionKind.FLAG,
            variable_ref=flag_variable.id,
            expected=True,
        ),
        exceptions=(
            Condition(
                kind=ConditionKind.FLAG,
                variable_ref=flag_variable.id,
                expected=False,
            ),
        ),
        validation_status=ValidationStatus.REVIEWED,
        notes="synthetic rule",
    )
    assert rule.applies_to is not None
    assert len(rule.exceptions) == 1
    assert rule.validation_status is ValidationStatus.REVIEWED
    assert rule.notes == "synthetic rule"


def test_rule_requires_provenance(numeric_variable: Variable) -> None:
    with pytest.raises(TypeError):
        Rule(
            id="rule_x",
            condition=_condition(numeric_variable.id),
            action_refs=("act_decide",),
        )


def test_rule_rejects_empty_action_refs(numeric_variable: Variable) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        Rule(
            id="rule_x",
            condition=_condition(numeric_variable.id),
            action_refs=(),
            provenance=_provenance(),
        )


def test_rule_rejects_invalid_action_ref(numeric_variable: Variable) -> None:
    with pytest.raises(ValueError, match="must match"):
        Rule(
            id="rule_x",
            condition=_condition(numeric_variable.id),
            action_refs=("bad ref",),
            provenance=_provenance(),
        )


def test_rule_requires_identifier(numeric_variable: Variable) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        Rule(
            id="",
            condition=_condition(numeric_variable.id),
            action_refs=("act_decide",),
            provenance=_provenance(),
        )


def test_action_construction_with_all_types() -> None:
    for action_type in ActionType:
        action = Action(id=f"act_{action_type.value.lower()}", type=action_type)
        assert action.type is action_type


def test_decision_is_an_action() -> None:
    action = Action(id="act_decide", type=ActionType.DECISION, label="Hospitalize")
    assert action.type is ActionType.DECISION
    assert action.label == "Hospitalize"


def test_action_with_payload() -> None:
    action = Action(
        id="act_prescribe",
        type=ActionType.PRESCRIBE,
        payload={"drug": "x_agent", "dose_mg": 500},
    )
    assert action.payload == {"drug": "x_agent", "dose_mg": 500}


def test_action_requires_identifier() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        Action(id="", type=ActionType.DECISION)


def test_rule_accepts_logical_expression_condition(
    numeric_variable: Variable,
    flag_variable: Variable,
) -> None:
    expression = LogicalExpression(
        operator=LogicalOperator.AND,
        operands=(
            _condition(numeric_variable.id),
            Condition(kind=ConditionKind.FLAG, variable_ref=flag_variable.id, expected=True),
        ),
    )
    rule = Rule(
        id="rule_x",
        condition=expression,
        action_refs=("act_decide",),
        provenance=_provenance(),
    )
    assert rule.condition is expression
