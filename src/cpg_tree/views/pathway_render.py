"""Deterministic static SVG renderer for the clinical pathway (Phase 10 D3).

Pure Python layout: no graph libraries, no JavaScript, no browser-dependent
measurements, no randomness. Identical inputs produce byte-identical SVG.

Layout strategy (deterministic):
- Kahn-style layering over the presentation edges with sorted tie-breaking;
  any residual cycle is appended as a final layer (never crashes, never
  deletes edges, never invents direction).
- Connected components ordered by their smallest node key; components are
  packed into a fixed number of columns (shortest-column-first) so
  disconnected rules remain visible without manufactured connectors.
- Node size is uniform (height = the tallest node), so boxes can never
  overlap.
"""

from __future__ import annotations

import html
import math
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass

from cpg_tree.knowledge.protocol import ProtocolVersion
from cpg_tree.reconciliation.model import ReconciliationInventory
from cpg_tree.views.clinical import (
    _Line,
    _action_lines,
    _expression_lines,
    _provenance_line,
    _wrap,
)
from cpg_tree.views.manifest import VisualizationManifest
from cpg_tree.views.pathway import (
    BranchContextNode,
    PathwayEdge,
    PathwayEdgeKind,
    PathwayGraph,
    RuleNode,
    TerminalNode,
    build_pathway_graph,
)

_NODE_WIDTH = 340
_NODE_GAP_X = 30
_NODE_GAP_Y = 26
_COLUMN_GAP = 44
_MARGIN = 28
_CARD_PAD = 10
_EXPR_CHARS = 34
_TEXT_CHARS = 40
_MAX_COLUMNS = 4

_LINE_HEIGHTS = {
    "header": 18,
    "label": 14,
    "expr": 13,
    "small": 12,
    "action": 14,
    "lane": 13,
    "link": 13,
}

_SAFETY_NOTES = (
    "Los conectores representan relaciones de presentación reconciliadas con la "
    "fuente; no constituyen una inferencia automática de flujo clínico adicional.",
    "Los nodos de contexto y terminales son elementos de presentación y no forman "
    "parte del paquete canónico de reglas. Las franjas TRUE/FALSE/UNKNOWN describen "
    "la semántica del motor, no una evaluación de un paciente. Prototipo de "
    "investigación; no es consejo clínico.",
)

_NO_RECONCILIATION_NOTE = (
    "No hay artefacto de reconciliación D2.5 disponible para este protocolo y "
    "versión; la vía clínica de decisión no se renderiza. Las vistas de conocimiento "
    "clínico y técnica permanecen disponibles."
)


@dataclass(frozen=True, slots=True)
class _NodeBox:
    key: str
    kind: str
    lines: tuple[_Line, ...]
    height: int


def render_pathway_view(
    package: ProtocolVersion,
    reconciliation: ReconciliationInventory | None,
    manifest: VisualizationManifest | None = None,
) -> str:
    """Render the clinical pathway section of the visualization document.

    Returns a deterministic HTML fragment. With a valid reconciliation
    artifact the fragment contains the pathway SVG plus conflict/gap notices;
    without one it contains an explicit, deterministic notice (the other
    views remain available).
    """
    if reconciliation is None:
        return (
            '<h2 class="domain" id="pathway">Vía clínica de decisión</h2>\n'
            f'<p class="map-note">{_esc(_NO_RECONCILIATION_NOTE)}</p>\n'
        )
    graph = build_pathway_graph(package, reconciliation, manifest)
    svg = render_pathway_svg(package, graph)
    parts: list[str] = [
        f'<h2 class="domain" id="pathway">Vía clínica de decisión '
        f'<span class="count">({len(graph.rule_nodes)} reglas)</span></h2>',
    ]
    parts.extend(f'<p class="map-note">{_esc(note)}</p>' for note in _SAFETY_NOTES)
    parts.append(_render_legend())
    parts.append(svg)
    if graph.notices:
        parts.append(_render_notices(graph))
    return "\n".join(parts) + "\n"


