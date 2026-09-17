"""Dataclasses and enums of the reconciliation layer (Phase 10 D2.5)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PresentationRole(StrEnum):
    """Final presentation role of a relationship, after source reconciliation.

    FLOW is restricted to transitions, branches, or sequencing explicitly
    established by the source between two specific rules. INFERRED and
    UNRESOLVED evidence can never carry the FLOW role.

    The remaining roles are presentation-safe: they are retained for
    reconciliation/provenance but never become ordinary Rule-to-Rule pathway
    edges:

    - REFERENCE: contextual/documentary relationship; not workflow.
    - COMPOSITION: internal logical structure (OR/AND/AT_LEAST_N); not sequence.
    - EXCEPTION_CONTEXT: an exception or conditional alternative declared by
      the source; D3 must render it from the canonical Rule exception
      semantics, never as a transition or a medication sequence, and never
      with an invented destination.
    - BRANCH_CONTEXT: condition-based alternatives that share a
      presentation-only branch context; the alternatives are selected by
      their own canonical conditions, never sequentially.
    - INTERNAL: a relationship internal to a canonical Rule (for example its
      declarative actions); never a pathway edge.
    - GAP / OMITTED: unresolved or deliberately excluded relationships.
    """

    FLOW = "FLOW"
    REFERENCE = "REFERENCE"
    COMPOSITION = "COMPOSITION"
    EXCEPTION_CONTEXT = "EXCEPTION_CONTEXT"
    BRANCH_CONTEXT = "BRANCH_CONTEXT"
    INTERNAL = "INTERNAL"
    GAP = "GAP"
    OMITTED = "OMITTED"


class EvidenceClass(StrEnum):
    """How the relationship evidence was derived from the source."""

    SOURCE_STATED = "SOURCE_STATED"
    EXTRACTED = "EXTRACTED"
    NORMALIZED = "NORMALIZED"
    INFERRED = "INFERRED"
    UNRESOLVED = "UNRESOLVED"


class SourceRepresentation(StrEnum):
    """How the supporting evidence is represented in the source document.

    The purpose is to distinguish "not extracted as text" from "not present
    in the source": IMAGE and DIAGRAM evidence exists even when the text
    layer does not capture it.
    """

    TEXT = "TEXT"
    TABLE = "TABLE"
    IMAGE = "IMAGE"
    DIAGRAM = "DIAGRAM"
    PAGE_LAYOUT = "PAGE_LAYOUT"
    MULTI_SOURCE = "MULTI_SOURCE"


class SourceEvidenceStatus(StrEnum):
    """Verification state of the quoted evidence during reconciliation."""

    VERIFIED_TEXT = "VERIFIED_TEXT"
    VERIFIED_TABLE = "VERIFIED_TABLE"
    PAGE_LAYER_ONLY = "PAGE_LAYER_ONLY"
    EXTRACTION_LIMITED = "EXTRACTION_LIMITED"
    SOURCE_CONTENT_ABSENT = "SOURCE_CONTENT_ABSENT"
    PENDING_VISUAL_CONFIRMATION = "PENDING_VISUAL_CONFIRMATION"


class ReviewStatus(StrEnum):
    """Human review state of a candidate. Reconciliation never approves."""

    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    OMITTED = "OMITTED"


class ReconciliationStatus(StrEnum):
    """Outcome of D2.5 source reconciliation for one candidate.

    READY_FOR_REVIEW means the source supports the relationship in its final
    presentation role and a human can approve it in D3. It is never applied
    to INFERRED or UNRESOLVED evidence.
    """

    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    INFERRED_STRUCTURE = "INFERRED_STRUCTURE"
    REJECTED = "REJECTED"
    OMITTED = "OMITTED"
    GAP = "GAP"
    CONFLICT = "CONFLICT"
    UNRESOLVED_MAPPING = "UNRESOLVED_MAPPING"


class ConflictStatus(StrEnum):
    """Lifecycle of a source-conflict record."""

    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


class ConflictResolution(StrEnum):
    """Resolution state of a source conflict.

    A reconciliation record never selects a winner between two source
    representations; UNRESOLVED is the only state this layer produces.
    RESOLVED_BY_HUMAN exists for future reviewer outcomes.
    """

    UNRESOLVED = "UNRESOLVED"
    RESOLVED_BY_HUMAN = "RESOLVED_BY_HUMAN"


FLOW_ALLOWED_EVIDENCE = frozenset(
    {EvidenceClass.SOURCE_STATED, EvidenceClass.EXTRACTED, EvidenceClass.NORMALIZED}
)

_MIN_CONFLICT_REPRESENTATIONS = 2

_TERMINAL_PREFIX = "TERMINAL:"
_EXCEPTED_PREFIX = "EXCEPTED:"
_BRANCH_CONTEXT_PREFIX = "BRANCH_CONTEXT:"
_PSEUDO_REF_PREFIXES = frozenset({_TERMINAL_PREFIX, _EXCEPTED_PREFIX, _BRANCH_CONTEXT_PREFIX})


@dataclass(frozen=True, slots=True)
class ReconciledCandidate:
    """One relationship candidate after source reconciliation.

    ``from_ref`` and ``to_refs`` reference canonical entity ids (rules,
    variables, actions, fragments), pseudo-references (``TERMINAL:<text>`` =
    presentation-only terminal, ``EXCEPTED:<text>`` = exception with no
    declared destination, ``BRANCH_CONTEXT:<text>`` = presentation-only branch
    anchor), or free-text descriptions in parentheses for GAP/OMITTED/
    UNRESOLVED rows. Pseudo-references are presentation-only and are never
    canonical Rule nodes. Wildcard ids (``*``) are never permitted.
    ``review_status`` remains PROPOSED until a human reviews the inventory.
    """

    candidate_id: str
    from_ref: str
    to_refs: tuple[str, ...]
    relation: str
    presentation_role: PresentationRole
    branch_label: str | None
    evidence_quote: str
    fragment_ids: tuple[str, ...]
    page: str
    evidence_class: EvidenceClass
    review_status: ReviewStatus
    reconciliation_status: ReconciliationStatus
    source_representation: SourceRepresentation
    source_location: str | None
    source_conflict_ids: tuple[str, ...]
    source_evidence_status: SourceEvidenceStatus
    reviewer_notes: str
    reconciliation_notes: str

    def __post_init__(self) -> None:
        if not self.candidate_id or not self.candidate_id.strip():
            raise ValueError("ReconciledCandidate.candidate_id must not be empty")
        if "*" in self.from_ref or any("*" in ref for ref in self.to_refs):
            raise ValueError(f"candidate {self.candidate_id!r} must not use wildcard references")
        if not self.page or not self.page.strip():
            raise ValueError(f"candidate {self.candidate_id!r} requires a non-empty page")


@dataclass(frozen=True, slots=True)
class ConflictRepresentation:
    """One side of a source conflict, with its verification state."""

    representation: SourceRepresentation
    page: int | None
    statement: str
    verification: SourceEvidenceStatus

    def __post_init__(self) -> None:
        if not self.statement or not self.statement.strip():
            raise ValueError("ConflictRepresentation.statement must not be empty")


@dataclass(frozen=True, slots=True)
class SourceConflict:
    """An explicit disagreement between two source representations.

    A conflict record never selects a winner. Both representations are
    preserved verbatim with their pages and verification states.
    """

    conflict_id: str
    topic: str
    status: ConflictStatus
    resolution: ConflictResolution
    representations: tuple[ConflictRepresentation, ...]
    notes: str

    def __post_init__(self) -> None:
        if not self.conflict_id or not self.conflict_id.strip():
            raise ValueError("SourceConflict.conflict_id must not be empty")
        if not self.topic or not self.topic.strip():
            raise ValueError(f"conflict {self.conflict_id!r} requires a non-empty topic")
        if len(self.representations) < _MIN_CONFLICT_REPRESENTATIONS:
            raise ValueError(
                f"conflict {self.conflict_id!r} requires at least "
                f"{_MIN_CONFLICT_REPRESENTATIONS} source representations"
            )
        if not self.notes or not self.notes.strip():
            raise ValueError(f"conflict {self.conflict_id!r} requires non-empty notes")


@dataclass(frozen=True, slots=True)
class ReconciliationInventory:
    """The reconciliation record of one protocol version."""

    protocol: str
    version: str
    candidates: tuple[ReconciledCandidate, ...]
    conflicts: tuple[SourceConflict, ...]

    def __post_init__(self) -> None:
        if not self.protocol or not self.protocol.strip():
            raise ValueError("ReconciliationInventory.protocol must not be empty")
        if not self.version or not self.version.strip():
            raise ValueError("ReconciliationInventory.version must not be empty")
