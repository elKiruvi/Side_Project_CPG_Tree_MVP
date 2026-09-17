"""Tests for Variable construction and structural invariants."""

from __future__ import annotations

import pytest

from cpg_tree.knowledge import Variable, VariableType


def test_numeric_variable_with_unit() -> None:
    variable = Variable(id="count_x", label="Count X", type=VariableType.NUMERIC, unit="cells")
    assert variable.type is VariableType.NUMERIC
    assert variable.unit == "cells"
    assert variable.allowed_values is None


def test_categorical_variable_with_allowed_values() -> None:
    variable = Variable(
        id="category_z",
        label="Category Z",
        type=VariableType.CATEGORICAL,
        allowed_values=("alpha", "beta", "gamma"),
    )
    assert variable.allowed_values == ("alpha", "beta", "gamma")


def test_boolean_variable() -> None:
    variable = Variable(id="flag_y", label="Flag Y", type=VariableType.BOOLEAN)
    assert variable.type is VariableType.BOOLEAN


def test_duration_variable_with_unit() -> None:
    variable = Variable(id="span_t", label="Span T", type=VariableType.DURATION, unit="hours")
    assert variable.type is VariableType.DURATION
    assert variable.unit == "hours"


def test_allowed_values_rejected_for_non_categorical() -> None:
    with pytest.raises(ValueError, match="only valid for CATEGORICAL"):
        Variable(
            id="count_x",
            label="Count X",
            type=VariableType.NUMERIC,
            allowed_values=("alpha",),
        )


def test_empty_allowed_values_rejected() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        Variable(
            id="category_z", label="Category Z", type=VariableType.CATEGORICAL, allowed_values=()
        )


def test_empty_identifier_rejected() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        Variable(id="", label="Count X", type=VariableType.NUMERIC)


def test_whitespace_identifier_rejected() -> None:
    with pytest.raises(ValueError, match="must match"):
        Variable(id="count x", label="Count X", type=VariableType.NUMERIC)


def test_empty_label_rejected() -> None:
    with pytest.raises(ValueError, match="label must not be empty"):
        Variable(id="count_x", label="", type=VariableType.NUMERIC)
