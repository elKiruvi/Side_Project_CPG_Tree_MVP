"""CLI integration tests for the visualize command using the real packages."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from cpg_tree.cli import EXIT_OK, main

PROTOCOLS_ROOT = Path(__file__).resolve().parents[3] / "protocols"

_RULE_ID_PATTERN = re.compile(r'class="rule-id">([^<]+)<')


def _run(argv: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str, str]:
    code = main(["--protocols-root", str(PROTOCOLS_ROOT), *argv])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _rendered_rule_ids(html_text: str) -> list[str]:
    return _RULE_ID_PATTERN.findall(html_text)


@pytest.mark.parametrize(
    ("protocol_id", "version", "expected_rules", "representative"),
    [
        ("CT-PL-197", "v06", 60, "rule_citoquimico_orina"),
        ("CT-PL-193", "v09", 42, "rule_hemocultivos"),
    ],
)
def test_visualize_real_packages(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    protocol_id: str,
    version: str,
    expected_rules: int,
    representative: str,
) -> None:
    code, out, err = _run(
        ["visualize", protocol_id, version, "--out", str(tmp_path)], capsys
    )
    assert code == EXIT_OK
    assert err == ""
    html_path = tmp_path / f"{protocol_id}-{version}.html"
    assert html_path.is_file()
    assert str(html_path) in out
    content = html_path.read_text(encoding="utf-8")
    assert f"Derived view" in content
    assert f"{protocol_id} · {version}" in content
    assert representative in content
    ids = _rendered_rule_ids(content)
    assert len(ids) == len(set(ids)) == expected_rules
    assert "Otras reglas" not in content


def test_visualize_itu_shows_exceptions_alternatives_and_provenance(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    code, _, _ = _run(["visualize", "CT-PL-197", "v06", "--out", str(tmp_path)], capsys)
    assert code == EXIT_OK
    content = (tmp_path / "CT-PL-197-v06.html").read_text(encoding="utf-8")
    assert "Exception 1" in content
    assert "sintomas_tipicos = true" in content
    assert "[alternative]" in content
    assert "never selected" in content
    assert "page 4" in content
    assert "6. TRATAMIENTO" in content
    assert "medicamento: Nitrofurantoína" in content


def test_visualize_nac_shows_shared_expression_badges(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    code, _, _ = _run(["visualize", "CT-PL-193", "v09", "--out", str(tmp_path)], capsys)
    assert code == EXIT_OK
    content = (tmp_path / "CT-PL-193-v09.html").read_text(encoding="utf-8")
    assert "@shared-" in content
    assert "used" in content and "times" in content
    assert "UCI/UCE" in content


def test_visualize_output_is_byte_deterministic(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    code, _, _ = _run(["visualize", "CT-PL-197", "v06", "--out", str(first_dir)], capsys)
    assert code == EXIT_OK
    code, _, _ = _run(["visualize", "CT-PL-197", "v06", "--out", str(second_dir)], capsys)
    assert code == EXIT_OK
    first = (first_dir / "CT-PL-197-v06.html").read_bytes()
    second = (second_dir / "CT-PL-197-v06.html").read_bytes()
    assert first == second


def test_visualize_unknown_protocol_fails(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    code, _, err = _run(
        ["visualize", "CT-PL-000", "--out", str(tmp_path)], capsys
    )
    assert code == 1
    assert "unknown protocol" in err
