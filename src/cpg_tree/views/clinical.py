"""Clinical knowledge view: presentation model and static SVG renderer.

This module is a pure presentation layer over the canonical knowledge
package. It builds a deterministic presentation graph (domains, rule nodes,
optional presentation connectors) and renders it as a static, self-contained
SVG knowledge map embedded in the visualization HTML.

Hard invariants:

- The canonical ``package.yaml`` remains the only source of truth; nothing
  here stores or invents clinical content.
- Conditions are formatted, never evaluated; the engine is never imported.
- Presentation connectors are display references ("referencia de
  presentación"), never clinical workflow, dependencies, or sequencing.
- Multiple PRESCRIBE actions on one rule are source-declared alternatives;
  they are never presented as a selection.
- Missing information is UNKNOWN, never silently FALSE: every rule node
  shows the engine's mechanical TRUE/FALSE/UNKNOWN lanes as static
  explanatory semantics, not as a live evaluation.
- Output is deterministic: identical package + manifest + code produce
  byte-identical SVG/HTML (no randomness, no timestamps, no JavaScript, no
  external resources).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from cpg_tree.knowledge.protocol import ProtocolVersion
from cpg_tree.knowledge.rules import Rule
from cpg_tree.views.manifest import (
    GraphEdge,
    VisualizationManifest,
    group_rules,
)
from cpg_tree.views.tree import build_projection


@dataclass(frozen=True, slots=True)
class ClinicalRuleNode:
    """One visual rule node: the canonical rule plus presentation positions."""

    rule_id: str
    section_title: str
    rule: Rule
    applies_to_shared_id: str | None
    condition_shared_id: str | None
    exception_shared_ids: tuple[str | None, ...]


@dataclass(frozen=True, slots=True)
class ClinicalDomain:
    """One presentation section holding ordered visual rule nodes."""

    title: str
    rule_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ClinicalGraph:
    """The deterministic presentation graph for one package version."""

    protocol_id: str
    version: str
    domains: tuple[ClinicalDomain, ...]
    nodes: Mapping[str, ClinicalRuleNode]
    edges: tuple[GraphEdge, ...]
    entry_points: tuple[str, ...]
    shared_usage: Mapping[str, int]


def build_clinical_graph(
    package: ProtocolVersion,
    manifest: VisualizationManifest | None,
) -> ClinicalGraph:
    """Build the presentation graph from a package and an optional manifest.

    Deterministic: domains follow manifest order (or a single fallback
    domain), rule nodes follow rule-id order within each domain, and every
    rule of the package appears exactly once. Optional graph metadata is
    validated strictly: unknown rule references, self-connectors, duplicate
    connectors, and unsupported connector kinds are rejected at manifest
    load; unknown ids are rejected here against the package.
    """
    grouped = group_rules(package, manifest)
    projection = build_projection(package)
    shared_ids_by_rule = {
        rule.rule_id: (
            rule.applies_to_shared_id,
            rule.condition_shared_id,
            rule.exception_shared_ids,
        )
        for rule in projection.rules
    }
    nodes: dict[str, ClinicalRuleNode] = {}
    domains: list[ClinicalDomain] = []
    for title, rule_ids in grouped:
        for rule_id in rule_ids:
            shared_ids = shared_ids_by_rule[rule_id]
            nodes[rule_id] = ClinicalRuleNode(
                rule_id=rule_id,
                section_title=title,
                rule=package.rules[rule_id],
                applies_to_shared_id=shared_ids[0],
                condition_shared_id=shared_ids[1],
                exception_shared_ids=shared_ids[2],
            )
        domains.append(ClinicalDomain(title=title, rule_ids=tuple(rule_ids)))

    graph = manifest.graph if manifest is not None else None
    edges: tuple[GraphEdge, ...] = ()
    entry_points: tuple[str, ...] = ()
    if graph is not None:
        for edge in graph.edges:
            if edge.source not in nodes:
                raise ValueError(
                    f"visualization manifest connector references unknown rule {edge.source!r}"
                )
            if edge.target not in nodes:
                raise ValueError(
                    f"visualization manifest connector references unknown rule {edge.target!r}"
                )
        edges = graph.edges
        for entry_point in graph.entry_points:
            if entry_point not in nodes:
                raise ValueError(
                    f"visualization manifest entry point references unknown rule {entry_point!r}"
                )
        entry_points = graph.entry_points

    shared_usage: dict[str, int] = {
        entry.id: entry.usage_count for entry in projection.shared_expressions
    }
    return ClinicalGraph(
        protocol_id=package.protocol.id,
        version=package.version,
        domains=tuple(domains),
        nodes=nodes,
        edges=edges,
        entry_points=entry_points,
        shared_usage=shared_usage,
    )
