"""Variable definition for the canonical knowledge model."""

from __future__ import annotations

from dataclasses import dataclass

from cpg_tree.knowledge._validation import validate_identifier
from cpg_tree.knowledge.enums import VariableType


@dataclass(frozen=True, slots=True)
class Variable:
    """A generic clinical data element referenced by conditions.

    The model is protocol-agnostic: a variable carries only its identifier,
    display label, generic type, and optional unit/allowed values. Clinical
    meaning lives in protocol knowledge packages, never in this class.
    """

    id: str
    label: str
    type: VariableType
    unit: str | None = None
    allowed_values: tuple[str, ...] | None = None
    description: str | None = None
    source_note: str | None = None

    def __post_init__(self) -> None:
        validate_identifier(self.id, "Variable.id")
        if not self.label:
            raise ValueError("Variable.label must not be empty")
        if self.allowed_values is not None:
            if self.type is not VariableType.CATEGORICAL:
                raise ValueError(
                    "Variable.allowed_values is only valid for CATEGORICAL variables"
                )
            if not self.allowed_values:
                raise ValueError("Variable.allowed_values must not be empty when set")
