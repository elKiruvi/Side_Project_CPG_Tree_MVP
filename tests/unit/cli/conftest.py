"""Shared fixtures for CLI tests: a synthetic protocol artifact tree."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from cpg_tree.knowledge import (
    Action,
    ActionType,
    Condition,
    ConditionKind,
    DerivationState,
    Protocol,
    ProtocolVersion,
    Provenance,
    Rule,
    SourceDocument,
    SourceFragment,
    TestCase,
    TruthValue,
    Variable,
    VariableType,
    dump_package,
)

# Prevent pytest from trying to collect the imported TestCase dataclass.
TestCase.__test__ = False  # type: ignore[misc]


@pytest.fixture
def cli_root(tmp_path: Path) -> Path:
    """A tmp_path artifact root containing TEST-PL-999 v01."""
    root = tmp_path / "protocols"
    target = root / "TEST-PL-999" / "v01"
    target.mkdir(parents=True)
    (target / "package.yaml").write_text(dump_package(_build_cli_package()), encoding="utf-8")
    return root


@pytest.fixture
def case_file(tmp_path: Path) -> Callable[[str], Path]:
    """A tmp_path case JSON file matching the synthetic package."""

    def write(text: str) -> Path:
        path = tmp_path / "case.json"
        path.write_text(text, encoding="utf-8")
        return path

    return write


def _build_cli_package() -> ProtocolVersion:
    protocol = Protocol(
        id="TEST-PL-999",
        name="Synthetic CLI Protocol",
        description="Synthetic scope statement",
    )
    document = SourceDocument(
        document_id="doc-0123456789abcdef",
        filename="test-protocol.pdf",
        sha256="a" * 64,
        file_format="pdf",
        byte_size=1234,
    )
    fragment = SourceFragment(
        id="frag_1",
        document_id="doc-0123456789abcdef",
        page=3,
        section="Criterios",
        verbatim_text="Fuente sintética: la decisión requiere el flag.",
    )
    variables = {
        "flag_y": Variable(id="flag_y", label="Flag Y", type=VariableType.BOOLEAN),
        "count_x": Variable(id="count_x", label="Count X", type=VariableType.NUMERIC),
        "category_z": Variable(
            id="category_z",
            label="Category Z",
            type=VariableType.CATEGORICAL,
            allowed_values=("alpha", "beta"),
        ),
    }
    actions = {
        "act_prescribe_a": Action(
            id="act_prescribe_a", type=ActionType.PRESCRIBE, label="Opción A"
        ),
        "act_prescribe_b": Action(
            id="act_prescribe_b", type=ActionType.PRESCRIBE, label="Opción B"
        ),
    }
    rules = {
        "rule_alternatives": Rule(
            id="rule_alternatives",
            condition=Condition(kind=ConditionKind.FLAG, variable_ref="flag_y", expected=True),
            action_refs=("act_prescribe_a", "act_prescribe_b"),
            provenance=Provenance(DerivationState.SOURCE_STATED, ("frag_1",)),
        ),
    }
    return ProtocolVersion(
        protocol=protocol,
        version="v01",
        approval_date="2026-01-01",
        variables=variables,
        rules=rules,
        actions=actions,
        test_cases={
            "case_1": TestCase(
                id="case_1",
                inputs={"flag_y": True},
                expected_results={"rule_alternatives": TruthValue.TRUE},
            ),
        },
        fragments={"frag_1": fragment},
        documents={"doc-0123456789abcdef": document},
    )
