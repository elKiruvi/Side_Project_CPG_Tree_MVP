# ruff: noqa: TRY004
"""Presentation metadata model for protocol visualization manifests.

A visualization manifest (``visualization.yaml`` next to ``package.yaml``)
carries presentation-only metadata: which existing rule ids appear in which
visual section, and — optionally — presentation-only connectors between rule
nodes. It contains no clinical content: every clinical fact (conditions,
thresholds, actions, exceptions, provenance) comes exclusively from
``package.yaml``, which remains the canonical source of truth.

Graph connectors are presentation references, never clinical workflow: a
``reference`` edge means "see also", not "follows", "next", "prerequisite",
or "depends on". The renderer displays them as "referencia de presentación".
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import yaml

from cpg_tree.knowledge.protocol import ProtocolVersion

_MANIFEST_FILENAME = "visualization.yaml"

_SECTION_KEYS = frozenset({"title", "prefixes", "rules"})
_GRAPH_KEYS = frozenset({"entry_points", "edges"})
_EDGE_KEYS = frozenset({"from", "to", "kind"})
_ALLOWED_EDGE_KINDS = frozenset({"reference"})
_DEFAULT_EDGE_KIND = "reference"

FALLBACK_SECTION = "Reglas"
OVERFLOW_SECTION = "Otras reglas"


@dataclass(frozen=True, slots=True)
class ManifestSection:
    """One presentation grouping: a title plus rule-id prefixes/explicit ids."""

    title: str
    prefixes: tuple[str, ...] = ()
    rules: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class GraphEdge:
    """One presentation-only connector between two rule nodes.

    ``kind`` is restricted to ``reference``: the connector is a display
    pointer ("see also"), never a clinical dependency or workflow step.
    """

    source: str
    target: str
    kind: str = _DEFAULT_EDGE_KIND


@dataclass(frozen=True, slots=True)
class GraphManifest:
    """Optional presentation-only topology for the clinical knowledge view."""

    entry_points: tuple[str, ...] = ()
    edges: tuple[GraphEdge, ...] = ()


@dataclass(frozen=True, slots=True)
class VisualizationManifest:
    """Presentation-only metadata for one package version."""

    sections: tuple[ManifestSection, ...]
    graph: GraphManifest | None = None


def load_manifest(path: Path) -> VisualizationManifest | None:
    """Load and validate a visualization manifest; None when absent.

    Malformed structure or invalid data raises ``ValueError`` deterministically;
    nothing is silently ignored. Rule-id existence is checked later against
    the package (see ``group_rules`` and the clinical graph builder).
    """
    if not path.is_file():
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise ValueError(f"malformed visualization manifest at {path}: {error}") from error
    if data is None:
        raise ValueError(f"visualization manifest at {path} is empty")
    if not isinstance(data, Mapping):
        raise ValueError(f"visualization manifest at {path} must be a mapping")
    unknown_keys = set(data) - {"sections", "graph"}
    if unknown_keys:
        raise ValueError(
            f"visualization manifest at {path} has unknown keys: {sorted(unknown_keys)}"
        )
    raw_sections = data.get("sections")
    if not isinstance(raw_sections, list) or not raw_sections:
        raise ValueError(f"visualization manifest at {path} requires a non-empty 'sections' list")
    sections: list[ManifestSection] = []
    for index, raw in enumerate(raw_sections):
        sections.append(_section_from_data(path, index, raw))
    graph = _graph_from_data(path, data.get("graph"))
    return VisualizationManifest(sections=tuple(sections), graph=graph)


def _section_from_data(path: Path, index: int, raw: object) -> ManifestSection:
    if not isinstance(raw, Mapping):
        raise ValueError(f"section {index} of {path} must be a mapping")
    unknown_keys = set(raw) - _SECTION_KEYS
    if unknown_keys:
        raise ValueError(f"section {index} of {path} has unknown keys: {sorted(unknown_keys)}")
    title = raw.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError(f"section {index} of {path} requires a non-empty 'title' string")
    prefixes = _string_list(raw.get("prefixes"), path, index, "prefixes")
    rules = _string_list(raw.get("rules"), path, index, "rules")
    if not prefixes and not rules:
        raise ValueError(f"section {index} of {path} requires 'prefixes' or 'rules'")
    return ManifestSection(title=title, prefixes=prefixes, rules=rules)


def _graph_from_data(path: Path, raw: object) -> GraphManifest | None:
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        raise ValueError(f"graph entry of {path} must be a mapping")
    unknown_keys = set(raw) - _GRAPH_KEYS
    if unknown_keys:
        raise ValueError(f"graph entry of {path} has unknown keys: {sorted(unknown_keys)}")
    entry_points = _string_list(raw.get("entry_points"), path, 0, "entry_points")
    if len(set(entry_points)) != len(entry_points):
        raise ValueError(f"graph entry_points of {path} must not repeat ids")
    raw_edges = raw.get("edges")
    edges: list[GraphEdge] = []
    if raw_edges is not None:
        if not isinstance(raw_edges, list):
            raise ValueError(f"graph edges of {path} must be a list")
        for index, raw_edge in enumerate(raw_edges):
            edges.append(_edge_from_data(path, index, raw_edge))
    seen: set[tuple[str, str, str]] = set()
    for edge in edges:
        key = (edge.source, edge.target, edge.kind)
        if key in seen:
            raise ValueError(
                f"graph edges of {path} declare the connector "
                f"{edge.source!r} -> {edge.target!r} more than once"
            )
        seen.add(key)
    return GraphManifest(entry_points=entry_points, edges=tuple(edges))


def _edge_from_data(path: Path, index: int, raw: object) -> GraphEdge:
    if not isinstance(raw, Mapping):
        raise ValueError(f"graph edge {index} of {path} must be a mapping")
    unknown_keys = set(raw) - _EDGE_KEYS
    if unknown_keys:
        raise ValueError(f"graph edge {index} of {path} has unknown keys: {sorted(unknown_keys)}")
    source = raw.get("from")
    if not isinstance(source, str) or not source:
        raise ValueError(f"graph edge {index} of {path} requires a non-empty 'from' string")
    target = raw.get("to")
    if not isinstance(target, str) or not target:
        raise ValueError(f"graph edge {index} of {path} requires a non-empty 'to' string")
    if source == target:
        raise ValueError(f"graph edge {index} of {path} must not connect a rule to itself")
    kind = raw.get("kind", _DEFAULT_EDGE_KIND)
    if kind not in _ALLOWED_EDGE_KINDS:
        raise ValueError(
            f"graph edge {index} of {path} has unsupported kind {kind!r}; "
            f"allowed: {sorted(_ALLOWED_EDGE_KINDS)}"
        )
    return GraphEdge(source=source, target=target, kind=kind)


def _string_list(raw: object, path: Path, index: int, field: str) -> tuple[str, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list) or not all(isinstance(entry, str) and entry for entry in raw):
        raise ValueError(
            f"section {index} of {path}: '{field}' must be a list of non-empty strings"
        )
    return tuple(raw)


def group_rules(
    package: ProtocolVersion,
    manifest: VisualizationManifest | None,
) -> list[tuple[str, list[str]]]:
    """Assign every rule to exactly one section; nothing may be dropped."""
    if manifest is None:
        return [(FALLBACK_SECTION, sorted(package.rules))]
    grouped: list[tuple[str, list[str]]] = []
    assigned: set[str] = set()
    for section in manifest.sections:
        matched: set[str] = set()
        for rule_id in section.rules:
            if rule_id not in package.rules:
                raise ValueError(f"visualization manifest references unknown rule {rule_id!r}")
            if rule_id in assigned:
                raise ValueError(f"visualization manifest assigns rule {rule_id!r} more than once")
            matched.add(rule_id)
        for prefix in section.prefixes:
            for rule_id in sorted(package.rules):
                if rule_id not in assigned and rule_id.startswith(prefix):
                    matched.add(rule_id)
        assigned.update(matched)
        grouped.append((section.title, sorted(matched)))
    remaining = sorted(set(package.rules) - assigned)
    if remaining:
        grouped.append((OVERFLOW_SECTION, remaining))
    return grouped
