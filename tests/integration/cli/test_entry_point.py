"""Subprocess smoke tests for the documented CLI entry point."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

EXIT_OK_CODE = 0
EXIT_ERROR_CODE = 1
EXIT_USAGE_CODE = 2


def _run_module(*argv: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    return subprocess.run(  # noqa: S603 — argv is built from repository constants only
        [sys.executable, "-m", "cpg_tree", "--protocols-root", str(REPO_ROOT / "protocols"), *argv],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env=env,
        check=False,
    )


def test_module_help_prints_usage() -> None:
    result = _run_module("--help")
    assert result.returncode == EXIT_OK_CODE
    assert "list" in result.stdout
    assert "evaluate" in result.stdout


def test_module_list_discovers_both_protocols() -> None:
    result = _run_module("list")
    assert result.returncode == EXIT_OK_CODE
    assert "CT-PL-193" in result.stdout
    assert "CT-PL-197" in result.stdout


def test_module_reports_errors_without_tracebacks() -> None:
    result = _run_module("inspect", "CT-PL-000")
    assert result.returncode == EXIT_ERROR_CODE
    assert result.stdout == ""
    assert result.stderr.startswith("error: unknown protocol 'CT-PL-000'")
    assert "Traceback" not in result.stderr


def test_module_usage_errors_exit_two() -> None:
    result = _run_module("no_such_command")
    assert result.returncode == EXIT_USAGE_CODE
