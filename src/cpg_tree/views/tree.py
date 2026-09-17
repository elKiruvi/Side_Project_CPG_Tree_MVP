"""Derived decision-tree projection over a canonical knowledge package.

The projection is a view, never a source of truth: it adds no clinical nodes
and invents no decision flow. Rules are independent in the canonical model,
so each rule appears as a top-level branch under the protocol root, ordered
by rule id (the engine's own ordering). Subexpressions that occur more than
once anywhere in the package are merged by structural fingerprint and
rendered once, with later occurrences shown as explicit references — this
preserves the canonical fact that one predicate backs several rules without
duplicating it or implying independence.

Nothing here evaluates conditions; text and JSON are purely structural.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cpg_tree.knowledge.conditions import LogicalOperand
from cpg_tree.knowledge.enums import DerivationState, ValidationStatus
from cpg_tree.knowledge.protocol import ProtocolVersion
from cpg_tree.knowledge.serialization import to_dict
from cpg_tree.views.expression import expression_fingerprint, render_operand

_POSITION_APPLIES_TO = "applies_to"
_POSITION_CONDITION = "condition"
_MIN_SHARED_USES = 2


@dataclass(frozen=True, slots=True)
class SharedExpression:
    """One structurally unique subexpression used by more than one position."""

    id: str
    fingerprint: str
    usage_count: int
    first_rule_id: str
    first_position: str
    expression: LogicalOperand


@dataclass(frozen=True, slots=True)
class RuleProjection:
    """One rule as seen by the tree: its canonical structure plus shared refs."""

    rule_id: str
    validation_status: ValidationStatus
    derivation: DerivationState
    applies_to: LogicalOperand | None
    condition: LogicalOperand
    exceptions: tuple[LogicalOperand, ...]
    action_refs: tuple[str, ...]
    fragment_refs: tuple[str, ...]
    applies_to_shared_id: str | None
    condition_shared_id: str | None
    exception_shared_ids: tuple[str | None, ...]


@dataclass(frozen=True, slots=True)
class DecisionProjection:
    """The derived tree: protocol root, shared expressions, and rule branches."""

    protocol_id: str
    version: str
    shared_expressions: tuple[SharedExpression, ...]
    rules: tuple[RuleProjection, ...]


def build_projection(version: ProtocolVersion) -> DecisionProjection:
    """Project a package into a deterministic decision structure."""
    rules = sorted(version.rules.values(), key=lambda rule: rule.id)
    counts: dict[str, int] = {}
    first_seen: dict[str, tuple[str, str]] = {}
    first_expression: dict[str, LogicalOperand] = {}

    def record(operand: LogicalOperand, rule_id: str, position: str) -> None:
        fingerprint = expression_fingerprint(operand)
        counts[fingerprint] = counts.get(fingerprint, 0) + 1
        if fingerprint not in first_seen:
            first_seen[fingerprint] = (rule_id, position)
            first_expression[fingerprint] = operand

    for rule in rules:
        if rule.applies_to is not None:
            record(rule.applies_to, rule.id, _POSITION_APPLIES_TO)
        record(rule.condition, rule.id, _POSITION_CONDITION)
        for index, exception in enumerate(rule.exceptions):
            record(exception, rule.id, f"exception:{index}")

    shared_by_fingerprint: dict[str, SharedExpression] = {}
    counter = 0
    for fingerprint, (rule_id, position) in first_seen.items():
        if counts[fingerprint] < _MIN_SHARED_USES:
            continue
        counter += 1
        shared_by_fingerprint[fingerprint] = SharedExpression(
            id=f"shared-{counter:02d}",
            fingerprint=fingerprint,
            usage_count=counts[fingerprint],
            first_rule_id=rule_id,
            first_position=position,
            expression=first_expression[fingerprint],
        )

    projections: list[RuleProjection] = []
    for rule in rules:
        projections.append(
            RuleProjection(
                rule_id=rule.id,
                validation_status=rule.validation_status,
                derivation=rule.provenance.derivation,
                applies_to=rule.applies_to,
                condition=rule.condition,
                exceptions=rule.exceptions,
                action_refs=rule.action_refs,
                fragment_refs=rule.provenance.fragment_refs,
                applies_to_shared_id=_shared_id(shared_by_fingerprint, rule.applies_to),
                condition_shared_id=_shared_id(shared_by_fingerprint, rule.condition),
                exception_shared_ids=tuple(
                    _shared_id(shared_by_fingerprint, exception) for exception in rule.exceptions
                ),
            )
        )
    return DecisionProjection(
        protocol_id=version.protocol.id,
        version=version.version,
        shared_expressions=tuple(shared_by_fingerprint.values()),
        rules=tuple(projections),
    )


def _shared_id(
    shared_by_fingerprint: dict[str, SharedExpression],
    operand: LogicalOperand | None,
) -> str | None:
    if operand is None:
        return None
    entry = shared_by_fingerprint.get(expression_fingerprint(operand))
    return entry.id if entry is not None else None


def render_projection(projection: DecisionProjection, version: ProtocolVersion) -> str:
    """Render the projection as a deterministic ASCII tree."""
    lines = [f"{projection.protocol_id} {projection.version}"]
    shared_by_id = {entry.id: entry for entry in projection.shared_expressions}
    for index, rule in enumerate(projection.rules):
        is_last = index == len(projection.rules) - 1
        node_line = (
            f"{'└── ' if is_last else '├── '}{rule.rule_id}  "
            f"[{rule.validation_status.value} / {rule.derivation.value}]"
        )
        prefix = "    " if is_last else "│   "
        children = _rule_children(rule, shared_by_id, version)
        lines.extend(_render_node(node_line, prefix, children))
    return "\n".join(lines)


def _rule_children(
    rule: RuleProjection,
    shared_by_id: dict[str, SharedExpression],
    version: ProtocolVersion,
) -> list[tuple[str, str]]:
    children: list[tuple[str, str]] = []
    if rule.applies_to is not None:
        entry = shared_by_id.get(rule.applies_to_shared_id or "")
        children.append(
            (
                "applies_to",
                _position_text(rule.applies_to, _POSITION_APPLIES_TO, rule, entry),
            )
        )
    entry = shared_by_id.get(rule.condition_shared_id or "")
    children.append(
        (
            "condition",
            _position_text(rule.condition, _POSITION_CONDITION, rule, entry),
        )
    )
    for index, exception in enumerate(rule.exceptions):
        entry = shared_by_id.get(rule.exception_shared_ids[index] or "")
        children.append(
            (
                "exception",
                _position_text(exception, f"exception:{index}", rule, entry),
            )
        )
    actions = ", ".join(f"{ref} ({_action_kind(version, ref)})" for ref in rule.action_refs)
    children.append(("actions", actions or "(none declared)"))
    return children


def _action_kind(version: ProtocolVersion, action_ref: str) -> str:
    action = version.actions.get(action_ref)
    return action.type.value if action is not None else "unresolved"


def _position_text(
    operand: LogicalOperand,
    position: str,
    rule: RuleProjection,
    entry: SharedExpression | None,
) -> str:
    if entry is None:
        return str(render_operand(operand))
    if entry.first_rule_id == rule.rule_id and entry.first_position == position:
        marker = f" [{entry.id} — used {entry.usage_count} time(s)]"
        return str(render_operand(operand)) + marker
    return f"@{entry.id} (first seen in {entry.first_rule_id})"


def _render_node(node_line: str, prefix: str, children: list[tuple[str, str]]) -> list[str]:
    lines = [node_line]
    for index, (label, content) in enumerate(children):
        is_last = index == len(children) - 1
        connector = "└── " if is_last else "├── "
        content_lines = content.splitlines()
        lines.append(f"{prefix}{connector}{label}: {content_lines[0]}")
        continuation = prefix + ("    " if is_last else "│   ")
        lines.extend(f"{continuation}{line}" for line in content_lines[1:])
    return lines


def projection_to_json(projection: DecisionProjection) -> dict[str, Any]:
    """Project the tree into primitives in fixed key order."""
    return {
        "protocol_id": projection.protocol_id,
        "version": projection.version,
        "shared_expressions": [
            {
                "id": entry.id,
                "fingerprint": entry.fingerprint,
                "usage_count": entry.usage_count,
                "first_rule_id": entry.first_rule_id,
                "first_position": entry.first_position,
                "expression": to_dict(entry.expression),
            }
            for entry in projection.shared_expressions
        ],
        "rules": [
            {
                "rule_id": rule.rule_id,
                "validation_status": rule.validation_status.value,
                "derivation": rule.derivation.value,
                "applies_to": to_dict(rule.applies_to) if rule.applies_to is not None else None,
                "applies_to_shared_id": rule.applies_to_shared_id,
                "condition": to_dict(rule.condition),
                "condition_shared_id": rule.condition_shared_id,
                "exceptions": [to_dict(exception) for exception in rule.exceptions],
                "exception_shared_ids": list(rule.exception_shared_ids),
                "action_refs": list(rule.action_refs),
                "fragment_refs": list(rule.fragment_refs),
            }
            for rule in projection.rules
        ],
    }