def _render_legend() -> str:
    items = (
        "Regla: rectángulo con borde continuo — una regla canónica; enlaza a su "
        "tarjeta técnica.",
        "Contexto de rama: rectángulo con borde discontinuo — nodo de presentación; "
        "no es una regla.",
        "Terminal: cápsula — terminal de presentación; no es una regla.",
        "Aristas FLOW: relaciones reconciliadas en D2.5 con evidencia de fuente; "
        "no son flujo clínico inferido. Aristas de rama: alternativas condicionales.",
        "Semántica del motor: TRUE → MATCHED · FALSE → NOT_MATCHED · UNKNOWN → "
        "INDETERMINATE (UNKNOWN nunca es FALSE).",
        "Acciones declarativas: nunca ejecutadas; las alternativas nunca se "
        "seleccionan.",
    )
    rows = "".join(f"<li>{_esc(item)}</li>" for item in items)
    return f'<section class="pathway-legend"><strong>Cómo leer la vía</strong><ul>{rows}</ul></section>'


def _render_notices(graph: PathwayGraph) -> str:
    rows: list[str] = []
    for notice in graph.notices:
        kind = notice.kind.value
        rows.append(f'<li class="notice-{kind.lower()}"><code>{kind}</code> {_esc(notice.text)}</li>')
    return (
        '<section class="pathway-notices"><h3>Conflictos y brechas de fuente '
        '(sin resolver en la presentación)</h3><ul>' + "".join(rows) + "</ul></section>"
    )


def render_pathway_svg(package: ProtocolVersion, graph: PathwayGraph) -> str:
    """Render the pathway graph as a deterministic static SVG document."""
    boxes = _build_boxes(package, graph)
    node_height = max(box.height for box in boxes)
    positions, width, height, cyclic = _compute_layout(graph, boxes)
    parts: list[str] = [
        f'<svg class="pathway-map" xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'role="img" aria-label="Vía clínica de decisión — vista de presentación">',
        "<defs>"
        '<marker id="parrow" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" class="pedge-arrow"/></marker>'
        "</defs>",
    ]
    if cyclic:
        parts.append(
            f'<text class="pnode-small" x="{_MARGIN}" y="{_MARGIN}">'
            "La topología reconciliada contiene ciclos; el ordenamiento es un "
            "recurso determinista de presentación, no un flujo clínico.</text>"
        )
    parts.extend(_render_edges(graph, positions, boxes))
    for box in boxes:
        x, y = positions[box.key]
        parts.append(_render_node(box, x, y, node_height))
    parts.append("</svg>")
    return "\n".join(parts)


def _build_boxes(package: ProtocolVersion, graph: PathwayGraph) -> list[_NodeBox]:
    boxes: list[_NodeBox] = []
    for rule_id in sorted(graph.rule_nodes):
        lines = _rule_lines(package, graph, rule_id)
        boxes.append(_NodeBox(rule_id, "rule", lines, _height_of(lines)))
    for context_id in sorted(graph.branch_contexts):
        context = graph.branch_contexts[context_id]
        lines = _context_lines(context)
        boxes.append(_NodeBox(context_id, "context", lines, _height_of(lines)))
    for terminal_id in sorted(graph.terminals):
        terminal = graph.terminals[terminal_id]
        lines = _terminal_lines(terminal)
        boxes.append(_NodeBox(terminal_id, "terminal", lines, _height_of(lines)))
    return boxes


def _height_of(lines: tuple[_Line, ...]) -> int:
    return _CARD_PAD * 2 + sum(_LINE_HEIGHTS[line.style] for line in lines)


def _rule_lines(package: ProtocolVersion, graph: PathwayGraph, rule_id: str) -> tuple[_Line, ...]:
    rule = package.rules[rule_id]
    lines: list[_Line] = [_Line(rule.id, "header")]
    badge_texts = [rule.validation_status.value, rule.provenance.derivation.value]
    badge_texts.extend(graph.badges.get(rule_id, ()))
    lines.append(_Line(" · ".join(badge_texts), "label"))
    lines.append(_Line("evaluación: applies_to → condición → excepciones", "small"))
    if rule.applies_to is not None:
        lines.append(_Line("APPLIES TO — alcance/población", "label"))
        lines.extend(_expression_lines(rule.applies_to))
    lines.append(_Line("CONDICIÓN", "label"))
    lines.extend(_expression_lines(rule.condition))
    lines.append(_Line("semántica del motor (estática, sin evaluación)", "label"))
    lines.append(_Line("TRUE → MATCHED (acciones declarativas)", "lane"))
    lines.append(_Line("FALSE → NOT_MATCHED", "lane"))
    lines.append(_Line("UNKNOWN → INDETERMINATE (nunca FALSE)", "lane"))
    if rule.exceptions:
        lines.append(
            _Line("excepción TRUE → EXCEPTED · excepción UNKNOWN → INDETERMINATE", "lane")
        )
        for index, exception in enumerate(rule.exceptions):
            lines.append(_Line(f"EXCEPCIÓN {index + 1}", "label"))
            lines.extend(_expression_lines(exception))
    lines.extend(_action_lines(package, rule))
    if rule.notes:
        lines.append(_Line("NOTAS", "label"))
        lines.extend(_Line(wrapped, "small") for wrapped in _wrap(rule.notes, _TEXT_CHARS))
    lines.append(_Line("FUENTE", "label"))
    lines.append(_Line(_provenance_line(package, rule), "small"))
    lines.append(_Line("ver detalle técnico ↗", "link"))
    return tuple(lines)


