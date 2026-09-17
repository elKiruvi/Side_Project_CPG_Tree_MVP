"""Deterministic I/O for the reconciliation layer."""

from __future__ import annotations

from pathlib import Path

import pytest

from cpg_tree.reconciliation.io import (
    dump_reconciliation,
    load_reconciliation,
    write_reconciliation,
)
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

_VALID_DOCUMENT = """\
schema: relationship-reconciliation
schema_version: 2
protocol: TEST-PL-999
version: v01
candidates:
- candidate_id: rel-test-001
  from: rule_a
  to: rule_b
  relation: branches
  presentation_role: FLOW
  branch_label: null
  evidence_quote: quote
  fragment_ids:
  - frag_x
  page: '1'
  evidence_class: SOURCE_STATED
  review_status: PROPOSED
  reconciliation_status: READY_FOR_REVIEW
  source_representation: TEXT
  source_location: null
  source_conflict_ids: []
  source_evidence_status: VERIFIED_TEXT
  reviewer_notes: notes
  reconciliation_notes: notes
conflicts:
- conflict_id: SC-TEST-001
  topic: threshold disagreement
  status: OPEN
  resolution: UNRESOLVED
  representations:
  - representation: TEXT
    page: 4
    statement: value >= 2
    verification: VERIFIED_TEXT
  - representation: DIAGRAM
    page: 6
    statement: value > 2
    verification: PENDING_VISUAL_CONFIRMATION
  notes: never select a winner
"""


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "reconciliation.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def _sample_inventory() -> ReconciliationInventory:
    return ReconciliationInventory(
        protocol="TEST-PL-999",
        version="v01",
        candidates=(
            ReconciledCandidate(
                candidate_id="rel-test-001",
                from_ref="rule_a",
                to_refs=("rule_b",),
                relation="branches",
                presentation_role=PresentationRole.FLOW,
                branch_label=None,
                evidence_quote="quote",
                fragment_ids=("frag_x",),
                page="1",
                evidence_class=EvidenceClass.SOURCE_STATED,
                review_status=ReviewStatus.PROPOSED,
                reconciliation_status=ReconciliationStatus.READY_FOR_REVIEW,
                source_representation=SourceRepresentation.TEXT,
                source_location=None,
                source_conflict_ids=(),
                source_evidence_status=SourceEvidenceStatus.VERIFIED_TEXT,
                reviewer_notes="notes",
                reconciliation_notes="notes",
            ),
        ),
        conflicts=(
            SourceConflict(
                conflict_id="SC-TEST-001",
                topic="threshold disagreement",
                status=ConflictStatus.OPEN,
                resolution=ConflictResolution.UNRESOLVED,
                representations=(
                    ConflictRepresentation(
                        SourceRepresentation.TEXT,
                        4,
                        "value >= 2",
                        SourceEvidenceStatus.VERIFIED_TEXT,
                    ),
                    ConflictRepresentation(
                        SourceRepresentation.DIAGRAM,
                        6,
                        "value > 2",
                        SourceEvidenceStatus.PENDING_VISUAL_CONFIRMATION,
                    ),
                ),
                notes="never select a winner",
            ),
        ),
    )


def test_load_valid_document(tmp_path: Path) -> None:
    inventory = load_reconciliation(_write(tmp_path, _VALID_DOCUMENT))
    assert inventory.protocol == "TEST-PL-999"
    assert inventory.version == "v01"
    assert len(inventory.candidates) == 1
    assert len(inventory.conflicts) == 1


def test_load_rejects_unknown_top_level_key(tmp_path: Path) -> None:
    document = _VALID_DOCUMENT.replace(
        "protocol: TEST-PL-999",
        "protocol: TEST-PL-999\nsurprise_key: 1",
    )
    with pytest.raises(ValueError, match="unknown keys"):
        load_reconciliation(_write(tmp_path, document))


def test_load_rejects_wrong_schema(tmp_path: Path) -> None:
    document = _VALID_DOCUMENT.replace(
        "schema: relationship-reconciliation",
        "schema: something-else",
    )
    with pytest.raises(ValueError, match="schema"):
        load_reconciliation(_write(tmp_path, document))


def test_load_rejects_invalid_presentation_role(tmp_path: Path) -> None:
    document = _VALID_DOCUMENT.replace(
        "presentation_role: FLOW",
        "presentation_role: SEQUENCE",
    )
    with pytest.raises(ValueError, match="presentation_role"):
        load_reconciliation(_write(tmp_path, document))


def test_load_rejects_invalid_evidence_class(tmp_path: Path) -> None:
    document = _VALID_DOCUMENT.replace(
        "evidence_class: SOURCE_STATED",
        "evidence_class: GUESSED",
    )
    with pytest.raises(ValueError, match="evidence_class"):
        load_reconciliation(_write(tmp_path, document))


def test_load_rejects_invalid_source_representation(tmp_path: Path) -> None:
    document = _VALID_DOCUMENT.replace(
        "representation: TEXT\n    page: 4",
        "representation: FLOWCHART\n    page: 4",
    )
    with pytest.raises(ValueError, match="representation"):
        load_reconciliation(_write(tmp_path, document))


def test_load_rejects_unknown_candidate_key(tmp_path: Path) -> None:
    document = _VALID_DOCUMENT.replace(
        "  relation: branches",
        "  relation: branches\n  invented_field: x",
    )
    with pytest.raises(ValueError, match="unknown keys"):
        load_reconciliation(_write(tmp_path, document))


def test_load_normalizes_single_to_tuple(tmp_path: Path) -> None:
    inventory = load_reconciliation(_write(tmp_path, _VALID_DOCUMENT))
    assert inventory.candidates[0].to_refs == ("rule_b",)


def test_load_accepts_to_list(tmp_path: Path) -> None:
    document = _VALID_DOCUMENT.replace(
        "  to: rule_b",
        "  to:\n  - rule_b\n  - rule_c",
    )
    path = tmp_path / "recon_to_list.yaml"
    path.write_text(document, encoding="utf-8")
    inventory = load_reconciliation(path)
    assert inventory.candidates[0].to_refs == ("rule_b", "rule_c")


def test_dump_is_deterministic_and_round_trips(tmp_path: Path) -> None:
    inventory = _sample_inventory()
    first = dump_reconciliation(inventory)
    second = dump_reconciliation(inventory)
    assert first == second
    path = tmp_path / "roundtrip.yaml"
    write_reconciliation(inventory, path)
    assert load_reconciliation(path) == inventory


def test_dump_never_emits_python_tags(tmp_path: Path) -> None:
    text = dump_reconciliation(_sample_inventory())
    assert "!!python" not in text
