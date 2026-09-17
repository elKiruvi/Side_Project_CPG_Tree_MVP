"""Validate the committed D2.5 reconciliation artifacts against the packages."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from cpg_tree.protocols.itu_v06 import build_itu_package
from cpg_tree.protocols.nac_v09 import build_nac_package
from cpg_tree.reconciliation.checks import validate_reconciliation
from cpg_tree.reconciliation.io import dump_reconciliation, load_reconciliation
from cpg_tree.reconciliation.model import (
    EvidenceClass,
    PresentationRole,
    ReconciliationInventory,
    ReconciliationStatus,
    ReviewStatus,
    SourceEvidenceStatus,
)

_PATHWAY_DIR = Path(__file__).resolve().parents[3] / "evaluation" / "pathway"

_ARTIFACTS = (
    ("CT-PL-193-v09-reconciliation.yaml", build_nac_package()),
    ("CT-PL-197-v06-reconciliation.yaml", build_itu_package()),
)


def _load(name: str) -> ReconciliationInventory:
    return load_reconciliation(_PATHWAY_DIR / name)


def test_every_committed_artifact_is_valid_in_strict_mode() -> None:
    for name, package in _ARTIFACTS:
        inventory = _load(name)
        report = validate_reconciliation(inventory, package)
        assert report.is_valid(), (
            f"{name}: {[(f.code, f.path, f.message) for f in report.findings]}"
        )


def test_committed_artifacts_cover_every_inventory_candidate() -> None:
    for name, _package in _ARTIFACTS:
        inventory = _load(name)
        ids = [candidate.candidate_id for candidate in inventory.candidates]
        assert len(ids) == len(set(ids))
        assert ids == sorted(ids)


def test_committed_artifacts_are_byte_deterministic_after_round_trip() -> None:
    for name, _package in _ARTIFACTS:
        path = _PATHWAY_DIR / name
        inventory = _load(name)
        assert dump_reconciliation(inventory) == path.read_text(encoding="utf-8"), (
            f"{name} is not byte-identical to its deterministic dump"
        )


def test_nac_counts() -> None:
    inventory = _load("CT-PL-193-v09-reconciliation.yaml")
    assert inventory.protocol == "CT-PL-193"
    assert inventory.version == "v09"
    assert len(inventory.candidates) == 30
    assert len(inventory.conflicts) == 4
    roles = Counter(c.presentation_role for c in inventory.candidates)
    assert roles == Counter(
        {
            PresentationRole.FLOW: 9,
            PresentationRole.REFERENCE: 4,
            PresentationRole.COMPOSITION: 6,
            PresentationRole.GAP: 3,
            PresentationRole.OMITTED: 6,
            PresentationRole.INTERNAL: 2,
        }
    )
    statuses = Counter(c.reconciliation_status for c in inventory.candidates)
    assert statuses == Counter(
        {
            ReconciliationStatus.READY_FOR_REVIEW: 18,
            ReconciliationStatus.INFERRED_STRUCTURE: 1,
            ReconciliationStatus.REJECTED: 4,
            ReconciliationStatus.OMITTED: 2,
            ReconciliationStatus.GAP: 2,
            ReconciliationStatus.CONFLICT: 2,
            ReconciliationStatus.UNRESOLVED_MAPPING: 1,
        }
    )


def test_itu_counts() -> None:
    inventory = _load("CT-PL-197-v06-reconciliation.yaml")
    assert inventory.protocol == "CT-PL-197"
    assert inventory.version == "v06"
    assert len(inventory.candidates) == 43
    assert len(inventory.conflicts) == 0
    roles = Counter(c.presentation_role for c in inventory.candidates)
    assert roles == Counter(
        {
            PresentationRole.FLOW: 8,
            PresentationRole.REFERENCE: 13,
            PresentationRole.COMPOSITION: 5,
            PresentationRole.GAP: 1,
            PresentationRole.OMITTED: 11,
            PresentationRole.EXCEPTION_CONTEXT: 3,
            PresentationRole.BRANCH_CONTEXT: 2,
        }
    )
    statuses = Counter(c.reconciliation_status for c in inventory.candidates)
    assert statuses == Counter(
        {
            ReconciliationStatus.READY_FOR_REVIEW: 31,
            ReconciliationStatus.REJECTED: 4,
            ReconciliationStatus.OMITTED: 7,
            ReconciliationStatus.GAP: 1,
        }
    )


def test_no_wildcards_anywhere() -> None:
    for name, _package in _ARTIFACTS:
        for candidate in _load(name).candidates:
            assert "*" not in candidate.from_ref
            for ref in candidate.to_refs:
                assert "*" not in ref


def test_no_inferred_or_unresolved_flow() -> None:
    for name, _package in _ARTIFACTS:
        for candidate in _load(name).candidates:
            if candidate.presentation_role is PresentationRole.FLOW:
                assert candidate.evidence_class in {
                    EvidenceClass.SOURCE_STATED,
                    EvidenceClass.EXTRACTED,
                    EvidenceClass.NORMALIZED,
                }


def test_every_candidate_keeps_proposed_review_status() -> None:
    for name, _package in _ARTIFACTS:
        for candidate in _load(name).candidates:
            assert candidate.review_status is ReviewStatus.PROPOSED


def test_conflicts_preserve_both_sides_and_are_open() -> None:
    inventory = _load("CT-PL-193-v09-reconciliation.yaml")
    assert {c.conflict_id for c in inventory.conflicts} == {
        "SC-NAC-001",
        "SC-NAC-002",
        "SC-NAC-003",
        "SC-NAC-004",
    }
    for conflict in inventory.conflicts:
        assert len(conflict.representations) == 2
        assert conflict.status.value == "OPEN"
        assert conflict.resolution.value == "UNRESOLVED"
        verifications = {r.verification for r in conflict.representations}
        assert verifications == {
            SourceEvidenceStatus.VERIFIED_TEXT,
            SourceEvidenceStatus.PENDING_VISUAL_CONFIRMATION,
        }


# ---------------------------------------------------------------------------
# Presentation-semantic safety: what D3 may render as pathway edges
# ---------------------------------------------------------------------------


def _by_id(inventory: ReconciliationInventory) -> dict[str, object]:
    return {c.candidate_id: c for c in inventory.candidates}


def test_nac_flow_set_is_exactly_the_source_supported_edges() -> None:
    by_id = _by_id(_load("CT-PL-193-v09-reconciliation.yaml"))
    flow_ids = {cid for cid, c in by_id.items() if c.presentation_role is PresentationRole.FLOW}
    assert flow_ids == {
        "rel-nac-002",
        "rel-nac-003",
        "rel-nac-005",
        "rel-nac-006",
        "rel-nac-009",
        "rel-nac-010",
        "rel-nac-011",
        "rel-nac-012",
        "rel-nac-013",
    }


def test_itu_flow_set_is_exactly_the_source_supported_edges() -> None:
    by_id = _by_id(_load("CT-PL-197-v06-reconciliation.yaml"))
    flow_ids = {cid for cid, c in by_id.items() if c.presentation_role is PresentationRole.FLOW}
    assert flow_ids == {
        "rel-itu-002",
        "rel-itu-003",
        "rel-itu-004",
        "rel-itu-010",
        "rel-itu-011",
        "rel-itu-017",
        "rel-itu-018",
        "rel-itu-020",
    }


def test_nac_action_relationships_are_internal_not_flow() -> None:
    by_id = _by_id(_load("CT-PL-193-v09-reconciliation.yaml"))
    for candidate_id in ("rel-nac-016", "rel-nac-017"):
        candidate = by_id[candidate_id]
        assert candidate.presentation_role is PresentationRole.INTERNAL
        assert candidate.presentation_role is not PresentationRole.FLOW
        assert candidate.relation == "attaches"
        assert candidate.from_ref == "rule_plan_egreso"


def test_nac_labs_hospitalization_relation_uses_support_semantics() -> None:
    candidate = _by_id(_load("CT-PL-193-v09-reconciliation.yaml"))["rel-nac-005"]
    assert candidate.presentation_role is PresentationRole.FLOW
    assert candidate.relation == "supports"
    assert candidate.branch_label == "apoya la decisión de hospitalización"


def test_itu_amikacin_meropenem_is_not_a_medication_sequence() -> None:
    candidate = _by_id(_load("CT-PL-197-v06-reconciliation.yaml"))["rel-itu-009"]
    assert candidate.presentation_role is PresentationRole.EXCEPTION_CONTEXT
    assert candidate.presentation_role is not PresentationRole.FLOW
    assert candidate.relation == "excepts"


def test_itu_gestante_treatment_is_not_a_medication_chain() -> None:
    by_id = _by_id(_load("CT-PL-197-v06-reconciliation.yaml"))
    for candidate_id in ("rel-itu-023", "rel-itu-024"):
        candidate = by_id[candidate_id]
        assert candidate.presentation_role is PresentationRole.BRANCH_CONTEXT
        assert candidate.presentation_role is not PresentationRole.FLOW
        assert candidate.from_ref.startswith("BRANCH_CONTEXT:")
    assert by_id["rel-itu-023"].to_refs == ("rule_t2_itu_alta_gestante_piperacilina",)
    assert by_id["rel-itu-024"].to_refs == ("rule_t2_itu_alta_gestante_meropenem",)
    assert by_id["rel-itu-023"].from_ref == by_id["rel-itu-024"].from_ref


def test_no_sequential_medication_flow_exists_anywhere() -> None:
    for name, _package in _ARTIFACTS:
        for candidate in _load(name).candidates:
            if candidate.presentation_role is not PresentationRole.FLOW:
                continue
            forbidden_pairs = {
                ("rule_t1_alta_hosp_con_fr_amikacina", "rule_t1_alta_hosp_con_fr_meropenem"),
                ("rule_t2_itu_alta_gestante_cefazolina", "rule_t2_itu_alta_gestante_piperacilina"),
                ("rule_t2_itu_alta_gestante_piperacilina", "rule_t2_itu_alta_gestante_meropenem"),
            }
            for to_ref in candidate.to_refs:
                assert (candidate.from_ref, to_ref) not in forbidden_pairs, (
                    f"{candidate.candidate_id} renders a medication sequence as FLOW"
                )


def test_itu_exceptions_do_not_invent_destinations() -> None:
    by_id = _by_id(_load("CT-PL-197-v06-reconciliation.yaml"))
    for candidate_id in ("rel-itu-012", "rel-itu-013"):
        candidate = by_id[candidate_id]
        assert candidate.presentation_role is PresentationRole.EXCEPTION_CONTEXT
        assert all(ref.startswith("EXCEPTED:") for ref in candidate.to_refs)


def test_terminal_targets_are_presentation_only_not_canonical_rules() -> None:
    package = build_itu_package()
    candidate = _by_id(_load("CT-PL-197-v06-reconciliation.yaml"))["rel-itu-011"]
    assert candidate.presentation_role is PresentationRole.FLOW
    assert candidate.to_refs == ("TERMINAL: diagnóstico descartado",)
    terminal_text = candidate.to_refs[0].split("TERMINAL: ", maxsplit=1)[1]
    assert terminal_text not in package.rules
    assert candidate.to_refs[0] not in package.rules


def test_composition_relationships_are_never_flow() -> None:
    composition_ids = {
        "rel-nac-040",
        "rel-nac-041",
        "rel-nac-042",
        "rel-nac-043",
        "rel-nac-044",
        "rel-nac-045",
        "rel-itu-040",
        "rel-itu-041",
        "rel-itu-042",
        "rel-itu-043",
        "rel-itu-044",
    }
    for name, _package in _ARTIFACTS:
        by_id = _by_id(_load(name))
        for candidate_id in composition_ids:
            candidate = by_id.get(candidate_id)
            if candidate is None:
                continue
            assert candidate.presentation_role is PresentationRole.COMPOSITION
            assert candidate.presentation_role is not PresentationRole.FLOW


def test_conflicts_remain_conflict_and_unresolved() -> None:
    by_id = _by_id(_load("CT-PL-193-v09-reconciliation.yaml"))
    for candidate_id in ("rel-nac-041", "rel-nac-042"):
        candidate = by_id[candidate_id]
        assert candidate.reconciliation_status is ReconciliationStatus.CONFLICT
        assert candidate.presentation_role is not PresentationRole.FLOW
        assert "SC-NAC-003" in candidate.source_conflict_ids


def test_inferred_structure_never_becomes_flow() -> None:
    candidate = _by_id(_load("CT-PL-193-v09-reconciliation.yaml"))["rel-nac-043"]
    assert candidate.presentation_role is not PresentationRole.FLOW
    assert candidate.reconciliation_status is ReconciliationStatus.INFERRED_STRUCTURE
    assert candidate.evidence_class is EvidenceClass.INFERRED


def test_gaps_remain_gaps() -> None:
    nac = _by_id(_load("CT-PL-193-v09-reconciliation.yaml"))
    for candidate_id in ("rel-nac-050", "rel-nac-051", "rel-nac-052"):
        candidate = nac[candidate_id]
        assert candidate.presentation_role is PresentationRole.GAP
        assert candidate.presentation_role is not PresentationRole.FLOW
    itu = _by_id(_load("CT-PL-197-v06-reconciliation.yaml"))
    assert itu["rel-itu-050"].presentation_role is PresentationRole.GAP


def test_reference_relationships_never_become_flow() -> None:
    reference_ids = {
        "rel-nac-014",
        "rel-nac-015",
        "rel-nac-030",
        "rel-nac-031",
        "rel-itu-001",
        "rel-itu-005",
        "rel-itu-006",
        "rel-itu-007",
        "rel-itu-008",
        "rel-itu-021",
        "rel-itu-022",
        "rel-itu-025",
        "rel-itu-026",
        "rel-itu-030",
        "rel-itu-031",
        "rel-itu-032",
        "rel-itu-033",
    }
    for name, _package in _ARTIFACTS:
        by_id = _by_id(_load(name))
        for candidate_id in reference_ids:
            candidate = by_id.get(candidate_id)
            if candidate is None:
                continue
            assert candidate.presentation_role is PresentationRole.REFERENCE
            assert candidate.presentation_role is not PresentationRole.FLOW


def test_changed_candidates_retain_source_evidence() -> None:
    changed_ids = {
        "rel-nac-005",
        "rel-nac-016",
        "rel-nac-017",
        "rel-itu-009",
        "rel-itu-012",
        "rel-itu-013",
        "rel-itu-023",
        "rel-itu-024",
    }
    for name, _package in _ARTIFACTS:
        for candidate in _load(name).candidates:
            if candidate.candidate_id not in changed_ids:
                continue
            assert candidate.evidence_quote.strip()
            assert candidate.fragment_ids
            assert candidate.page
            assert candidate.evidence_class in {
                EvidenceClass.SOURCE_STATED,
                EvidenceClass.EXTRACTED,
                EvidenceClass.NORMALIZED,
            }
            assert candidate.source_evidence_status in {
                SourceEvidenceStatus.VERIFIED_TEXT,
                SourceEvidenceStatus.VERIFIED_TABLE,
            }
            assert candidate.reviewer_notes.strip()
            assert candidate.reconciliation_notes.strip()
