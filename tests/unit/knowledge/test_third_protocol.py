"""A synthetic third protocol proves the generic model needs no protocol-specific classes."""

from __future__ import annotations

from cpg_tree.knowledge import (
    Condition,
    LogicalExpression,
    ProtocolVersion,
    Variable,
    dump_package,
    load_package,
)


def test_third_protocol_uses_only_generic_classes(
    synthetic_package: ProtocolVersion,
) -> None:
    for variable in synthetic_package.variables.values():
        assert type(variable) is Variable
    for rule in synthetic_package.rules.values():
        assert isinstance(rule.condition, Condition | LogicalExpression)
    assert synthetic_package.protocol.id == "TEST-PL-999"
    assert synthetic_package.version == "v01"


def test_third_protocol_survives_yaml_round_trip(
    synthetic_package: ProtocolVersion,
) -> None:
    loaded = load_package(dump_package(synthetic_package))
    assert loaded == synthetic_package


def test_third_protocol_covers_all_logical_operators(
    synthetic_package: ProtocolVersion,
) -> None:
    operators: set[str] = set()
    for rule in synthetic_package.rules.values():
        operators.update(_collect_operators(rule.condition))
        if rule.applies_to is not None:
            operators.update(_collect_operators(rule.applies_to))
        for exception in rule.exceptions:
            operators.update(_collect_operators(exception))
    assert operators == {"AND", "OR", "NOT", "AT_LEAST_N"}


def _collect_operators(operand: object) -> set[str]:
    if isinstance(operand, LogicalExpression):
        collected = {operand.operator.value}
        for child in operand.operands:
            collected.update(_collect_operators(child))
        return collected
    return set()


def test_third_protocol_covers_all_condition_kinds(
    synthetic_package: ProtocolVersion,
) -> None:
    kinds: set[str] = set()
    for rule in synthetic_package.rules.values():
        kinds.update(_collect_condition_kinds(rule.condition))
    assert kinds == {"COMPARISON", "MEMBERSHIP", "FLAG", "TEMPORAL"}


def _collect_condition_kinds(operand: object) -> set[str]:
    if isinstance(operand, Condition):
        return {operand.kind.value}
    if isinstance(operand, LogicalExpression):
        collected: set[str] = set()
        for child in operand.operands:
            collected.update(_collect_condition_kinds(child))
        return collected
    return set()
