"""Shared fixtures for knowledge-model tests."""

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
    Variable,
    VariableType,
)

# Prevent pytest from trying to collect the imported TestCase dataclass.
TestCase.__test__ = False  # type: ignore[misc]

OPERAND_HIGH = 100
OPERAND_VERY_HIGH = 1000
THRESHOLD_TWO = 2
DURATION_HOURS = 48

SYNTHETIC_SHA256 = "3a1654757801b7b618661f846f8335ced6fb9e388891d6bca96f1cd81d6f5882"


@pytest.fixture
def numeric_variable() -> Variable:
    return Variable(
        id="count_x",
        label="Count X",
        type=VariableType.NUMERIC,
        unit="cells",
    )


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
    return Variable(
        id="span_t",
        label="Span T",
        type=VariableType.DURATION,
        unit="hours",
    )


@pytest.fixture
def synthetic_package() -> ProtocolVersion:
    """A synthetic third-protocol package exercising every model feature."""
    return _build_synthetic_package()


def _build_synthetic_package() -> ProtocolVersion:
    protocol = Protocol(
        id="TEST-PL-999",
        name="Synthetic Protocol",
        description="Model coverage package",
    )
    fragments = {
        "frag_1": SourceFragment(
            id="frag_1",
            document_id="doc_1",
            page=3,
            section="Diagnosis",
            verbatim_text="criterion expressed in the source text",
        ),
        "frag_2": SourceFragment(
            id="frag_2",
            document_id="doc_1",
            page=5,
            section="Management",
            verbatim_text="management recommendation",
        ),
    }
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
        "act_decide": Action(id="act_decide", type=ActionType.DECISION, label="Decide"),
        "act_classify": Action(id="act_classify", type=ActionType.CLASSIFY),
        "act_request": Action(id="act_request", type=ActionType.REQUEST_TEST),
        "act_prescribe": Action(
            id="act_prescribe",
            type=ActionType.PRESCRIBE,
            payload={"drug": "x_agent", "dose_mg": 500},
        ),
        "act_follow": Action(id="act_follow", type=ActionType.FOLLOW_UP),
        "act_admit": Action(id="act_admit", type=ActionType.ADMIT),
        "act_discharge": Action(id="act_discharge", type=ActionType.DISCHARGE),
        "act_educate": Action(id="act_educate", type=ActionType.EDUCATE),
        "act_restrict": Action(id="act_restrict", type=ActionType.RESTRICTION),
    }
    comparison = Condition(
        kind=ConditionKind.COMPARISON,
        variable_ref="count_x",
        operator=ComparisonOperator.GT,
        operand=OPERAND_HIGH,
    )
    flag_true = Condition(
        kind=ConditionKind.FLAG,
        variable_ref="flag_y",
        expected=True,
    )
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
            provenance=Provenance(
                derivation=DerivationState.SOURCE_STATED,
                fragment_refs=("frag_1",),
                reviewer="reviewer_x",
                reviewed_at="2026-09-16",
            ),
        ),
        "rule_flag": Rule(
            id="rule_flag",
            condition=flag_true,
            action_refs=("act_request",),
            provenance=Provenance(
                derivation=DerivationState.SOURCE_STATED, fragment_refs=("frag_1",)
            ),
        ),
        "rule_membership": Rule(
            id="rule_membership",
            condition=membership,
            action_refs=("act_classify",),
            applies_to=flag_true,
            provenance=Provenance(derivation=DerivationState.EXTRACTED, fragment_refs=("frag_1",)),
        ),
        "rule_temporal": Rule(
            id="rule_temporal",
            condition=temporal,
            action_refs=("act_follow",),
            provenance=Provenance(derivation=DerivationState.EXTRACTED, fragment_refs=("frag_2",)),
        ),
        "rule_composite": Rule(
            id="rule_composite",
            condition=composite,
            action_refs=("act_admit", "act_prescribe"),
            exceptions=(LogicalExpression(operator=LogicalOperator.NOT, operands=(flag_true,)),),
            provenance=Provenance(derivation=DerivationState.EXTRACTED, fragment_refs=("frag_2",)),
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
            action_refs=("act_discharge",),
            provenance=Provenance(derivation=DerivationState.EXTRACTED, fragment_refs=("frag_2",)),
        ),
        "rule_educate": Rule(
            id="rule_educate",
            condition=LogicalExpression(
                operator=LogicalOperator.AND,
                operands=(
                    Condition(
                        kind=ConditionKind.FLAG,
                        variable_ref="flag_y",
                        expected=False,
                    ),
                    Condition(
                        kind=ConditionKind.COMPARISON,
                        variable_ref="count_x",
                        operator=ComparisonOperator.LE,
                        operand=OPERAND_HIGH,
                    ),
                ),
            ),
            action_refs=("act_educate", "act_restrict"),
            provenance=Provenance(derivation=DerivationState.EXTRACTED, fragment_refs=("frag_2",)),
        ),
    }
    test_cases = {
        "tc_full": TestCase(
            id="tc_full",
            inputs={"count_x": 101, "flag_y": True, "category_z": "alpha", "span_t": 48},
            expected_results={
                "rule_compare": TruthValue.TRUE,
                "rule_composite": TruthValue.TRUE,
                "rule_temporal": TruthValue.TRUE,
            },
        ),
        "tc_missing": TestCase(
            id="tc_missing",
            inputs={"count_x": 101, "flag_y": False, "category_z": None, "span_t": None},
            expected_results={
                "rule_membership": TruthValue.UNKNOWN,
                "rule_temporal": TruthValue.UNKNOWN,
            },
        ),
    }
    validation_items = {
        "vi_1": ValidationItem(
            id="vi_1",
            category="ambiguity",
            description="synthetic open item",
            severity="high",
            related_ids=("rule_compare",),
        )
    }
    return ProtocolVersion(
        protocol=protocol,
        version="v01",
        approval_date="2026-01-15",
        change_summary="first synthetic version",
        variables=variables,
        rules=rules,
        actions=actions,
        test_cases=test_cases,
        validation_items=validation_items,
        fragments=fragments,
        documents={
            "doc_1": SourceDocument(
                document_id="doc_1",
                filename="synthetic_protocol.pdf",
                sha256=SYNTHETIC_SHA256,
                file_format="pdf",
                byte_size=1024,
            )
        },
    )
