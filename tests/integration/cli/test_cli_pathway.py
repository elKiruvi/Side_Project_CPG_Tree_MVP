"""CLI integration tests: the visualize command renders the D3 pathway view."""

from __future__ import annotations

from pathlib import Path

import pytest

from cpg_tree.cli import EXIT_ERROR, EXIT_OK, main

PROTOCOLS_ROOT = Path(__file__).resolve().parents[3] / "protocols"

NAC_RULES = 42
ITU_RULES = 60


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
def test_visualize_renders_pathway_with_every_rule_once(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    protocol_id: str,
    version: str,
    expected_rules: int,
) -> None:
    code, _out, err = _run(["visualize", protocol_id, version, "--out", str(tmp_path)], capsys)
    assert code == EXIT_OK, err
    html_path = tmp_path / f"{protocol_id}-{version}.html"
    assert html_path.is_file()
    document = html_path.read_text(encoding="utf-8")
    assert 'id="pathway"' in document
    assert "Vía clínica de decisión" in document
    assert "pathway_rule_" in document
    node_count = document.count("pnode-box pnode-rule")
    assert node_count == expected_rules
    assert "Vista técnica" in document
    assert "↩ en vía clínica" in document


def test_visualize_without_reconciliation_renders_explicit_notice(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    code, _out, err = _run(
        [
            "visualize",
            "CT-PL-197",
            "v06",
            "--out",
            str(tmp_path),
            "--reconciliation",
            str(tmp_path / "does-not-exist.yaml"),
        ],
        capsys,
    )
    assert code == EXIT_ERROR
    assert "error:" in err


def test_visualize_pathway_output_is_deterministic(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    _run(["visualize", "CT-PL-193", "v09", "--out", str(first_dir)], capsys)
    _run(["visualize", "CT-PL-193", "v09", "--out", str(second_dir)], capsys)
    first = (first_dir / "CT-PL-193-v09.html").read_text(encoding="utf-8")
    second = (second_dir / "CT-PL-193-v09.html").read_text(encoding="utf-8")
    assert first == second
