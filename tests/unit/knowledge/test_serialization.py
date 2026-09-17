"""Tests for YAML serialization: determinism, round-trip, and safety."""

from __future__ import annotations

import pytest
import yaml
from yaml.constructor import ConstructorError

from cpg_tree.knowledge import (
    ComparisonOperator,
    Condition,
    ConditionKind,
    LogicalExpression,
    LogicalOperator,
    ProtocolVersion,
    dump_package,
    from_dict,
    load_package,
    to_dict,
)

OPERAND_HIGH = 100
SYNTHETIC_BYTE_SIZE = 1024


def test_to_dict_omits_none_fields() -> None:
    condition = Condition(
        kind=ConditionKind.FLAG,
        variable_ref="flag_y",
        expected=True,
    )
    data = to_dict(condition)
    assert data == {"kind": "FLAG", "variable_ref": "flag_y", "expected": True}


def test_to_dict_rejects_non_model_values() -> None:
    with pytest.raises(ValueError, match="cannot serialize"):
        to_dict("plain string")


def test_from_dict_rejects_non_mapping() -> None:
    with pytest.raises(ValueError, match="expected a mapping"):
        from_dict("plain string")


def test_from_dict_rejects_unrecognized_mapping() -> None:
    with pytest.raises(ValueError, match="without 'kind' or 'operator'"):
        from_dict({"unknown": True})


def test_condition_round_trip() -> None:
    original = Condition(
        kind=ConditionKind.COMPARISON,
        variable_ref="count_x",
        operator=ComparisonOperator.GT,
        operand=OPERAND_HIGH,
    )
    assert from_dict(to_dict(original)) == original


def test_expression_round_trip() -> None:
    original = LogicalExpression(
        operator=LogicalOperator.AT_LEAST_N,
        threshold=2,
        operands=(
            Condition(kind=ConditionKind.FLAG, variable_ref="flag_y", expected=True),
            Condition(
                kind=ConditionKind.COMPARISON,
                variable_ref="count_x",
                operator=ComparisonOperator.GT,
                operand=OPERAND_HIGH,
            ),
            Condition(
                kind=ConditionKind.MEMBERSHIP,
                variable_ref="category_z",
                values=("alpha",),
            ),
        ),
    )
    assert from_dict(to_dict(original)) == original


def test_dump_is_deterministic(synthetic_package: ProtocolVersion) -> None:
    assert dump_package(synthetic_package) == dump_package(synthetic_package)


def test_dump_contains_no_python_object_tags(synthetic_package: ProtocolVersion) -> None:
    text = dump_package(synthetic_package)
    assert "!!python" not in text


def test_dump_is_readable_yaml(synthetic_package: ProtocolVersion) -> None:
    data = yaml.safe_load(dump_package(synthetic_package))
    assert isinstance(data, dict)
    assert data["protocol"]["id"] == "TEST-PL-999"
    assert data["version"]["version"] == "v01"
    assert "count_x" in data["variables"]
    assert "rule_composite" in data["rules"]


def test_package_round_trip_equality(synthetic_package: ProtocolVersion) -> None:
    loaded = load_package(dump_package(synthetic_package))
    assert loaded == synthetic_package
    assert (
        loaded.rules["rule_composite"].condition
        == synthetic_package.rules["rule_composite"].condition
    )


def test_load_rejects_unsafe_python_tags() -> None:
    with pytest.raises(ConstructorError):
        load_package("protocol: !!python/object:os.system []\nversion: {version: v01}\n")


def test_load_rejects_non_mapping_root() -> None:
    with pytest.raises(ValueError, match="root must be a mapping"):
        load_package("- just\n- a\n- list\n")


def test_load_rejects_missing_protocol_block() -> None:
    with pytest.raises(ValueError, match="requires a 'protocol' mapping"):
        load_package("version: {version: v01}\n")


def test_load_rejects_missing_version_block() -> None:
    with pytest.raises(ValueError, match="requires a 'version' mapping"):
        load_package("protocol: {id: TEST-PL-999, name: Synthetic}\n")


_RULE_PACKAGE_HEADER = "protocol: {id: TEST-PL-999, name: Synthetic}\nversion: {version: v01}\n"


def test_load_rejects_rule_without_provenance() -> None:
    text = (
        _RULE_PACKAGE_HEADER + "rules:\n"
        "  rule_x:\n"
        "    id: rule_x\n"
        "    condition: {kind: FLAG, variable_ref: flag_y, expected: true}\n"
        "    action_refs: [act_decide]\n"
        "actions:\n"
        "  act_decide: {id: act_decide, type: DECISION}\n"
    )
    with pytest.raises(ValueError, match="requires a 'provenance' mapping"):
        load_package(text)


def test_load_rejects_rule_with_non_mapping_provenance() -> None:
    text = (
        _RULE_PACKAGE_HEADER + "rules:\n"
        "  rule_x:\n"
        "    id: rule_x\n"
        "    condition: {kind: FLAG, variable_ref: flag_y, expected: true}\n"
        "    action_refs: [act_decide]\n"
        "    provenance: source-text\n"
    )
    with pytest.raises(ValueError, match="requires a 'provenance' mapping"):
        load_package(text)


