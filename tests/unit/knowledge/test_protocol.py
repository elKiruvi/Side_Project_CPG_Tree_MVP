"""Tests for Protocol and ProtocolVersion construction and invariants."""

from __future__ import annotations

import pytest

from cpg_tree.knowledge import (
    Action,
    ActionType,
    ComparisonOperator,
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
    ValidationItem,
    Variable,
    VariableType,
)

OPERAND_HIGH = 100
VALID_SHA256 = "3a1654757801b7b618661f846f8335ced6fb9e388891d6bca96f1cd81d6f5882"


def test_protocol_construction() -> None:
    protocol = Protocol(
        id="TEST-PL-999",
        name="Synthetic Protocol",
        description="model coverage",
    )
    assert protocol.id == "TEST-PL-999"
    assert protocol.name == "Synthetic Protocol"
    assert protocol.description == "model coverage"


def test_protocol_requires_identifier() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        Protocol(id="", name="Synthetic Protocol")


def test_protocol_rejects_whitespace_in_identifier() -> None:
    with pytest.raises(ValueError, match="must match"):
        Protocol(id="TEST PL", name="Synthetic Protocol")


def test_protocol_requires_name() -> None:
    with pytest.raises(ValueError, match="name must not be empty"):
        Protocol(id="TEST-PL-999", name="")


def test_protocol_version_construction() -> None:
    protocol = Protocol(id="TEST-PL-999", name="Synthetic Protocol")
    version = ProtocolVersion(
        protocol=protocol,
        version="v01",
        approval_date="2026-01-15",
        change_summary="first synthetic version",
    )
    assert version.protocol is protocol
    assert version.version == "v01"
    assert version.approval_date == "2026-01-15"
    assert version.variables == {}
    assert version.rules == {}


def test_protocol_version_requires_version() -> None:
    protocol = Protocol(id="TEST-PL-999", name="Synthetic Protocol")
    with pytest.raises(ValueError, match="version must not be empty"):
        ProtocolVersion(protocol=protocol, version="")


def test_protocol_version_rejects_whitespace_version() -> None:
    protocol = Protocol(id="TEST-PL-999", name="Synthetic Protocol")
    with pytest.raises(ValueError, match="empty or whitespace"):
        ProtocolVersion(protocol=protocol, version="   ")


def test_protocol_version_accepts_generic_version_format() -> None:
    protocol = Protocol(id="TEST-PL-999", name="Synthetic Protocol")
    version = ProtocolVersion(protocol=protocol, version="2026.09")
    assert version.version == "2026.09"


def test_protocol_version_rejects_invalid_approval_date() -> None:
    protocol = Protocol(id="TEST-PL-999", name="Synthetic Protocol")
    with pytest.raises(ValueError, match="ISO-8601"):
        ProtocolVersion(protocol=protocol, version="v01", approval_date="15-01-2026")


def test_protocol_version_accepts_iso_approval_date() -> None:
    protocol = Protocol(id="TEST-PL-999", name="Synthetic Protocol")
    version = ProtocolVersion(protocol=protocol, version="v01", approval_date="2026-01-15")
    assert version.approval_date == "2026-01-15"


def test_protocol_version_validates_collection_keys() -> None:
    protocol = Protocol(id="TEST-PL-999", name="Synthetic Protocol")
    mismatched = {"wrong_key": Variable(id="count_x", label="Count X", type=VariableType.NUMERIC)}
    with pytest.raises(ValueError, match="does not match entry id"):
        ProtocolVersion(protocol=protocol, version="v01", variables=mismatched)


def test_protocol_version_accepts_all_collection_types() -> None:
    protocol = Protocol(id="TEST-PL-999", name="Synthetic Protocol")
    version = ProtocolVersion(
        protocol=protocol,
        version="v01",
        variables={"count_x": Variable(id="count_x", label="Count X", type=VariableType.NUMERIC)},
        rules={
            "rule_x": Rule(
                id="rule_x",
                condition=Condition(
                    kind=ConditionKind.COMPARISON,
                    variable_ref="count_x",
                    operator=ComparisonOperator.GT,
                    operand=OPERAND_HIGH,
                ),
                action_refs=("act_decide",),
                provenance=Provenance(derivation=DerivationState.SOURCE_STATED),
            )
        },
        actions={"act_decide": Action(id="act_decide", type=ActionType.DECISION)},
        test_cases={"tc_1": TestCase(id="tc_1")},
        validation_items={
            "vi_1": ValidationItem(id="vi_1", category="ambiguity", description="open item")
        },
        fragments={"frag_1": SourceFragment(id="frag_1")},
    )
    assert set(version.variables) == {"count_x"}
    assert set(version.rules) == {"rule_x"}
    assert set(version.actions) == {"act_decide"}
    assert set(version.test_cases) == {"tc_1"}
    assert set(version.validation_items) == {"vi_1"}
    assert set(version.fragments) == {"frag_1"}


def _source_document(document_id: str) -> SourceDocument:
    return SourceDocument(document_id=document_id, filename="x.pdf", sha256=VALID_SHA256)


def test_protocol_version_defaults_to_empty_documents() -> None:
    protocol = Protocol(id="TEST-PL-999", name="Synthetic Protocol")
    version = ProtocolVersion(protocol=protocol, version="v01")
    assert version.documents == {}


def test_protocol_version_accepts_documents_collection() -> None:
    protocol = Protocol(id="TEST-PL-999", name="Synthetic Protocol")
    document = _source_document("doc_1")
    version = ProtocolVersion(protocol=protocol, version="v01", documents={"doc_1": document})
    assert set(version.documents) == {"doc_1"}
    assert version.documents["doc_1"] is document


def test_protocol_version_validates_document_keys() -> None:
    protocol = Protocol(id="TEST-PL-999", name="Synthetic Protocol")
    mismatched = {"wrong_key": _source_document("doc_1")}
    with pytest.raises(ValueError, match="does not match document_id"):
        ProtocolVersion(protocol=protocol, version="v01", documents=mismatched)
