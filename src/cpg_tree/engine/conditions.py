# ruff: noqa: TRY004
"""Atomic condition and operand evaluation for the deterministic engine.

Every condition evaluates against a ``Case`` to a ``TruthValue``. The engine
raises ``EngineInputError`` for case values whose type is incompatible with
the condition, and ``EngineConfigurationError`` for knowledge that is invalid
for execution. Missing and explicitly UNKNOWN case values always evaluate to
``TruthValue.UNKNOWN``; the engine never treats them as FALSE.

TRY004 is disabled for this module on purpose: engine configuration and input
errors raise ValueError subclasses by API contract, and the test suite asserts
them explicitly.
"""

from __future__ import annotations

from collections.abc import Mapping

from cpg_tree.engine.case import Case, CaseValueState
from cpg_tree.engine.errors import EngineConfigurationError, EngineInputError
from cpg_tree.engine.logic import and3, at_least_n3, not3, or3
from cpg_tree.knowledge.conditions import Condition, LogicalOperand
from cpg_tree.knowledge.enums import (
    ComparisonOperator,
    ConditionKind,
    LogicalOperator,
    TemporalOperator,
    TruthValue,
    VariableType,
)
from cpg_tree.knowledge.types import Scalar
from cpg_tree.knowledge.variables import Variable


def evaluate_condition(
    condition: Condition,
    case: Case,
    variables: Mapping[str, Variable] | None = None,
) -> TruthValue:
    """Evaluate one atomic condition against a case.

    ``variables`` is the optional variable registry:

    - When ``None``, no reference-existence, variable-type, or unit checks are
      performed; only the supplied case value is checked against the value
      type required by the condition.
    - When provided, every ``variable_ref`` must resolve to a declared
      variable, and its ``VariableType`` (and temporal unit) must be
      compatible with the condition kind; otherwise
      ``EngineConfigurationError`` is raised.
    """
    if condition.kind is ConditionKind.COMPARISON:
        return _evaluate_comparison(condition, case, variables)
    if condition.kind is ConditionKind.MEMBERSHIP:
        return _evaluate_membership(condition, case, variables)
    if condition.kind is ConditionKind.FLAG:
        return _evaluate_flag(condition, case, variables)
    return _evaluate_temporal(condition, case, variables)


def evaluate_operand(
    operand: LogicalOperand,
    case: Case,
    variables: Mapping[str, Variable] | None = None,
) -> TruthValue:
    """Evaluate a condition or logical expression to a single TruthValue."""
    if isinstance(operand, Condition):
        return evaluate_condition(operand, case, variables)
    if operand.operator is LogicalOperator.NOT:
        return not3(evaluate_operand(operand.operands[0], case, variables))
    results = tuple(evaluate_operand(child, case, variables) for child in operand.operands)
    if operand.operator is LogicalOperator.AND:
        return and3(results)
    if operand.operator is LogicalOperator.OR:
        return or3(results)
    if operand.operator is LogicalOperator.AT_LEAST_N:
        return at_least_n3(results, operand.threshold)
    raise EngineConfigurationError(f"unsupported logical operator {operand.operator!r}")


def _resolve_value(case: Case, variable_ref: str) -> Scalar:
    """Return the KNOWN value, or None for absent/UNKNOWN case entries.

    Absent variables and explicit UNKNOWN both surface as ``None`` here; call
    sites convert ``None`` to ``TruthValue.UNKNOWN``.
    """
    entry = case.values.get(variable_ref)
    if entry is None or entry.state is CaseValueState.UNKNOWN:
        return None
    return entry.value


def _require_variable(
    variables: Mapping[str, Variable] | None,
    variable_ref: str,
) -> Variable | None:
    """Resolve a variable against the registry when one is provided."""
    if variables is None:
        return None
    variable = variables.get(variable_ref)
    if variable is None:
        raise EngineConfigurationError(
            f"variable_ref {variable_ref!r} does not resolve to a declared variable"
        )
    return variable


def _require_numeric_value(value: object, condition: Condition) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EngineInputError(
            f"Condition on variable {condition.variable_ref!r} requires a numeric "
            f"value; got {type(value).__name__}"
        )
    return value


