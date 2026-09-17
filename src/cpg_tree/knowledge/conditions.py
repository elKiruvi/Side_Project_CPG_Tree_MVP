# ruff: noqa: TRY004
"""Atomic conditions and composite logical expressions.

TRY004 is disabled for this module on purpose: structural validation of the
canonical model raises ValueError by domain contract, and the test suite
asserts ValueError explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from cpg_tree.knowledge._validation import validate_identifier
from cpg_tree.knowledge.enums import (
    ComparisonOperator,
    ConditionKind,
    LogicalOperator,
    TemporalOperator,
)
from cpg_tree.knowledge.types import ScalarOperand

_MIN_DURATION: Final = 0.0
_MIN_THRESHOLD: Final = 1
_NOT_ARITY: Final = 1

_CONDITION_EXTRA_FIELDS = (
    "operator",
    "operand",
    "values",
    "expected",
    "temporal_operator",
    "duration_value",
    "duration_unit",
)

_FIELD_RULES: Final[dict[ConditionKind, tuple[tuple[str, ...], tuple[str, ...]]]] = {
    ConditionKind.COMPARISON: (
        ("operator", "operand"),
        ("values", "expected", "temporal_operator", "duration_value", "duration_unit"),
    ),
    ConditionKind.MEMBERSHIP: (
        ("values",),
        ("operator", "operand", "expected", "temporal_operator", "duration_value", "duration_unit"),
    ),
    ConditionKind.FLAG: (
        ("expected",),
        ("operator", "operand", "values", "temporal_operator", "duration_value", "duration_unit"),
    ),
    ConditionKind.TEMPORAL: (
        ("temporal_operator", "duration_value", "duration_unit"),
        ("operator", "operand", "values", "expected"),
    ),
}


@dataclass(frozen=True, slots=True)
class Condition:
    """An atomic predicate over a single variable.

    The ``kind`` discriminator selects which fields are meaningful:

    - ``COMPARISON``: ``operator`` + numeric ``operand``.
    - ``MEMBERSHIP``: ``values`` set of allowed categories.
    - ``FLAG``: ``expected`` boolean value.
    - ``TEMPORAL``: ``temporal_operator`` + ``duration_value``/``duration_unit``.

    Conditions are inert data: nothing here evaluates. Missing data semantics
    (UNKNOWN) belong to the future deterministic engine, and this design keeps
    them possible by never implying an evaluation outcome.
    """

    kind: ConditionKind
    variable_ref: str
    operator: ComparisonOperator | None = None
    operand: ScalarOperand | None = None
    values: tuple[str, ...] | None = None
    expected: bool | None = None
    temporal_operator: TemporalOperator | None = None
    duration_value: float | None = None
    duration_unit: str | None = None

    def __post_init__(self) -> None:
        validate_identifier(self.variable_ref, "Condition.variable_ref")
        required, forbidden = _FIELD_RULES[self.kind]
        for field_name in required:
            if getattr(self, field_name) is None:
                raise ValueError(f"{self.kind.value} conditions require Condition.{field_name}")
        for field_name in forbidden:
            if getattr(self, field_name) is not None:
                raise ValueError(
                    f"Condition.{field_name} is not valid for {self.kind.value} conditions"
                )
        self._validate_kind_fields()

    def _validate_kind_fields(self) -> None:
        if self.kind is ConditionKind.COMPARISON:
            self._require_number(self.operand, "COMPARISON operands")
        elif self.kind is ConditionKind.MEMBERSHIP:
            if not self.values:
                raise ValueError("MEMBERSHIP conditions require at least one value")
        elif self.kind is ConditionKind.TEMPORAL:
            self._require_number(self.duration_value, "TEMPORAL duration_value")
            if self.duration_value is None or self.duration_value <= _MIN_DURATION:
                raise ValueError("TEMPORAL duration_value must be positive")
            if not self.duration_unit:
                raise ValueError("TEMPORAL conditions require a non-empty duration_unit")

    @staticmethod
    def _require_number(value: object, label: str) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{label} must be int or float")


type LogicalOperand = Condition | LogicalExpression
"""Operand of a logical expression: an atomic condition or a nested expression."""


@dataclass(frozen=True, slots=True)
class LogicalExpression:
    """A composite predicate over conditions or nested expressions.

    ``AT_LEAST_N`` requires ``threshold``: satisfied when at least ``threshold``
    operands are satisfied. The composite operators enable representing the
    multi-criteria rules present in source protocols without reducing them to
    binary trees.
    """

    operator: LogicalOperator
    operands: tuple[LogicalOperand, ...]
    threshold: int | None = None

    def __post_init__(self) -> None:
        if not self.operands:
            raise ValueError("LogicalExpression.operands must not be empty")
        if self.operator is LogicalOperator.NOT:
            if len(self.operands) != _NOT_ARITY:
                raise ValueError("NOT expressions require exactly one operand")
            if self.threshold is not None:
                raise ValueError("NOT expressions do not accept a threshold")
        elif self.operator is LogicalOperator.AT_LEAST_N:
            if self.threshold is None:
                raise ValueError("AT_LEAST_N expressions require a threshold")
            if isinstance(self.threshold, bool) or not isinstance(self.threshold, int):
                raise ValueError("AT_LEAST_N threshold must be an integer")
            if not _MIN_THRESHOLD <= self.threshold <= len(self.operands):
                raise ValueError("AT_LEAST_N threshold must be between 1 and the operand count")
        elif self.threshold is not None:
            raise ValueError(f"{self.operator.value} expressions do not accept a threshold")
