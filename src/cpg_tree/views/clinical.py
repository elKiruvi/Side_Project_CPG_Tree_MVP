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

import html
from collections.abc import Mapping
from dataclasses import dataclass

from cpg_tree.knowledge.enums import ActionType, DerivationState
from cpg_tree.knowledge.protocol import ProtocolVersion
from cpg_tree.knowledge.rules import Rule
from cpg_tree.views.expression import render_operand
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


# ---------------------------------------------------------------------------
# Deterministic static SVG renderer
# ---------------------------------------------------------------------------

_GRID_COLUMNS = 2
_NODE_WIDTH = 340
_NODE_GAP_X = 28
_NODE_GAP_Y = 22
_MARGIN = 28
_TITLE_BAND_H = 40
_DOMAIN_GAP = 52
_CARD_PAD = 10
_EXPR_CHARS = 34
_TEXT_CHARS = 40

_LINE_HEIGHTS = {
    "header": 20,
    "label": 15,
    "expr": 14,
    "small": 13,
    "action": 15,
}

_SAFETY_NOTE = (
    "Mapa de conocimiento derivado del paquete canónico. Las secciones son "
    "agrupaciones de presentación y las líneas punteadas son referencias de "
    "presentación: ninguna representa flujo de trabajo, secuencia clínica ni "
    "dependencia entre reglas. Las reglas son independientes. Las franjas "
    "TRUE/FALSE/UNKNOWN describen la semántica mecánica del motor, no una "
    "evaluación de un paciente. Las acciones son declarativas y nunca se "
    "ejecutan. Prototipo de investigación; no es consejo clínico."
)


@dataclass(frozen=True, slots=True)
class _Line:
    text: str
    style: str


@dataclass(frozen=True, slots=True)
class _NodeBox:
    node: ClinicalRuleNode
    lines: tuple[_Line, ...]
    height: int


def render_clinical_view(package: ProtocolVersion, manifest: VisualizationManifest | None) -> str:
    """Render the clinical knowledge map section of the visualization.

    Returns a deterministic HTML fragment (title, explanatory note, and the
    static SVG map). The fragment is embedded by ``visualize.py``; it never
    evaluates conditions and never mutates the package.
    """
    graph = build_clinical_graph(package, manifest)
    svg = render_clinical_svg(package, graph)
    return (
        f'<h2 class="domain" id="clinical">Vista de conocimiento clínico '
        f'<span class="count">({len(graph.nodes)} reglas)</span></h2>\n'
        f'<p class="map-note">{_esc(_SAFETY_NOTE)}</p>\n'
        f"{svg}\n"
    )


def render_clinical_svg(package: ProtocolVersion, graph: ClinicalGraph) -> str:
    """Render the presentation graph as a deterministic static SVG map."""
    boxes, positions, width, height = _compute_layout(package, graph)
    parts: list[str] = [
        f'<svg class="clinical-map" xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'role="img" aria-label="Mapa de conocimiento clínico — vista de presentación">',
        "<defs>"
        '<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" class="edge-arrow"/></marker>'
        "</defs>",
    ]
    for title, start_y, _end_y in _domain_bands(graph, boxes, positions):
        parts.append(
            f'<text class="domain-title" x="{_MARGIN}" y="{start_y + _TITLE_BAND_H - 14}">'
            f"{_esc(title)} ({_domain_rule_count(graph, title)})</text>"
        )
        parts.append(
            f'<line class="domain-rule" x1="{_MARGIN}" y1="{start_y + _TITLE_BAND_H - 8}" '
            f'x2="{width - _MARGIN}" y2="{start_y + _TITLE_BAND_H - 8}"/>'
        )
    for box in boxes:
        x, y = positions[box.node.rule_id]
        parts.append(_render_node_foreign_object(box, x, y))
    parts.extend(_render_connectors(graph, positions, boxes))
    parts.append("</svg>")
    return "\n".join(parts)


