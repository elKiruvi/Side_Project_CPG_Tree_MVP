"""Deterministic rendering of engine evaluation results.

This module presents ``EvaluationResult`` objects produced by the existing
Phase 4 engine. It never evaluates conditions itself, never mutates the
engine, the package, or the case, and never executes actions. Actions are
declarative: multiple ``PRESCRIBE`` actions attached to one matched rule are
rendered as alternatives declared by the source protocol, never as a
selection.
"""

from __future__ import annotations

from typing import Any

from cpg_tree.engine.case import Case, CaseValueState
from cpg_tree.engine.rules import EvaluationResult, RuleEvaluation, RuleOutcome
from cpg_tree.knowledge.enums import ActionType, DerivationState, TruthValue
from cpg_tree.knowledge.protocol import ProtocolVersion
from cpg_tree.knowledge.rules import Action, Rule
from cpg_tree.views._text import bullet_text, indent_text
from cpg_tree.views.expression import render_operand

_SAFETY_NOTICE = (
    "Note: deterministic mechanical evaluation of the source protocol (research "
    "prototype); not clinical advice. Declared actions were not executed."
)

_ALTERNATIVE_NOTE = (
    "    alternatives are declared by the source protocol as an OR choice; "
    "this tool never selects one"
)


def render_evaluation(
    result: EvaluationResult,
    version: ProtocolVersion,
    case: Case,
    show_expressions: bool = False,
) -> str:
    """Render an evaluation result deterministically as plain text."""
    known, unknown = _case_counts(case)
    lines = [
        f"Evaluation : {result.protocol_id} {result.version}",
        f"Case       : {len(case.values)} values provided ({known} known, {unknown} unknown)",
        "",
    ]
    for rule_result in result.rule_results:
        lines.extend(_render_rule_result(rule_result, version, show_expressions))
        lines.append("")
    lines.append(_SAFETY_NOTICE)
    return "\n".join(lines)


def evaluation_to_json(
    result: EvaluationResult,
    version: ProtocolVersion,
    case: Case,
) -> dict[str, Any]:
    """Project the evaluation result into primitives in fixed key order."""
    case_values = {
        key: entry.value if entry.state is CaseValueState.KNOWN else None
        for key, entry in sorted(case.values.items())
    }
    rule_results: list[dict[str, Any]] = []
    for rule_result in result.rule_results:
        actions: list[dict[str, Any]] = []
        for action_ref in rule_result.action_refs:
            action = version.actions.get(action_ref)
            actions.append(
                {
                    "ref": action_ref,
                    "type": action.type.value if action is not None else None,
                    "label": action.label if action is not None else None,
                    "group": "declared",
                }
            )
        if len(actions) > 1:
            actions = _mark_prescribe_alternatives(actions)
        rule_results.append(
            {
                "rule_id": rule_result.rule_id,
                "outcome": rule_result.outcome.value,
                "applies_to_result": _truth_value(rule_result.applies_to_result),
                "condition_result": rule_result.condition_result.value,
                "exception_results": [entry.value for entry in rule_result.exception_results],
                "action_refs": list(rule_result.action_refs),
                "actions": actions,
                "validation_status": rule_result.validation_status.value,
                "derivation": rule_result.provenance.derivation.value,
            }
        )
    return {
        "protocol_id": result.protocol_id,
        "version": result.version,
        "case_values": case_values,
        "rule_results": rule_results,
    }


def _case_counts(case: Case) -> tuple[int, int]:
    known = sum(1 for entry in case.values.values() if entry.state is CaseValueState.KNOWN)
    return known, len(case.values) - known


def _truth_value(value: TruthValue | None) -> str | None:
    return value.value if value is not None else None