def _context_lines(context: BranchContextNode) -> tuple[_Line, ...]:
    lines: list[_Line] = [_Line(wrapped, "header") for wrapped in _wrap(context.label, _TEXT_CHARS)]
    lines.append(_Line("Contexto de presentación — no es una regla canónica", "small"))
    return tuple(lines)


def _terminal_lines(terminal: TerminalNode) -> tuple[_Line, ...]:
    lines: list[_Line] = [
        _Line(wrapped, "header") for wrapped in _wrap(terminal.label, _TEXT_CHARS)
    ]
    lines.append(_Line("Terminal de presentación — no es una regla canónica", "small"))
    return tuple(lines)


# ---------------------------------------------------------------------------
# Deterministic layout
# ---------------------------------------------------------------------------


def _compute_layout(
    graph: PathwayGraph,
    boxes: list[_NodeBox],
) -> tuple[dict[str, tuple[int, int]], int, int, bool]:
    node_height = max(box.height for box in boxes)
    keys = [box.key for box in boxes]
    adjacency: dict[str, set[str]] = defaultdict(set)
    predecessors: dict[str, set[str]] = defaultdict(set)
    for edge in graph.edges:
        adjacency[edge.source].add(edge.target)
        predecessors[edge.target].add(edge.source)

    indegree = {key: len(predecessors.get(key, ())) for key in keys}
    layers: dict[str, int] = {}
    ready = sorted(key for key in keys if indegree[key] == 0)
    layer_index = 0
    while ready:
        for key in ready:
            layers[key] = layer_index
        promoted: set[str] = set()
        for key in ready:
            for target in sorted(adjacency.get(key, ())):
                indegree[target] -= 1
                if indegree[target] == 0:
                    promoted.add(target)
        ready = sorted(promoted)
        layer_index += 1
    leftover = sorted(key for key in keys if key not in layers)
    if leftover:
        for key in leftover:
            layers[key] = layer_index
        layer_index += 1
    cyclic = bool(leftover)

    components = _components(keys, graph.edges)
    component_bounds: dict[str, tuple[int, int]] = {}
    nodes_by_component: dict[str, list[str]] = defaultdict(list)
    for key in keys:
        component = components[key]
        nodes_by_component[component].append(key)
    ordered_components = sorted(nodes_by_component, key=lambda component: min(nodes_by_component[component]))
    for component in ordered_components:
        nodes = nodes_by_component[component]
        component_layers = {layers[key] for key in nodes}
        layer_count = max(component_layers) - min(component_layers) + 1
        widest = max(len([key for key in nodes if layers[key] == level]) for level in component_layers)
        component_bounds[component] = (
            layer_count * node_height + (layer_count - 1) * _NODE_GAP_Y,
            widest * _NODE_WIDTH + (widest - 1) * _NODE_GAP_X,
        )

    column_count = max(1, min(_MAX_COLUMNS, math.ceil(math.sqrt(len(ordered_components)))))
    column_heights = [0] * column_count
    column_components: list[list[str]] = [[] for _ in range(column_count)]
    for component in ordered_components:
        column = min(range(column_count), key=lambda index: column_heights[index])
        column_components[column].append(component)
        column_heights[column] += component_bounds[component][0] + _COLUMN_GAP
    column_widths = [
        max((component_bounds[component][1] for component in components_list), default=_NODE_WIDTH)
        for components_list in column_components
    ]
    column_x: list[int] = []
    cursor = _MARGIN
    for width in column_widths:
        column_x.append(cursor)
        cursor += width + _COLUMN_GAP

    positions: dict[str, tuple[int, int]] = {}
    column_y = [_MARGIN] * column_count
    for column_index, components_list in enumerate(column_components):
        for component in components_list:
            nodes = sorted(nodes_by_component[component])
            min_layer = min(layers[key] for key in nodes)
            block_top = column_y[column_index]
            by_layer: dict[int, list[str]] = defaultdict(list)
            for key in nodes:
                by_layer[layers[key]].append(key)
            component_width = component_bounds[component][1]
            for level in sorted(by_layer):
                layer_nodes = sorted(by_layer[level])
                layer_width = len(layer_nodes) * _NODE_WIDTH + (len(layer_nodes) - 1) * _NODE_GAP_X
                offset_x = (component_width - layer_width) // 2
                y = block_top + (level - min_layer) * (node_height + _NODE_GAP_Y)
                for slot, key in enumerate(layer_nodes):
                    x = column_x[column_index] + offset_x + slot * (_NODE_WIDTH + _NODE_GAP_X)
                    positions[key] = (x, y)
            column_y[column_index] += component_bounds[component][0] + _COLUMN_GAP

    width = cursor - _COLUMN_GAP + _MARGIN
    height = max(column_heights, default=_MARGIN) + _MARGIN
    return positions, width, height, cyclic