def _compute_layout(
    package: ProtocolVersion,
    graph: ClinicalGraph,
) -> tuple[list[_NodeBox], dict[str, tuple[int, int]], int, int]:
    boxes = [_build_node_box(package, graph, node) for node in graph.nodes.values()]
    boxes_by_id = {box.node.rule_id: box for box in boxes}
    positions: dict[str, tuple[int, int]] = {}
    cursor_y = _MARGIN
    for domain in graph.domains:
        ids = domain.rule_ids
        rows: list[list[str]] = [list(ids[index::_GRID_COLUMNS]) for index in range(_GRID_COLUMNS)]
        row_count = max((len(row) for row in rows), default=0)
        y = cursor_y + _TITLE_BAND_H
        for row_index in range(row_count):
            row_height = max(
                (boxes_by_id[row[row_index]].height for row in rows if row_index < len(row)),
                default=0,
            )
            for column_index, row in enumerate(rows):
                if row_index >= len(row):
                    continue
                rule_id = row[row_index]
                x = _MARGIN + column_index * (_NODE_WIDTH + _NODE_GAP_X)
                positions[rule_id] = (x, y)
            y += row_height + _NODE_GAP_Y
        cursor_y = y - _NODE_GAP_Y + _DOMAIN_GAP
    width = _MARGIN * 2 + _GRID_COLUMNS * _NODE_WIDTH + (_GRID_COLUMNS - 1) * _NODE_GAP_X
    height = cursor_y - _DOMAIN_GAP + _MARGIN
    return boxes, positions, width, height


def _domain_bands(
    graph: ClinicalGraph,
    boxes: list[_NodeBox],
    positions: dict[str, tuple[int, int]],
) -> list[tuple[str, int, int]]:
    boxes_by_id = {box.node.rule_id: box for box in boxes}
    bands: list[tuple[str, int, int]] = []
    for domain in graph.domains:
        ys = [positions[rule_id][1] for rule_id in domain.rule_ids]
        if not ys:
            continue
        top = min(ys) - _NODE_GAP_Y - _TITLE_BAND_H
        bottom = max(
            ys
            + [positions[rule_id][1] + boxes_by_id[rule_id].height for rule_id in domain.rule_ids]
        )
        bands.append((domain.title, top, bottom))
    return bands


def _domain_rule_count(graph: ClinicalGraph, title: str) -> int:
    for domain in graph.domains:
        if domain.title == title:
            return len(domain.rule_ids)
    return 0


def _build_node_box(
    package: ProtocolVersion,
    graph: ClinicalGraph,
    node: ClinicalRuleNode,
) -> _NodeBox:
    rule = node.rule
    lines: list[_Line] = []
    is_entry = node.rule_id in graph.entry_points
    lines.append(_Line(rule.id, "header"))
    badges = f"{rule.validation_status.value} · {rule.provenance.derivation.value}"
    if is_entry:
        badges += " · punto de partida (presentación)"
    lines.append(_Line(badges, "label"))
    lines.append(_Line("evaluación: applies_to → condition → excepciones", "small"))
    if rule.applies_to is not None:
        lines.append(
            _Line(
                _shared_label("APPLIES TO — alcance/población", node.applies_to_shared_id, graph),
                "label",
            )
        )
        lines.extend(_expression_lines(rule.applies_to))
    lines.append(_Line(_shared_label("CONDICIÓN", node.condition_shared_id, graph), "label"))
    lines.extend(_expression_lines(rule.condition))
    lines.append(_Line("semántica del motor (estática, sin evaluación)", "label"))
    lines.append(_Line("TRUE → MATCHED (acciones declarativas)", "small"))
    lines.append(_Line("FALSE → NOT_MATCHED", "small"))
    lines.append(_Line("UNKNOWN → INDETERMINATE (nunca FALSE)", "small"))
    if rule.exceptions:
        lines.append(_Line("excepción TRUE → EXCEPTED", "small"))
        lines.append(_Line("excepción UNKNOWN → INDETERMINATE", "small"))
    for index, exception in enumerate(rule.exceptions):
        shared_id = (
            node.exception_shared_ids[index] if index < len(node.exception_shared_ids) else None
        )
        lines.append(_Line(_shared_label(f"EXCEPCIÓN {index + 1}", shared_id, graph), "label"))
        lines.extend(_expression_lines(exception))
    lines.extend(_action_lines(package, rule))
    if rule.notes:
        lines.append(_Line("NOTAS", "label"))
        lines.extend(_Line(wrapped, "small") for wrapped in _wrap(rule.notes, _TEXT_CHARS))
    lines.append(_Line("FUENTE", "label"))
    lines.append(_Line(_provenance_line(package, rule), "small"))
    if rule.provenance.derivation is DerivationState.UNRESOLVED:
        lines.append(_Line("derivación UNRESOLVED — no es conocimiento validado", "small"))
    elif rule.provenance.derivation is DerivationState.INFERRED:
        lines.append(_Line("derivación INFERRED — no tratar como conocimiento validado", "small"))
    lines.append(_Line("ver detalle técnico", "small"))
    height = _CARD_PAD * 2 + sum(_LINE_HEIGHTS[line.style] for line in lines)
    return _NodeBox(node=node, lines=tuple(lines), height=height)


