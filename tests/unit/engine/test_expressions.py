"""Tests for composite expression evaluation and UNKNOWN propagation."""

from __future__ import annotations

import pytest

from cpg_tree.engine import Case, EngineConfigurationError, evaluate_operand
from cpg_tree.knowledge import (
    ComparisonOperator,
    Condition,
    ConditionKind,
    LogicalExpression,
    LogicalOperator,
    TruthValue,
)

T = TruthValue.TRUE
F = TruthValue.FALSE
U = TruthValue.UNKNOWN


def _flag(ref: str = "flag_y", expected: bool = True) -> Condition:
    return Condition(kind=ConditionKind.FLAG, variable_ref=ref, expected=expected)


def _comparison(ref: str = "count_x", operand: int = 100) -> Condition:
    return Condition(
        kind=ConditionKind.COMPARISON,
        variable_ref=ref,
        operator=ComparisonOperator.GT,
        operand=operand,
    )


def test_not_over_unknown_is_unknown() -> None:
    expression = LogicalExpression(operator=LogicalOperator.NOT, operands=(_flag(),))
    assert evaluate_operand(expression, Case.from_inputs({"flag_y": None})) is U


def test_nested_and_or_not_with_unknown() -> None:
    inner = LogicalExpression(
        operator=LogicalOperator.OR,
        operands=(_flag("flag_a"), _flag("flag_b")),
    )
    outer = LogicalExpression(
        operator=LogicalOperator.AND,
        operands=(inner, LogicalExpression(operator=LogicalOperator.NOT, operands=(_flag("flag_c"),))),
    )
    case = Case.from_inputs({"flag_a": False, "flag_b": None, "flag_c": False})
    assert evaluate_operand(outer, case) is U


def test_nested_at_least_n_inside_and() -> None:
    inner = LogicalExpression(
        operator=LogicalOperator.AT_LEAST_N,
        threshold=2,
        operands=(_comparison(), _flag("flag_y"), _flag("flag_b")),
    )
    outer = LogicalExpression(operator=LogicalOperator.AND, operands=(inner, _flag("flag_c")))
    case = Case.from_inputs(
        {"count_x": 101, "flag_y": True, "flag_b": False, "flag_c": True}
    )
    assert evaluate_operand(outer, case) is T


def test_at_least_n_with_mixed_unknowns() -> None:
    expression = LogicalExpression(
        operator=LogicalOperator.AT_LEAST_N,
        threshold=2,
        operands=(_comparison(), _flag("flag_y"), _flag("flag_b")),
    )
    assert evaluate_operand(
        expression, Case.from_inputs({"count_x": 101, "flag_y": True, "flag_b": False})
    ) is T
    assert evaluate_operand(
        expression, Case.from_inputs({"count_x": 101, "flag_y": None, "flag_b": False})
    ) is U
    assert evaluate_operand(
        expression, Case.from_inputs({"count_x": 50, "flag_y": None, "flag_b": False})
    ) is F


def test_nested_expression_evaluation_is_deterministic() -> None:
    expression = LogicalExpression(
        operator=LogicalOperator.AND,
        operands=(
            _comparison(),
            LogicalExpression(
                operator=LogicalOperator.OR,
                operands=(_flag("flag_y"), _flag("flag_b")),
            ),
        ),
    )
    case = Case.from_inputs({"count_x": 101, "flag_y": False, "flag_b": None})
    first = evaluate_operand(expression, case)
    second = evaluate_operand(expression, case)
    assert first is second is U


def test_operand_dispatches_plain_conditions() -> None:
    assert evaluate_operand(_flag("flag_y"), Case.from_inputs({"flag_y": True})) is T


def test_unsupported_operator_is_configuration_error() -> None:
    expression = LogicalExpression(operator=LogicalOperator.AND, operands=(_flag(),))
    object.__setattr__(expression, "operator", "XOR")
    with pytest.raises(EngineConfigurationError, match="unsupported"):
        evaluate_operand(expression, Case.from_inputs({"flag_y": True}))
