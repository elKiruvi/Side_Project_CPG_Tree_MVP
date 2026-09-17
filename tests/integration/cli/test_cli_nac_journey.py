"""NAC CT-PL-193 v09 CLI journey: discovery, inspection, provenance, evaluation.

The journey exercises the committed package artifact through the generic CLI
without importing any protocol builder. It demonstrates the architecture
(rather than clinical semantics): deterministic evaluation, outcome
preservation, declarative actions, and source traceability.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cpg_tree.cli import EXIT_OK, main

PROTOCOLS_ROOT = Path(__file__).resolve().parents[3] / "protocols"

NAC_MATCHED_RULE_COUNT = 5
NAC_ACTIONS_FOR_HOSPITALIZATION = (
    "act_pcr",
    "act_creatinina",
    "act_lactato",
    "act_sodio",
)


def _run(argv: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str, str]:
    code = main(["--protocols-root", str(PROTOCOLS_ROOT), *argv])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_list_discovers_nac(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(["list"], capsys)
    assert code == EXIT_OK
    assert "CT-PL-193" in out
    assert "v09" in out


def test_inspect_shows_nac_metadata_and_counts(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, _ = _run(["inspect", "CT-PL-193"], capsys)
    assert code == EXIT_OK
    assert "Protocol : CT-PL-193 (v09)" in out
    assert "variables: 66" in out
    assert "rules: 42" in out
    assert "actions: 26" in out
    assert "test_cases: 30" in out
    assert "fragments: 35" in out
    assert "validation_items: 8" in out
    assert "valid: yes" in out
    assert "info: 2" in out


def test_rule_detail_shows_evaluation_order(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, _ = _run(["rules", "CT-PL-193", "--rule", "rule_hemocultivos"], capsys)
    assert code == EXIT_OK
    assert "applies_to -> condition -> exceptions" in out
    assert "bun > 30" in out
    assert "act_hemocultivos" in out


def test_provenance_reaches_source_evidence(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, _ = _run(["provenance", "CT-PL-193", "--rule", "rule_hemocultivos"], capsys)
    assert code == EXIT_OK
    assert "Derivation" in out
    assert "Source fragments:" in out
    assert "Source documents:" in out
    assert "sha256   :" in out


def test_validate_reports_traceability_integrity(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, _ = _run(["validate", "CT-PL-193"], capsys)
    assert code == EXIT_OK
    assert "valid: yes" in out
    assert "info: 2" in out


def test_tree_derives_from_canonical_package(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, _ = _run(["tree", "CT-PL-193"], capsys)
    assert code == EXIT_OK
    assert "CT-PL-193 v09" in out
    assert "rule_hospitalizacion" in out
    assert "shared-" in out


def test_evaluate_matched_rules_and_declarative_actions(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    case_path = tmp_path / "case.json"
    case_path.write_text('{"curb65_score": 2, "bun": 35}', encoding="utf-8")
    code, out, _ = _run(["evaluate", "CT-PL-193", str(case_path)], capsys)
    assert code == EXIT_OK
    assert out.count("MATCHED") >= NAC_MATCHED_RULE_COUNT
    assert "rule_hospitalizacion" in out
    for action in NAC_ACTIONS_FOR_HOSPITALIZATION:
        assert action in out
    assert "declared actions" in out
    assert "Note: deterministic mechanical evaluation" in out


def test_evaluate_preserves_outcome_distinctions(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    case_path = tmp_path / "case.json"
    case_path.write_text(
        json.dumps(
            {
                "curb65_score": 1,
                "bun": 10,
                "pcr": 5,
                "leucocitos": 5000,
                "pad": 90,
                "fc": 80,
                "fr_respiratoria": 18,
                "dolor_pleuritico": False,
                "descompensacion_enfermedad_base": False,
                "inmunosuprimido": False,
                "sospecha_germenes_resistentes": False,
                "intolerancia_via_oral": False,
                "sepsis_origen_pulmonar": False,
                "choque_origen_pulmonar": False,
                "compromiso_multilobar": False,
                "derrame_pleural_rx": False,
                "factores_sociales": False,
                "requerimiento_oxigeno_suplementario": False,
            }
        ),
        encoding="utf-8",
    )
    code, out, _ = _run(["evaluate", "CT-PL-193", str(case_path)], capsys)
    assert code == EXIT_OK
    assert "NOT_APPLICABLE" in out
    assert "applies_to evaluated FALSE" in out
    assert "NOT_MATCHED" in out
    assert "INDETERMINATE" in out


def test_evaluate_json_is_deterministic(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    case_path = tmp_path / "case.json"
    case_path.write_text('{"curb65_score": 2, "bun": 35}', encoding="utf-8")
    first = _run(["evaluate", "CT-PL-193", str(case_path), "--json"], capsys)[1]
    second = _run(["evaluate", "CT-PL-193", str(case_path), "--json"], capsys)[1]
    assert first == second
    data = json.loads(first)
    assert data["protocol_id"] == "CT-PL-193"
    assert data["version"] == "v09"
    rule_ids = [entry["rule_id"] for entry in data["rule_results"]]
    assert rule_ids == sorted(rule_ids)
