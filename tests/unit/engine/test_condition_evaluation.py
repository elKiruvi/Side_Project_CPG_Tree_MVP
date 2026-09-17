"""Tests for atomic condition evaluation: every ConditionKind, error contract."""

from __future__ import annotations

import pytest

from cpg_tree.engine import Case, EngineConfigurationError, EngineInputError, evaluate_condition
from cpg_tree.knowledge import (
    ComparisonOperator,
    Condition,
    ConditionKind,
    TemporalOperator,
    TruthValue,
    Variable,
    VariableType,
)

T = TruthValue.TRUE
F = TruthValue.FALSE
U = TruthValue.UNKNOWN


def _comparison(operator: ComparisonOperator, operand: int = 100) -> Condition:
    return Condition(
        kind=ConditionKind.COMPARISON,
        variable_ref="count_x",
        operator=operator,
        operand=operand,
    )


def _flag(expected: bool = True) -> Condition:
    return Condition(kind=ConditionKind.FLAG, variable_ref="flag_y", expected=expected)


def _membership(*values: str) -> Condition:
    return Condition(kind=ConditionKind.MEMBERSHIP, variable_ref="category_z", values=values)


def _temporal(
    operator: TemporalOperator,
    duration_value: float,
    unit: str = "hours",
    variable_ref: str = "span_t",
) -> Condition:
    return Condition(
        kind=ConditionKind.TEMPORAL,
        variable_ref=variable_ref,
        temporal_operator=operator,
        duration_value=duration_value,
        duration_unit=unit,
    )


# --- COMPARISON ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("operator", "value", "expected"),
    [
        (ComparisonOperator.EQ, 100, T),
        (ComparisonOperator.EQ, 101, F),
        (ComparisonOperator.NE, 100, F),
        (ComparisonOperator.NE, 101, T),
        (ComparisonOperator.LT, 99, T),
        (ComparisonOperator.LT, 100, F),
        (ComparisonOperator.LE, 100, T),
        (ComparisonOperator.LE, 101, F),
        (ComparisonOperator.GT, 101, T),
        (ComparisonOperator.GT, 100, F),
        (ComparisonOperator.GE, 100, T),
        (ComparisonOperator.GE, 99, F),
    ],
)
def test_comparison_operator_boundaries(
    operator: ComparisonOperator,
    value: int,
    expected: TruthValue,
) -> None:
    assert evaluate_condition(_comparison(operator), Case.from_inputs({"count_x": value})) is expected


def test_comparison_accepts_float_values() -> None:
    condition = Condition(
        kind=ConditionKind.COMPARISON,
        variable_ref="count_x",
        operator=ComparisonOperator.EQ,
        operand=100.0,
    )
    assert evaluate_condition(condition, Case.from_inputs({"count_x": 100})) is T


@pytest.mark.parametrize("bad_value", [True, False, "high"])
def test_comparison_rejects_non_numeric_values(bad_value: object) -> None:
    with pytest.raises(EngineInputError, match="numeric"):
        evaluate_condition(_comparison(ComparisonOperator.GT), Case.from_inputs({"count_x": bad_value}))  # type: ignore[arg-type]


def test_comparison_missing_variable_is_unknown() -> None:
    assert evaluate_condition(_comparison(ComparisonOperator.GT), Case.from_inputs({})) is U


def test_comparison_explicit_unknown_is_unknown() -> None:
    assert evaluate_condition(_comparison(ComparisonOperator.GT), Case.from_inputs({"count_x": None})) is U


def test_comparison_accepts_duration_variable() -> None:
    variables = {"span_t": Variable(id="span_t", label="Span T", type=VariableType.DURATION)}
    condition = Condition(
        kind=ConditionKind.COMPARISON,
        variable_ref="span_t",
        operator=ComparisonOperator.GT,
        operand=10,
    )
    assert evaluate_condition(condition, Case.from_inputs({"span_t": 12}), variables) is T


def test_comparison_rejects_boolean_variable() -> None:
    variables = {"flag_y": Variable(id="flag_y", label="Flag Y", type=VariableType.BOOLEAN)}
    with pytest.raises(EngineConfigurationError, match="NUMERIC or DURATION"):
        evaluate_condition(
            Condition(
                kind=ConditionKind.COMPARISON,
                variable_ref="flag_y",
                operator=ComparisonOperator.GT,
                operand=10,
            ),
            Case.from_inputs({"flag_y": True}),
            variables,
        )


