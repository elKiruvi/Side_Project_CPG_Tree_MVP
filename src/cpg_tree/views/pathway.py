"""Clinical pathway presentation graph (Phase 10 D3).

This module builds the pathway presentation graph exclusively from the D2.5
reconciliation contract. It never rediscovers relationships, never infers
clinical workflow, never evaluates conditions, and never mutates the
canonical package.

Graph invariants (enforced at build time; ``ValueError`` on violation):

- Every canonical Rule of the package appears exactly once as a RULE node.
- Only reconciliation candidates with ``presentation_role = FLOW`` create
  pathway edges, and every FLOW edge must have a canonical Rule source and a
  canonical Rule destination — or, exclusively, a typed presentation
  ``TERMINAL:`` destination.
- ``BRANCH_CONTEXT`` candidates create presentation-only context nodes
  (never canonical Rules) with branch edges to canonical Rules.
- INTERNAL, EXCEPTION_CONTEXT, REFERENCE, COMPOSITION, GAP, OMITTED,
  CONFLICT, and INFERRED_STRUCTURE candidates never create pathway topology;
  conflicts/gaps/inferred structures surface as node badges and notices.
- No self-edges; no duplicate edges.

The module is protocol-agnostic: it contains no protocol-specific ids and
imports neither the engine nor protocol builders.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from cpg_tree.knowledge.enums import DerivationState, ValidationStatus
from cpg_tree.knowledge.protocol import ProtocolVersion
from cpg_tree.reconciliation.checks import validate_reconciliation
from cpg_tree.reconciliation.model import (
    PresentationRole,
    ReconciliationInventory,
    ReconciliationStatus,
    ReconciledCandidate,
)
from cpg_tree.views.manifest import VisualizationManifest, group_rules

_TERMINAL_PREFIX = "TERMINAL:"
_BRANCH_CONTEXT_PREFIX = "BRANCH_CONTEXT:"
_EXCEPTED_PREFIX = "EXCEPTED:"

_QUOTE_BUDGET = 110
_NOTES_BUDGET = 120

_BADGE_DERIVATION_UNRESOLVED = "derivación UNRESOLVED — no es conocimiento validado"
_BADGE_DERIVATION_INFERRED = "derivación INFERRED — no tratar como conocimiento validado"
_BADGE_VALIDATION_UNRESOLVED = "estado de validación UNRESOLVED"
_BADGE_SOURCE_CONFLICT = "conflicto de fuente sin resolver"
_BADGE_INFERRED_STRUCTURE = "estructura inferida — no validada"
_BADGE_GAP = "evidencia insuficiente (GAP de fuente)"


class PathwayNodeKind(StrEnum):
    """Presentation node types of the pathway graph."""

    RULE = "RULE"
    BRANCH_CONTEXT = "BRANCH_CONTEXT"
    TERMINAL = "TERMINAL"


class PathwayEdgeKind(StrEnum):
    """Edge kinds: reconciled FLOW vs presentation-only branch."""

    FLOW = "FLOW"
    BRANCH = "BRANCH"


@dataclass(frozen=True, slots=True)
class RuleNode:
    """One canonical Rule presented in the pathway (exactly once)."""

    rule_id: str
    section_title: str


@dataclass(frozen=True, slots=True)
class BranchContextNode:
    """Presentation-only branch anchor; NOT a canonical Rule."""

    context_id: str
    label: str


@dataclass(frozen=True, slots=True)
class TerminalNode:
    """Presentation-only terminal; NOT a canonical Rule."""

    terminal_id: str
    label: str


@dataclass(frozen=True, slots=True)
class PathwayEdge:
    """One presentation edge with its D2.5 provenance."""

    source: str
    target: str
    kind: PathwayEdgeKind
    branch_label: str | None
    candidate_id: str
    fragment_ids: tuple[str, ...]


class PathwayNoticeKind(StrEnum):
    """Kinds of reconciliation notices shown next to the pathway."""

    SOURCE_CONFLICT = "SOURCE_CONFLICT"
    GAP = "GAP"
    UNRESOLVED_MAPPING = "UNRESOLVED_MAPPING"


@dataclass(frozen=True, slots=True)
class PathwayNotice:
    """One deterministic, non-topological reconciliation notice."""

    kind: PathwayNoticeKind
    text: str


@dataclass(frozen=True, slots=True)
class PathwayGraph:
    """The validated pathway presentation graph for one package version."""

    protocol_id: str
    version: str
    rule_nodes: Mapping[str, RuleNode]
    branch_contexts: Mapping[str, BranchContextNode]
    terminals: Mapping[str, TerminalNode]
    edges: tuple[PathwayEdge, ...]
    badges: Mapping[str, tuple[str, ...]]
    notices: tuple[PathwayNotice, ...]


def build_pathway_graph(
    package: ProtocolVersion,
    reconciliation: ReconciliationInventory,
    manifest: VisualizationManifest | None = None,
) -> PathwayGraph:
    """Build and validate the pathway presentation graph.

    The reconciliation artifact is validated first (strict mode against the
    package); invalid reconciliation raises ``ValueError`` with the finding
    codes — the presentation must never silently reinterpret the D2.5
    contract.
    """
    report = validate_reconciliation(reconciliation, package)
    if not report.is_valid():
        codes = sorted(
            {finding.code for finding in report.findings if finding.severity.value == "ERROR"}
        )
        raise ValueError(
            f"reconciliation validation failed for {reconciliation.protocol} "
            f"{reconciliation.version} [{', '.join(codes)}]; refusing to render the pathway"
        )

    grouped = group_rules(package, manifest)
    rule_nodes: dict[str, RuleNode] = {}
    for section_title, rule_ids in grouped:
        for rule_id in rule_ids:
            rule_nodes[rule_id] = RuleNode(rule_id=rule_id, section_title=section_title)
    if len(rule_nodes) != len(package.rules):
        raise ValueError(
            f"pathway rule-node invariant violated: {len(rule_nodes)} nodes for "
            f"{len(package.rules)} canonical rules"
        )

    badges: dict[str, list[str]] = defaultdict(list)
    for rule_id, rule in package.rules.items():
        if rule.provenance.derivation is DerivationState.UNRESOLVED:
            badges[rule_id].append(_BADGE_DERIVATION_UNRESOLVED)
        elif rule.provenance.derivation is DerivationState.INFERRED:
            badges[rule_id].append(_BADGE_DERIVATION_INFERRED)
        if rule.validation_status is ValidationStatus.UNRESOLVED:
            badges[rule_id].append(_BADGE_VALIDATION_UNRESOLVED)

    branch_contexts: dict[str, BranchContextNode] = {}
    terminals: dict[str, TerminalNode] = {}
    edges: list[PathwayEdge] = []
    notices: list[PathwayNotice] = []

    for candidate in reconciliation.candidates:
        _dispatch_candidate(
            candidate,
            package,
            branch_contexts,
            terminals,
            edges,
            badges,
            notices,
        )

    for conflict in reconciliation.conflicts:
        notices.append(
            PathwayNotice(
                kind=PathwayNoticeKind.SOURCE_CONFLICT,
                text=(
                    f"{conflict.conflict_id}: {conflict.topic} — estado {conflict.status.value}, "
                    f"resolución {conflict.resolution.value}; la presentación no elige un ganador"
                ),
            )
        )

    _validate_topology(edges, rule_nodes, branch_contexts, terminals)

    return PathwayGraph(
        protocol_id=package.protocol.id,
        version=package.version,
        rule_nodes=rule_nodes,
        branch_contexts=branch_contexts,
        terminals=terminals,
        edges=tuple(edges),
        badges={rule_id: tuple(sorted(set(texts))) for rule_id, texts in sorted(badges.items())},
        notices=tuple(notices),
    )


def _dispatch_candidate(
    candidate: ReconciledCandidate,
    package: ProtocolVersion,
    branch_contexts: dict[str, BranchContextNode],
    terminals: dict[str, TerminalNode],
    edges: list[PathwayEdge],
    badges: dict[str, list[str]],
    notices: list[PathwayNotice],
) -> None:
    role = candidate.presentation_role
    if role is PresentationRole.FLOW:
        _add_flow_edges(candidate, package, terminals, edges)
    elif role is PresentationRole.BRANCH_CONTEXT:
        _add_branch_edges(candidate, package, branch_contexts, edges)
    # INTERNAL, EXCEPTION_CONTEXT, REFERENCE, COMPOSITION: never topology.
    _record_badges(candidate, badges, notices)


def _add_flow_edges(
    candidate: ReconciledCandidate,
    package: ProtocolVersion,
    terminals: dict[str, TerminalNode],
    edges: list[PathwayEdge],
) -> None:
    source = candidate.from_ref
    if source.startswith(_TERMINAL_PREFIX) or source.startswith(_BRANCH_CONTEXT_PREFIX):
        raise ValueError(
            f"candidate {candidate.candidate_id}: FLOW source must be a canonical rule; "
            f"got {source!r}"
        )
    if source not in package.rules:
        raise ValueError(
            f"candidate {candidate.candidate_id}: FLOW source {source!r} is not a "
            "canonical rule of the package"
        )
    for target in candidate.to_refs:
        if target.startswith(_BRANCH_CONTEXT_PREFIX) or target.startswith(_EXCEPTED_PREFIX):
            raise ValueError(
                f"candidate {candidate.candidate_id}: FLOW target {target!r} is not "
                "a canonical rule or a presentation terminal"
            )
        if target.startswith(_TERMINAL_PREFIX):
            label = target[len(_TERMINAL_PREFIX) :].strip()
            if not label:
                raise ValueError(f"candidate {candidate.candidate_id}: empty TERMINAL target")
            terminals.setdefault(target, TerminalNode(terminal_id=target, label=label))
            edges.append(
                PathwayEdge(
                    source=source,
                    target=target,
                    kind=PathwayEdgeKind.FLOW,
                    branch_label=candidate.branch_label,
                    candidate_id=candidate.candidate_id,
                    fragment_ids=candidate.fragment_ids,
                )
            )
            continue
        if target not in package.rules:
            raise ValueError(
                f"candidate {candidate.candidate_id}: FLOW target {target!r} is not a "
                "canonical rule of the package"
            )
        edges.append(
            PathwayEdge(
                source=source,
                target=target,
                kind=PathwayEdgeKind.FLOW,
                branch_label=candidate.branch_label,
                candidate_id=candidate.candidate_id,
                fragment_ids=candidate.fragment_ids,
            )
        )


def _add_branch_edges(
    candidate: ReconciledCandidate,
    package: ProtocolVersion,
    branch_contexts: dict[str, BranchContextNode],
    edges: list[PathwayEdge],
) -> None:
    context_id = candidate.from_ref
    if not context_id.startswith(_BRANCH_CONTEXT_PREFIX):
        raise ValueError(
            f"candidate {candidate.candidate_id}: BRANCH_CONTEXT source must be a "
            f"'{_BRANCH_CONTEXT_PREFIX}<text>' anchor; got {context_id!r}"
        )
    label = context_id[len(_BRANCH_CONTEXT_PREFIX) :].strip()
    if not label:
        raise ValueError(f"candidate {candidate.candidate_id}: empty branch context label")
    branch_contexts.setdefault(
        context_id,
        BranchContextNode(context_id=context_id, label=label),
    )
    for target in candidate.to_refs:
        if target not in package.rules:
            raise ValueError(
                f"candidate {candidate.candidate_id}: BRANCH_CONTEXT target {target!r} "
                "is not a canonical rule of the package"
            )
        edges.append(
            PathwayEdge(
                source=context_id,
                target=target,
                kind=PathwayEdgeKind.BRANCH,
                branch_label=candidate.branch_label,
                candidate_id=candidate.candidate_id,
                fragment_ids=candidate.fragment_ids,
            )
        )


def _record_badges(
    candidate: ReconciledCandidate,
    badges: dict[str, list[str]],
    notices: list[PathwayNotice],
) -> None:
    status = candidate.reconciliation_status
    rule_refs = [
        ref
        for ref in (candidate.from_ref, *candidate.to_refs)
        if not ref.startswith(_TERMINAL_PREFIX)
        and not ref.startswith(_BRANCH_CONTEXT_PREFIX)
        and not ref.startswith(_EXCEPTED_PREFIX)
        and not ref.startswith("(")
    ]
    if status is ReconciliationStatus.CONFLICT:
        for rule_id in rule_refs:
            badges[rule_id].append(_BADGE_SOURCE_CONFLICT)
    elif status is ReconciliationStatus.INFERRED_STRUCTURE:
        for rule_id in rule_refs:
            badges[rule_id].append(_BADGE_INFERRED_STRUCTURE)
    elif candidate.presentation_role is PresentationRole.GAP:
        for rule_id in rule_refs:
            badges[rule_id].append(_BADGE_GAP)
        notices.append(
            PathwayNotice(
                kind=PathwayNoticeKind.GAP,
                text=_notice_text(candidate, "GAP de fuente"),
            )
        )
    elif status is ReconciliationStatus.UNRESOLVED_MAPPING:
        notices.append(
            PathwayNotice(
                kind=PathwayNoticeKind.UNRESOLVED_MAPPING,
                text=_notice_text(candidate, "mapeo no resuelto"),
            )
        )


def _notice_text(candidate: ReconciledCandidate, prefix: str) -> str:
    quote = candidate.evidence_quote.replace("\n", " ").strip()
    if len(quote) > _QUOTE_BUDGET:
        quote = quote[:_QUOTE_BUDGET].rstrip() + "…"
    notes = candidate.reconciliation_notes.replace("\n", " ").strip()
    if len(notes) > _NOTES_BUDGET:
        notes = notes[:_NOTES_BUDGET].rstrip() + "…"
    return f"{candidate.candidate_id} ({prefix}): «{quote}» (pág. {candidate.page}) — {notes}"


def _validate_topology(
    edges: list[PathwayEdge],
    rule_nodes: Mapping[str, RuleNode],
    branch_contexts: Mapping[str, BranchContextNode],
    terminals: Mapping[str, TerminalNode],
) -> None:
    known_keys = set(rule_nodes) | set(branch_contexts) | set(terminals)
    seen: set[tuple[str, str, str]] = set()
    for edge in edges:
        if edge.source not in known_keys:
            raise ValueError(f"edge {edge.candidate_id!r} has unknown source {edge.source!r}")
        if edge.target not in known_keys:
            raise ValueError(f"edge {edge.candidate_id!r} has unknown target {edge.target!r}")
        if edge.source == edge.target:
            raise ValueError(
                f"edge {edge.candidate_id!r} is a self-loop; the reconciled contract "
                "does not support self-edges"
            )
        key = (edge.source, edge.target, edge.kind.value, edge.branch_label or "")
        if key in seen:
            raise ValueError(
                f"duplicate presentation edge {edge.source!r} -> {edge.target!r} "
                f"({edge.kind.value})"
            )
        seen.add(key)
