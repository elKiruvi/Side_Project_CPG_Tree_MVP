"""Tests for the clinical knowledge view presentation model."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from cpg_tree.knowledge import (
    DerivationState,
    ProtocolVersion,
    Provenance,
    Rule,
    dump_package,
)
from cpg_tree.views.clinical import (
    build_clinical_graph,
    render_clinical_svg,
    render_clinical_view,
)
from cpg_tree.views.manifest import VisualizationManifest, load_manifest

_EXPECTED_SHARED_USAGE = 2


def _manifest(tmp_path: Path, text: str) -> VisualizationManifest:
    path = tmp_path / "visualization.yaml"
    path.write_text(text, encoding="utf-8")
    loaded = load_manifest(path)
    assert loaded is not None
    return loaded


def test_fallback_single_domain_covers_every_rule(
    synthetic_package: ProtocolVersion,
) -> None:
    graph = build_clinical_graph(synthetic_package, None)
    assert graph.protocol_id == "TEST-PL-999"
    assert graph.version == "v01"
    assert len(graph.domains) == 1
    assert graph.domains[0].title == "Reglas"
    assert set(graph.domains[0].rule_ids) == set(synthetic_package.rules)
    assert len(graph.nodes) == len(synthetic_package.rules)
    assert graph.edges == ()
    assert graph.entry_points == ()


def test_domains_follow_manifest_order_and_partition_rules(
    tmp_path: Path,
    synthetic_package: ProtocolVersion,
) -> None:
    manifest = _manifest(
        tmp_path,
        "sections:\n"
        "  - title: Primera\n    rules: [rule_alternatives]\n"
        "  - title: Segunda\n    rules: [rule_composite]\n",
    )
    graph = build_clinical_graph(synthetic_package, manifest)
    assert [domain.title for domain in graph.domains] == ["Primera", "Segunda"]
    all_ids = [rule_id for domain in graph.domains for rule_id in domain.rule_ids]
    assert sorted(all_ids) == sorted(synthetic_package.rules)
    assert len(all_ids) == len(set(all_ids)) == len(synthetic_package.rules)


def test_node_rule_ids_are_real_and_match_section(
    tmp_path: Path,
    synthetic_package: ProtocolVersion,
) -> None:
    manifest = _manifest(
        tmp_path,
        "sections:\n  - title: Primera\n    rules: [rule_alternatives]\n",
    )
    graph = build_clinical_graph(synthetic_package, manifest)
    node = graph.nodes["rule_alternatives"]
    assert node.rule_id == "rule_alternatives"
    assert node.section_title == "Primera"
    assert node.rule is synthetic_package.rules["rule_alternatives"]


def test_unknown_connector_source_rejected(
    tmp_path: Path,
    synthetic_package: ProtocolVersion,
) -> None:
    manifest = _manifest(
        tmp_path,
        "sections:\n  - title: X\n    rules: [rule_alternatives]\n"
        "graph:\n  edges:\n    - from: rule_no_existe\n      to: rule_alternatives\n",
    )
    with pytest.raises(ValueError, match="unknown rule 'rule_no_existe'"):
        build_clinical_graph(synthetic_package, manifest)


def test_unknown_connector_target_rejected(
    tmp_path: Path,
    synthetic_package: ProtocolVersion,
) -> None:
    manifest = _manifest(
        tmp_path,
        "sections:\n  - title: X\n    rules: [rule_alternatives]\n"
        "graph:\n  edges:\n    - from: rule_alternatives\n      to: rule_no_existe\n",
    )
    with pytest.raises(ValueError, match="unknown rule 'rule_no_existe'"):
        build_clinical_graph(synthetic_package, manifest)


def test_unknown_entry_point_rejected(
    tmp_path: Path,
    synthetic_package: ProtocolVersion,
) -> None:
    manifest = _manifest(
        tmp_path,
        "sections:\n  - title: X\n    rules: [rule_alternatives]\n"
        "graph:\n  entry_points: [rule_no_existe]\n",
    )
    with pytest.raises(ValueError, match="entry point references unknown rule 'rule_no_existe'"):
        build_clinical_graph(synthetic_package, manifest)


def test_valid_connectors_and_entry_points_preserved(
    tmp_path: Path,
    synthetic_package: ProtocolVersion,
) -> None:
    manifest = _manifest(
        tmp_path,
        "sections:\n  - title: X\n    rules: [rule_alternatives, rule_composite]\n"
        "graph:\n"
        "  entry_points: [rule_composite]\n"
        "  edges:\n    - from: rule_composite\n      to: rule_alternatives\n",
    )
    graph = build_clinical_graph(synthetic_package, manifest)
    assert graph.entry_points == ("rule_composite",)
    assert [(edge.source, edge.target) for edge in graph.edges] == [
        ("rule_composite", "rule_alternatives")
    ]


def test_top_level_shared_expression_is_detected(
    synthetic_package: ProtocolVersion,
) -> None:
    shared_condition = synthetic_package.rules["rule_composite"].applies_to
    assert shared_condition is not None
    extra_rule = replace(
        synthetic_package.rules["rule_alternatives"],
        id="rule_zzz_shared_user",
        condition=shared_condition,
        action_refs=(),
    )
    package = replace(
        synthetic_package, rules={**synthetic_package.rules, "rule_zzz_shared_user": extra_rule}
    )
    graph = build_clinical_graph(package, None)
    node = graph.nodes["rule_zzz_shared_user"]
    assert node.condition_shared_id is not None
    assert node.condition_shared_id in graph.shared_usage
    assert graph.shared_usage[node.condition_shared_id] == _EXPECTED_SHARED_USAGE


def test_shared_ids_are_consistent_with_projection(
    synthetic_package: ProtocolVersion,
) -> None:
    graph = build_clinical_graph(synthetic_package, None)
    for node in graph.nodes.values():
        shared_ids = (
            node.applies_to_shared_id,
            node.condition_shared_id,
            *node.exception_shared_ids,
        )
        for shared_id in shared_ids:
            if shared_id is not None:
                assert shared_id in graph.shared_usage
    assert graph.shared_usage == {}


# ---------------------------------------------------------------------------
# Renderer tests
# ---------------------------------------------------------------------------


def _svg_text(
    package: ProtocolVersion,
    manifest: VisualizationManifest | None = None,
) -> str:
    graph = build_clinical_graph(package, manifest)
    # cpg_tree imports resolve as Any from test files under the current mypy
    # configuration (pre-existing repo-wide condition); the runtime value is
    # the deterministic SVG text asserted below.
    return render_clinical_svg(package, graph)  # type: ignore[no-any-return]


def _node_block(svg_text: str, rule_id: str) -> str:
    start = svg_text.index(f'id="clinical_rule_{rule_id}"')
    end = svg_text.index("</foreignObject>", start)
    return svg_text[start:end]


def test_render_clinical_view_fragment_is_deterministic(
    synthetic_package: ProtocolVersion,
) -> None:
    first = render_clinical_view(synthetic_package, None)
    second = render_clinical_view(synthetic_package, None)
    assert first == second
    assert "Vista de conocimiento clínico" in first
    assert "<svg" in first
    assert "presentación" in first


def test_svg_renders_every_rule_exactly_once(synthetic_package: ProtocolVersion) -> None:
    svg_text = _svg_text(synthetic_package)
    nodes = svg_text.count('class="cnode"')
    assert nodes == len(synthetic_package.rules)
    assert nodes == len(set(synthetic_package.rules))
    for rule_id in synthetic_package.rules:
        assert f'id="clinical_rule_{rule_id}"' in svg_text


def test_every_node_links_to_its_technical_card(synthetic_package: ProtocolVersion) -> None:
    svg_text = _svg_text(synthetic_package)
    for rule_id in synthetic_package.rules:
        block = _node_block(svg_text, rule_id)
        assert f'href="#{rule_id}"' in block
        assert "ver detalle técnico" in block


def test_unknown_lane_is_present_and_distinct_from_false(
    synthetic_package: ProtocolVersion,
) -> None:
    svg_text = _svg_text(synthetic_package)
    for rule_id in synthetic_package.rules:
        block = _node_block(svg_text, rule_id)
        assert "UNKNOWN → INDETERMINATE (nunca FALSE)" in block
        assert "FALSE → NOT_MATCHED" in block
        assert "TRUE → MATCHED" in block


def test_exception_lanes_only_for_rules_with_exceptions(
    synthetic_package: ProtocolVersion,
) -> None:
    svg_text = _svg_text(synthetic_package)
    composite = _node_block(svg_text, "rule_composite")
    assert "EXCEPCIÓN 1" in composite
    assert "excepción TRUE → EXCEPTED" in composite
    alternatives = _node_block(svg_text, "rule_alternatives")
    assert "EXCEPCIÓN" not in alternatives
    assert "excepción TRUE → EXCEPTED" not in alternatives


def test_compound_conditions_and_applies_to_are_rendered(
    synthetic_package: ProtocolVersion,
) -> None:
    svg_text = _svg_text(synthetic_package)
    composite = _node_block(svg_text, "rule_composite")
    assert "APPLIES TO — alcance/población" in composite
    assert "AND(" in composite
    assert "count_x" in composite


def test_prescribe_alternatives_are_never_selected(
    synthetic_package: ProtocolVersion,
) -> None:
    svg_text = _svg_text(synthetic_package)
    block = _node_block(svg_text, "rule_alternatives")
    assert "act_prescribe_a" in block
    assert "act_prescribe_b" in block
    assert "[alternativa]" in block
    assert "alternativas declaradas por la fuente; nunca seleccionadas" in block
    assert "ACCIONES DECLARATIVAS — NUNCA EJECUTADAS" in block


def test_provenance_line_keeps_fragment_page_and_derivation(
    synthetic_package: ProtocolVersion,
) -> None:
    svg_text = _svg_text(synthetic_package)
    block = _node_block(svg_text, "rule_composite")
    assert "SOURCE_STATED" in block
    assert "frag_1" in block
    assert "pág 3" in block


def test_escaping_applies_to_node_content(synthetic_package: ProtocolVersion) -> None:
    sneaky_notes = '<script>alert("x")</script> & umbral > 5'
    rule = Rule(
        id="rule_zzz_sneaky",
        condition=synthetic_package.rules["rule_alternatives"].condition,
        action_refs=(),
        provenance=Provenance(DerivationState.SOURCE_STATED, ("frag_1",)),
        notes=sneaky_notes,
    )
    package = replace(synthetic_package, rules={**synthetic_package.rules, "rule_zzz_sneaky": rule})
    svg_text = _svg_text(package)
    assert "<script>alert" not in svg_text
    assert "&lt;script&gt;alert" in svg_text


def test_svg_has_no_scripts_and_no_external_resources(
    synthetic_package: ProtocolVersion,
) -> None:
    svg_text = _svg_text(synthetic_package)
    assert "<script" not in svg_text
    assert 'href="http' not in svg_text
    assert 'src="http' not in svg_text
    assert "src=" not in svg_text


def test_svg_is_byte_deterministic(synthetic_package: ProtocolVersion) -> None:
    first = _svg_text(synthetic_package)
    second = _svg_text(synthetic_package)
    assert first == second


def test_connectors_render_only_declared_edges(
    tmp_path: Path,
    synthetic_package: ProtocolVersion,
) -> None:
    manifest = _manifest(
        tmp_path,
        "sections:\n  - title: X\n    rules: [rule_alternatives, rule_composite]\n"
        "graph:\n"
        "  entry_points: [rule_composite]\n"
        "  edges:\n    - from: rule_composite\n      to: rule_alternatives\n",
    )
    svg_text = _svg_text(synthetic_package, manifest)
    assert svg_text.count('class="c-edge"') == 1
    block = _node_block(svg_text, "rule_composite")
    assert "punto de partida (presentación)" in block


def test_no_edges_when_graph_absent(synthetic_package: ProtocolVersion) -> None:
    svg_text = _svg_text(synthetic_package)
    assert 'class="c-edge"' not in svg_text


def test_shared_expression_badge_appears_in_node(
    synthetic_package: ProtocolVersion,
) -> None:
    shared_condition = synthetic_package.rules["rule_composite"].applies_to
    assert shared_condition is not None
    extra_rule = replace(
        synthetic_package.rules["rule_alternatives"],
        id="rule_zzz_shared_user",
        condition=shared_condition,
        action_refs=(),
    )
    package = replace(
        synthetic_package, rules={**synthetic_package.rules, "rule_zzz_shared_user": extra_rule}
    )
    svg_text = _svg_text(package)
    assert "@shared-" in svg_text
    assert "usado 2 veces" in svg_text


def test_render_clinical_view_does_not_mutate_package(
    synthetic_package: ProtocolVersion,
) -> None:
    before = dump_package(synthetic_package)
    render_clinical_view(synthetic_package, None)
    assert dump_package(synthetic_package) == before


def test_membership_and_temporal_conditions_are_rendered(
    synthetic_package: ProtocolVersion,
) -> None:
    svg_text = _svg_text(synthetic_package)
    block = _node_block(svg_text, "rule_composite")
    assert "category_z IN {alpha, beta}" in block
    assert "AT_LEAST_FOR_LAST" in block
    assert "span_t" in block


def test_not_and_at_least_n_expressions_are_rendered(
    synthetic_package: ProtocolVersion,
) -> None:
    from cpg_tree.knowledge import (
        Condition,
        ConditionKind,
        LogicalExpression,
        LogicalOperator,
    )

    flag_false = Condition(kind=ConditionKind.FLAG, variable_ref="flag_y", expected=False)
    not_expr = LogicalExpression(operator=LogicalOperator.NOT, operands=(flag_false,))
    at_least = LogicalExpression(
        operator=LogicalOperator.AT_LEAST_N,
        operands=(flag_false, synthetic_package.rules["rule_alternatives"].condition),
        threshold=1,
    )
    rule = replace(
        synthetic_package.rules["rule_alternatives"],
        id="rule_zzz_not_atleast",
        condition=LogicalExpression(operator=LogicalOperator.AND, operands=(not_expr, at_least)),
        action_refs=(),
    )
    package = replace(
        synthetic_package, rules={**synthetic_package.rules, "rule_zzz_not_atleast": rule}
    )
    svg_text = _svg_text(package)
    block = _node_block(svg_text, "rule_zzz_not_atleast")
    assert "NOT(" in block
    assert "AT_LEAST_N(" in block
