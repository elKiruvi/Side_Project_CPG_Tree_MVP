"""Model invariants for the reconciliation layer."""

from __future__ import annotations

import pytest

from cpg_tree.reconciliation.model import (
    ConflictRepresentation,
    ConflictResolution,
    ConflictStatus,
    EvidenceClass,
    PresentationRole,
    ReconciledCandidate,
    ReconciliationInventory,
    ReconciliationStatus,
    ReviewStatus,
    SourceConflict,
    SourceEvidenceStatus,
    SourceRepresentation,
)


def _candidate(**overrides: object) -> ReconciledCandidate:
    fields: dict[str, object] = {
        "candidate_id": "rel-test-001",
        "from_ref": "rule_a",
        "to_refs": ("rule_b",),
        "relation": "branches",
        "presentation_role": PresentationRole.FLOW,
        "branch_label": None,
        "evidence_quote": "source quote",
        "fragment_ids": ("frag_x",),
        "page": "1",
        "evidence_class": EvidenceClass.SOURCE_STATED,
        "review_status": ReviewStatus.PROPOSED,
        "reconciliation_status": ReconciliationStatus.READY_FOR_REVIEW,
        "source_representation": SourceRepresentation.TEXT,
        "source_location": None,
        "source_conflict_ids": (),
        "source_evidence_status": SourceEvidenceStatus.VERIFIED_TEXT,
        "reviewer_notes": "notes",
        "reconciliation_notes": "notes",
    }
    fields.update(overrides)
    return ReconciledCandidate(**fields)  # type: ignore[arg-type]


def _conflict() -> SourceConflict:
    return SourceConflict(
        conflict_id="SC-TEST-001",
        topic="threshold disagreement",
        status=ConflictStatus.OPEN,
        resolution=ConflictResolution.UNRESOLVED,
        representations=(
            ConflictRepresentation(
                SourceRepresentation.TEXT, 4, "value >= 2", SourceEvidenceStatus.VERIFIED_TEXT
            ),
            ConflictRepresentation(
                SourceRepresentation.DIAGRAM,
                6,
                "value > 2",
                SourceEvidenceStatus.PENDING_VISUAL_CONFIRMATION,
            ),
        ),
        notes="never select a winner",
    )


def test_candidate_requires_non_empty_candidate_id() -> None:
    with pytest.raises(ValueError, match="candidate_id"):
        _candidate(candidate_id="  ")


def test_candidate_requires_page() -> None:
    with pytest.raises(ValueError, match="page"):
        _candidate(page=" ")


def test_candidate_rejects_wildcard_in_from() -> None:
    with pytest.raises(ValueError, match="wildcard"):
        _candidate(from_ref="rule_*")


def test_candidate_rejects_wildcard_in_to() -> None:
    with pytest.raises(ValueError, match="wildcard"):
        _candidate(to_refs=("rule_*",))


def test_conflict_requires_two_representations() -> None:
    with pytest.raises(ValueError, match="at least 2 source representations"):
        SourceConflict(
            conflict_id="SC-X",
            topic="topic",
            status=ConflictStatus.OPEN,
            resolution=ConflictResolution.UNRESOLVED,
            representations=(),
            notes="notes",
        )


def test_conflict_requires_notes() -> None:
    with pytest.raises(ValueError, match="notes"):
        SourceConflict(
            conflict_id="SC-X",
            topic="topic",
            status=ConflictStatus.OPEN,
            resolution=ConflictResolution.UNRESOLVED,
            representations=_conflict().representations,
            notes="  ",
        )


def test_inventory_requires_protocol_and_version() -> None:
    with pytest.raises(ValueError, match="protocol"):
        ReconciliationInventory(
            protocol=" ",
            version="v01",
            candidates=(),
            conflicts=(),
        )


def test_conflict_preserves_both_statements_verbatim() -> None:
    conflict = _conflict()
    statements = [representation.statement for representation in conflict.representations]
    assert statements == ["value >= 2", "value > 2"]
    assert conflict.resolution is ConflictResolution.UNRESOLVED
