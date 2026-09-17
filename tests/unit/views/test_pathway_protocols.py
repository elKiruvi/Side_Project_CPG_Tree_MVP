"""Real-package acceptance tests for the clinical pathway presentation (D3).

All protocol-specific expectations live here in tests; the renderer is
generic. The pathway topology is asserted against the committed D2.5
reconciliation artifacts, never hardcoded in renderer code.
"""

from __future__ import annotations

from pathlib import Path

from cpg_tree.knowledge.protocol import ProtocolVersion
from cpg_tree.protocols.itu_v06 import build_itu_package
from cpg_tree.protocols.nac_v09 import build_nac_package
from cpg_tree.reconciliation.io import load_reconciliation
from cpg_tree.reconciliation.model import ReconciliationInventory
from cpg_tree.views.manifest import load_manifest
from cpg_tree.views.pathway import PathwayEdgeKind, PathwayGraph, build_pathway_graph
from cpg_tree.views.pathway_render import render_pathway_svg
from cpg_tree.views.visualize import build_visual_document

_ROOT = Path(__file__).resolve().parents[3]


def _reconciliation(protocol_id: str, version: str) -> ReconciliationInventory:
    return load_reconciliation(
        _ROOT / "evaluation" / "pathway" / f"{protocol_id}-{version}-reconciliation.yaml"
    )


def _manifest(protocol_id: str, version: str):
    return load_manifest(_ROOT / "protocols" / protocol_id / version / "visualization.yaml")


def _graph(
    package: ProtocolVersion,
    protocol_id: str,
    version: str,
) -> PathwayGraph:
    return build_pathway_graph(
        package,
        _reconciliation(protocol_id, version),
        _manifest(protocol_id, version),
    )


def _svg(package: ProtocolVersion, protocol_id: str, version: str) -> str:
    return render_pathway_svg(package, _graph(package, protocol_id, version))


def _node_block(svg: str, rule_id: str) -> str:
    start = svg.index(f'id="pathway_rule_{rule_id}"')
    end = svg.index("</g>", start)
    return svg[start:end]


# ---------------------------------------------------------------------------
# NAC CT-PL-193 v09
# ---------------------------------------------------------------------------

NAC_FLOW_PAIRS = {
    ("rule_rx_torax_indicada", "rule_rx_repetir_48h"),
    ("rule_rx_torax_indicada", "rule_tc_torax"),
    ("rule_labs_sospecha", "rule_hospitalizacion"),
    ("rule_hospitalizacion", "rule_labs_hospitalizacion"),
    ("rule_toracentesis_paraneumonico", "rule_labs_derrame_pleural"),
    ("rule_hospitalizacion", "rule_hemocultivos"),
    ("rule_hospitalizacion", "rule_gram_cultivo_esputo"),
    ("rule_gram_cultivo_esputo", "rule_esputo_inducido"),
    ("rule_hospitalizacion", "rule_filmarray"),
}


def test_nac_has_42_rule_nodes_exactly_once() -> None:
    package = build_nac_package()
    graph = _graph(package, "CT-PL-193", "v09")
    assert len(graph.rule_nodes) == 42 == len(package.rules)
    assert set(graph.rule_nodes) == set(package.rules)


def test_nac_flow_topology_is_exactly_the_reconciled_set() -> None:
    graph = _graph(build_nac_package(), "CT-PL-193", "v09")
    flow_pairs = {
        (edge.source, edge.target)
        for edge in graph.edges
        if edge.kind is PathwayEdgeKind.FLOW
    }
    assert flow_pairs == NAC_FLOW_PAIRS
    assert len(graph.terminals) == 0
    assert len(graph.branch_contexts) == 0


def test_nac_has_no_exception_lanes() -> None:
    svg = _svg(build_nac_package(), "CT-PL-193", "v09")
    assert "EXCEPCIÓN" not in svg
    assert "excepción TRUE → EXCEPTED" not in svg


