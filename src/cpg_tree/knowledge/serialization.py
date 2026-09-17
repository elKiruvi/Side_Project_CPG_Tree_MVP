# ruff: noqa: TRY004
"""Explicit, deterministic YAML serialization for the knowledge model.

Serialization is kept separate from the domain classes. Only YAML-safe
primitives are produced or consumed: str, int, float, bool, None, list, dict.
Enums are serialized as their string values. No ``!!python/object`` tags and
no unsafe loader mechanisms are used.

TRY004 is disabled for this module on purpose: deserialization of malformed
package documents raises ValueError by API contract (Phase 1 review), not
TypeError, and the test suite asserts ValueError explicitly.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable, Mapping
from enum import StrEnum
from typing import Any

import yaml

from cpg_tree.knowledge.conditions import Condition, LogicalExpression
from cpg_tree.knowledge.enums import (
    ActionType,
    ComparisonOperator,
    ConditionKind,
    DerivationState,
    LogicalOperator,
    TemporalOperator,
    TruthValue,
    ValidationItemStatus,
    ValidationStatus,
    VariableType,
)
from cpg_tree.knowledge.protocol import Protocol, ProtocolVersion
from cpg_tree.knowledge.provenance import Provenance, SourceFragment, ValidationItem
from cpg_tree.knowledge.rules import Action, Rule
from cpg_tree.knowledge.test_case import TestCase
from cpg_tree.knowledge.variables import Variable

type _EntityBuilder[T] = Callable[[Mapping[str, Any]], T]


def to_dict(obj: object) -> dict[str, Any]:
    """Serialize a knowledge-model object into YAML-safe primitives."""
    if isinstance(obj, ProtocolVersion):
        return _package_to_dict(obj)
    if dataclasses.is_dataclass(obj):
        return _entity_to_dict(obj)
    raise ValueError(f"cannot serialize {type(obj).__name__}; expected a model object")


def from_dict(data: object) -> Any:
    """Deserialize the polymorphic condition/expression shape into model objects."""
    if not isinstance(data, Mapping):
        raise ValueError(f"cannot deserialize {type(data).__name__}; expected a mapping")
    if "kind" in data:
        return _condition_from_dict(data)
    if "operator" in data:
        return _logical_expression_from_dict(data)
    raise ValueError("cannot deserialize mapping without 'kind' or 'operator'")


def dump_package(version: ProtocolVersion) -> str:
    """Serialize a ProtocolVersion into deterministic YAML text."""
    return str(yaml.safe_dump(to_dict(version), sort_keys=False, allow_unicode=True))


def load_package(text: str) -> ProtocolVersion:
    """Deserialize YAML text produced by dump_package back into a ProtocolVersion."""
    data = yaml.safe_load(text)
    if not isinstance(data, Mapping):
        raise ValueError("package YAML root must be a mapping")
    protocol_data = data.get("protocol")
    if not isinstance(protocol_data, Mapping):
        raise ValueError("package YAML requires a 'protocol' mapping")
    version_data = data.get("version")
    if not isinstance(version_data, Mapping):
        raise ValueError("package YAML requires a 'version' mapping")
    return ProtocolVersion(
        protocol=_protocol_from_dict(protocol_data),
        version=version_data.get("version"),
        approval_date=version_data.get("approval_date"),
        change_summary=version_data.get("change_summary"),
        variables=_entity_map_from_dict(data.get("variables"), _variable_from_dict),
        rules=_entity_map_from_dict(data.get("rules"), _rule_from_dict),
        actions=_entity_map_from_dict(data.get("actions"), _action_from_dict),
        test_cases=_entity_map_from_dict(data.get("test_cases"), _test_case_from_dict),
        validation_items=_entity_map_from_dict(
            data.get("validation_items"), _validation_item_from_dict
        ),
        fragments=_entity_map_from_dict(data.get("fragments"), _fragment_from_dict),
    )


def _entity_to_dict(obj: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for field in dataclasses.fields(obj):
        value = getattr(obj, field.name)
        if value is None:
            continue
        result[field.name] = _scalarize(value)
    return result


def _scalarize(value: object) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if dataclasses.is_dataclass(value):
        return _entity_to_dict(value)
    if isinstance(value, tuple):
        return [_scalarize(item) for item in value]
    if isinstance(value, dict):
        return {key: _scalarize(item) for key, item in value.items()}
    return value


def _package_to_dict(version: ProtocolVersion) -> dict[str, Any]:
    version_block: dict[str, Any] = {"version": version.version}
    if version.approval_date is not None:
        version_block["approval_date"] = version.approval_date
    if version.change_summary is not None:
        version_block["change_summary"] = version.change_summary
    return {
        "protocol": _entity_to_dict(version.protocol),
        "version": version_block,
        "variables": _entity_map_to_dict(version.variables),
        "rules": _entity_map_to_dict(version.rules),
        "actions": _entity_map_to_dict(version.actions),
        "test_cases": _entity_map_to_dict(version.test_cases),
        "validation_items": _entity_map_to_dict(version.validation_items),
        "fragments": _entity_map_to_dict(version.fragments),
    }


def _entity_map_to_dict(mapping: Mapping[str, object]) -> dict[str, Any]:
    return {key: _entity_to_dict(value) for key, value in mapping.items()}


def _entity_map_from_dict[T](raw: object, builder: _EntityBuilder[T]) -> dict[str, T]:
    if raw is None:
        return {}
    if not isinstance(raw, Mapping):
        raise ValueError(f"expected a mapping of entries; got {type(raw).__name__}")
    result: dict[str, T] = {}
    for key, entry in raw.items():
        if not isinstance(entry, Mapping):
            raise ValueError(f"entry {key!r} must be a mapping; got {type(entry).__name__}")
        result[str(key)] = builder(entry)
    return result


def _as_tuple(raw: object, field_name: str) -> tuple[Any, ...]:
    """Require a list-like value, so strings are never silently split."""
    if not isinstance(raw, (list, tuple)):
        raise ValueError(f"{field_name} must be a list; got {type(raw).__name__}")
    return tuple(raw)


def _protocol_from_dict(data: Mapping[str, Any]) -> Protocol:
    return Protocol(
        id=data.get("id"),
        name=data.get("name"),
        description=data.get("description"),
    )


def _variable_from_dict(data: Mapping[str, Any]) -> Variable:
    allowed_values = data.get("allowed_values")
    return Variable(
        id=data.get("id"),
        label=data.get("label"),
        type=VariableType(data.get("type")),
        unit=data.get("unit"),
        allowed_values=_as_tuple(allowed_values, "Variable.allowed_values")
        if allowed_values is not None
        else None,
        description=data.get("description"),
        source_note=data.get("source_note"),
    )


def _condition_from_dict(data: Mapping[str, Any]) -> Condition:
    values = data.get("values")
    return Condition(
        kind=ConditionKind(data.get("kind")),
        variable_ref=data.get("variable_ref"),
        operator=ComparisonOperator(data.get("operator"))
        if data.get("operator") is not None
        else None,
        operand=data.get("operand"),
        values=_as_tuple(values, "Condition.values") if values is not None else None,
        expected=data.get("expected"),
        temporal_operator=TemporalOperator(data.get("temporal_operator"))
        if data.get("temporal_operator") is not None
        else None,
        duration_value=data.get("duration_value"),
        duration_unit=data.get("duration_unit"),
    )


def _logical_expression_from_dict(data: Mapping[str, Any]) -> LogicalExpression:
    operands = data.get("operands")
    if operands is None:
        raise ValueError("LogicalExpression requires 'operands'")
    operand_list = _as_tuple(operands, "LogicalExpression.operands")
    return LogicalExpression(
        operator=LogicalOperator(data.get("operator")),
        operands=tuple(from_dict(operand) for operand in operand_list),
        threshold=data.get("threshold"),
    )


def _action_from_dict(data: Mapping[str, Any]) -> Action:
    payload = data.get("payload")
    if payload is not None and not isinstance(payload, Mapping):
        raise ValueError(f"Action.payload must be a mapping; got {type(payload).__name__}")
    provenance = data.get("provenance")
    return Action(
        id=data.get("id"),
        type=ActionType(data.get("type")),
        label=data.get("label"),
        payload=dict(payload) if isinstance(payload, Mapping) else None,
        provenance=_provenance_from_dict(provenance) if isinstance(provenance, Mapping) else None,
    )


def _provenance_from_dict(data: Mapping[str, Any]) -> Provenance:
    derivation = data.get("derivation")
    if derivation is None:
        raise ValueError("Provenance requires a 'derivation' field")
    fragment_refs = data.get("fragment_refs")
    return Provenance(
        derivation=DerivationState(derivation),
        fragment_refs=_as_tuple(fragment_refs, "Provenance.fragment_refs")
        if fragment_refs is not None
        else (),
        reviewer=data.get("reviewer"),
        reviewed_at=data.get("reviewed_at"),
        notes=data.get("notes"),
    )


def _rule_from_dict(data: Mapping[str, Any]) -> Rule:
    action_refs = data.get("action_refs")
    exceptions = data.get("exceptions")
    provenance = data.get("provenance")
    if not isinstance(provenance, Mapping):
        raise ValueError("Rule requires a 'provenance' mapping")
    applies_to = data.get("applies_to")
    if applies_to is not None and not isinstance(applies_to, Mapping):
        raise ValueError(f"Rule.applies_to must be a mapping; got {type(applies_to).__name__}")
    return Rule(
        id=data.get("id"),
        condition=from_dict(data.get("condition")),
        action_refs=_as_tuple(action_refs, "Rule.action_refs") if action_refs is not None else (),
        provenance=_provenance_from_dict(provenance),
        applies_to=from_dict(applies_to) if isinstance(applies_to, Mapping) else None,
        exceptions=tuple(
            from_dict(exception)
            for exception in (
                _as_tuple(exceptions, "Rule.exceptions") if exceptions is not None else ()
            )
        ),
        validation_status=ValidationStatus(data.get("validation_status"))
        if data.get("validation_status") is not None
        else ValidationStatus.DRAFT,
        notes=data.get("notes"),
    )


def _test_case_from_dict(data: Mapping[str, Any]) -> TestCase:
    inputs = data.get("inputs")
    if inputs is not None and not isinstance(inputs, Mapping):
        raise ValueError(f"TestCase.inputs must be a mapping; got {type(inputs).__name__}")
    expected = data.get("expected_results")
    if expected is not None and not isinstance(expected, Mapping):
        raise ValueError(
            f"TestCase.expected_results must be a mapping; got {type(expected).__name__}"
        )
    return TestCase(
        id=data.get("id"),
        inputs=dict(inputs) if isinstance(inputs, Mapping) else {},
        expected_results={
            str(rule_id): TruthValue(value)
            for rule_id, value in (expected if isinstance(expected, Mapping) else {}).items()
        },
    )


def _validation_item_from_dict(data: Mapping[str, Any]) -> ValidationItem:
    related_ids = data.get("related_ids")
    return ValidationItem(
        id=data.get("id"),
        category=data.get("category"),
        description=data.get("description"),
        severity=data.get("severity"),
        related_ids=_as_tuple(related_ids, "ValidationItem.related_ids")
        if related_ids is not None
        else (),
        status=ValidationItemStatus(data.get("status"))
        if data.get("status") is not None
        else ValidationItemStatus.OPEN,
    )


def _fragment_from_dict(data: Mapping[str, Any]) -> SourceFragment:
    return SourceFragment(
        id=data.get("id"),
        document_id=data.get("document_id"),
        page=data.get("page"),
        section=data.get("section"),
        verbatim_text=data.get("verbatim_text"),
    )
