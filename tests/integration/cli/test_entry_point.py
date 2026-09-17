"""Subprocess smoke tests for the documented CLI entry point."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _run_module(*argv: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    return subprocess.run(
        [sys.executable, "-m", "cpg_tree", "--protocols-root", str(REPO_ROOT / "protocols"), *argv],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env=env,
        check=False,
    )


def test_module_help_prints_usage() -> None:
    result = _run_module("--help")
    assert result.returncode == 0
    assert "list" in result.stdout
    assert "evaluate" in result.stdout


def test_module_list_discovers_both_protocols() -> None:
    result = _run_module("list")
    assert result.returncode == 0
    assert "CT-PL-193" in result.stdout
    assert "CT-PL-197" in result.stdout


def test_module_reports_errors_without_tracebacks() -> None:
    result = _run_module("inspect", "CT-PL-000")
    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr.startswith("error: unknown protocol 'CT-PL-000'")
    assert "Traceback" not in result.stderr


def test_module_usage_errors_exit_two() -> None:
    result = _run_module("no_such_command")
    assert result.returncode == 2
