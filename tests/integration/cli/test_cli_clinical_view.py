"""Real-package integration tests for the clinical knowledge view.

These tests run the unchanged CLI ``visualize`` command against the committed
NAC and ITU artifacts and assert structural invariants of the clinical SVG
map. All protocol-specific expectations live here, in tests; the renderer
itself is generic.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cpg_tree.cli import EXIT_OK, main

PROTOCOLS_ROOT = Path(__file__).resolve().parents[3] / "protocols"

NAC_RULES = 42
ITU_RULES = 60
ITU_EXCEPTION_RULES = 3


def _run(argv: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str, str]:
    code = main(["--protocols-root", str(PROTOCOLS_ROOT), *argv])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


@pytest.mark.parametrize(
    ("protocol_id", "version", "expected_rules"),
    [
        ("CT-PL-193", "v09", NAC_RULES),
        ("CT-PL-197", "v06", ITU_RULES),
    ],
)
def test_clinical_map_renders_every_rule_exactly_once(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    protocol_id: str,
    version: str,
    expected_rules: int,
) -> None:
    code, _, err = _run(["visualize", protocol_id, version, "--out", str(tmp_path)], capsys)
    assert code == EXIT_OK
    assert err == ""
    content = (tmp_path / f"{protocol_id}-{version}.html").read_text(encoding="utf-8")
    nodes = content.count('class="cnode"')
    assert nodes == expected_rules
    assert 'id="clinical"' in content
    assert 'id="technical"' in content
    assert "<script" not in content


@pytest.mark.parametrize(
    ("protocol_id", "version"),
    [("CT-PL-193", "v09"), ("CT-PL-197", "v06")],
)
def test_clinical_nodes_are_anchored_to_real_rule_ids(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    protocol_id: str,
    version: str,
) -> None:
    code, _, _ = _run(["visualize", protocol_id, version, "--out", str(tmp_path)], capsys)
    assert code == EXIT_OK
    content = (tmp_path / f"{protocol_id}-{version}.html").read_text(encoding="utf-8")
    anchor_count = content.count('id="clinical_rule_')
    assert anchor_count in (NAC_RULES, ITU_RULES)
    assert content.count('href="#clinical_rule_') == anchor_count


def _clinical_map_svg(content: str) -> str:
    marker = '<svg class="clinical-map"'
    start = content.index(marker)
    end = content.index("</svg>", start)
    return content[start:end]


@pytest.mark.parametrize(
    ("protocol_id", "version"),
    [("CT-PL-193", "v09"), ("CT-PL-197", "v06")],
)
def test_unknown_lane_is_present_for_every_rule(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    protocol_id: str,
    version: str,
) -> None:
    code, _, _ = _run(["visualize", protocol_id, version, "--out", str(tmp_path)], capsys)
    assert code == EXIT_OK
    content = (tmp_path / f"{protocol_id}-{version}.html").read_text(encoding="utf-8")
    expected = NAC_RULES if protocol_id == "CT-PL-193" else ITU_RULES
    clinical = _clinical_map_svg(content)
    assert clinical.count("UNKNOWN → INDETERMINATE (nunca FALSE)") == expected


def test_nac_has_no_fabricated_exception_lanes(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    code, _, _ = _run(["visualize", "CT-PL-193", "v09", "--out", str(tmp_path)], capsys)
    assert code == EXIT_OK
    content = (tmp_path / "CT-PL-193-v09.html").read_text(encoding="utf-8")
    assert "EXCEPCIÓN" not in content
    assert "excepción TRUE → EXCEPTED" not in content


def test_itu_exception_lanes_match_the_canonical_exception_rules(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    code, _, _ = _run(["visualize", "CT-PL-197", "v06", "--out", str(tmp_path)], capsys)
    assert code == EXIT_OK
    content = (tmp_path / "CT-PL-197-v06.html").read_text(encoding="utf-8")
    clinical = _clinical_map_svg(content)
    assert clinical.count("excepción TRUE → EXCEPTED") == ITU_EXCEPTION_RULES
    assert clinical.count("EXCEPCIÓN 1") == ITU_EXCEPTION_RULES


def test_itu_prescribe_alternatives_remain_alternatives(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    code, _, _ = _run(["visualize", "CT-PL-197", "v06", "--out", str(tmp_path)], capsys)
    assert code == EXIT_OK
    content = (tmp_path / "CT-PL-197-v06.html").read_text(encoding="utf-8")
    assert "[alternativa]" in content
    assert "nunca seleccionadas" in content
    assert "ACCIONES DECLARATIVAS — NUNCA EJECUTADAS" in content


def test_real_manifests_keep_zero_presentation_edges(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    for protocol_id, version in [("CT-PL-193", "v09"), ("CT-PL-197", "v06")]:
        code, _, _ = _run(["visualize", protocol_id, version, "--out", str(tmp_path)], capsys)
        assert code == EXIT_OK
        content = (tmp_path / f"{protocol_id}-{version}.html").read_text(encoding="utf-8")
        assert 'class="c-edge"' not in content


def test_clinical_map_mentions_presentation_not_workflow(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    code, _, _ = _run(["visualize", "CT-PL-197", "v06", "--out", str(tmp_path)], capsys)
    assert code == EXIT_OK
    content = (tmp_path / "CT-PL-197-v06.html").read_text(encoding="utf-8")
    assert "referencias de presentación" in content
    assert "no es consejo clínico" in content
