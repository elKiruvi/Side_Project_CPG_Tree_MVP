"""Tests for the three-valued logic combinators (strong Kleene)."""

from __future__ import annotations

import pytest

from cpg_tree.engine import EngineConfigurationError, and3, at_least_n3, not3, or3
from cpg_tree.knowledge import TruthValue

T = TruthValue.TRUE
F = TruthValue.FALSE
U = TruthValue.UNKNOWN


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        (T, T, T),
        (T, F, F),
        (T, U, U),
        (F, T, F),
        (F, F, F),
        (F, U, F),
        (U, T, U),
        (U, F, F),
        (U, U, U),
    ],
)
def test_and_full_table(left: TruthValue, right: TruthValue, expected: TruthValue) -> None:
    assert and3((left, right)) is expected


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        (T, T, T),
        (T, F, T),
        (T, U, T),
        (F, T, T),
        (F, F, F),
        (F, U, U),
        (U, T, T),
        (U, F, U),
        (U, U, U),
    ],
)
def test_or_full_table(left: TruthValue, right: TruthValue, expected: TruthValue) -> None:
    assert or3((left, right)) is expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [(T, F), (F, T), (U, U)],
)
def test_not_table(value: TruthValue, expected: TruthValue) -> None:
    assert not3(value) is expected


@pytest.mark.parametrize(
    ("operands", "threshold", "expected"),
    [
        # k=2 exhaustive
        ((T, T), 2, T),
        ((T, U), 2, U),
        ((T, F), 2, F),
        ((U, U), 2, U),
        ((U, F), 2, F),
        ((F, F), 2, F),
        # k=3 exhaustive
        ((T, T, T), 3, T),
        ((T, T, U), 3, U),
        ((T, U, U), 3, U),
        ((T, T, F), 3, F),
        ((T, F, U), 3, F),
        ((T, F, F), 3, F),
        ((U, U, U), 3, U),
        ((U, U, F), 3, F),
        ((F, F, F), 3, F),
        # k=1
        ((T,), 1, T),
        ((U,), 1, U),
        ((F,), 1, F),
        ((T, U), 1, T),
        ((U, F), 1, U),
        ((F, F), 1, F),
    ],
)
def test_at_least_n_formula(
    operands: tuple[TruthValue, ...],
    threshold: int,
    expected: TruthValue,
) -> None:
    assert at_least_n3(operands, threshold) is expected


def test_single_operand_and_is_identity() -> None:
    assert and3((T,)) is T
    assert and3((U,)) is U
    assert and3((F,)) is F


def test_single_operand_or_is_identity() -> None:
    assert or3((T,)) is T
    assert or3((U,)) is U
    assert or3((F,)) is F


def test_three_operand_and_with_unknown() -> None:
    assert and3((T, U, T)) is U
    assert and3((T, U, F)) is F


def test_three_operand_or_with_unknown() -> None:
    assert or3((F, U, F)) is U
    assert or3((F, U, T)) is T


def test_and_rejects_empty_operands() -> None:
    with pytest.raises(EngineConfigurationError, match="at least one operand"):
        and3(())


def test_or_rejects_empty_operands() -> None:
    with pytest.raises(EngineConfigurationError, match="at least one operand"):
        or3(())


def test_at_least_n_rejects_empty_operands() -> None:
    with pytest.raises(EngineConfigurationError, match="at least one operand"):
        at_least_n3((), 1)


def test_at_least_n_rejects_bool_threshold() -> None:
    with pytest.raises(EngineConfigurationError, match="must be an integer"):
        at_least_n3((T,), True)  # type: ignore[arg-type]


def test_at_least_n_rejects_none_threshold() -> None:
    with pytest.raises(EngineConfigurationError, match="must be an integer"):
        at_least_n3((T,), None)


def test_at_least_n_rejects_zero_threshold() -> None:
    with pytest.raises(EngineConfigurationError, match="between 1 and the operand count"):
        at_least_n3((T,), 0)


def test_at_least_n_rejects_threshold_above_operand_count() -> None:
    with pytest.raises(EngineConfigurationError, match="between 1 and the operand count"):
        at_least_n3((T, T), 3)
