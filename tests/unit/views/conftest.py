"""Shared fixtures for view tests: synthetic third-protocol knowledge."""

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
    SourceDocument,
    SourceFragment,
    TemporalOperator,
    TestCase,
    TruthValue,
    ValidationItem,
    ValidationStatus,
    Variable,
    VariableType,
)

# Prevent pytest from trying to collect the imported TestCase dataclass.
TestCase.__test__ = False  # type: ignore[misc]


@pytest.fixture
def flag_true() -> Condition:
    return Condition(kind=ConditionKind.FLAG, variable_ref="flag_y", expected=True)


@pytest.fixture
def synthetic_package() -> ProtocolVersion:
    """A synthetic third-protocol package exercising every view feature."""
    return _build_synthetic_package()


def _build_synthetic_package() -> ProtocolVersion:
    protocol = Protocol(
        id="TEST-PL-999",
        name="Synthetic Protocol",
        description="Synthetic scope statement for view tests",
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
        verbatim_text="Fuente sintética: el conteo supera el umbral.",
    )
    variables = {
        "count_x": Variable(
            id="count_x",
            label="Count X",
            type=VariableType.NUMERIC,
            unit="cells",
            provenance=Provenance(DerivationState.SOURCE_STATED, ("frag_1",)),
        ),
        "flag_y": Variable(
            id="flag_y",
            label="Flag Y",
            type=VariableType.BOOLEAN,
        ),
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
    condition_compare = Condition(
        kind=ConditionKind.COMPARISON,
        variable_ref="count_x",
        operator=ComparisonOperator.GT,
        operand=100,
    )
    condition_flag = Condition(kind=ConditionKind.FLAG, variable_ref="flag_y", expected=True)
    condition_membership = Condition(
        kind=ConditionKind.MEMBERSHIP,
        variable_ref="category_z",
        values=("alpha", "beta"),
    )
    condition_temporal = Condition(
        kind=ConditionKind.TEMPORAL,
        variable_ref="span_t",
        temporal_operator=TemporalOperator.AT_LEAST_FOR_LAST,
        duration_value=48,
        duration_unit="hours",
    )
    shared_condition = LogicalExpression(
        operator=LogicalOperator.AND,
        operands=(condition_compare, condition_flag),
    )
    actions = {
        "act_request": Action(
            id="act_request",
            type=ActionType.REQUEST_TEST,
            label="Solicitar prueba sintética",
        ),
        "act_prescribe_a": Action(
            id="act_prescribe_a",
            type=ActionType.PRESCRIBE,
            label="Opción A",
        ),
        "act_prescribe_b": Action(
            id="act_prescribe_b",
            type=ActionType.PRESCRIBE,
            label="Opción B",
        ),
    }
    rules = {
        "rule_composite": Rule(
            id="rule_composite",
            condition=LogicalExpression(
                operator=LogicalOperator.OR,
                operands=(shared_condition, condition_temporal),
            ),
            action_refs=("act_request",),
            provenance=Provenance(DerivationState.SOURCE_STATED, ("frag_1",)),
            applies_to=shared_condition,
            exceptions=(condition_membership,),
            validation_status=ValidationStatus.EXTRACTED,
        ),
        "rule_alternatives": Rule(
            id="rule_alternatives",
            condition=condition_flag,
            action_refs=("act_prescribe_a", "act_prescribe_b"),
            provenance=Provenance(DerivationState.NORMALIZED, ("frag_1",), notes="tabla"),
            validation_status=ValidationStatus.EXTRACTED,
        ),
    }
    test_cases = {
        "case_1": TestCase(
            id="case_1",
            inputs={"count_x": 101, "flag_y": True},
            expected_results={"rule_composite": TruthValue.TRUE},
        ),
    }
    return ProtocolVersion(
        protocol=protocol,
        version="v01",
        approval_date="2026-01-01",
        change_summary="Synthetic change summary",
        variables=variables,
        rules=rules,
        actions=actions,
        test_cases=test_cases,
        validation_items={
            "vi_1": ValidationItem(
                id="vi_1",
                category="ambiguity",
                description="Synthetic ambiguity item",
                related_ids=("rule_alternatives",),
            ),
        },
        fragments={"frag_1": fragment},
        documents={"doc-0123456789abcdef": document},
    )