def test_load_rejects_provenance_without_derivation() -> None:
    text = (
        _RULE_PACKAGE_HEADER + "rules:\n"
        "  rule_x:\n"
        "    id: rule_x\n"
        "    condition: {kind: FLAG, variable_ref: flag_y, expected: true}\n"
        "    action_refs: [act_decide]\n"
        "    provenance: {fragment_refs: [frag_1]}\n"
    )
    with pytest.raises(ValueError, match="requires a 'derivation' field"):
        load_package(text)


def test_load_rejects_expression_without_operands() -> None:
    text = (
        _RULE_PACKAGE_HEADER + "rules:\n"
        "  rule_x:\n"
        "    id: rule_x\n"
        "    condition: {operator: AND}\n"
        "    action_refs: [act_decide]\n"
        "    provenance: {derivation: SOURCE_STATED}\n"
    )
    with pytest.raises(ValueError, match="requires 'operands'"):
        load_package(text)


def test_load_rejects_non_list_operands() -> None:
    text = (
        _RULE_PACKAGE_HEADER + "rules:\n"
        "  rule_x:\n"
        "    id: rule_x\n"
        "    condition: {operator: AND, operands: single}\n"
        "    action_refs: [act_decide]\n"
        "    provenance: {derivation: SOURCE_STATED}\n"
    )
    with pytest.raises(ValueError, match="must be a list"):
        load_package(text)


def test_load_rejects_non_mapping_operand() -> None:
    text = (
        _RULE_PACKAGE_HEADER + "rules:\n"
        "  rule_x:\n"
        "    id: rule_x\n"
        "    condition:\n"
        "      operator: AND\n"
        "      operands: [plain-string]\n"
        "    action_refs: [act_decide]\n"
        "    provenance: {derivation: SOURCE_STATED}\n"
    )
    with pytest.raises(ValueError, match="expected a mapping"):
        load_package(text)


def test_load_rejects_non_integer_threshold() -> None:
    text = (
        _RULE_PACKAGE_HEADER + "rules:\n"
        "  rule_x:\n"
        "    id: rule_x\n"
        "    condition:\n"
        "      operator: AT_LEAST_N\n"
        "      threshold: two\n"
        "      operands: [{kind: FLAG, variable_ref: flag_y, expected: true}]\n"
        "    action_refs: [act_decide]\n"
        "    provenance: {derivation: SOURCE_STATED}\n"
    )
    with pytest.raises(ValueError, match="threshold must be an integer"):
        load_package(text)


def test_load_rejects_scalar_membership_values() -> None:
    text = (
        _RULE_PACKAGE_HEADER + "rules:\n"
        "  rule_x:\n"
        "    id: rule_x\n"
        "    condition: {kind: MEMBERSHIP, variable_ref: category_z, values: alpha}\n"
        "    action_refs: [act_decide]\n"
        "    provenance: {derivation: SOURCE_STATED}\n"
    )
    with pytest.raises(ValueError, match=r"Condition\.values must be a list"):
        load_package(text)


def test_load_rejects_non_list_exceptions() -> None:
    text = (
        _RULE_PACKAGE_HEADER + "rules:\n"
        "  rule_x:\n"
        "    id: rule_x\n"
        "    condition: {kind: FLAG, variable_ref: flag_y, expected: true}\n"
        "    action_refs: [act_decide]\n"
        "    provenance: {derivation: SOURCE_STATED}\n"
        "    exceptions: single\n"
    )
    with pytest.raises(ValueError, match=r"Rule\.exceptions must be a list"):
        load_package(text)


def test_round_trip_preserves_variable_types(synthetic_package: ProtocolVersion) -> None:
    loaded = load_package(dump_package(synthetic_package))
    assert loaded.variables["count_x"].type == synthetic_package.variables["count_x"].type
    assert (
        loaded.variables["category_z"].allowed_values
        == synthetic_package.variables["category_z"].allowed_values
    )


def test_documents_survive_round_trip(synthetic_package: ProtocolVersion) -> None:
    assert synthetic_package.documents
    loaded = load_package(dump_package(synthetic_package))
    assert loaded.documents == synthetic_package.documents
    document = loaded.documents["doc_1"]
    assert document.sha256 == synthetic_package.documents["doc_1"].sha256
    assert document.file_format == "pdf"
    assert document.byte_size == SYNTHETIC_BYTE_SIZE


def test_load_tolerates_missing_documents_key() -> None:
    text = (
        _RULE_PACKAGE_HEADER + "rules:\n"
        "  rule_x:\n"
        "    id: rule_x\n"
        "    condition: {kind: FLAG, variable_ref: flag_y, expected: true}\n"
        "    action_refs: [act_decide]\n"
        "    provenance: {derivation: SOURCE_STATED, fragment_refs: [frag_1]}\n"
        "actions:\n"
        "  act_decide: {id: act_decide, type: DECISION}\n"
    )
    loaded = load_package(text)
    assert loaded.documents == {}


def test_dump_contains_documents_block(synthetic_package: ProtocolVersion) -> None:
    data = yaml.safe_load(dump_package(synthetic_package))
    assert data["documents"]["doc_1"]["document_id"] == "doc_1"
