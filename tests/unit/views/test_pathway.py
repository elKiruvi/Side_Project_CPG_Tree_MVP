"""Presentation graph builder tests: D2.5 contract consumption (Phase 10 D3)."""

from __future__ import annotations

import pytest

from cpg_tree.knowledge.protocol import ProtocolVersion
from cpg_tree.reconciliation.model import (
    ConflictRepresentation,
    ConflictResolution,
    ConflictStatus,
    EvidenceClass,
    PresentationRole,
    ReconciliationInventory,
    ReconciliationStatus,
    ReconciledCandidate,
    ReviewStatus,
    SourceConflict,
    SourceEvidenceStatus,
    SourceRepresentation,
)
from cpg_tree.views.pathway import (
    PathwayEdgeKind,
    PathwayGraph,
    PathwayNodeKind,
    build_pathway_graph,
)


def _candidate(
    candidate_id: str,
    role: PresentationRole,
    from_ref: str,
    to_refs: tuple[str, ...] | str,
    status: ReconciliationStatus = ReconciliationStatus.READY_FOR_REVIEW,
    evidence_class: EvidenceClass = EvidenceClass.SOURCE_STATED,
    relation: str = "branches",
    branch_label: str | None = None,
    source_conflict_ids: tuple[str, ...] = (),
    fragment_ids: tuple[str, ...] = ("frag_1",),
) -> ReconciledCandidate:
    if isinstance(to_refs, str):
        to_refs = (to_refs,)
    return ReconciledCandidate(
        candidate_id=candidate_id,
        from_ref=from_ref,
        to_refs=to_refs,
        relation=relation,
        presentation_role=role,
        branch_label=branch_label,
        evidence_quote="quote",
        fragment_ids=fragment_ids,
        page="3",
        evidence_class=evidence_class,
        review_status=ReviewStatus.PROPOSED,
        reconciliation_status=status,
        source_representation=SourceRepresentation.TEXT,
        source_location=None,
        source_conflict_ids=source_conflict_ids,
        source_evidence_status=SourceEvidenceStatus.VERIFIED_TEXT,
        reviewer_notes="notes",
        reconciliation_notes="notes",
    )


def _conflict() -> SourceConflict:
    return SourceConflict(
        conflict_id="SC-TEST-001",
        topic="umbral en conflicto",
        status=ConflictStatus.OPEN,
        resolution=ConflictResolution.UNRESOLVED,
        representations=(
            ConflictRepresentation(
                SourceRepresentation.TEXT, 4, "x >= 2", SourceEvidenceStatus.VERIFIED_TEXT
            ),
            ConflictRepresentation(
                SourceRepresentation.DIAGRAM,
                6,
                "x > 2",
                SourceEvidenceStatus.PENDING_VISUAL_CONFIRMATION,
            ),
        ),
        notes="sin ganador",
    )


def _inventory(
    candidates: tuple[ReconciledCandidate, ...],
    conflicts: tuple[SourceConflict, ...] = (),
) -> ReconciliationInventory:
    return ReconciliationInventory(
        protocol="TEST-PL-999",
        version="v01",
        candidates=candidates,
        conflicts=conflicts,
    )


def _graph(
    synthetic_package: ProtocolVersion,
    candidates: tuple[ReconciledCandidate, ...],
    conflicts: tuple[SourceConflict, ...] = (),
) -> PathwayGraph:
    return build_pathway_graph(synthetic_package, _inventory(candidates, conflicts))


def test_every_canonical_rule_appears_exactly_once(
    synthetic_package: ProtocolVersion,
) -> None:
    graph = _graph(synthetic_package, ())
    assert set(graph.rule_nodes) == set(synthetic_package.rules)
    assert len(graph.rule_nodes) == len(synthetic_package.rules)


def test_flow_candidate_creates_rule_to_rule_edge(
    synthetic_package: ProtocolVersion,
) -> None:
    graph = _graph(
        synthetic_package,
        (
            _candidate(
                "rel-t-001",
                PresentationRole.FLOW,
                "rule_composite",
                "rule_alternatives",
            ),
        ),
    )
    assert len(graph.edges) == 1
    edge = graph.edges[0]
    assert edge.kind is PathwayEdgeKind.FLOW
    assert (edge.source, edge.target) == ("rule_composite", "rule_alternatives")
    assert edge.candidate_id == "rel-t-001"


