"""Deterministic, protocol-agnostic rule evaluation engine.

The engine consumes the canonical knowledge model (conditions, logical
expressions, rules, variables) and evaluates it against a Case using
three-valued logic (TRUE / FALSE / UNKNOWN). It is purely mechanical:

- missing data is UNKNOWN, never FALSE;
- invalid input types raise EngineInputError;
- invalid knowledge configuration raises EngineConfigurationError;
- actions are declarative and are never executed;
- evaluation is pure: no mutation, no clock, no randomness, no I/O;
- the validation layer is never consulted and never imported.
"""

from cpg_tree.engine.case import Case, CaseValue, CaseValueState
from cpg_tree.engine.conditions import evaluate_condition, evaluate_operand
from cpg_tree.engine.errors import (
    CaseError,
    EngineConfigurationError,
    EngineError,
    EngineInputError,
)
from cpg_tree.engine.logic import and3, at_least_n3, not3, or3
from cpg_tree.engine.rules import (
    EvaluationResult,
    RuleEvaluation,
    RuleOutcome,
    evaluate_package,
    evaluate_rule,
)
from cpg_tree.engine.test_cases import TestCaseOutcome, run_test_cases

__all__ = [
    "Case",
    "CaseError",
    "CaseValue",
    "CaseValueState",
    "EngineConfigurationError",
    "EngineError",
    "EngineInputError",
    "EvaluationResult",
    "RuleEvaluation",
    "RuleOutcome",
    "TestCaseOutcome",
    "and3",
    "at_least_n3",
    "evaluate_condition",
    "evaluate_operand",
    "evaluate_package",
    "evaluate_rule",
    "not3",
    "or3",
    "run_test_cases",
]
