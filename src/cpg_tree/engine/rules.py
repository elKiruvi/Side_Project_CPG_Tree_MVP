"""Rule evaluation for the deterministic engine.

A rule is evaluated in a fixed order: applicability, condition, exceptions.
Evaluation is purely mechanical: it never executes actions, never mutates the
rule, the package, or the case, and never claims clinical validity.

Provenance contract: ``evaluate_rule`` and ``evaluate_package`` produce
mechanical evaluation results only. They do not determine whether a rule is
validated, authorized, or executable in a workflow. The rule's provenance
(including its ``DerivationState``) is carried verbatim into the result; in
particular, a rule with ``DerivationState.UNRESOLVED`` is still mechanically
evaluated, and consumers must not treat its outcome as validated knowledge.

TRY004 is disabled for this module on purpose: engine configuration errors
raise ValueError subclasses by API contract, and the test suite asserts them
explicitly.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from cpg_tree.engine.case import Case
from cpg_tree.engine.conditions import evaluate_operand
from cpg_tree.engine.errors import EngineConfigurationError
from cpg_tree.knowledge.enums import TruthValue, ValidationStatus
from cpg_tree.knowledge.protocol import ProtocolVersion
from cpg_tree.knowledge.provenance import Provenance
from cpg_tree.knowledge.rules import Rule
from cpg_tree.knowledge.variables import Variable


class RuleOutcome(StrEnum):
    """Deterministic outcome of mechanically evaluating one rule."""

    MATCHED = "MATCHED"
    NOT_MATCHED = "NOT_MATCHED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    EXCEPTED = "EXCEPTED"
    INDETERMINATE = "INDETERMINATE"


@dataclass(frozen=True, slots=True)
class RuleEvaluation:
    """Immutable mechanical evaluation result of one rule.

    ``condition_result`` is ``UNKNOWN`` when the condition was not evaluated
    because applicability already determined the outcome: UNKNOWN, never
    FALSE, marks "not evaluated". ``exception_results`` is populated only when
    the condition evaluated to TRUE. ``action_refs`` carries the rule's
    declared action refs only when the outcome is MATCHED (possibly empty);
    every other outcome carries an empty tuple. Actions are never executed.
    """

    rule_id: str
    outcome: RuleOutcome
    condition_result: TruthValue
    applies_to_result: TruthValue | None
    exception_results: tuple[TruthValue, ...]
    action_refs: tuple[str, ...]
    validation_status: ValidationStatus
    provenance: Provenance


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    """Immutable evaluation result for one protocol version.

    ``rule_results`` is ordered by rule id for deterministic output.
    """

    protocol_id: str
    version: str
    rule_results: tuple[RuleEvaluation, ...]


def evaluate_rule(
    rule: Rule,
    case: Case,
    variables: Mapping[str, Variable] | None = None,
) -> RuleEvaluation:
    """Evaluate one rule mechanically; never executes actions.

    Outcome order: applicability (applies_to), condition, exceptions.
    An UNKNOWN exception never silently allows a match. ``validation_status``
    and ``provenance`` are carried into the result but never gate evaluation.
    """
    applies_to_result: TruthValue | None = None
    if rule.applies_to is not None:
        applies_to_result = evaluate_operand(rule.applies_to, case, variables)
        if applies_to_result is TruthValue.FALSE:
            return _unevaluated_rule_result(rule, RuleOutcome.NOT_APPLICABLE, applies_to_result)
        if applies_to_result is TruthValue.UNKNOWN:
            return _unevaluated_rule_result(rule, RuleOutcome.INDETERMINATE, applies_to_result)

    condition_result = evaluate_operand(rule.condition, case, variables)
    if condition_result is not TruthValue.TRUE:
        outcome = (
            RuleOutcome.NOT_MATCHED
            if condition_result is TruthValue.FALSE
            else (RuleOutcome.INDETERMINATE)
        )
        return RuleEvaluation(
            rule_id=rule.id,
            outcome=outcome,
            condition_result=condition_result,
            applies_to_result=applies_to_result,
            exception_results=(),
            action_refs=(),
            validation_status=rule.validation_status,
            provenance=rule.provenance,
        )

    exception_results = tuple(
        evaluate_operand(exception, case, variables) for exception in rule.exceptions
    )
    if any(result is TruthValue.TRUE for result in exception_results):
        outcome = RuleOutcome.EXCEPTED
    elif any(result is TruthValue.UNKNOWN for result in exception_results):
        outcome = RuleOutcome.INDETERMINATE
    else:
        outcome = RuleOutcome.MATCHED
    return RuleEvaluation(
        rule_id=rule.id,
        outcome=outcome,
        condition_result=condition_result,
        applies_to_result=applies_to_result,
        exception_results=exception_results,
        action_refs=rule.action_refs if outcome is RuleOutcome.MATCHED else (),
        validation_status=rule.validation_status,
        provenance=rule.provenance,
    )


def _unevaluated_rule_result(
    rule: Rule,
    outcome: RuleOutcome,
    applies_to_result: TruthValue,
) -> RuleEvaluation:
    return RuleEvaluation(
        rule_id=rule.id,
        outcome=outcome,
        condition_result=TruthValue.UNKNOWN,
        applies_to_result=applies_to_result,
        exception_results=(),
        action_refs=(),
        validation_status=rule.validation_status,
        provenance=rule.provenance,
    )


def evaluate_package(version: ProtocolVersion, case: Case) -> EvaluationResult:
    """Evaluate every rule of a package deterministically.

    Results are ordered by rule id. The engine resolves the references it
    depends on itself (action refs here, variable refs during condition
    evaluation) and raises ``EngineConfigurationError`` on unresolvable ones;
    it never calls the validation layer. The package and the case are not
    mutated, no action is executed, and no clock or I/O is used.
    """
    rule_results: list[RuleEvaluation] = []
    for rule_id in sorted(version.rules):
        rule = version.rules[rule_id]
        for action_ref in rule.action_refs:
            if action_ref not in version.actions:
                raise EngineConfigurationError(
                    f"rule {rule_id!r} action_ref {action_ref!r} does not resolve "
                    "to an action in the package"
                )
        rule_results.append(evaluate_rule(rule, case, version.variables))
    return EvaluationResult(
        protocol_id=version.protocol.id,
        version=version.version,
        rule_results=tuple(rule_results),
    )


__all__ = [
    "EvaluationResult",
    "RuleEvaluation",
    "RuleOutcome",
    "evaluate_package",
    "evaluate_rule",
]
