"""ITU CT-PL-197 v06 CLI journey: alternatives, exceptions, provenance.

The journey exercises the committed ITU artifact through the generic CLI and
demonstrates the Phase 6 contract: multiple PRESCRIBE actions on one rule are
source-declared alternatives, rendered as an OR choice, never selected.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cpg_tree.cli import EXIT_OK, main

PROTOCOLS_ROOT = Path(__file__).resolve().parents[3] / "protocols"

ITU_ALTERNATIVE_ACTIONS = (
    "act_t1_nitrofurantoina",
    "act_t1_cefalexina",
    "act_t1_fosfomicina",
)


def _run(argv: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str, str]:
    code = main(["--protocols-root", str(PROTOCOLS_ROOT), *argv])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_list_discovers_itu(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(["list"], capsys)
    assert code == EXIT_OK
    assert "CT-PL-197" in out
    assert "v06" in out


def test_inspect_shows_itu_counts(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(["inspect", "CT-PL-197"], capsys)
    assert code == EXIT_OK
    assert "Protocol : CT-PL-197 (v06)" in out
    assert "fragments: 84" in out
    assert "variables: 76" in out
    assert "rules: 60" in out
    assert "actions: 45" in out
    assert "valid: yes" in out
    assert "rules with source evidence: 60/60" in out
    assert "variables with source evidence: 76/76" in out
    assert "actions with source evidence: 45/45" in out
    assert "fragments with document: 84" in out
    assert "fragments with verbatim text: 84" in out
    assert "derivation: NORMALIZED=45, SOURCE_STATED=15" in out
    assert "derivation (variables): NORMALIZED=23, SOURCE_STATED=53" in out
    assert "validation items: OPEN=12" in out


def test_rule_detail_shows_declared_prescribe_actions(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, _ = _run(["rules", "CT-PL-197", "--rule", "rule_t1_itu_baja"], capsys)
    assert code == EXIT_OK
    for action in ITU_ALTERNATIVE_ACTIONS:
        assert action in out
    assert "PRESCRIBE" in out


def test_provenance_reaches_treatment_table_fragments(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, _ = _run(["provenance", "CT-PL-197", "--rule", "rule_t1_itu_baja"], capsys)
    assert code == EXIT_OK
    assert "frag_p4_t1_itu_baja" in out
    assert "Source documents:" in out


def test_evaluate_renders_alternatives_as_or_choice(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    case_path = tmp_path / "case.json"
    case_path.write_text(
        '{"itu_baja": true, "en_urgencias": true, "sospecha_itu": true, '
        '"mujer": true, "primer_episodio": true, "sintomas_tipicos": true}',
        encoding="utf-8",
    )
    code, out, _ = _run(["evaluate", "CT-PL-197", str(case_path)], capsys)
    assert code == EXIT_OK
    alternatives_block = out[out.index("rule_t1_itu_baja") :]
    for action in ITU_ALTERNATIVE_ACTIONS:
        assert action in alternatives_block
    assert "multiple PRESCRIBE = alternatives declared by the source" in alternatives_block
    assert "this tool never selects one" in alternatives_block


def test_evaluate_demonstrates_excepted_outcome(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    case_path = tmp_path / "case.json"
    case_path.write_text(
        '{"en_urgencias": true, "sospecha_itu": true, "mujer": true, '
        '"primer_episodio": true, "sintomas_tipicos": true}',
        encoding="utf-8",
    )
    code, out, _ = _run(["evaluate", "CT-PL-197", str(case_path)], capsys)
    assert code == EXIT_OK
    assert "rule_citoquimico_orina" in out
    assert "EXCEPTED" in out
    assert "condition TRUE but an exception evaluated TRUE" in out


def test_evaluate_empty_case_is_indeterminate(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    case_path = tmp_path / "case.json"
    case_path.write_text("{}", encoding="utf-8")
    code, out, _ = _run(["evaluate", "CT-PL-197", str(case_path)], capsys)
    assert code == EXIT_OK
    assert "INDETERMINATE" in out
    assert "required information is UNKNOWN" in out
