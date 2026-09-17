"""Shared fixtures for engine tests: a synthetic third-protocol package."""

from __future__ import annotations

import pytest

from cpg_tree.knowledge import (
    Action,
    ActionType,
    ComparisonOperator,
    Condition,
    ConditionKind,
    DerivationState,
    LogicalExpression,
    LogicalOperator,
    Protocol,
    ProtocolVersion,
    Provenance,
    Rule,
    TemporalOperator,
    TestCase,
    TruthValue,
    Variable,
    VariableType,
)

# Prevent pytest from trying to collect the imported TestCase dataclass.
TestCase.__test__ = False  # type: ignore[misc]

OPERAND_HIGH = 100
OPERAND_VERY_HIGH = 1000
THRESHOLD_TWO = 2
DURATION_HOURS = 48


@pytest.fixture
def numeric_variable() -> Variable:
    return Variable(id="count_x", label="Count X", type=VariableType.NUMERIC, unit="cells")


@pytest.fixture
def flag_variable() -> Variable:
    return Variable(id="flag_y", label="Flag Y", type=VariableType.BOOLEAN)


@pytest.fixture
def categorical_variable() -> Variable:
    return Variable(
        id="category_z",
        label="Category Z",
        type=VariableType.CATEGORICAL,
        allowed_values=("alpha", "beta", "gamma"),
    )


@pytest.fixture
def duration_variable() -> Variable:
    return Variable(id="span_t", label="Span T", type=VariableType.DURATION, unit="hours")


@pytest.fixture
def synthetic_package() -> ProtocolVersion:
    """A synthetic third-protocol package exercising every engine feature."""
    return _build_synthetic_package()


def _build_synthetic_package() -> ProtocolVersion:
    protocol = Protocol(
        id="TEST-PL-999",
        name="Synthetic Protocol",
        description="Engine coverage package",
    )
    variables = {
        "count_x": Variable(
            id="count_x",
            label="Count X",
            type=VariableType.NUMERIC,
            unit="cells",
        ),
        "flag_y": Variable(id="flag_y", label="Flag Y", type=VariableType.BOOLEAN),
        "category_z": Variable(
            id="category_z",
            label="Category Z",
            type=VariableType.CATEGORICAL,
            allowed_values=("alpha", "beta", "gamma"),
        ),
        "span_t": Variable(
            id="span_t",
            label="Span T",
            type=VariableType.DURATION,
            unit="hours",
        ),
    }
    actions = {
        "act_decide": Action(id="act_decide", type=ActionType.DECISION),
        "act_classify": Action(id="act_classify", type=ActionType.CLASSIFY),
        "act_follow": Action(id="act_follow", type=ActionType.FOLLOW_UP),
    }
    comparison = Condition(
        kind=ConditionKind.COMPARISON,
        variable_ref="count_x",
        operator=ComparisonOperator.GT,
        operand=OPERAND_HIGH,
    )
    flag_true = Condition(kind=ConditionKind.FLAG, variable_ref="flag_y", expected=True)
    membership = Condition(
        kind=ConditionKind.MEMBERSHIP,
        variable_ref="category_z",
        values=("alpha", "beta"),
    )
    temporal = Condition(
        kind=ConditionKind.TEMPORAL,
        variable_ref="span_t",
        temporal_operator=TemporalOperator.AT_LEAST_FOR_LAST,
        duration_value=DURATION_HOURS,
        duration_unit="hours",
    )
    composite = LogicalExpression(
        operator=LogicalOperator.AT_LEAST_N,
        threshold=THRESHOLD_TWO,
        operands=(comparison, flag_true, membership),
    )
    rules = {
        "rule_compare": Rule(
            id="rule_compare",
            condition=comparison,
            action_refs=("act_decide",),
            provenance=Provenance(derivation=DerivationState.SOURCE_STATED),
        ),
        "rule_flag": Rule(
            id="rule_flag",
            condition=flag_true,
            action_refs=("act_classify",),
            provenance=Provenance(derivation=DerivationState.SOURCE_STATED),
        ),
        "rule_membership": Rule(
            id="rule_membership",
            condition=membership,
            action_refs=("act_classify",),
            applies_to=flag_true,
            provenance=Provenance(derivation=DerivationState.EXTRACTED),
        ),
        "rule_temporal": Rule(
            id="rule_temporal",
            condition=temporal,
            action_refs=("act_follow",),
            provenance=Provenance(derivation=DerivationState.EXTRACTED),
        ),
        "rule_composite": Rule(
            id="rule_composite",
            condition=composite,
            action_refs=("act_decide", "act_classify"),
            exceptions=(LogicalExpression(operator=LogicalOperator.NOT, operands=(flag_true,)),),
            provenance=Provenance(derivation=DerivationState.EXTRACTED),
        ),
        "rule_or": Rule(
            id="rule_or",
            condition=LogicalExpression(
                operator=LogicalOperator.OR,
                operands=(
                    Condition(
                        kind=ConditionKind.MEMBERSHIP,
                        variable_ref="category_z",
                        values=("gamma",),
                    ),
                    Condition(
                        kind=ConditionKind.COMPARISON,
                        variable_ref="count_x",
                        operator=ComparisonOperator.GE,
                        operand=OPERAND_VERY_HIGH,
                    ),
                ),
            ),
            action_refs=("act_follow",),
            provenance=Provenance(derivation=DerivationState.EXTRACTED),
        ),
        "rule_zero": Rule(
            id="rule_zero",
            condition=Condition(kind=ConditionKind.FLAG, variable_ref="flag_y", expected=False),
            action_refs=(),
            provenance=Provenance(derivation=DerivationState.SOURCE_STATED),
        ),
        "rule_unresolved": Rule(
            id="rule_unresolved",
            condition=flag_true,
            action_refs=("act_decide",),
            provenance=Provenance(derivation=DerivationState.UNRESOLVED),
        ),
    }
    test_cases = {
        "tc_full": TestCase(
            id="tc_full",
            inputs={"count_x": 101, "flag_y": True, "category_z": "alpha", "span_t": 48},
            expected_results={
                "rule_compare": TruthValue.TRUE,
                "rule_flag": TruthValue.TRUE,
                "rule_membership": TruthValue.TRUE,
                "rule_temporal": TruthValue.TRUE,
                "rule_composite": TruthValue.TRUE,
                "rule_or": TruthValue.FALSE,
                "rule_zero": TruthValue.FALSE,
                "rule_unresolved": TruthValue.TRUE,
            },
        ),
        "tc_missing": TestCase(
            id="tc_missing",
            inputs={"count_x": 101, "flag_y": None, "category_z": None, "span_t": None},
            expected_results={
                "rule_compare": TruthValue.TRUE,
                "rule_flag": TruthValue.UNKNOWN,
                "rule_membership": TruthValue.UNKNOWN,
                "rule_temporal": TruthValue.UNKNOWN,
                "rule_composite": TruthValue.UNKNOWN,
                "rule_or": TruthValue.UNKNOWN,
                "rule_zero": TruthValue.UNKNOWN,
                "rule_unresolved": TruthValue.UNKNOWN,
            },
        ),
    }
    return ProtocolVersion(
        protocol=protocol,
        version="v01",
        approval_date="2026-01-15",
        variables=variables,
        rules=rules,
        actions=actions,
        test_cases=test_cases,
    )
