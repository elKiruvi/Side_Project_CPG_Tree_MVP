"""Tests for the deterministic HTML visualization renderer."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from cpg_tree.knowledge import ProtocolVersion, dump_package, load_package
from cpg_tree.views.visualize import (
    VisualizationManifest,
    build_visual_document,
    load_manifest,
    visualize_package,
)

_RULE_ID_PATTERN = re.compile(r'class="rule-id">([^<]+)<')


def _manifest(tmp_path: Path, text: str) -> VisualizationManifest:
    path = tmp_path / "visualization.yaml"
    path.write_text(text, encoding="utf-8")
    loaded = load_manifest(path)
    assert loaded is not None
    return loaded


def _rendered_rule_ids(html_text: str) -> list[str]:
    return _RULE_ID_PATTERN.findall(html_text)


def test_fallback_rendering_sorts_all_rules(synthetic_package: ProtocolVersion) -> None:
    html_text = build_visual_document(synthetic_package, None)
    ids = _rendered_rule_ids(html_text)
    assert ids == sorted(synthetic_package.rules)
    assert set(ids) == set(synthetic_package.rules)
    assert "Reglas" in html_text
    assert "TEST-PL-999" in html_text
    assert "v01" in html_text
    assert "Derived view" in html_text


def test_manifest_grouping_with_prefixes_and_explicit_rules(
    tmp_path: Path,
    synthetic_package: ProtocolVersion,
) -> None:
    manifest = _manifest(
        tmp_path,
        "sections:\n"
        "  - title: Primera\n"
        "    rules: [rule_alternatives]\n"
        "    prefixes: [rule_composite]\n"
        "  - title: Segunda\n"
        "    prefixes: [rule_none_]\n",
    )
    html_text = build_visual_document(synthetic_package, manifest)
    assert "Primera" in html_text
    assert "Segunda" in html_text
    assert "Otras reglas" not in html_text
    ids = _rendered_rule_ids(html_text)
    assert len(ids) == len(set(ids)) == len(synthetic_package.rules)


def test_unmatched_rules_go_to_otras_reglas(
    tmp_path: Path,
    synthetic_package: ProtocolVersion,
) -> None:
    manifest = _manifest(
        tmp_path,
        "sections:\n"
        "  - title: Solo una\n"
        "    rules: [rule_alternatives]\n",
    )
    html_text = build_visual_document(synthetic_package, manifest)
    assert "Otras reglas" in html_text
    assert "Solo una" in html_text
    ids = _rendered_rule_ids(html_text)
    assert len(ids) == len(set(ids)) == len(synthetic_package.rules)


def test_manifest_validation_rejects_bad_input(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="malformed visualization manifest"):
        _manifest(tmp_path, "sections: [unclosed")
    with pytest.raises(ValueError, match="must be a mapping"):
        _manifest(tmp_path, "- just\n- a\n- list\n")
    with pytest.raises(ValueError, match="unknown keys"):
        _manifest(tmp_path, "sections: []\nnotes: nope\n")
    with pytest.raises(ValueError, match="non-empty 'sections' list"):
        _manifest(tmp_path, "sections: []\n")
    with pytest.raises(ValueError, match="requires a non-empty 'title'"):
        _manifest(tmp_path, "sections:\n  - prefixes: [rule_]\n")
    with pytest.raises(ValueError, match="list of non-empty strings"):
        _manifest(tmp_path, "sections:\n  - title: X\n    prefixes: [3]\n")
    with pytest.raises(ValueError, match="requires 'prefixes' or 'rules'"):
        _manifest(tmp_path, "sections:\n  - title: X\n")


def test_unknown_explicit_rule_id_fails(
    tmp_path: Path,
    synthetic_package: ProtocolVersion,
) -> None:
    manifest = _manifest(
        tmp_path,
        "sections:\n  - title: X\n    rules: [rule_no_existe]\n",
    )
    with pytest.raises(ValueError, match="unknown rule 'rule_no_existe'"):
        build_visual_document(synthetic_package, manifest)


def test_duplicate_assignment_fails(
    tmp_path: Path,
    synthetic_package: ProtocolVersion,
) -> None:
    manifest = _manifest(
        tmp_path,
        "sections:\n"
        "  - title: X\n    rules: [rule_alternatives]\n"
        "  - title: Y\n    rules: [rule_alternatives]\n",
    )
    with pytest.raises(ValueError, match="more than once"):
        build_visual_document(synthetic_package, manifest)


def test_html_escaping_of_special_characters(
    synthetic_package: ProtocolVersion,
) -> None:
    from dataclasses import replace

    from cpg_tree.knowledge import DerivationState, Provenance, Rule

    sneaky_notes = '<script>alert("x")</script> & umbral > 5'
    rule = Rule(
        id="rule_zzz_sneaky",
        condition=synthetic_package.rules["rule_alternatives"].condition,
        action_refs=(),
        provenance=Provenance(DerivationState.SOURCE_STATED, ("frag_1",)),
        notes=sneaky_notes,
    )
    package = replace(synthetic_package, rules={**synthetic_package.rules, "rule_zzz_sneaky": rule})
    html_text = build_visual_document(package, None)
    assert "<script>alert" not in html_text
    assert "&lt;script&gt;alert" in html_text
    assert "&amp; umbral" in html_text


def test_rendering_is_byte_deterministic(synthetic_package: ProtocolVersion) -> None:
    first = build_visual_document(synthetic_package, None)
    second = build_visual_document(synthetic_package, None)
    assert first == second


def test_visualize_package_writes_deterministic_file(
    tmp_path: Path,
    synthetic_package: ProtocolVersion,
) -> None:
    first = visualize_package(synthetic_package, None, tmp_path)
    second = visualize_package(synthetic_package, None, tmp_path)
    assert first == second
    assert first.name == "TEST-PL-999-v01.html"
    assert first.read_bytes() == second.read_bytes()


def test_shared_expression_badges_reuse_tree_projection(
    synthetic_package: ProtocolVersion,
) -> None:
    from cpg_tree.views.tree import build_projection

    projection = build_projection(synthetic_package)
    html_text = build_visual_document(synthetic_package, None)
    for entry in projection.shared_expressions:
        assert f"@{entry.id}" in html_text
        assert f"used {entry.usage_count} times" in html_text


def test_actions_and_alternatives_marker(synthetic_package: ProtocolVersion) -> None:
    html_text = build_visual_document(synthetic_package, None)
    assert "act_prescribe_a" in html_text
    assert "PRESCRIBE" in html_text
    assert "[alternative]" in html_text
    assert "never selected" in html_text


def test_provenance_chain_rendered(synthetic_package: ProtocolVersion) -> None:
    html_text = build_visual_document(synthetic_package, None)
    assert "frag_1" in html_text
    assert "page 3" in html_text
    assert "Criterios" in html_text
    document = synthetic_package.documents["doc-0123456789abcdef"]
    assert document.document_id[:12] in html_text
    assert document.sha256 in html_text


def test_visualization_does_not_mutate_package(
    synthetic_package: ProtocolVersion,
) -> None:
    before = dump_package(synthetic_package)
    build_visual_document(synthetic_package, None)
    assert dump_package(synthetic_package) == before


@pytest.mark.parametrize(
    ("relative", "expected"),
    [
        ("protocols/CT-PL-197/v06/package.yaml", 60),
        ("protocols/CT-PL-193/v09/package.yaml", 42),
    ],
)
def test_real_packages_render_every_rule_exactly_once(
    relative: str,
    expected: int,
) -> None:
    package = load_package(
        (Path(__file__).resolve().parents[3] / relative).read_text(encoding="utf-8")
    )
    manifest_path = Path(__file__).resolve().parents[3] / relative.replace(
        "package.yaml", "visualization.yaml"
    )
    manifest = load_manifest(manifest_path)
    html_text = build_visual_document(package, manifest)
    ids = _rendered_rule_ids(html_text)
    assert len(ids) == len(set(ids)) == expected
    assert set(ids) == set(package.rules)
    assert "Otras reglas" not in html_text
