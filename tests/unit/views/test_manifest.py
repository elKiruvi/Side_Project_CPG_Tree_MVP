"""Tests for the presentation manifest model, including the optional graph."""

from __future__ import annotations

from pathlib import Path

import pytest

from cpg_tree.views.manifest import GraphEdge, GraphManifest, VisualizationManifest, load_manifest


def _load(tmp_path: Path, text: str) -> VisualizationManifest:
    path = tmp_path / "visualization.yaml"
    path.write_text(text, encoding="utf-8")
    loaded = load_manifest(path)
    assert loaded is not None
    return loaded


def _graph(tmp_path: Path, text: str) -> GraphManifest:
    return _load(tmp_path, text).graph


def test_sections_only_manifest_has_no_graph(tmp_path: Path) -> None:
    manifest = _load(tmp_path, "sections:\n  - title: X\n    prefixes: [rule_]\n")
    assert manifest.graph is None


def test_graph_with_entry_points_and_edges(tmp_path: Path) -> None:
    graph = _graph(
        tmp_path,
        "sections:\n  - title: X\n    prefixes: [rule_]\n"
        "graph:\n"
        "  entry_points: [rule_a]\n"
        "  edges:\n"
        "    - from: rule_a\n"
        "      to: rule_b\n",
    )
    assert graph is not None
    assert graph.entry_points == ("rule_a",)
    assert graph.edges == (GraphEdge(source="rule_a", target="rule_b", kind="reference"),)


def test_graph_kind_defaults_to_reference(tmp_path: Path) -> None:
    graph = _graph(
        tmp_path,
        "sections:\n  - title: X\n    prefixes: [rule_]\n"
        "graph:\n  edges:\n    - from: rule_a\n      to: rule_b\n      kind: reference\n",
    )
    assert graph is not None
    assert graph.edges[0].kind == "reference"


def test_unknown_top_level_key_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown keys"):
        _load(tmp_path, "sections: []\nworkflow: [a]\n")


def test_graph_must_be_mapping(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="graph entry .* must be a mapping"):
        _load(tmp_path, "sections:\n  - title: X\n    prefixes: [r]\ngraph: [1]\n")


def test_graph_unknown_keys_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="graph entry .* unknown keys"):
        _load(
            tmp_path,
            "sections:\n  - title: X\n    prefixes: [r]\n"
            "graph:\n  entry_points: [r]\n  order: [r]\n",
        )


def test_entry_points_must_be_strings(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="list of non-empty strings"):
        _graph(
            tmp_path,
            "sections:\n  - title: X\n    prefixes: [r]\n"
            "graph:\n  entry_points: [3]\n",
        )


def test_entry_points_must_not_repeat(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="must not repeat ids"):
        _graph(
            tmp_path,
            "sections:\n  - title: X\n    prefixes: [r]\n"
            "graph:\n  entry_points: [rule_a, rule_a]\n",
        )


def test_edges_must_be_list(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="graph edges .* must be a list"):
        _graph(
            tmp_path,
            "sections:\n  - title: X\n    prefixes: [r]\ngraph:\n  edges: nope\n",
        )


def test_edge_must_be_mapping(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="graph edge 0 .* must be a mapping"):
        _graph(
            tmp_path,
            "sections:\n  - title: X\n    prefixes: [r]\ngraph:\n  edges: [1]\n",
        )


def test_edge_unknown_keys_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="graph edge 0 .* unknown keys"):
        _graph(
            tmp_path,
            "sections:\n  - title: X\n    prefixes: [r]\n"
            "graph:\n  edges:\n    - from: a\n      to: b\n      weight: 1\n",
        )


def test_edge_requires_from_and_to(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="non-empty 'from' string"):
        _graph(
            tmp_path,
            "sections:\n  - title: X\n    prefixes: [r]\ngraph:\n  edges:\n    - to: b\n",
        )
    with pytest.raises(ValueError, match="non-empty 'to' string"):
        _graph(
            tmp_path,
            "sections:\n  - title: X\n    prefixes: [r]\ngraph:\n  edges:\n    - from: a\n",
        )


def test_self_edge_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="must not connect a rule to itself"):
        _graph(
            tmp_path,
            "sections:\n  - title: X\n    prefixes: [r]\n"
            "graph:\n  edges:\n    - from: rule_a\n      to: rule_a\n",
        )


def test_duplicate_edge_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="more than once"):
        _graph(
            tmp_path,
            "sections:\n  - title: X\n    prefixes: [r]\n"
            "graph:\n  edges:\n"
            "    - from: rule_a\n      to: rule_b\n"
            "    - from: rule_a\n      to: rule_b\n",
        )


def test_unsupported_kind_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unsupported kind"):
        _graph(
            tmp_path,
            "sections:\n  - title: X\n    prefixes: [r]\n"
            "graph:\n  edges:\n    - from: rule_a\n      to: rule_b\n      kind: next\n",
        )
