"""Tests for LogicalExpression construction and operator-specific arities."""

from __future__ import annotations

import pytest

from cpg_tree.knowledge import (
    ComparisonOperator,
    Condition,
    ConditionKind,
    LogicalExpression,
    LogicalOperator,
    Variable,
)

THRESHOLD_TWO = 2


def _comparison(variable_ref: str, operand: int = 100) -> Condition:
    return Condition(
        kind=ConditionKind.COMPARISON,
        variable_ref=variable_ref,
        operator=ComparisonOperator.GT,
        operand=operand,
    )


def _flag(variable_ref: str, expected: bool = True) -> Condition:
    return Condition(kind=ConditionKind.FLAG, variable_ref=variable_ref, expected=expected)


def test_and_expression(numeric_variable: Variable, flag_variable: Variable) -> None:
    expression = LogicalExpression(
        operator=LogicalOperator.AND,
        operands=(_comparison(numeric_variable.id), _flag(flag_variable.id)),
    )
    assert expression.operator is LogicalOperator.AND
    assert len(expression.operands) == THRESHOLD_TWO
    assert expression.threshold is None


def test_or_expression(numeric_variable: Variable, flag_variable: Variable) -> None:
    expression = LogicalExpression(
        operator=LogicalOperator.OR,
        operands=(_comparison(numeric_variable.id), _flag(flag_variable.id)),
    )
    assert expression.operator is LogicalOperator.OR
    assert expression.threshold is None


def test_single_operand_allowed(flag_variable: Variable) -> None:
    expression = LogicalExpression(
        operator=LogicalOperator.AND,
        operands=(_flag(flag_variable.id),),
    )
    assert len(expression.operands) == 1


def test_not_expression(flag_variable: Variable) -> None:
    expression = LogicalExpression(
        operator=LogicalOperator.NOT,
        operands=(_flag(flag_variable.id),),
    )
    assert expression.operator is LogicalOperator.NOT
    assert expression.threshold is None


def test_not_requires_exactly_one_operand(flag_variable: Variable) -> None:
    with pytest.raises(ValueError, match="exactly one operand"):
        LogicalExpression(
            operator=LogicalOperator.NOT,
            operands=(_flag(flag_variable.id), _flag(flag_variable.id)),
        )


def test_not_rejects_threshold(flag_variable: Variable) -> None:
    with pytest.raises(ValueError, match="do not accept a threshold"):
        LogicalExpression(
            operator=LogicalOperator.NOT,
            operands=(_flag(flag_variable.id),),
            threshold=THRESHOLD_TWO,
        )


def test_at_least_n_expression(
    numeric_variable: Variable,
    flag_variable: Variable,
    categorical_variable: Variable,
) -> None:
    expression = LogicalExpression(
        operator=LogicalOperator.AT_LEAST_N,
        threshold=THRESHOLD_TWO,
        operands=(
            _comparison(numeric_variable.id),
            _flag(flag_variable.id),
            Condition(
                kind=ConditionKind.MEMBERSHIP,
                variable_ref=categorical_variable.id,
                values=("alpha",),
            ),
        ),
    )
    assert expression.threshold == THRESHOLD_TWO
    assert len(expression.operands) == 3


def test_at_least_n_requires_threshold(flag_variable: Variable) -> None:
    with pytest.raises(ValueError, match="require a threshold"):
        LogicalExpression(
            operator=LogicalOperator.AT_LEAST_N,
            operands=(_flag(flag_variable.id),),
        )


def test_at_least_n_rejects_zero_threshold(flag_variable: Variable) -> None:
    with pytest.raises(ValueError, match="between 1 and the operand count"):
        LogicalExpression(
            operator=LogicalOperator.AT_LEAST_N,
            threshold=0,
            operands=(_flag(flag_variable.id),),
        )


def test_at_least_n_rejects_threshold_above_operand_count(
    flag_variable: Variable,
) -> None:
    with pytest.raises(ValueError, match="between 1 and the operand count"):
        LogicalExpression(
            operator=LogicalOperator.AT_LEAST_N,
            threshold=THRESHOLD_TWO,
            operands=(_flag(flag_variable.id),),
        )


def test_and_rejects_threshold(flag_variable: Variable) -> None:
    with pytest.raises(ValueError, match="do not accept a threshold"):
        LogicalExpression(
            operator=LogicalOperator.AND,
            operands=(_flag(flag_variable.id),),
            threshold=THRESHOLD_TWO,
        )


def test_empty_operands_rejected() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        LogicalExpression(operator=LogicalOperator.AND, operands=())


def test_nested_expressions(
    numeric_variable: Variable,
    flag_variable: Variable,
    categorical_variable: Variable,
) -> None:
    inner = LogicalExpression(
        operator=LogicalOperator.AT_LEAST_N,
        threshold=THRESHOLD_TWO,
        operands=(
            _comparison(numeric_variable.id),
            _flag(flag_variable.id),
            Condition(
                kind=ConditionKind.MEMBERSHIP,
                variable_ref=categorical_variable.id,
                values=("alpha",),
            ),
        ),
    )
    outer = LogicalExpression(
        operator=LogicalOperator.AND,
        operands=(inner, _flag(flag_variable.id, expected=False)),
    )
    assert outer.operands[0] is inner
