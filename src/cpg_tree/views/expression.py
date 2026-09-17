"""Deterministic rendering of canonical conditions and logical expressions.

This module is a pure formatter: it converts ``Condition`` and
``LogicalExpression`` objects into human-readable text without ever
evaluating them. It is protocol-agnostic and operates exclusively on the
generic knowledge model.

``expression_fingerprint`` provides the structural-equality contract used by
derived views: two expressions built independently produce the same
fingerprint if and only if they are structurally identical (same operators,
variable refs, operands, thresholds, values, and units). Python object
identity is never involved.
"""

from __future__ import annotations

from cpg_tree.knowledge.conditions import Condition, LogicalExpression, LogicalOperand
from cpg_tree.knowledge.enums import ComparisonOperator, LogicalOperator

_INDENT = "    "

_COMPARISON_SYMBOLS: dict[ComparisonOperator, str] = {
    ComparisonOperator.EQ: "=",
    ComparisonOperator.NE: "!=",
    ComparisonOperator.LT: "<",
    ComparisonOperator.LE: "<=",
    ComparisonOperator.GT: ">",
    ComparisonOperator.GE: ">=",
}

_BLOCK_OPERATORS = (LogicalOperator.AND, LogicalOperator.OR)


def render_condition(condition: Condition) -> str:
    """Render one atomic condition as a single deterministic line."""
    if condition.operator is not None and condition.operand is not None:
        symbol = _COMPARISON_SYMBOLS[condition.operator]
        return f"{condition.variable_ref} {symbol} {condition.operand}"
    if condition.values is not None:
        values = ", ".join(condition.values)
        return f"{condition.variable_ref} IN {{{values}}}"
    if condition.expected is not None:
        rendered = "true" if condition.expected else "false"
        return f"{condition.variable_ref} = {rendered}"
    if condition.temporal_operator is not None:
        return (
            f"{condition.variable_ref} {condition.temporal_operator.value} "
            f"{condition.duration_value} {condition.duration_unit}"
        )
    raise ValueError(f"condition {condition.variable_ref!r} has no renderable fields")


def render_operand(operand: LogicalOperand) -> str:
    """Render a condition or expression preserving nesting unambiguously.

    ``AND`` and ``OR`` render as indented blocks; ``NOT`` and ``AT_LEAST_N``
    render inline. Operands always appear in their canonical tuple order, so
    identical expressions always produce identical text.
    """
    if isinstance(operand, Condition):
        return render_condition(operand)
    if operand.operator is LogicalOperator.NOT:
        return f"NOT({_render_inline(operand.operands[0])})"
    if operand.operator is LogicalOperator.AT_LEAST_N:
        items = ", ".join(_render_inline(child) for child in operand.operands)
        return f"AT_LEAST_N({operand.threshold}; {items})"
    return _render_block(operand, indent=0)


def expression_fingerprint(operand: LogicalOperand) -> str:
    """Return a stable structural fingerprint of an operand.

    The fingerprint is the ``repr`` of a canonical nested tuple built from the
    operand's fields, so it is unambiguous, deterministic, and independent of
    object identity. Structurally equal expressions share one fingerprint.
    """
    return repr(_fingerprint_form(operand))


def _fingerprint_form(operand: LogicalOperand) -> object:
    if isinstance(operand, Condition):
        return (
            "condition",
            operand.kind.value,
            operand.variable_ref,
            operand.operator.value if operand.operator is not None else None,
            operand.operand,
            operand.values,
            operand.expected,
            operand.temporal_operator.value if operand.temporal_operator is not None else None,
            operand.duration_value,
            operand.duration_unit,
        )
    return (
        "expression",
        operand.operator.value,
        operand.threshold,
        tuple(_fingerprint_form(child) for child in operand.operands),
    )


def _render_inline(operand: LogicalOperand) -> str:
    """Render any operand as a single line (used inside NOT/AT_LEAST_N)."""
    if isinstance(operand, Condition):
        return render_condition(operand)
    if operand.operator is LogicalOperator.NOT:
        return f"NOT({_render_inline(operand.operands[0])})"
    items = ", ".join(_render_inline(child) for child in operand.operands)
    if operand.operator is LogicalOperator.AT_LEAST_N:
        return f"AT_LEAST_N({operand.threshold}; {items})"
    return f"{operand.operator.value}({items})"


def _render_block(operand: LogicalOperand, indent: int) -> str:
    """Render an AND/OR expression as an indented block."""
    pad = _INDENT * indent
    lines = [f"{pad}{operand.operator.value}("]
    for index, child in enumerate(operand.operands):
        comma = "," if index < len(operand.operands) - 1 else ""
        if isinstance(child, LogicalExpression) and child.operator in _BLOCK_OPERATORS:
            block = _render_block(child, indent + 1)
        else:
            block = f"{pad}{_INDENT}{render_operand(child)}"
        lines.append(block + comma)
    lines.append(f"{pad})")
    return "\n".join(lines)
