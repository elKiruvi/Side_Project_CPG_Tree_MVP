"""Rules, actions, and their shared payload types."""

from __future__ import annotations

from dataclasses import dataclass

from cpg_tree.knowledge._validation import validate_identifier
from cpg_tree.knowledge.conditions import LogicalOperand
from cpg_tree.knowledge.enums import ActionType, ValidationStatus
from cpg_tree.knowledge.provenance import Provenance
from cpg_tree.knowledge.types import Scalar


@dataclass(frozen=True, slots=True)
class Action:
    """A typed consequence a rule may recommend.

    A decision is represented as an Action with ``type=ActionType.DECISION``;
    no separate Decision class exists.
    """

    id: str
    type: ActionType
    label: str | None = None
    payload: dict[str, Scalar] | None = None
    provenance: Provenance | None = None

    def __post_init__(self) -> None:
        validate_identifier(self.id, "Action.id")


@dataclass(frozen=True, slots=True)
class Rule:
    """IF condition THEN actions, with applicability, exceptions, and provenance.

    ``action_refs`` identify Action entries held by the owning ProtocolVersion.
    ``applies_to`` restricts the population the rule applies to; ``exceptions``
    suppress the rule when satisfied.
    """

    id: str
    condition: LogicalOperand
    action_refs: tuple[str, ...]
    provenance: Provenance
    applies_to: LogicalOperand | None = None
    exceptions: tuple[LogicalOperand, ...] = ()
    validation_status: ValidationStatus = ValidationStatus.DRAFT
    notes: str | None = None

    def __post_init__(self) -> None:
        validate_identifier(self.id, "Rule.id")
        if not self.action_refs:
            raise ValueError("Rule.action_refs must not be empty")
        for action_ref in self.action_refs:
            validate_identifier(action_ref, "Rule.action_refs entry")