def _render_rule_result(
    rule_result: RuleEvaluation,
    version: ProtocolVersion,
    show_expressions: bool,
) -> list[str]:
    lines = [f"{rule_result.rule_id:<40} {rule_result.outcome.value}"]
    if rule_result.applies_to_result is not None:
        lines.append(f"    applies_to : {rule_result.applies_to_result.value}")
    if rule_result.outcome is not RuleOutcome.NOT_APPLICABLE:
        lines.append(f"    condition  : {rule_result.condition_result.value}")
    if rule_result.exception_results:
        rendered = ", ".join(entry.value for entry in rule_result.exception_results)
        lines.append(f"    exceptions : {rendered}")
    reason = _reason_line(rule_result)
    if reason is not None:
        lines.append(reason)
    if show_expressions:
        rule = version.rules.get(rule_result.rule_id)
        if rule is not None:
            lines.extend(_render_expressions(rule, rule_result))
    if rule_result.outcome is RuleOutcome.MATCHED:
        lines.extend(_render_actions(rule_result, version))
    lines.append(
        f"    status     : {rule_result.validation_status.value} / "
        f"{rule_result.provenance.derivation.value}"
    )
    if rule_result.provenance.derivation is DerivationState.UNRESOLVED:
        lines.append(
            "    note       : mechanically evaluated; UNRESOLVED derivation — "
            "not validated knowledge"
        )
    return lines


def _reason_line(rule_result: RuleEvaluation) -> str | None:
    if rule_result.outcome is RuleOutcome.NOT_APPLICABLE:
        return "    reason     : applies_to evaluated FALSE (population/scope not satisfied)"
    if rule_result.outcome is RuleOutcome.EXCEPTED:
        return "    reason     : condition TRUE but an exception evaluated TRUE"
    if rule_result.outcome is RuleOutcome.INDETERMINATE:
        if rule_result.applies_to_result is TruthValue.UNKNOWN:
            return "    reason     : applies_to evaluated UNKNOWN (required information is UNKNOWN)"
        if rule_result.condition_result is TruthValue.UNKNOWN:
            return "    reason     : condition evaluated UNKNOWN (required information is UNKNOWN)"
        return "    reason     : an exception evaluated UNKNOWN (required information is UNKNOWN)"
    return None


def _render_expressions(rule: Rule, rule_result: RuleEvaluation) -> list[str]:
    lines = ["    expressions:"]
    if rule.applies_to is not None:
        value = _truth_value(rule_result.applies_to_result) or "—"
        lines.append(bullet_text(f"applies_to → {value}"))
        lines.append(indent_text(render_operand(rule.applies_to), "            "))
    value = rule_result.condition_result.value
    lines.append(bullet_text(f"condition → {value}"))
    lines.append(indent_text(render_operand(rule.condition), "            "))
    for index, exception in enumerate(rule.exceptions):
        rendered = "—"
        if index < len(rule_result.exception_results):
            rendered = rule_result.exception_results[index].value
        lines.append(bullet_text(f"exception → {rendered}"))
        lines.append(indent_text(render_operand(exception), "            "))
    return lines


def _render_actions(rule_result: RuleEvaluation, version: ProtocolVersion) -> list[str]:
    if not rule_result.action_refs:
        return ["    actions    : (none declared)"]
    resolved: list[tuple[str, Action | None]] = [
        (ref, version.actions.get(ref)) for ref in rule_result.action_refs
    ]
    prescribe = [
        action
        for _, action in resolved
        if action is not None and action.type is ActionType.PRESCRIBE
    ]
    alternatives = len(prescribe) > 1
    if alternatives:
        lines = ["    declared actions (multiple PRESCRIBE = alternatives declared by the source):"]
    else:
        lines = ["    declared actions:"]
    for ref, action in resolved:
        if action is None:
            lines.append(f"        {ref} (unresolved)")
            continue
        marker = "   [alternative]" if alternatives and action.type is ActionType.PRESCRIBE else ""
        label = action.label or "(no label)"
        lines.append(f"        {ref}: {action.type.value} — {label}{marker}")
    if alternatives:
        lines.append(_ALTERNATIVE_NOTE)
    return lines


def _mark_prescribe_alternatives(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prescribe = [entry for entry in actions if entry["type"] == ActionType.PRESCRIBE.value]
    if len(prescribe) <= 1:
        return actions
    marked: list[dict[str, Any]] = []
    for entry in actions:
        copy = dict(entry)
        if copy["type"] == ActionType.PRESCRIBE.value:
            copy["group"] = "alternatives"
        marked.append(copy)
    return marked
