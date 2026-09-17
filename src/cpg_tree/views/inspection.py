"""Deterministic inspection views over a loaded knowledge package.

Every field shown here comes from the canonical package; nothing is invented.
In particular the model has no dedicated population/scope field (scope is the
protocol ``description``) and no page-count field (fragments carry optional
page numbers), so the views present exactly those facts.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from cpg_tree.knowledge.documents import SourceDocument
from cpg_tree.knowledge.protocol import ProtocolVersion
from cpg_tree.knowledge.serialization import to_dict
from cpg_tree.validation.model import ValidationReport
from cpg_tree.views._text import bullet_text, indent_text
from cpg_tree.views.expression import render_operand

_COUNT_KEYS = (
    "documents",
    "fragments",
    "variables",
    "rules",
    "actions",
    "test_cases",
    "validation_items",
)


@dataclass(frozen=True, slots=True)
class PackageSummary:
    """Facts about one loaded package, ready for deterministic rendering."""

    protocol_id: str
    name: str
    description: str | None
    version: str
    approval_date: str | None
    change_summary: str | None
    counts: Mapping[str, int]
    documents: tuple[SourceDocument, ...]
    rules_with_evidence: int
    rules_without_evidence: int
    fragments_with_page: int
    derivation_counts: Mapping[str, int]
    status_counts: Mapping[str, int]
    validation: ValidationReport | None


def build_summary(
    version: ProtocolVersion,
    report: ValidationReport | None = None,
) -> PackageSummary:
    """Collect the summary facts of a package without evaluating anything."""
    rules = sorted(version.rules.values(), key=lambda rule: rule.id)
    with_evidence = sum(1 for rule in rules if rule.provenance.fragment_refs)
    derivation_counts: dict[str, int] = {}
    status_counts: dict[str, int] = {}
    for rule in rules:
        derivation = rule.provenance.derivation.value
        derivation_counts[derivation] = derivation_counts.get(derivation, 0) + 1
        status = rule.validation_status.value
        status_counts[status] = status_counts.get(status, 0) + 1
    return PackageSummary(
        protocol_id=version.protocol.id,
        name=version.protocol.name,
        description=version.protocol.description,
        version=version.version,
        approval_date=version.approval_date,
        change_summary=version.change_summary,
        counts={key: len(getattr(version, key)) for key in _COUNT_KEYS},
        documents=tuple(sorted(version.documents.values(), key=lambda doc: doc.document_id)),
        rules_with_evidence=with_evidence,
        rules_without_evidence=len(rules) - with_evidence,
        fragments_with_page=sum(1 for frag in version.fragments.values() if frag.page is not None),
        derivation_counts=dict(sorted(derivation_counts.items())),
        status_counts=dict(sorted(status_counts.items())),
        validation=report,
    )


def render_summary(summary: PackageSummary) -> str:
    """Render the package summary as deterministic plain text."""
    lines = [
        f"Protocol : {summary.protocol_id} ({summary.version})",
        f"Name     : {summary.name}",
    ]
    if summary.description:
        lines.append(f"Scope    : {summary.description}")
    if summary.approval_date:
        lines.append(f"Approval : {summary.approval_date}")
    if summary.change_summary:
        lines.append(f"Change   : {summary.change_summary}")
    lines.append("")
    lines.append(f"Source documents ({len(summary.documents)}):")
    for document in summary.documents:
        size = f"{document.byte_size} bytes" if document.byte_size is not None else "unknown size"
        lines.append(
            f"  {document.document_id}  sha256: {document.sha256}  "
            f"file: {document.filename} ({document.file_format}, {size})"
        )
    lines.append("")
    lines.append("Package counts:")
    for key in _COUNT_KEYS:
        lines.append(f"  {key}: {summary.counts[key]}")
    lines.append("")
    lines.append("Provenance status:")
    total_rules = summary.rules_with_evidence + summary.rules_without_evidence
    lines.append(f"  rules with source evidence: {summary.rules_with_evidence}/{total_rules}")
    lines.append(f"  fragments with page info: {summary.fragments_with_page}")
    lines.append("  derivation: " + ", ".join(f"{k}={v}" for k, v in summary.derivation_counts.items()))
    lines.append(
        "  validation status: " + ", ".join(f"{k}={v}" for k, v in summary.status_counts.items())
    )
    lines.append("")
    lines.append(_render_validation_block(summary.validation))
    return "\n".join(lines)


def _render_validation_block(report: ValidationReport | None) -> str:
    if report is None:
        return "Validation : not run"
    valid = "yes" if report.is_valid() else "no"
    lines = [
        "Validation :",
        f"  valid: {valid}  errors: {report.error_count}  warnings: "
        f"{report.warning_count}  info: {report.info_count}",
        "  note: 'valid' means structural/provenance integrity of the package; "
        "it does not mean clinical validation",
    ]
    return "\n".join(lines)


def summary_to_json(summary: PackageSummary) -> dict[str, Any]:
    """Project the summary into YAML/JSON-safe primitives in fixed key order."""
    validation: dict[str, Any] | None = None
    if summary.validation is not None:
        validation = {
            "valid": summary.validation.is_valid(),
            "error_count": summary.validation.error_count,
            "warning_count": summary.validation.warning_count,
            "info_count": summary.validation.info_count,
        }
    return {
        "protocol_id": summary.protocol_id,
        "name": summary.name,
        "description": summary.description,
        "version": summary.version,
        "approval_date": summary.approval_date,
        "change_summary": summary.change_summary,
        "documents": [to_dict(document) for document in summary.documents],
        "counts": dict(summary.counts),
        "rules_with_evidence": summary.rules_with_evidence,
        "rules_without_evidence": summary.rules_without_evidence,
        "fragments_with_page": summary.fragments_with_page,
        "derivation_counts": dict(summary.derivation_counts),
        "status_counts": dict(summary.status_counts),
        "validation": validation,
    }


def render_variables(version: ProtocolVersion) -> str:
    """Render the knowledge variable definitions (not runtime values)."""
    lines = [f"Variables ({len(version.variables)}):"]
    for variable in sorted(version.variables.values(), key=lambda item: item.id):
        type_line = variable.type.value
        if variable.unit:
            type_line += f", unit: {variable.unit}"
        if variable.allowed_values:
            type_line += f", allowed: {', '.join(variable.allowed_values)}"
        lines.append(f"  {variable.id} [{type_line}]")
        lines.append(f"    label: {variable.label}")
        if variable.description:
            lines.append(f"    description: {variable.description}")
        if variable.source_note:
            lines.append(f"    source note: {variable.source_note}")
        if variable.provenance is not None:
            lines.append(f"    derivation: {variable.provenance.derivation.value}")
            if variable.provenance.fragment_refs:
                lines.append(f"    fragments: {', '.join(variable.provenance.fragment_refs)}")
    return "\n".join(lines)


def variables_to_json(version: ProtocolVersion) -> dict[str, Any]:
    """Project variable definitions into primitives in fixed key order."""
    return {
        "protocol_id": version.protocol.id,
        "version": version.version,
        "variables": [
            to_dict(variable)
            for variable in sorted(version.variables.values(), key=lambda item: item.id)
        ],
    }


def render_rules(version: ProtocolVersion) -> str:
    """Render one summary line per rule, ordered by rule id."""
    lines = [f"Rules ({len(version.rules)}):"]
    for rule in sorted(version.rules.values(), key=lambda item: item.id):
        applies = "yes" if rule.applies_to is not None else "no"
        lines.append(
            f"  {rule.id:<32} {rule.validation_status.value:<11} "
            f"{rule.provenance.derivation.value:<15} applies_to: {applies:<3} "
            f"exceptions: {len(rule.exceptions)}  actions: {len(rule.action_refs)}"
        )
    return "\n".join(lines)


def render_rule_detail(version: ProtocolVersion, rule_id: str) -> str:
    """Render one rule fully, presenting the engine's evaluation order."""
    rule = version.rules.get(rule_id)
    if rule is None:
        raise ValueError(f"unknown rule {rule_id!r} in protocol {version.protocol.id!r}")
    lines = [
        f"Rule : {rule.id}",
        f"  validation status : {rule.validation_status.value}",
        f"  derivation        : {rule.provenance.derivation.value}",
        "  evaluation order  : applies_to -> condition -> exceptions",
    ]
    if rule.applies_to is not None:
        lines.append("  applies_to:")
        lines.append(indent_text(render_operand(rule.applies_to), "      "))
    lines.append("  condition:")
    lines.append(indent_text(render_operand(rule.condition), "      "))
    if rule.exceptions:
        lines.append("  exceptions:")
        for exception in rule.exceptions:
            lines.append(bullet_text(render_operand(exception)))
    else:
        lines.append("  exceptions        : (none)")
    lines.append("  actions (declared):")
    for action_ref in rule.action_refs:
        action = version.actions.get(action_ref)
        if action is None:
            lines.append(f"    - {action_ref} (unresolved)")
        else:
            label = action.label or "(no label)"
            lines.append(f"    - {action_ref}: {action.type.value} — {label}")
    if not rule.action_refs:
        lines.append("    (none)")
    if rule.notes:
        lines.append(f"  notes             : {rule.notes}")
    if rule.provenance.fragment_refs:
        lines.append(f"  source fragments  : {', '.join(rule.provenance.fragment_refs)}")
    return "\n".join(lines)


def rules_to_json(version: ProtocolVersion) -> dict[str, Any]:
    """Project every rule into primitives; adds only a convenience text field."""
    rules: list[dict[str, Any]] = []
    for rule in sorted(version.rules.values(), key=lambda item: item.id):
        entry = to_dict(rule)
        entry["condition_text"] = render_operand(rule.condition)
        if rule.applies_to is not None:
            entry["applies_to_text"] = render_operand(rule.applies_to)
        if rule.exceptions:
            entry["exception_texts"] = [render_operand(e) for e in rule.exceptions]
        rules.append(entry)
    return {"protocol_id": version.protocol.id, "version": version.version, "rules": rules}
