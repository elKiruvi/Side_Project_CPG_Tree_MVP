"""Tests for the clinical knowledge view presentation model."""

from __future__ import annotations

from pathlib import Path

import pytest

from cpg_tree.knowledge import ProtocolVersion
from cpg_tree.views.clinical import build_clinical_graph
from cpg_tree.views.manifest import load_manifest


def _manifest(tmp_path: Path, text: str):
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
    from dataclasses import replace

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
    assert graph.shared_usage[node.condition_shared_id] == 2


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
