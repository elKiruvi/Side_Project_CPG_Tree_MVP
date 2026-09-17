"""Tests for Case and CaseValue construction, immutability, and bridges."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from types import MappingProxyType

import pytest

from cpg_tree.engine import Case, CaseError, CaseValue, CaseValueState

SCALAR_SAMPLES = ("alpha", 42, 3.5, True)


def test_known_scalar_values_accepted() -> None:
    for scalar in SCALAR_SAMPLES:
        case_value = CaseValue(state=CaseValueState.KNOWN, value=scalar)
        assert case_value.state is CaseValueState.KNOWN
        assert case_value.value == scalar


def test_unknown_requires_none_value() -> None:
    case_value = CaseValue(state=CaseValueState.UNKNOWN)
    assert case_value.state is CaseValueState.UNKNOWN
    assert case_value.value is None


def test_unknown_rejects_value() -> None:
    with pytest.raises(CaseError, match="must have value None"):
        CaseValue(state=CaseValueState.UNKNOWN, value=42)


def test_known_rejects_none() -> None:
    with pytest.raises(CaseError, match="non-None"):
        CaseValue(state=CaseValueState.KNOWN, value=None)


@pytest.mark.parametrize("bad_value", [[1, 2], {"a": 1}, {1, 2}, (1, 2), object()])
def test_known_rejects_non_scalars(bad_value: object) -> None:
    with pytest.raises(CaseError, match="must be str, int, float, or bool"):
        CaseValue(state=CaseValueState.KNOWN, value=bad_value)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad_number", [float("nan"), float("inf"), float("-inf")])
def test_known_rejects_non_finite_numbers(bad_number: float) -> None:
    with pytest.raises(CaseError, match="finite"):
        CaseValue(state=CaseValueState.KNOWN, value=bad_number)


def test_case_value_is_frozen() -> None:
    case_value = CaseValue(state=CaseValueState.KNOWN, value=42)
    with pytest.raises(FrozenInstanceError):
        case_value.value = 43  # type: ignore[misc]


def test_absent_and_explicit_unknown_are_structurally_distinct() -> None:
    absent = Case(values={})
    explicit = Case(values={"flag_y": CaseValue(state=CaseValueState.UNKNOWN)})
    assert "flag_y" not in absent.values
    assert "flag_y" in explicit.values
    assert explicit.values["flag_y"].state is CaseValueState.UNKNOWN


def test_case_values_are_read_only() -> None:
    case = Case(values={"flag_y": CaseValue(state=CaseValueState.KNOWN, value=True)})
    assert type(case.values) is MappingProxyType
    with pytest.raises(TypeError):
        case.values["flag_y"] = CaseValue(state=CaseValueState.UNKNOWN)  # type: ignore[index]


def test_case_rejects_non_string_keys() -> None:
    with pytest.raises(CaseError, match="non-empty strings"):
        Case(values={1: CaseValue(state=CaseValueState.KNOWN, value=True)})  # type: ignore[dict-item]


def test_case_rejects_non_casevalue_entries() -> None:
    with pytest.raises(CaseError, match="CaseValue instances"):
        Case(values={"flag_y": True})  # type: ignore[dict-item]


def test_extraneous_keys_are_allowed() -> None:
    case = Case(
        values={
            "flag_y": CaseValue(state=CaseValueState.KNOWN, value=True),
            "extra_zzz": CaseValue(state=CaseValueState.KNOWN, value="ignored"),
        }
    )
    assert "extra_zzz" in case.values


def test_from_inputs_maps_none_to_unknown() -> None:
    case = Case.from_inputs({"flag_y": None, "count_x": 7})
    assert case.values["flag_y"].state is CaseValueState.UNKNOWN
    assert case.values["count_x"].state is CaseValueState.KNOWN
    assert case.values["count_x"].value == 7


def test_from_inputs_accepts_all_scalar_kinds() -> None:
    case = Case.from_inputs({"s": "alpha", "i": 3, "f": 2.5, "b": False})
    assert case.values["s"].value == "alpha"
    assert case.values["i"].value == 3
    assert case.values["f"].value == 2.5
    assert case.values["b"].value is False


def test_from_inputs_rejects_non_scalars() -> None:
    with pytest.raises(CaseError, match="must be str, int, float, or bool"):
        Case.from_inputs({"flag_y": [1, 2]})  # type: ignore[dict-item]


def test_from_inputs_rejects_non_string_keys() -> None:
    with pytest.raises(CaseError, match="non-empty strings"):
        Case.from_inputs({1: True})  # type: ignore[dict-item]