def _evaluate_comparison(
    condition: Condition,
    case: Case,
    variables: Mapping[str, Variable] | None,
) -> TruthValue:
    if condition.operator is None or condition.operand is None:
        raise EngineConfigurationError("COMPARISON conditions require an operator and operand")
    variable = _require_variable(variables, condition.variable_ref)
    if variable is not None and variable.type not in (VariableType.NUMERIC, VariableType.DURATION):
        raise EngineConfigurationError(
            f"COMPARISON requires a NUMERIC or DURATION variable; "
            f"{condition.variable_ref!r} is {variable.type.value}"
        )
    value = _resolve_value(case, condition.variable_ref)
    if value is None:
        return TruthValue.UNKNOWN
    numeric = _require_numeric_value(value, condition)
    if condition.operator is ComparisonOperator.EQ:
        satisfied = numeric == condition.operand
    elif condition.operator is ComparisonOperator.NE:
        satisfied = numeric != condition.operand
    elif condition.operator is ComparisonOperator.LT:
        satisfied = numeric < condition.operand
    elif condition.operator is ComparisonOperator.LE:
        satisfied = numeric <= condition.operand
    elif condition.operator is ComparisonOperator.GT:
        satisfied = numeric > condition.operand
    elif condition.operator is ComparisonOperator.GE:
        satisfied = numeric >= condition.operand
    else:
        raise EngineConfigurationError(f"unsupported comparison operator {condition.operator!r}")
    return TruthValue.TRUE if satisfied else TruthValue.FALSE


def _evaluate_membership(
    condition: Condition,
    case: Case,
    variables: Mapping[str, Variable] | None,
) -> TruthValue:
    if condition.values is None:
        raise EngineConfigurationError("MEMBERSHIP conditions require a values tuple")
    variable = _require_variable(variables, condition.variable_ref)
    if variable is not None and variable.type is not VariableType.CATEGORICAL:
        raise EngineConfigurationError(
            f"MEMBERSHIP requires a CATEGORICAL variable; "
            f"{condition.variable_ref!r} is {variable.type.value}"
        )
    value = _resolve_value(case, condition.variable_ref)
    if value is None:
        return TruthValue.UNKNOWN
    if not isinstance(value, str):
        raise EngineInputError(
            f"Condition on variable {condition.variable_ref!r} requires a string "
            f"value; got {type(value).__name__}"
        )
    return TruthValue.TRUE if value in condition.values else TruthValue.FALSE


def _evaluate_flag(
    condition: Condition,
    case: Case,
    variables: Mapping[str, Variable] | None,
) -> TruthValue:
    if condition.expected is None:
        raise EngineConfigurationError("FLAG conditions require an expected value")
    variable = _require_variable(variables, condition.variable_ref)
    if variable is not None and variable.type is not VariableType.BOOLEAN:
        raise EngineConfigurationError(
            f"FLAG requires a BOOLEAN variable; "
            f"{condition.variable_ref!r} is {variable.type.value}"
        )
    value = _resolve_value(case, condition.variable_ref)
    if value is None:
        return TruthValue.UNKNOWN
    if type(value) is not bool:
        raise EngineInputError(
            f"Condition on variable {condition.variable_ref!r} requires a boolean "
            f"value; got {type(value).__name__}"
        )
    return TruthValue.TRUE if value is condition.expected else TruthValue.FALSE


def _evaluate_temporal(
    condition: Condition,
    case: Case,
    variables: Mapping[str, Variable] | None,
) -> TruthValue:
    if condition.temporal_operator is None or condition.duration_value is None:
        raise EngineConfigurationError(
            "TEMPORAL conditions require a temporal_operator and duration_value"
        )
    if isinstance(condition.duration_value, bool) or not isinstance(
        condition.duration_value, (int, float)
    ):
        raise EngineConfigurationError("TEMPORAL duration_value must be int or float")
    if condition.duration_value < 0:
        raise EngineConfigurationError("TEMPORAL duration_value must not be negative")
    variable = _require_variable(variables, condition.variable_ref)
    if variable is not None:
        if variable.type is not VariableType.DURATION:
            raise EngineConfigurationError(
                f"TEMPORAL requires a DURATION variable; "
                f"{condition.variable_ref!r} is {variable.type.value}"
            )
        if (
            variable.unit is not None
            and condition.duration_unit is not None
            and variable.unit != condition.duration_unit
        ):
            raise EngineConfigurationError(
                f"TEMPORAL duration_unit {condition.duration_unit!r} does not match "
                f"variable unit {variable.unit!r}"
            )
    value = _resolve_value(case, condition.variable_ref)
    if value is None:
        return TruthValue.UNKNOWN
    numeric = _require_numeric_value(value, condition)
    if condition.temporal_operator is TemporalOperator.AT_LEAST_FOR_LAST:
        satisfied = numeric >= condition.duration_value
    elif condition.temporal_operator is TemporalOperator.WITHIN_LAST:
        satisfied = numeric <= condition.duration_value
    else:
        raise EngineConfigurationError(
            f"unsupported temporal operator {condition.temporal_operator!r}"
        )
    return TruthValue.TRUE if satisfied else TruthValue.FALSE


__all__ = ["evaluate_condition", "evaluate_operand"]