def test_nac_unresolved_and_inferred_badges_are_present() -> None:
    svg = _svg(build_nac_package(), "CT-PL-193", "v09")
    curb = _node_block(svg, "rule_hosp_criterio_curb65")
    assert "derivación UNRESOLVED" in curb
    assert "estado de validación UNRESOLVED" in curb
    assert "GAP de fuente" in curb
    bullet = _node_block(svg, "rule_uci_bullet1")
    assert "derivación INFERRED" in bullet
    assert "estructura inferida — no validada" in bullet


def test_nac_conflict_badges_are_present() -> None:
    svg = _svg(build_nac_package(), "CT-PL-193", "v09")
    block = _node_block(svg, "rule_uci_criterios_3de")
    assert "conflicto de fuente sin resolver" in block


def test_nac_conflict_and_gap_notices_are_present() -> None:
    package = build_nac_package()
    document = build_visual_document(
        package,
        _manifest("CT-PL-193", "v09"),
        _reconciliation("CT-PL-193", "v09"),
    )
    for conflict_id in ("SC-NAC-001", "SC-NAC-002", "SC-NAC-003", "SC-NAC-004"):
        assert conflict_id in document
    assert "rel-nac-050" in document
    assert "rel-nac-051" in document


# ---------------------------------------------------------------------------
# ITU CT-PL-197 v06
# ---------------------------------------------------------------------------

ITU_FLOW_PAIRS = {
    ("rule_def_ba", "rule_tto_ba_indicado"),
    ("rule_def_ba", "rule_t1_ba_row"),
    ("rule_def_ba", "rule_t2_ba_gestante"),
    ("rule_t1_alta_ambulatoria", "rule_reevaluar_48h"),
    ("rule_tirilla_descarta_diagnostico", "TERMINAL: diagnóstico descartado"),
    ("rule_def_itu_complicada_estructural", "rule_imagen_urotomografia"),
    ("rule_def_itu_complicada_estructural", "rule_imagen_ecografia_funcional"),
    ("rule_hospitalizacion", "rule_analisis_sangre"),
}

FORBIDDEN_MEDICATION_PAIRS = {
    ("rule_t1_alta_hosp_con_fr_amikacina", "rule_t1_alta_hosp_con_fr_meropenem"),
    ("rule_t2_itu_alta_gestante_cefazolina", "rule_t2_itu_alta_gestante_piperacilina"),
    ("rule_t2_itu_alta_gestante_piperacilina", "rule_t2_itu_alta_gestante_meropenem"),
}


def test_itu_has_60_rule_nodes_exactly_once() -> None:
    package = build_itu_package()
    graph = _graph(package, "CT-PL-197", "v06")
    assert len(graph.rule_nodes) == 60 == len(package.rules)
    assert set(graph.rule_nodes) == set(package.rules)


def test_itu_flow_topology_is_exactly_the_reconciled_set() -> None:
    graph = _graph(build_itu_package(), "CT-PL-197", "v06")
    flow_pairs = {
        (edge.source, edge.target)
        for edge in graph.edges
        if edge.kind is PathwayEdgeKind.FLOW
    }
    assert flow_pairs == ITU_FLOW_PAIRS


def test_itu_has_exactly_one_gestational_branch_context() -> None:
    graph = _graph(build_itu_package(), "CT-PL-197", "v06")
    assert len(graph.branch_contexts) == 1
    context_id = next(iter(graph.branch_contexts))
    assert "ITU alta en gestante" in graph.branch_contexts[context_id].label
    branch_edges = [edge for edge in graph.edges if edge.kind is PathwayEdgeKind.BRANCH]
    assert {(edge.source, edge.target) for edge in branch_edges} == {
        (context_id, "rule_t2_itu_alta_gestante_piperacilina"),
        (context_id, "rule_t2_itu_alta_gestante_meropenem"),
    }
    assert context_id not in graph.rule_nodes