def _shared_label(base: str, shared_id: str | None, graph: ClinicalGraph) -> str:
    if shared_id is None:
        return base
    usage = graph.shared_usage.get(shared_id, 0)
    return f"{base} — @{shared_id} (usado {usage} veces)"


def _expression_lines(operand: object) -> list[_Line]:
    rendered = render_operand(operand)  # type: ignore[arg-type]
    lines: list[_Line] = []
    for raw_line in rendered.splitlines():
        lines.extend(_Line(wrapped, "expr") for wrapped in _wrap(raw_line, _EXPR_CHARS))
    return lines


def _action_lines(package: ProtocolVersion, rule: Rule) -> list[_Line]:
    lines = [_Line("ACCIONES DECLARATIVAS — NUNCA EJECUTADAS", "label")]
    if not rule.action_refs:
        lines.append(_Line("(ninguna acción declarada)", "small"))
        return lines
    resolved = [(ref, package.actions.get(ref)) for ref in rule.action_refs]
    prescribe_count = sum(
        1 for _, action in resolved if action is not None and action.type is ActionType.PRESCRIBE
    )
    alternatives = prescribe_count > 1
    for ref, action in resolved:
        if action is None:
            lines.append(_Line(f"{ref} (no resuelta)", "action"))
            continue
        marker = " [alternativa]" if alternatives and action.type is ActionType.PRESCRIBE else ""
        label = f" — {action.label}" if action.label else ""
        lines.append(_Line(f"{ref} {action.type.value}{label}{marker}", "action"))
        if action.payload:
            payload_text = "; ".join(f"{key}: {value}" for key, value in action.payload.items())
            lines.extend(_Line(wrapped, "small") for wrapped in _wrap(payload_text, _TEXT_CHARS))
    if alternatives:
        lines.append(_Line("alternativas declaradas por la fuente; nunca seleccionadas", "small"))
    return lines


def _provenance_line(package: ProtocolVersion, rule: Rule) -> str:
    refs: list[str] = []
    document_ref = ""
    for ref in rule.provenance.fragment_refs:
        fragment = package.fragments.get(ref)
        if fragment is None:
            refs.append(ref)
            continue
        detail = f"(pág {fragment.page})" if fragment.page is not None else ""
        refs.append(f"{ref}{detail}")
        if not document_ref and fragment.document_id:
            document_ref = f" → {fragment.document_id[:12]}"
    derivation = rule.provenance.derivation.value
    if not refs:
        return f"{derivation} · sin fragmentos declarados"
    return f"{derivation} · {', '.join(refs)}{document_ref}"


def _render_node_foreign_object(box: _NodeBox, x: int, y: int) -> str:
    parts = [
        f'<foreignObject x="{x}" y="{y}" width="{_NODE_WIDTH}" height="{box.height}">',
        f'<div xmlns="http://www.w3.org/1999/xhtml" class="cnode" '
        f'id="clinical_rule_{_esc(box.node.rule_id)}">',
    ]
    parts.append(f'<a class="clink" href="#{_esc(box.node.rule_id)}">ver detalle técnico ↗</a>')
    for line in box.lines:
        parts.append(f'<div class="cline {line.style}">{_esc(line.text)}</div>')
    parts.append("</div>")
    parts.append("</foreignObject>")
    return "\n".join(parts)


def _render_connectors(
    graph: ClinicalGraph,
    positions: dict[str, tuple[int, int]],
    boxes: list[_NodeBox],
) -> list[str]:
    heights = {box.node.rule_id: box.height for box in boxes}
    parts: list[str] = []
    for edge in graph.edges:
        source_x, source_y = positions[edge.source]
        target_x, target_y = positions[edge.target]
        start = (source_x + _NODE_WIDTH // 2, source_y + heights[edge.source])
        end = (target_x + _NODE_WIDTH // 2, target_y)
        parts.append(
            f'<path class="c-edge" d="M {start[0]} {start[1]} C {start[0]} '
            f'{start[1] + 30}, {end[0]} {end[1] - 30}, {end[0]} {end[1]}" '
            f'marker-end="url(#arrow)"/>'
        )
    return parts


def _wrap(text: str, budget: int) -> list[str]:
    if not text:
        return [""]
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        if len(word) > budget:
            if current:
                lines.append(current)
                current = ""
            for index in range(0, len(word), budget):
                lines.append(word[index : index + budget])
            continue
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= budget:
            current += f" {word}"
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def _esc(text: object) -> str:
    return html.escape(str(text), quote=True)
