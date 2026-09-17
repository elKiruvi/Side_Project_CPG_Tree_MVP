"""Provenance, source fragments, and validation items."""

from __future__ import annotations

from dataclasses import dataclass

from cpg_tree.knowledge._validation import validate_identifier, validate_iso_date
from cpg_tree.knowledge.enums import DerivationState, ValidationItemStatus


@dataclass(frozen=True, slots=True)
class SourceFragment:
    """A verbatim text span in a source document that backs knowledge elements.

    ``document_id`` anchors the fragment to a SourceDocument; the SourceDocument
    entity itself belongs to the ingestion pipeline (Phase 2).
    """

    id: str
    document_id: str | None = None
    page: int | None = None
    section: str | None = None
    verbatim_text: str | None = None

    def __post_init__(self) -> None:
        validate_identifier(self.id, "SourceFragment.id")
        if self.document_id is not None:
            validate_identifier(self.document_id, "SourceFragment.document_id")


@dataclass(frozen=True, slots=True)
class Provenance:
    """Traceability record attached to knowledge elements.

    ``fragment_refs`` identify SourceFragment entries. An empty list is legal
    but explicit: a rule without a source must not silently look validated.
    """

    derivation: DerivationState
    fragment_refs: tuple[str, ...] = ()
    reviewer: str | None = None
    reviewed_at: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        for ref in self.fragment_refs:
            validate_identifier(ref, "Provenance.fragment_refs entry")
        if self.reviewed_at is not None:
            validate_iso_date(self.reviewed_at, "Provenance.reviewed_at")


@dataclass(frozen=True, slots=True)
class ValidationItem:
    """An explicit record of ambiguity, gap, or pending review."""

    id: str
    category: str
    description: str
    severity: str | None = None
    related_ids: tuple[str, ...] = ()
    status: ValidationItemStatus = ValidationItemStatus.OPEN

    def __post_init__(self) -> None:
        validate_identifier(self.id, "ValidationItem.id")
        if not self.category:
            raise ValueError("ValidationItem.category must not be empty")
        if not self.description:
            raise ValueError("ValidationItem.description must not be empty")
        for related in self.related_ids:
            validate_identifier(related, "ValidationItem.related_ids entry")