def test_itu_terminal_diagnostico_descartado_is_presentation_only() -> None:
    package = build_itu_package()
    graph = _graph(package, "CT-PL-197", "v06")
    assert "TERMINAL: diagnóstico descartado" in graph.terminals
    assert "TERMINAL: diagnóstico descartado" not in package.rules
    assert "TERMINAL: diagnóstico descartado" not in graph.rule_nodes


def test_no_medication_sequence_edges_exist() -> None:
    graph = _graph(build_itu_package(), "CT-PL-197", "v06")
    for edge in graph.edges:
        pair = (edge.source, edge.target)
        assert pair not in FORBIDDEN_MEDICATION_PAIRS, (
            f"medication sequence {pair} rendered as an edge"
        )
    assert not any(
        edge.kind is PathwayEdgeKind.FLOW and (edge.source, edge.target) in FORBIDDEN_MEDICATION_PAIRS
        for edge in graph.edges
    )


def test_itu_exception_semantics_inside_rule_nodes() -> None:
    package = build_itu_package()
    svg = _svg(package, "CT-PL-197", "v06")
    exception_rules = {
        rule_id for rule_id, rule in package.rules.items() if rule.exceptions
    }
    assert len(exception_rules) == 3
    for rule_id in exception_rules:
        block = _node_block(svg, rule_id)
        assert "EXCEPCIÓN 1" in block
        assert "excepción TRUE → EXCEPTED" in block
    assert svg.count("EXCEPCIÓN 1") == 3


def test_unknown_semantics_preserved_everywhere() -> None:
    package = build_itu_package()
    svg = _svg(package, "CT-PL-197", "v06")
    assert svg.count("UNKNOWN → INDETERMINATE (nunca FALSE)") == 60
    assert "UNKNOWN → FALSE" not in svg


# ---------------------------------------------------------------------------
# Shared acceptance: navigation, provenance, determinism
# ---------------------------------------------------------------------------


def test_every_rule_node_links_to_technical_card_and_back() -> None:
    for package, protocol_id, version in (
        (build_nac_package(), "CT-PL-193", "v09"),
        (build_itu_package(), "CT-PL-197", "v06"),
    ):
        document = build_visual_document(
            package,
            _manifest(protocol_id, version),
            _reconciliation(protocol_id, version),
        )
        for rule_id in package.rules:
            assert f'id="pathway_rule_{rule_id}"' in document
            assert f'href="#pathway_rule_{rule_id}"' in document
            assert f'id="{rule_id}"' in document
        svg = render_pathway_svg(package, _graph(package, protocol_id, version))
        for rule_id in package.rules:
            block = _node_block(svg, rule_id)
            assert f'href="#{rule_id}"' in block
            assert "FUENTE" in block
            assert "frag" in block


def test_provenance_remains_accessible_in_every_node() -> None:
    for package, protocol_id, version in (
        (build_nac_package(), "CT-PL-193", "v09"),
        (build_itu_package(), "CT-PL-197", "v06"),
    ):
        svg = _svg(package, protocol_id, version)
        for rule_id in package.rules:
            assert "FUENTE" in _node_block(svg, rule_id)


def test_full_html_and_svg_are_byte_deterministic() -> None:
    for package, protocol_id, version in (
        (build_nac_package(), "CT-PL-193", "v09"),
        (build_itu_package(), "CT-PL-197", "v06"),
    ):
        reconciliation = _reconciliation(protocol_id, version)
        manifest = _manifest(protocol_id, version)
        graph = _graph(package, protocol_id, version)
        assert render_pathway_svg(package, graph) == render_pathway_svg(package, graph)
        assert build_visual_document(
            package, manifest, reconciliation
        ) == build_visual_document(package, manifest, reconciliation)


def test_reconciliation_artifacts_were_consumed_without_semantic_change() -> None:
    for protocol_id, version in (("CT-PL-193", "v09"), ("CT-PL-197", "v06")):
        inventory = _reconciliation(protocol_id, version)
        for candidate in inventory.candidates:
            assert candidate.review_status.value == "PROPOSED"
