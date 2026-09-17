"""Golden tests for the deterministic expression renderer."""

from __future__ import annotations

from cpg_tree.knowledge import (
    ComparisonOperator,
    Condition,
    ConditionKind,
    LogicalExpression,
    LogicalOperator,
    TemporalOperator,
)
from cpg_tree.views.expression import (
    expression_fingerprint,
    render_condition,
    render_operand,
)

FLAG_A = Condition(kind=ConditionKind.FLAG, variable_ref="edad_adulta", expected=True)
FLAG_B = Condition(kind=ConditionKind.FLAG, variable_ref="criterio_b", expected=False)
COMPARE = Condition(
    kind=ConditionKind.COMPARISON,
    variable_ref="bun",
    operator=ComparisonOperator.GT,
    operand=30,
)
MEMBERSHIP = Condition(
    kind=ConditionKind.MEMBERSHIP,
    variable_ref="categoria",
    values=("x", "y"),
)
TEMPORAL = Condition(
    kind=ConditionKind.TEMPORAL,
    variable_ref="afebril_horas",
    temporal_operator=TemporalOperator.AT_LEAST_FOR_LAST,
    duration_value=48,
    duration_unit="hours",
)


def test_render_comparison_conditions() -> None:
    assert (
        render_condition(
            Condition(
                kind=ConditionKind.COMPARISON,
                variable_ref="plaquetas",
                operator=ComparisonOperator.LT,
                operand=100000,
            )
        )
        == "plaquetas < 100000"
    )
    assert (
        render_condition(
            Condition(
                kind=ConditionKind.COMPARISON,
                variable_ref="curb65_score",
                operator=ComparisonOperator.GE,
                operand=2,
            )
        )
        == "curb65_score >= 2"
    )


def test_render_flag_membership_and_temporal_conditions() -> None:
    assert render_condition(FLAG_A) == "edad_adulta = true"
    assert render_condition(FLAG_B) == "criterio_b = false"
    assert render_condition(MEMBERSHIP) == "categoria IN {x, y}"
    assert render_condition(TEMPORAL) == "afebril_horas AT_LEAST_FOR_LAST 48 hours"


def test_render_or_block() -> None:
    expression = LogicalExpression(operator=LogicalOperator.OR, operands=(FLAG_A, COMPARE))
    assert render_operand(expression) == (
        "OR(\n"
        "    edad_adulta = true,\n"
        "    bun > 30\n"
        ")"
    )


def test_render_nested_blocks_preserve_nesting() -> None:
    inner = LogicalExpression(operator=LogicalOperator.OR, operands=(FLAG_A, COMPARE))
    expression = LogicalExpression(
        operator=LogicalOperator.AND,
        operands=(inner, MEMBERSHIP, TEMPORAL),
    )
    assert render_operand(expression) == (
        "AND(\n"
        "    OR(\n"
        "        edad_adulta = true,\n"
        "        bun > 30\n"
        "    ),\n"
        "    categoria IN {x, y},\n"
        "    afebril_horas AT_LEAST_FOR_LAST 48 hours\n"
        ")"
    )


def test_render_not_and_at_least_n_inline() -> None:
    not_expression = LogicalExpression(operator=LogicalOperator.NOT, operands=(FLAG_A,))
    assert render_operand(not_expression) == "NOT(edad_adulta = true)"
    at_least = LogicalExpression(
        operator=LogicalOperator.AT_LEAST_N,
        operands=(FLAG_A, COMPARE, MEMBERSHIP),
        threshold=2,
    )
    assert render_operand(at_least) == "AT_LEAST_N(2; edad_adulta = true, bun > 30, categoria IN {x, y})"


def test_render_is_deterministic() -> None:
    expression = LogicalExpression(
        operator=LogicalOperator.AND,
        operands=(FLAG_A, LogicalExpression(operator=LogicalOperator.OR, operands=(COMPARE, MEMBERSHIP))),
    )
    assert render_operand(expression) == render_operand(expression)
    assert render_operand(TEMPORAL) == render_operand(TEMPORAL)


def test_fingerprint_identifies_structurally_equal_expressions() -> None:
    first = LogicalExpression(operator=LogicalOperator.AND, operands=(FLAG_A, COMPARE))
    flag_again = Condition(kind=ConditionKind.FLAG, variable_ref="edad_adulta", expected=True)
    compare_again = Condition(
        kind=ConditionKind.COMPARISON,
        variable_ref="bun",
        operator=ComparisonOperator.GT,
        operand=30,
    )
    second = LogicalExpression(operator=LogicalOperator.AND, operands=(flag_again, compare_again))
    assert first is not second
    assert expression_fingerprint(first) == expression_fingerprint(second)


def test_fingerprint_distinguishes_different_structures() -> None:
    or_expression = LogicalExpression(operator=LogicalOperator.OR, operands=(FLAG_A, COMPARE))
    and_expression = LogicalExpression(operator=LogicalOperator.AND, operands=(FLAG_A, COMPARE))
    assert expression_fingerprint(or_expression) != expression_fingerprint(and_expression)
    assert expression_fingerprint(FLAG_A) != expression_fingerprint(FLAG_B)
    assert expression_fingerprint(MEMBERSHIP) != expression_fingerprint(TEMPORAL)


def test_fingerprint_is_stable_across_calls() -> None:
    expression = LogicalExpression(operator=LogicalOperator.OR, operands=(MEMBERSHIP, TEMPORAL))
    assert expression_fingerprint(expression) == expression_fingerprint(expression)
