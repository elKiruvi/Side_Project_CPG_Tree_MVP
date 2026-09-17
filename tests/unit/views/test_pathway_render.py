"""Deterministic SVG rendering tests for the clinical pathway view."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from cpg_tree.knowledge.protocol import ProtocolVersion
from cpg_tree.reconciliation.model import (
    EvidenceClass,
    PresentationRole,
    ReconciliationInventory,
    ReconciliationStatus,
    ReconciledCandidate,
    ReviewStatus,
    SourceEvidenceStatus,
    SourceRepresentation,
)
from cpg_tree.views.pathway import build_pathway_graph
from cpg_tree.views.pathway_render import render_pathway_svg, render_pathway_view
from cpg_tree.views.visualize import build_visual_document


def _candidate(
    candidate_id: str,
    role: PresentationRole,
    from_ref: str,
    to_refs: tuple[str, ...] | str,
    relation: str = "branches",
    branch_label: str | None = None,
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
        fragment_ids=("frag_1",),
        page="3",
        evidence_class=EvidenceClass.SOURCE_STATED,
        review_status=ReviewStatus.PROPOSED,
        reconciliation_status=ReconciliationStatus.READY_FOR_REVIEW,
        source_representation=SourceRepresentation.TEXT,
        source_location=None,
        source_conflict_ids=(),
        source_evidence_status=SourceEvidenceStatus.VERIFIED_TEXT,
        reviewer_notes="notes",
        reconciliation_notes="notes",
    )


def _inventory(candidates: tuple[ReconciledCandidate, ...]) -> ReconciliationInventory:
    return ReconciliationInventory(
        protocol="TEST-PL-999",
        version="v01",
        candidates=candidates,
        conflicts=(),
    )


def _svg_text(
    synthetic_package: ProtocolVersion,
    candidates: tuple[ReconciledCandidate, ...],
) -> str:
    graph = build_pathway_graph(synthetic_package, _inventory(candidates))
    return render_pathway_svg(synthetic_package, graph)


def test_svg_is_deterministic(synthetic_package: ProtocolVersion) -> None:
    candidates = (
        _candidate(
            "rel-t-100",
            PresentationRole.FLOW,
            "rule_composite",
            "rule_alternatives",
        ),
    )
    first = _svg_text(synthetic_package, candidates)
    second = _svg_text(synthetic_package, candidates)
    assert first == second


def test_svg_is_well_formed_xml(synthetic_package: ProtocolVersion) -> None:
    svg = _svg_text(
        synthetic_package,
        (
            _candidate(
                "rel-t-101",
                PresentationRole.BRANCH_CONTEXT,
                "BRANCH_CONTEXT: contexto sintético",
                "rule_composite",
                branch_label="rama A",
            ),
        ),
    )
    root = ET.fromstring(svg)  # raises on malformed XML
    assert root.tag.endswith("svg")


def test_svg_has_no_scripts_and_no_external_resources(
    synthetic_package: ProtocolVersion,
) -> None:
    svg = _svg_text(synthetic_package, ())
    assert "<script" not in svg
    assert 'src="' not in svg
    assert 'href="http' not in svg


def test_unknown_lane_is_present_and_distinct_from_false(
    synthetic_package: ProtocolVersion,
) -> None:
    svg = _svg_text(synthetic_package, ())
    assert svg.count("UNKNOWN → INDETERMINATE (nunca FALSE)") == len(
        synthetic_package.rules
    )
    assert "FALSE → NOT_MATCHED" in svg
    assert "TRUE → MATCHED" in svg


def test_exception_lanes_only_for_rules_with_exceptions(
    synthetic_package: ProtocolVersion,
) -> None:
    svg = _svg_text(synthetic_package, ())
    composite_start = svg.index('id="pathway_rule_rule_composite"')
    composite_end = svg.index("</g>", composite_start)
    composite = svg[composite_start:composite_end]
    alternatives_start = svg.index('id="pathway_rule_rule_alternatives"')
    alternatives_end = svg.index("</g>", alternatives_start)
    alternatives = svg[alternatives_start:alternatives_end]
    assert "EXCEPCIÓN 1" in composite
    assert "excepción TRUE → EXCEPTED" in composite
    assert "EXCEPCIÓN" not in alternatives


def test_rule_nodes_link_to_technical_cards(
    synthetic_package: ProtocolVersion,
) -> None:
    svg = _svg_text(synthetic_package, ())
    for rule_id in synthetic_package.rules:
        assert f'href="#{rule_id}"' in svg
    assert "ver detalle técnico" in svg


def test_branch_context_and_terminal_are_visually_distinct(
    synthetic_package: ProtocolVersion,
) -> None:
    svg = _svg_text(
        synthetic_package,
        (
            _candidate(
                "rel-t-102",
                PresentationRole.BRANCH_CONTEXT,
                "BRANCH_CONTEXT: contexto sintético",
                "rule_composite",
                branch_label="rama A",
            ),
            _candidate(
                "rel-t-103",
                PresentationRole.FLOW,
                "rule_alternatives",
                "TERMINAL: fin de la vía",
                branch_label="NO",
            ),
        ),
    )
    assert "pnode-context" in svg
    assert "pnode-terminal" in svg
    assert "Contexto de presentación — no es una regla canónica" in svg
    assert "Terminal de presentación — no es una regla canónica" in svg
    assert 'class="pedge-branch"' in svg
    assert 'class="pedge-flow"' in svg


def test_escaping_applies_to_node_content(synthetic_package: ProtocolVersion) -> None:
    from dataclasses import replace

    from cpg_tree.knowledge import Provenance, Rule

    sneaky_notes = '<script>alert("x")</script> & umbral > 5'
    rule = replace(
        synthetic_package.rules["rule_alternatives"],
        id="rule_zzz_sneaky",
        notes=sneaky_notes,
        provenance=Provenance(
            synthetic_package.rules["rule_alternatives"].provenance.derivation,
            ("frag_1",),
        ),
    )
    package = replace(
        synthetic_package,
        rules={**synthetic_package.rules, "rule_zzz_sneaky": rule},
    )
    svg = _svg_text(package, ())
    assert "<script>alert" not in svg
    assert "&lt;script&gt;alert" in svg


def test_boxes_never_overlap(synthetic_package: ProtocolVersion) -> None:
    svg = _svg_text(
        synthetic_package,
        (
            _candidate(
                "rel-t-104a",
                PresentationRole.FLOW,
                "rule_composite",
                "rule_alternatives",
            ),
            _candidate(
                "rel-t-104b",
                PresentationRole.BRANCH_CONTEXT,
                "BRANCH_CONTEXT: contexto sintético",
                "rule_composite",
                branch_label="rama A",
            ),
        ),
    )
    boxes = re.findall(
        r'<rect class="pnode-box[^"]*" x="(\d+)" y="(\d+)" width="(\d+)" height="(\d+)"',
        svg,
    )
    rects = [(int(x), int(y), int(w), int(h)) for x, y, w, h in boxes]
    assert len(rects) == 3
    for index, (x_a, y_a, w_a, h_a) in enumerate(rects):
        for x_b, y_b, w_b, h_b in rects[index + 1 :]:
            overlap = x_a < x_b + w_b and x_b < x_a + w_a and y_a < y_b + h_b and y_b < y_a + h_a
            assert not overlap, f"boxes overlap: {(x_a, y_a)} vs {(x_b, y_b)}"


def test_cyclic_topology_renders_deterministically_with_notice(
    synthetic_package: ProtocolVersion,
) -> None:
    candidates = (
        _candidate("rel-t-105a", PresentationRole.FLOW, "rule_composite", "rule_alternatives"),
        _candidate("rel-t-105b", PresentationRole.FLOW, "rule_alternatives", "rule_composite"),
    )
    svg = _svg_text(synthetic_package, candidates)
    assert "contiene ciclos" in svg
    assert svg == _svg_text(synthetic_package, candidates)


def test_view_without_reconciliation_renders_explicit_notice(
    synthetic_package: ProtocolVersion,
) -> None:
    fragment = render_pathway_view(synthetic_package, None)
    assert "Vía clínica de decisión" in fragment
    assert "no se renderiza" in fragment
    assert "<svg" not in fragment


def test_view_with_reconciliation_renders_svg_and_legend(
    synthetic_package: ProtocolVersion,
) -> None:
    fragment = render_pathway_view(
        synthetic_package,
        _inventory(
            (
                _candidate(
                    "rel-t-106",
                    PresentationRole.FLOW,
                    "rule_composite",
                    "rule_alternatives",
                ),
            )
        ),
    )
    assert "<svg" in fragment
    assert "Cómo leer la vía" in fragment
    assert "no constituyen una inferencia automática de flujo clínico adicional" in fragment
    assert "no forman parte del paquete canónico de reglas" in fragment


def test_html_document_has_three_views_and_cross_links(
    synthetic_package: ProtocolVersion,
) -> None:
    inventory = _inventory(
        (
            _candidate(
                "rel-t-107",
                PresentationRole.FLOW,
                "rule_composite",
                "rule_alternatives",
            ),
        )
    )
    document = build_visual_document(synthetic_package, None, inventory)
    assert 'href="#pathway"' in document
    assert 'href="#clinical"' in document
    assert 'href="#technical"' in document
    assert 'id="pathway"' in document
    for rule_id in synthetic_package.rules:
        assert f'id="pathway_rule_{rule_id}"' in document
        assert f'href="#pathway_rule_{rule_id}"' in document
        assert f'id="{rule_id}"' in document


def test_html_document_without_reconciliation_lacks_pathway_backlinks(
    synthetic_package: ProtocolVersion,
) -> None:
    document = build_visual_document(synthetic_package, None)
    assert "no se renderiza" in document
    assert "↩ en vía clínica" not in document


def test_html_document_is_deterministic(
    synthetic_package: ProtocolVersion,
) -> None:
    inventory = _inventory(())
    first = build_visual_document(synthetic_package, None, inventory)
    second = build_visual_document(synthetic_package, None, inventory)
    assert first == second
