"""Test case definitions for knowledge packages."""

from __future__ import annotations

from dataclasses import dataclass, field

from cpg_tree.knowledge._validation import validate_identifier
from cpg_tree.knowledge.enums import TruthValue
from cpg_tree.knowledge.types import Scalar


@dataclass(frozen=True, slots=True)
class TestCase:
    """A synthetic or curated case against a protocol version.

    ``inputs`` maps variable ids to plain scalar values; ``None`` denotes
    explicitly missing information. ``expected_results`` maps rule ids to the
    expected TruthValue once the deterministic engine exists (Phase 4); it is a
    Phase 1 placeholder for package structure, not an evaluator contract.
    """

    id: str
    inputs: dict[str, Scalar] = field(default_factory=dict)
    expected_results: dict[str, TruthValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        validate_identifier(self.id, "TestCase.id")
        for variable_ref in self.inputs:
            validate_identifier(variable_ref, "TestCase.inputs key")
        for rule_ref in self.expected_results:
            validate_identifier(rule_ref, "TestCase.expected_results key")