def test_comparison_rejects_categorical_variable() -> None:
    variables = {"category_z": Variable(id="category_z", label="Z", type=VariableType.CATEGORICAL)}
    with pytest.raises(EngineConfigurationError, match="NUMERIC or DURATION"):
        evaluate_condition(
            Condition(
                kind=ConditionKind.COMPARISON,
                variable_ref="category_z",
                operator=ComparisonOperator.GT,
                operand=10,
            ),
            Case.from_inputs({"category_z": "alpha"}),
            variables,
        )


# --- MEMBERSHIP ---------------------------------------------------------------


def test_membership_in_values() -> None:
    assert evaluate_condition(_membership("alpha", "beta"), Case.from_inputs({"category_z": "alpha"})) is T


def test_membership_outside_values() -> None:
    assert evaluate_condition(_membership("alpha", "beta"), Case.from_inputs({"category_z": "gamma"})) is F


def test_membership_duplicate_values_do_not_alter_semantics() -> None:
    condition = _membership("alpha", "alpha", "beta")
    assert evaluate_condition(condition, Case.from_inputs({"category_z": "beta"})) is T
    assert evaluate_condition(condition, Case.from_inputs({"category_z": "gamma"})) is F


def test_membership_value_outside_allowed_values_is_evaluated() -> None:
    variables = {
        "category_z": Variable(
            id="category_z",
            label="Z",
            type=VariableType.CATEGORICAL,
            allowed_values=("alpha", "beta", "gamma"),
        )
    }
    assert (
        evaluate_condition(_membership("alpha", "beta"), Case.from_inputs({"category_z": "delta"}), variables)
        is F
    )


@pytest.mark.parametrize("bad_value", [42, 3.5, True])
def test_membership_rejects_non_string_values(bad_value: object) -> None:
    with pytest.raises(EngineInputError, match="string"):
        evaluate_condition(_membership("alpha"), Case.from_inputs({"category_z": bad_value}))  # type: ignore[arg-type]


def test_membership_missing_variable_is_unknown() -> None:
    assert evaluate_condition(_membership("alpha"), Case.from_inputs({})) is U


def test_membership_explicit_unknown_is_unknown() -> None:
    assert evaluate_condition(_membership("alpha"), Case.from_inputs({"category_z": None})) is U


def test_membership_rejects_numeric_variable() -> None:
    variables = {"count_x": Variable(id="count_x", label="X", type=VariableType.NUMERIC)}
    condition = Condition(
        kind=ConditionKind.MEMBERSHIP,
        variable_ref="count_x",
        values=("alpha",),
    )
    with pytest.raises(EngineConfigurationError, match="CATEGORICAL"):
        evaluate_condition(condition, Case.from_inputs({"count_x": 42}), variables)


# --- FLAG ---------------------------------------------------------------------


def test_flag_matches_expected() -> None:
    assert evaluate_condition(_flag(True), Case.from_inputs({"flag_y": True})) is T


def test_flag_does_not_match_expected() -> None:
    assert evaluate_condition(_flag(True), Case.from_inputs({"flag_y": False})) is F


def test_flag_rejects_int_disguised_as_bool() -> None:
    with pytest.raises(EngineInputError, match="boolean"):
        evaluate_condition(_flag(True), Case.from_inputs({"flag_y": 1}))  # type: ignore[dict-item]


def test_flag_missing_variable_is_unknown() -> None:
    assert evaluate_condition(_flag(True), Case.from_inputs({})) is U


def test_flag_explicit_unknown_is_unknown() -> None:
    assert evaluate_condition(_flag(True), Case.from_inputs({"flag_y": None})) is U


def test_flag_rejects_numeric_variable() -> None:
    variables = {"count_x": Variable(id="count_x", label="X", type=VariableType.NUMERIC)}
    condition = Condition(kind=ConditionKind.FLAG, variable_ref="count_x", expected=True)
    with pytest.raises(EngineConfigurationError, match="BOOLEAN"):
        evaluate_condition(condition, Case.from_inputs({"count_x": True}), variables)


# --- TEMPORAL -----------------------------------------------------------------