def test_flow_to_typed_terminal_creates_presentation_terminal(
    synthetic_package: ProtocolVersion,
) -> None:
    graph = _graph(
        synthetic_package,
        (
            _candidate(
                "rel-t-002",
                PresentationRole.FLOW,
                "rule_alternatives",
                "TERMINAL: fin de la vía",
                branch_label="NO",
            ),
        ),
    )
    assert set(graph.terminals) == {"TERMINAL: fin de la vía"}
    assert graph.terminals["TERMINAL: fin de la vía"].label == "fin de la vía"
    assert "TERMINAL: fin de la vía" not in graph.rule_nodes
    assert graph.edges[0].target == "TERMINAL: fin de la vía"


def test_branch_context_is_presentation_only(
    synthetic_package: ProtocolVersion,
) -> None:
    graph = _graph(
        synthetic_package,
        (
            _candidate(
                "rel-t-003",
                PresentationRole.BRANCH_CONTEXT,
                "BRANCH_CONTEXT: contexto sintético",
                "rule_composite",
                branch_label="rama A",
            ),
        ),
    )
    assert set(graph.branch_contexts) == {"BRANCH_CONTEXT: contexto sintético"}
    assert graph.branch_contexts["BRANCH_CONTEXT: contexto sintético"].label == "contexto sintético"
    assert "BRANCH_CONTEXT: contexto sintético" not in graph.rule_nodes
    edge = graph.edges[0]
    assert edge.kind is PathwayEdgeKind.BRANCH
    assert edge.branch_label == "rama A"


def test_two_branch_candidates_share_one_context_node(
    synthetic_package: ProtocolVersion,
) -> None:
    graph = _graph(
        synthetic_package,
        (
            _candidate(
                "rel-t-004a",
                PresentationRole.BRANCH_CONTEXT,
                "BRANCH_CONTEXT: contexto compartido",
                "rule_composite",
                branch_label="rama A",
            ),
            _candidate(
                "rel-t-004b",
                PresentationRole.BRANCH_CONTEXT,
                "BRANCH_CONTEXT: contexto compartido",
                "rule_alternatives",
                branch_label="rama B",
            ),
        ),
    )
    assert len(graph.branch_contexts) == 1
    assert len(graph.edges) == 2


def test_reference_creates_no_topology(
    synthetic_package: ProtocolVersion,
) -> None:
    graph = _graph(
        synthetic_package,
        (
            _candidate(
                "rel-t-005",
                PresentationRole.REFERENCE,
                "rule_composite",
                "rule_alternatives",
            ),
        ),
    )
    assert graph.edges == ()
    assert graph.branch_contexts == {}
    assert graph.terminals == {}


def test_composition_creates_no_topology(
    synthetic_package: ProtocolVersion,
) -> None:
    graph = _graph(
        synthetic_package,
        (
            _candidate(
                "rel-t-006",
                PresentationRole.COMPOSITION,
                "rule_composite",
                "rule_alternatives",
            ),
        ),
    )
    assert graph.edges == ()


def test_internal_action_relationship_creates_no_topology(
    synthetic_package: ProtocolVersion,
) -> None:
    graph = _graph(
        synthetic_package,
        (
            _candidate(
                "rel-t-007",
                PresentationRole.INTERNAL,
                "rule_composite",
                "act_request",
                relation="attaches",
            ),
        ),
    )
    assert graph.edges == ()


def test_exception_context_creates_no_topology(
    synthetic_package: ProtocolVersion,
) -> None:
    graph = _graph(
        synthetic_package,
        (
            _candidate(
                "rel-t-008",
                PresentationRole.EXCEPTION_CONTEXT,
                "rule_composite",
                "EXCEPTED: destino no declarado en la fuente",
                relation="excepts",
                branch_label="excepción",
            ),
        ),
    )
    assert graph.edges == ()
    assert graph.terminals == {}


def test_gap_creates_no_topology_but_badges_involved_rule(
    synthetic_package: ProtocolVersion,
) -> None:
    graph = _graph(
        synthetic_package,
        (
            _candidate(
                "rel-t-009",
                PresentationRole.GAP,
                "rule_composite",
                ("(contenido ausente)",),
                status=ReconciliationStatus.GAP,
                evidence_class=EvidenceClass.UNRESOLVED,
                relation="missing",
            ),
        ),
    )
    assert graph.edges == ()
    assert any("GAP" in badge for badge in graph.badges.get("rule_composite", ()))
    assert any(notice.kind.value == "GAP" for notice in graph.notices)


def test_conflict_creates_no_topology_but_badges_involved_rules(
    synthetic_package: ProtocolVersion,
) -> None:
    graph = _graph(
        synthetic_package,
        (
            _candidate(
                "rel-t-010",
                PresentationRole.COMPOSITION,
                "rule_composite",
                "rule_alternatives",
                status=ReconciliationStatus.CONFLICT,
                source_conflict_ids=("SC-TEST-001",),
            ),
        ),
        conflicts=(_conflict(),),
    )
    assert graph.edges == ()
    assert "conflicto de fuente sin resolver" in graph.badges["rule_composite"]
    assert "conflicto de fuente sin resolver" in graph.badges["rule_alternatives"]


