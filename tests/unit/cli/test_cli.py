"""Behavior tests for the CLI: commands, errors, exit codes, determinism."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

from cpg_tree.cli import EXIT_ERROR, EXIT_OK, main
from cpg_tree.knowledge import (
    Condition,
    ConditionKind,
    DerivationState,
    ProtocolVersion,
    Provenance,
    Rule,
    dump_package,
)
from cpg_tree.views.discovery import discover_protocols, load_protocol


def _run(argv: list[str], cli_root: Path, capsys: pytest.CaptureFixture[str]) -> tuple[int, str, str]:
    code = main(["--protocols-root", str(cli_root), *argv])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _load_cli_package(root: Path) -> ProtocolVersion:
    package, _ = load_protocol(discover_protocols(root), "TEST-PL-999")
    return package


def test_list_discovers_protocols(cli_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err = _run(["list"], cli_root, capsys)
    assert code == EXIT_OK
    assert "TEST-PL-999" in out
    assert "v01" in out
    assert "Synthetic CLI Protocol" in out
    assert err == ""


def test_list_json_schema(cli_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(["list", "--json"], cli_root, capsys)
    assert code == EXIT_OK
    data = json.loads(out)
    assert list(data) == ["protocols"]
    assert data["protocols"][0]["id"] == "TEST-PL-999"
    assert data["protocols"][0]["versions"][0]["version"] == "v01"


def test_inspect_shows_metadata_counts_and_validation(
    cli_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out, _ = _run(["inspect", "TEST-PL-999"], cli_root, capsys)
    assert code == EXIT_OK
    assert "Protocol : TEST-PL-999 (v01)" in out
    assert "variables: 3" in out
    assert "rules: 1" in out
    assert "valid: yes" in out
    assert "not mean clinical validation" in out


def test_inspect_json_is_stable(cli_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    first = _run(["inspect", "TEST-PL-999", "--json"], cli_root, capsys)[1]
    second = _run(["inspect", "TEST-PL-999", "--json"], cli_root, capsys)[1]
    assert first == second
    data = json.loads(first)
    assert data["counts"]["variables"] == 3
    assert data["validation"]["valid"] is True


def test_variables_command(cli_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(["variables", "TEST-PL-999"], cli_root, capsys)
    assert code == EXIT_OK
    assert "category_z" in out
    assert "flag_y" in out
    assert "allowed: alpha, beta" in out


def test_rules_command_list_and_detail(cli_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(["rules", "TEST-PL-999"], cli_root, capsys)
    assert code == EXIT_OK
    assert "rule_alternatives" in out
    code, out, _ = _run(["rules", "TEST-PL-999", "--rule", "rule_alternatives"], cli_root, capsys)
    assert code == EXIT_OK
    assert "applies_to -> condition -> exceptions" in out
    assert "flag_y = true" in out


def test_provenance_command_shows_evidence(
    cli_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out, _ = _run(
        ["provenance", "TEST-PL-999", "--rule", "rule_alternatives"], cli_root, capsys
    )
    assert code == EXIT_OK
    assert "Derivation : SOURCE_STATED" in out
    assert "Fuente sintética" in out
    assert "sha256   : " + "a" * 64 in out
    code, out, _ = _run(
        ["provenance", "TEST-PL-999", "--rule", "rule_alternatives", "--no-evidence"],
        cli_root,
        capsys,
    )
    assert "Fuente sintética" not in out


def test_tree_command(cli_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(["tree", "TEST-PL-999"], cli_root, capsys)
    assert code == EXIT_OK
    assert "TEST-PL-999 v01" in out
    assert "rule_alternatives" in out
    assert "act_prescribe_a (PRESCRIBE)" in out


def test_validate_command(cli_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(["validate", "TEST-PL-999"], cli_root, capsys)
    assert code == EXIT_OK
    assert "valid: yes" in out
    data = json.loads(_run(["validate", "TEST-PL-999", "--json"], cli_root, capsys)[1])
    assert data["error_count"] == 0
    assert data["valid"] is True


def test_evaluate_matched_alternatives(
    cli_root: Path,
    capsys: pytest.CaptureFixture[str],
    case_file: Callable[[str], Path],
) -> None:
    case_path = case_file('{"flag_y": true}')
    code, out, _ = _run(["evaluate", "TEST-PL-999", str(case_path)], cli_root, capsys)
    assert code == EXIT_OK
    assert "MATCHED" in out
    assert "alternatives declared by the source" in out
    assert "this tool never selects one" in out
    assert "Note: deterministic mechanical evaluation" in out


def test_evaluate_json_is_deterministic(
    cli_root: Path,
    capsys: pytest.CaptureFixture[str],
    case_file: Callable[[str], Path],
) -> None:
    case_path = case_file('{"flag_y": true, "count_x": 5}')
    first = _run(["evaluate", "TEST-PL-999", str(case_path), "--json"], cli_root, capsys)[1]
    second = _run(["evaluate", "TEST-PL-999", str(case_path), "--json"], cli_root, capsys)[1]
    assert first == second
    data = json.loads(first)
    assert list(data) == ["protocol_id", "version", "case_values", "rule_results"]
    assert data["case_values"] == {"count_x": 5, "flag_y": True}
    assert data["rule_results"][0]["outcome"] == "MATCHED"


def test_evaluate_preserves_unknown(
    cli_root: Path,
    capsys: pytest.CaptureFixture[str],
    case_file: Callable[[str], Path],
) -> None:
    case_path = case_file('{"flag_y": null}')
    code, out, _ = _run(["evaluate", "TEST-PL-999", str(case_path)], cli_root, capsys)
    assert code == EXIT_OK
    assert "INDETERMINATE" in out
    assert "required information is UNKNOWN" in out


def test_evaluate_show_expressions(
    cli_root: Path,
    capsys: pytest.CaptureFixture[str],
    case_file: Callable[[str], Path],
) -> None:
    case_path = case_file('{"flag_y": true}')
    code, out, _ = _run(
        ["evaluate", "TEST-PL-999", str(case_path), "--show-expressions"], cli_root, capsys
    )
    assert code == EXIT_OK
    assert "condition → TRUE" in out
    assert "flag_y = true" in out


def test_unknown_protocol_fails_with_exit_one(
    cli_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out, err = _run(["inspect", "TEST-PL-000"], cli_root, capsys)
    assert code == EXIT_ERROR
    assert out == ""
    assert "error: unknown protocol 'TEST-PL-000'" in err


def test_unknown_version_fails_with_exit_one(
    cli_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, _, err = _run(["inspect", "TEST-PL-999", "v09"], cli_root, capsys)
    assert code == EXIT_ERROR
    assert "unknown version 'v09'" in err


def test_unknown_case_variable_fails(
    cli_root: Path,
    capsys: pytest.CaptureFixture[str],
    case_file: Callable[[str], Path],
) -> None:
    case_path = case_file('{"no_such": 1}')
    code, _, err = _run(["evaluate", "TEST-PL-999", str(case_path)], cli_root, capsys)
    assert code == EXIT_ERROR
    assert "unknown variable 'no_such'" in err


def test_incompatible_case_value_fails(
    cli_root: Path,
    capsys: pytest.CaptureFixture[str],
    case_file: Callable[[str], Path],
) -> None:
    case_path = case_file('{"flag_y": 1}')
    code, _, err = _run(["evaluate", "TEST-PL-999", str(case_path)], cli_root, capsys)
    assert code == EXIT_ERROR
    assert "variable is BOOLEAN" in err


def test_malformed_case_fails(
    cli_root: Path,
    capsys: pytest.CaptureFixture[str],
    case_file: Callable[[str], Path],
) -> None:
    case_path = case_file("{not json")
    code, _, err = _run(["evaluate", "TEST-PL-999", str(case_path)], cli_root, capsys)
    assert code == EXIT_ERROR
    assert "not valid JSON" in err


def test_ambiguous_version_fails(cli_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    package_v02 = replace(_load_cli_package(cli_root), version="v02")
    target = cli_root / "TEST-PL-999" / "v02"
    target.mkdir(parents=True)
    (target / "package.yaml").write_text(dump_package(package_v02), encoding="utf-8")
    code, _, err = _run(["inspect", "TEST-PL-999"], cli_root, capsys)
    assert code == EXIT_ERROR
    assert "multiple versions" in err
    code, out, _ = _run(["inspect", "TEST-PL-999", "v02"], cli_root, capsys)
    assert code == EXIT_OK
    assert "TEST-PL-999 (v02)" in out


def test_evaluate_refuses_invalid_package(
    cli_root: Path,
    capsys: pytest.CaptureFixture[str],
    case_file: Callable[[str], Path],
) -> None:
    broken = _load_cli_package(cli_root)
    broken_rule = Rule(
        id="rule_broken",
        condition=Condition(kind=ConditionKind.FLAG, variable_ref="flag_y", expected=True),
        action_refs=("missing_action",),
        provenance=Provenance(DerivationState.SOURCE_STATED, ("frag_1",)),
    )
    (cli_root / "TEST-PL-999" / "v01" / "package.yaml").write_text(
        dump_package(replace(broken, rules={**broken.rules, "rule_broken": broken_rule})),
        encoding="utf-8",
    )
    case_path = case_file('{"flag_y": true}')
    code, _, err = _run(["evaluate", "TEST-PL-999", str(case_path)], cli_root, capsys)
    assert code == EXIT_ERROR
    assert "refusing to evaluate" in err


def test_usage_error_exits_with_two(cli_root: Path) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--protocols-root", str(cli_root), "no_such_command"])
    assert excinfo.value.code == 2


def test_debug_reraises(cli_root: Path) -> None:
    with pytest.raises(ValueError, match="unknown protocol"):
        main(["--debug", "--protocols-root", str(cli_root), "inspect", "TEST-PL-000"])