def test_at_least_for_last_inclusive_boundary() -> None:
    condition = _temporal(TemporalOperator.AT_LEAST_FOR_LAST, 48)
    assert evaluate_condition(condition, Case.from_inputs({"span_t": 48})) is T
    assert evaluate_condition(condition, Case.from_inputs({"span_t": 47})) is F
    assert evaluate_condition(condition, Case.from_inputs({"span_t": 49})) is T


def test_within_last_inclusive_boundary() -> None:
    condition = _temporal(TemporalOperator.WITHIN_LAST, 48)
    assert evaluate_condition(condition, Case.from_inputs({"span_t": 48})) is T
    assert evaluate_condition(condition, Case.from_inputs({"span_t": 49})) is F
    assert evaluate_condition(condition, Case.from_inputs({"span_t": 47})) is T


def test_temporal_zero_duration_threshold() -> None:
    condition = _temporal(TemporalOperator.AT_LEAST_FOR_LAST, 0)
    assert evaluate_condition(condition, Case.from_inputs({"span_t": 0})) is T
    assert evaluate_condition(condition, Case.from_inputs({"span_t": 1})) is T


def test_temporal_negative_duration_is_configuration_error() -> None:
    condition = _temporal(TemporalOperator.WITHIN_LAST, 0)
    object.__setattr__(condition, "duration_value", -1)
    with pytest.raises(EngineConfigurationError, match="must not be negative"):
        evaluate_condition(condition, Case.from_inputs({"span_t": 0}))


def test_temporal_unit_mismatch_is_configuration_error() -> None:
    variables = {"span_t": Variable(id="span_t", label="Span T", type=VariableType.DURATION, unit="hours")}
    condition = _temporal(TemporalOperator.WITHIN_LAST, 48, unit="days")
    with pytest.raises(EngineConfigurationError, match="does not match"):
        evaluate_condition(condition, Case.from_inputs({"span_t": 24}), variables)


def test_temporal_variable_without_unit_is_accepted() -> None:
    variables = {"span_t": Variable(id="span_t", label="Span T", type=VariableType.DURATION)}
    condition = _temporal(TemporalOperator.WITHIN_LAST, 48, unit="days")
    assert evaluate_condition(condition, Case.from_inputs({"span_t": 24}), variables) is T


def test_temporal_matching_units_are_accepted() -> None:
    variables = {"span_t": Variable(id="span_t", label="Span T", type=VariableType.DURATION, unit="hours")}
    condition = _temporal(TemporalOperator.WITHIN_LAST, 48, unit="hours")
    assert evaluate_condition(condition, Case.from_inputs({"span_t": 24}), variables) is T


@pytest.mark.parametrize("bad_value", [True, False, "long"])
def test_temporal_rejects_non_numeric_values(bad_value: object) -> None:
    with pytest.raises(EngineInputError, match="numeric"):
        evaluate_condition(_temporal(TemporalOperator.WITHIN_LAST, 48), Case.from_inputs({"span_t": bad_value}))  # type: ignore[arg-type]


def test_temporal_missing_variable_is_unknown() -> None:
    assert evaluate_condition(_temporal(TemporalOperator.WITHIN_LAST, 48), Case.from_inputs({})) is U


def test_temporal_explicit_unknown_is_unknown() -> None:
    assert evaluate_condition(_temporal(TemporalOperator.WITHIN_LAST, 48), Case.from_inputs({"span_t": None})) is U


def test_temporal_rejects_numeric_variable() -> None:
    variables = {"count_x": Variable(id="count_x", label="X", type=VariableType.NUMERIC)}
    with pytest.raises(EngineConfigurationError, match="DURATION"):
        evaluate_condition(
            _temporal(TemporalOperator.WITHIN_LAST, 48, variable_ref="count_x"),
            Case.from_inputs({"count_x": 24}),
            variables,
        )


# --- registry and reference handling -----------------------------------------


def test_unknown_variable_reference_raises_configuration_error() -> None:
    variables = {"count_x": Variable(id="count_x", label="X", type=VariableType.NUMERIC)}
    with pytest.raises(EngineConfigurationError, match="does not resolve"):
        evaluate_condition(_flag(True), Case.from_inputs({"flag_y": True}), variables)


def test_variables_none_skips_registry_checks() -> None:
    assert evaluate_condition(_flag(True), Case.from_inputs({"flag_y": True})) is T
