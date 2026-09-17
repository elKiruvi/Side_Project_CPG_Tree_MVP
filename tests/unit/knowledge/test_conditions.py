"""Tests for Condition construction and kind-specific structural invariants."""

from __future__ import annotations

import pytest

from cpg_tree.knowledge import (
    ComparisonOperator,
    Condition,
    ConditionKind,
    TemporalOperator,
    Variable,
)

OPERAND_HIGH = 100
DURATION_DAYS = 90


def test_comparison_condition(numeric_variable: Variable) -> None:
    condition = Condition(
        kind=ConditionKind.COMPARISON,
        variable_ref=numeric_variable.id,
        operator=ComparisonOperator.GT,
        operand=OPERAND_HIGH,
    )
    assert condition.operator is ComparisonOperator.GT
    assert condition.operand == OPERAND_HIGH


def test_comparison_requires_operator(numeric_variable: Variable) -> None:
    with pytest.raises(ValueError, match=r"require Condition\.operator"):
        Condition(
            kind=ConditionKind.COMPARISON,
            variable_ref=numeric_variable.id,
            operand=OPERAND_HIGH,
        )


def test_comparison_requires_operand(numeric_variable: Variable) -> None:
    with pytest.raises(ValueError, match=r"require Condition\.operand"):
        Condition(
            kind=ConditionKind.COMPARISON,
            variable_ref=numeric_variable.id,
            operator=ComparisonOperator.GT,
        )


def test_comparison_rejects_bool_operand(numeric_variable: Variable) -> None:
    with pytest.raises(ValueError, match="must be int or float"):
        Condition(
            kind=ConditionKind.COMPARISON,
            variable_ref=numeric_variable.id,
            operator=ComparisonOperator.GT,
            operand=True,
        )


def test_comparison_rejects_foreign_fields(numeric_variable: Variable) -> None:
    with pytest.raises(ValueError, match="not valid for COMPARISON"):
        Condition(
            kind=ConditionKind.COMPARISON,
            variable_ref=numeric_variable.id,
            operator=ComparisonOperator.GT,
            operand=OPERAND_HIGH,
            values=("alpha",),
        )


def test_membership_condition(categorical_variable: Variable) -> None:
    condition = Condition(
        kind=ConditionKind.MEMBERSHIP,
        variable_ref=categorical_variable.id,
        values=("alpha", "beta"),
    )
    assert condition.values == ("alpha", "beta")


def test_membership_requires_values(categorical_variable: Variable) -> None:
    with pytest.raises(ValueError, match=r"require Condition\.values"):
        Condition(kind=ConditionKind.MEMBERSHIP, variable_ref=categorical_variable.id)


def test_membership_rejects_empty_values(categorical_variable: Variable) -> None:
    with pytest.raises(ValueError, match="at least one value"):
        Condition(
            kind=ConditionKind.MEMBERSHIP,
            variable_ref=categorical_variable.id,
            values=(),
        )


def test_membership_rejects_foreign_fields(categorical_variable: Variable) -> None:
    with pytest.raises(ValueError, match="not valid for MEMBERSHIP"):
        Condition(
            kind=ConditionKind.MEMBERSHIP,
            variable_ref=categorical_variable.id,
            values=("alpha",),
            operand=OPERAND_HIGH,
        )


def test_flag_condition(flag_variable: Variable) -> None:
    condition = Condition(
        kind=ConditionKind.FLAG,
        variable_ref=flag_variable.id,
        expected=True,
    )
    assert condition.expected is True


def test_flag_requires_expected(flag_variable: Variable) -> None:
    with pytest.raises(ValueError, match=r"require Condition\.expected"):
        Condition(kind=ConditionKind.FLAG, variable_ref=flag_variable.id)


def test_flag_rejects_foreign_fields(flag_variable: Variable) -> None:
    with pytest.raises(ValueError, match="not valid for FLAG"):
        Condition(
            kind=ConditionKind.FLAG,
            variable_ref=flag_variable.id,
            expected=True,
            operator=ComparisonOperator.GT,
        )


def test_temporal_condition(duration_variable: Variable) -> None:
    condition = Condition(
        kind=ConditionKind.TEMPORAL,
        variable_ref=duration_variable.id,
        temporal_operator=TemporalOperator.AT_LEAST_FOR_LAST,
        duration_value=DURATION_DAYS,
        duration_unit="days",
    )
    assert condition.temporal_operator is TemporalOperator.AT_LEAST_FOR_LAST
    assert condition.duration_value == DURATION_DAYS
    assert condition.duration_unit == "days"


def test_temporal_requires_operator_and_duration(duration_variable: Variable) -> None:
    with pytest.raises(ValueError, match=r"require Condition\.temporal_operator"):
        Condition(
            kind=ConditionKind.TEMPORAL,
            variable_ref=duration_variable.id,
            duration_value=DURATION_DAYS,
            duration_unit="days",
        )
    with pytest.raises(ValueError, match=r"require Condition\.duration_value"):
        Condition(
            kind=ConditionKind.TEMPORAL,
            variable_ref=duration_variable.id,
            temporal_operator=TemporalOperator.WITHIN_LAST,
            duration_unit="days",
        )
    with pytest.raises(ValueError, match=r"require Condition\.duration_unit"):
        Condition(
            kind=ConditionKind.TEMPORAL,
            variable_ref=duration_variable.id,
            temporal_operator=TemporalOperator.WITHIN_LAST,
            duration_value=DURATION_DAYS,
        )


def test_temporal_rejects_non_positive_duration(duration_variable: Variable) -> None:
    with pytest.raises(ValueError, match="must be positive"):
        Condition(
            kind=ConditionKind.TEMPORAL,
            variable_ref=duration_variable.id,
            temporal_operator=TemporalOperator.WITHIN_LAST,
            duration_value=0,
            duration_unit="days",
        )


def test_temporal_rejects_foreign_fields(duration_variable: Variable) -> None:
    with pytest.raises(ValueError, match="not valid for TEMPORAL"):
        Condition(
            kind=ConditionKind.TEMPORAL,
            variable_ref=duration_variable.id,
            temporal_operator=TemporalOperator.WITHIN_LAST,
            duration_value=DURATION_DAYS,
            duration_unit="days",
            expected=True,
        )


def test_condition_requires_variable_ref() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        Condition(kind=ConditionKind.FLAG, variable_ref="", expected=True)