def _components(keys: list[str], edges: tuple[PathwayEdge, ...]) -> Mapping[str, str]:
    parent = {key: key for key in keys}

    def find(node: str) -> str:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for edge in edges:
        root_a = find(edge.source)
        root_b = find(edge.target)
        if root_a != root_b:
            parent[max(root_a, root_b)] = min(root_a, root_b)
    return {key: find(key) for key in keys}


# ---------------------------------------------------------------------------
# SVG node and edge rendering
# ---------------------------------------------------------------------------


def _render_edges(
    graph: PathwayGraph,
    positions: dict[str, tuple[int, int]],
    boxes: list[_NodeBox],
) -> list[str]:
    heights = {box.key: box.height for box in boxes}
    parts: list[str] = []
    for edge in graph.edges:
        source_x, source_y = positions[edge.source]
        target_x, target_y = positions[edge.target]
        start = (source_x + _NODE_WIDTH // 2, source_y + heights[edge.source])
        end = (target_x + _NODE_WIDTH // 2, target_y)
        class_name = "pedge-branch" if edge.kind is PathwayEdgeKind.BRANCH else "pedge-flow"
        parts.append(
            f'<path class="{class_name}" d="M {start[0]} {start[1]} C {start[0]} '
            f'{start[1] + 26}, {end[0]} {end[1] - 26}, {end[0]} {end[1]}" '
            f'marker-end="url(#parrow)"/>'
        )
        if edge.branch_label:
            mid_x = (start[0] + end[0]) // 2
            mid_y = (start[1] + end[1]) // 2
            parts.append(
                f'<text class="pedge-label" x="{mid_x + 8}" y="{mid_y - 4}">'
                f"{_esc(edge.branch_label)}</text>"
            )
    return parts


def _render_node(box: _NodeBox, x: int, y: int, height: int) -> str:
    node_id = f"pathway_{box.kind}_{_slug(box.key)}"
    border_class = {
        "rule": "pnode-box pnode-rule",
        "context": "pnode-box pnode-context",
        "terminal": "pnode-box pnode-terminal",
    }[box.kind]
    parts = [f'<g id="{node_id}">']
    parts.append(
        f'<rect class="{border_class}" x="{x}" y="{y}" width="{_NODE_WIDTH}" '
        f'height="{height}" rx="8"/>'
    )
    parts.append(
        f"<title>{_esc(box.key)} — {box.kind}</title>"
    )
    cursor = y + _CARD_PAD
    for line in box.lines:
        line_y = cursor + _LINE_HEIGHTS[line.style]
        style_class = f"pnode-{line.style}"
        text = _esc(line.text)
        if line.style == "link" and box.kind == "rule":
            href = box.key
            parts.append(
                f'<a href="#{href}" xlink:href="#{href}">'
                f'<text class="{style_class} plink" x="{x + _CARD_PAD}" y="{line_y}">{text}</text></a>'
            )
        else:
            parts.append(
                f'<text class="{style_class}" x="{x + _CARD_PAD}" y="{line_y}">{text}</text>'
            )
        cursor = line_y
    parts.append("</g>")
    return "\n".join(parts)


def _slug(key: str) -> str:
    cleaned = "".join(
        character if character.isalnum() or character == "_" else "_" for character in key
    )
    return cleaned


def _esc(text: object) -> str:
    return html.escape(str(text), quote=True)
