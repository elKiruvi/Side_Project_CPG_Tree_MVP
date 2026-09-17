"""Tests for the runtime case input adapter."""

from __future__ import annotations

import pytest

from cpg_tree.engine import CaseValueState
from cpg_tree.knowledge import ProtocolVersion
from cpg_tree.views.case_loader import CaseLoadError, load_case_text

COUNT_X_KNOWN = 101
SPAN_T_KNOWN = 48


def test_valid_scalars_load_as_known_values(synthetic_package: ProtocolVersion) -> None:
    case = load_case_text(
        '{"count_x": 101, "flag_y": true, "category_z": "alpha", "span_t": 48}',
        synthetic_package.variables,
    )
    assert case.values["count_x"].state is CaseValueState.KNOWN
    assert case.values["count_x"].value == COUNT_X_KNOWN
    assert case.values["flag_y"].value is True
    assert case.values["category_z"].value == "alpha"
    assert case.values["span_t"].value == SPAN_T_KNOWN


def test_null_loads_as_explicit_unknown(synthetic_package: ProtocolVersion) -> None:
    case = load_case_text('{"count_x": null}', synthetic_package.variables)
    assert case.values["count_x"].state is CaseValueState.UNKNOWN
    assert case.values["count_x"].value is None


def test_absent_key_stays_absent(synthetic_package: ProtocolVersion) -> None:
    case = load_case_text('{"flag_y": true}', synthetic_package.variables)
    assert "count_x" not in case.values


def test_unknown_variable_fails_with_available_list(
    synthetic_package: ProtocolVersion,
) -> None:
    with pytest.raises(CaseLoadError, match="unknown variable 'no_such'"):
        load_case_text('{"no_such": 1}', synthetic_package.variables)


def test_boolean_value_requires_boolean_variable(
    synthetic_package: ProtocolVersion,
) -> None:
    with pytest.raises(CaseLoadError, match="variable is NUMERIC"):
        load_case_text('{"count_x": true}', synthetic_package.variables)


def test_numeric_value_requires_numeric_or_duration_variable(
    synthetic_package: ProtocolVersion,
) -> None:
    with pytest.raises(CaseLoadError, match="variable is BOOLEAN"):
        load_case_text('{"flag_y": 1}', synthetic_package.variables)
    with pytest.raises(CaseLoadError, match="variable is CATEGORICAL"):
        load_case_text('{"category_z": 1}', synthetic_package.variables)


def test_string_value_requires_categorical_variable(
    synthetic_package: ProtocolVersion,
) -> None:
    with pytest.raises(CaseLoadError, match="variable is BOOLEAN"):
        load_case_text('{"flag_y": "true"}', synthetic_package.variables)


def test_non_object_root_fails(synthetic_package: ProtocolVersion) -> None:
    with pytest.raises(CaseLoadError, match="JSON object"):
        load_case_text("[1, 2]", synthetic_package.variables)


def test_malformed_json_fails(synthetic_package: ProtocolVersion) -> None:
    with pytest.raises(CaseLoadError, match="not valid JSON"):
        load_case_text('{"flag_y": }', synthetic_package.variables)


def test_non_finite_numbers_are_rejected(synthetic_package: ProtocolVersion) -> None:
    with pytest.raises(CaseLoadError, match="finite"):
        load_case_text('{"count_x": NaN}', synthetic_package.variables)


def test_loading_is_deterministic(synthetic_package: ProtocolVersion) -> None:
    text = '{"count_x": 101, "flag_y": true}'
    first = load_case_text(text, synthetic_package.variables)
    second = load_case_text(text, synthetic_package.variables)
    assert first == second
    assert first.values["count_x"].value == second.values["count_x"].value
