"""Protocol and protocol version containers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol as TypingProtocol

from cpg_tree.knowledge._validation import validate_identifier, validate_iso_date
from cpg_tree.knowledge.documents import SourceDocument
from cpg_tree.knowledge.provenance import SourceFragment, ValidationItem
from cpg_tree.knowledge.rules import Action, Rule
from cpg_tree.knowledge.test_case import TestCase
from cpg_tree.knowledge.variables import Variable


class _Identified(TypingProtocol):
    id: str


@dataclass(frozen=True, slots=True)
class Protocol:
    """Stable identity of an institutional protocol."""

    id: str
    name: str
    description: str | None = None

    def __post_init__(self) -> None:
        validate_identifier(self.id, "Protocol.id")
        if not self.name:
            raise ValueError("Protocol.name must not be empty")


@dataclass(frozen=True, slots=True)
class ProtocolVersion:
    """A versioned knowledge container: the root of a knowledge package.

    Collections are keyed by the ``id`` of their entries (by ``document_id``
    for documents). Cross-references (variable_ref, action_refs, fragment_refs)
    are plain identifiers resolved against these collections by package
    validation (Phase 3). ``documents`` closes the provenance chain inside the
    package: fragments anchor to documents, documents anchor to content bytes.
    """

    protocol: Protocol
    version: str
    approval_date: str | None = None
    change_summary: str | None = None
    variables: dict[str, Variable] = field(default_factory=dict)
    rules: dict[str, Rule] = field(default_factory=dict)
    actions: dict[str, Action] = field(default_factory=dict)
    test_cases: dict[str, TestCase] = field(default_factory=dict)
    validation_items: dict[str, ValidationItem] = field(default_factory=dict)
    fragments: dict[str, SourceFragment] = field(default_factory=dict)
    documents: dict[str, SourceDocument] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.version or not self.version.strip():
            raise ValueError("ProtocolVersion.version must not be empty or whitespace")
        if self.approval_date is not None:
            validate_iso_date(self.approval_date, "ProtocolVersion.approval_date")
        self._check_keys(self.variables, "variables")
        self._check_keys(self.rules, "rules")
        self._check_keys(self.actions, "actions")
        self._check_keys(self.test_cases, "test_cases")
        self._check_keys(self.validation_items, "validation_items")
        self._check_keys(self.fragments, "fragments")
        self._check_documents(self.documents)

    @staticmethod
    def _check_keys(mapping: Mapping[str, _Identified], field_name: str) -> None:
        for key, value in mapping.items():
            if value.id != key:
                raise ValueError(
                    f"ProtocolVersion.{field_name} key {key!r} does not match entry id {value.id!r}"
                )

    @staticmethod
    def _check_documents(mapping: Mapping[str, SourceDocument]) -> None:
        for key, value in mapping.items():
            if value.document_id != key:
                raise ValueError(
                    f"ProtocolVersion.documents key {key!r} does not match "
                    f"document_id {value.document_id!r}"
                )