def test_inferred_structure_creates_no_topology_but_badges(
    synthetic_package: ProtocolVersion,
) -> None:
    graph = _graph(
        synthetic_package,
        (
            _candidate(
                "rel-t-011",
                PresentationRole.COMPOSITION,
                "rule_composite",
                "rule_alternatives",
                status=ReconciliationStatus.INFERRED_STRUCTURE,
                evidence_class=EvidenceClass.INFERRED,
            ),
        ),
    )
    assert graph.edges == ()
    assert "estructura inferida — no validada" in graph.badges["rule_composite"]


def test_conflict_notices_are_listed(
    synthetic_package: ProtocolVersion,
) -> None:
    inventory = ReconciliationInventory(
        protocol="TEST-PL-999",
        version="v01",
        candidates=(),
        conflicts=(_conflict(),),
    )
    graph = build_pathway_graph(synthetic_package, inventory)
    assert any(notice.kind.value == "SOURCE_CONFLICT" for notice in graph.notices)


def test_invalid_reconciliation_fails_clearly(
    synthetic_package: ProtocolVersion,
) -> None:
    candidates = (
        _candidate(
            "rel-t-012",
            PresentationRole.FLOW,
            "rule_composite",
            "rule_alternatives",
            evidence_class=EvidenceClass.INFERRED,
            status=ReconciliationStatus.INFERRED_STRUCTURE,
        ),
    )
    with pytest.raises(ValueError, match="reconciliation validation failed"):
        _graph(synthetic_package, candidates)


def test_flow_to_unknown_rule_fails_clearly(
    synthetic_package: ProtocolVersion,
) -> None:
    with pytest.raises(ValueError, match="reconciliation validation failed"):
        _graph(
            synthetic_package,
            (
                _candidate(
                    "rel-t-013",
                    PresentationRole.FLOW,
                    "rule_composite",
                    "rule_no_existe",
                ),
            ),
        )


def test_self_loop_edge_fails_clearly(
    synthetic_package: ProtocolVersion,
) -> None:
    with pytest.raises(ValueError, match="self-loop"):
        _graph(
            synthetic_package,
            (
                _candidate(
                    "rel-t-014",
                    PresentationRole.FLOW,
                    "rule_composite",
                    "rule_composite",
                ),
            ),
        )


def test_duplicate_edge_fails_clearly(
    synthetic_package: ProtocolVersion,
) -> None:
    with pytest.raises(ValueError, match="duplicate"):
        _graph(
            synthetic_package,
            (
                _candidate(
                    "rel-t-015a",
                    PresentationRole.FLOW,
                    "rule_composite",
                    "rule_alternatives",
                ),
                _candidate(
                    "rel-t-015b",
                    PresentationRole.FLOW,
                    "rule_composite",
                    "rule_alternatives",
                ),
            ),
        )


def test_cyclic_reconciliation_builds_without_crash(
    synthetic_package: ProtocolVersion,
) -> None:
    graph = _graph(
        synthetic_package,
        (
            _candidate(
                "rel-t-016a",
                PresentationRole.FLOW,
                "rule_composite",
                "rule_alternatives",
            ),
            _candidate(
                "rel-t-016b",
                PresentationRole.FLOW,
                "rule_alternatives",
                "rule_composite",
            ),
        ),
    )
    assert len(graph.edges) == 2


def test_disconnected_rule_still_appears(
    synthetic_package: ProtocolVersion,
) -> None:
    graph = _graph(
        synthetic_package,
        (
            _candidate(
                "rel-t-017",
                PresentationRole.FLOW,
                "rule_composite",
                "rule_alternatives",
            ),
        ),
    )
    assert set(graph.rule_nodes) == {"rule_composite", "rule_alternatives"}


def test_graph_is_immutable_and_deterministic(
    synthetic_package: ProtocolVersion,
) -> None:
    candidates = (
        _candidate(
            "rel-t-018",
            PresentationRole.FLOW,
            "rule_composite",
            "rule_alternatives",
        ),
    )
    first = _graph(synthetic_package, candidates)
    second = _graph(synthetic_package, candidates)
    assert first == second


def test_node_kinds_are_presentation_typed() -> None:
    assert PathwayNodeKind.RULE.value == "RULE"
    assert PathwayNodeKind.BRANCH_CONTEXT.value == "BRANCH_CONTEXT"
    assert PathwayNodeKind.TERMINAL.value == "TERMINAL"
