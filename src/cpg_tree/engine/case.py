"""Case input model for the deterministic rule engine.

A ``Case`` is the engine's runtime input: a frozen mapping of variable ids to
``CaseValue`` entries. It is deliberately distinct from the canonical knowledge
model, which describes protocols; the Case describes one concrete evaluation
request.

Two structural states are preserved:

- a variable **absent** from the Case (no key), and
- a variable **present** with ``CaseValue(UNKNOWN, None)``.

Both currently evaluate to ``UNKNOWN`` at condition level, but they remain
distinguishable so future states (e.g. NOT_COLLECTED) can be modeled without
changing the engine.

Malformed input never becomes UNKNOWN: non-scalar values and non-finite
numbers are rejected loudly at construction with ``CaseError``.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType

from cpg_tree.engine.errors import CaseError
from cpg_tree.knowledge.types import Scalar

_SCALAR_TYPES: tuple[type[object], ...] = (str, int, float, bool)


class CaseValueState(StrEnum):
    """Presence state of a single case value."""

    KNOWN = "KNOWN"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class CaseValue:
    """One variable value inside a Case.

    ``state=KNOWN`` requires a scalar value of type str, int, float, or bool.
    ``state=UNKNOWN`` requires ``value=None``: UNKNOWN is explicit missing
    information, never a silent default.
    """

    state: CaseValueState
    value: Scalar | None = None

    def __post_init__(self) -> None:
        if self.state is CaseValueState.UNKNOWN:
            if self.value is not None:
                raise CaseError("CaseValue with UNKNOWN state must have value None")
            return
        if self.value is None:
            raise CaseError("CaseValue with KNOWN state requires a non-None value")
        if not isinstance(self.value, _SCALAR_TYPES):
            raise CaseError(
                f"CaseValue values must be str, int, float, or bool; "
                f"got {type(self.value).__name__}"
            )
        if isinstance(self.value, float) and not math.isfinite(self.value):
            raise CaseError("CaseValue numbers must be finite; NaN and infinity are rejected")


@dataclass(frozen=True, slots=True)
class Case:
    """Frozen evaluation input: variable ids mapped to CaseValue entries.

    Extraneous keys (values for variables no condition references) are legal
    and ignored. The values mapping is exposed read-only through a
    ``MappingProxyType`` so the input cannot be mutated after construction.
    """

    values: Mapping[str, CaseValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key, entry in self.values.items():
            if not isinstance(key, str) or not key:
                raise CaseError("Case keys must be non-empty strings")
            if not isinstance(entry, CaseValue):
                raise CaseError("Case values must be CaseValue instances")
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))

    @classmethod
    def from_inputs(cls, inputs: Mapping[str, Scalar]) -> Case:
        """Build a Case from a plain scalar mapping.

        ``Scalar`` includes ``None``: a ``None`` value denotes explicitly
        missing information and becomes ``CaseValue(UNKNOWN, None)``. This is
        the bridge used by the test-case harness over ``TestCase.inputs``.
        """
        values: dict[str, CaseValue] = {}
        for key, value in inputs.items():
            if not isinstance(key, str) or not key:
                raise CaseError("Case keys must be non-empty strings")
            if value is None:
                values[key] = CaseValue(state=CaseValueState.UNKNOWN)
            else:
                values[key] = CaseValue(state=CaseValueState.KNOWN, value=value)
        return cls(values=values)
