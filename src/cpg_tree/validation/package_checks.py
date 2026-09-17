"""Package-level validation: cross-reference resolution and provenance invariants.

This module audits ``ProtocolVersion`` packages. It is pure: it never mutates
the package, never evaluates conditions, and never interprets clinical
meaning. Findings describe traceability and referential integrity only.

Checks are protocol-agnostic by construction: they operate exclusively on the
generic knowledge model (variables, rules, actions, fragments, documents,
provenance) and contain no protocol-specific knowledge.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final

from cpg_tree.knowledge.conditions import Condition, LogicalExpression, LogicalOperand
from cpg_tree.knowledge.enums import DerivationState, ValidationStatus
from cpg_tree.knowledge.protocol import ProtocolVersion
from cpg_tree.knowledge.provenance import Provenance, SourceFragment
from cpg_tree.knowledge.rules import Action, Rule
from cpg_tree.validation.model import (
    FindingSeverity,
    ValidationFinding,
    ValidationReport,
    finding_sort_key,
)

REF_UNKNOWN_FRAGMENT: Final = "REF.UNKNOWN_FRAGMENT"
REF_UNKNOWN_ACTION: Final = "REF.UNKNOWN_ACTION"
REF_UNKNOWN_VARIABLE: Final = "REF.UNKNOWN_VARIABLE"
REF_UNKNOWN_TEST_CASE_INPUT: Final = "REF.UNKNOWN_TEST_CASE_INPUT"
REF_UNKNOWN_TEST_CASE_RULE: Final = "REF.UNKNOWN_TEST_CASE_RULE"
REF_UNKNOWN_RELATED_ID: Final = "REF.UNKNOWN_RELATED_ID"

PROV_NO_DOCUMENTS_DECLARED: Final = "PROV.NO_DOCUMENTS_DECLARED"
PROV_UNKNOWN_DOCUMENT: Final = "PROV.UNKNOWN_DOCUMENT"
PROV_FRAGMENT_WITHOUT_DOCUMENT: Final = "PROV.FRAGMENT_WITHOUT_DOCUMENT"
PROV_SOURCE_STATED_NO_REFERENCE: Final = "PROV.SOURCE_STATED_NO_REFERENCE"
PROV_SOURCE_STATED_EMPTY_EVIDENCE: Final = "PROV.SOURCE_STATED_EMPTY_EVIDENCE"
PROV_NORMALIZED_NO_REFERENCE: Final = "PROV.NORMALIZED_NO_REFERENCE"
PROV_NORMALIZED_NO_TRANSFORMATION_NOTE: Final = "PROV.NORMALIZED_NO_TRANSFORMATION_NOTE"
PROV_EXTRACTED_NO_REFERENCE: Final = "PROV.EXTRACTED_NO_REFERENCE"
PROV_INFERRED_NOT_VALIDATED: Final = "PROV.INFERRED_NOT_VALIDATED"
PROV_UNRESOLVED_NOT_EXECUTABLE: Final = "PROV.UNRESOLVED_NOT_EXECUTABLE"
PROV_UNRESOLVED_CONFLICTING_STATUS: Final = "PROV.UNRESOLVED_CONFLICTING_STATUS"

_REVIEWED_OR_VALIDATED: Final = (ValidationStatus.REVIEWED, ValidationStatus.VALIDATED)


def validate_package(version: ProtocolVersion) -> ValidationReport:
    """Audit a ProtocolVersion and return its deterministic ValidationReport.

    The same package always produces the same findings in the same order. The
    report is a validation artifact: nothing here evaluates conditions, and no
    domain object is mutated.
    """
    findings: list[ValidationFinding] = []
    _check_documents(version, findings)
    _check_fragments(version, findings)
    for rule_id, rule in version.rules.items():
        _check_rule(version, rule_id, rule, findings)
    for action_id, action in version.actions.items():
        _check_action(version, action_id, action, findings)
    _check_test_cases(version, findings)
    _check_validation_items(version, findings)
    findings.sort(key=finding_sort_key)
    return ValidationReport(
        protocol_id=version.protocol.id,
        version=version.version,
        findings=tuple(findings),
    )


def _check_documents(version: ProtocolVersion, findings: list[ValidationFinding]) -> None:
    if not version.documents:
        findings.append(
            ValidationFinding(
                code=PROV_NO_DOCUMENTS_DECLARED,
                severity=FindingSeverity.WARNING,
                message="the package declares no source documents; the provenance chain "
                "cannot be closed inside the package",
            )
        )


def _check_fragments(version: ProtocolVersion, findings: list[ValidationFinding]) -> None:
    for fragment_id, fragment in version.fragments.items():
        path = f"fragments.{fragment_id}"
        if fragment.document_id is None:
            findings.append(
                ValidationFinding(
                    code=PROV_FRAGMENT_WITHOUT_DOCUMENT,
                    severity=FindingSeverity.WARNING,
                    message="fragment does not identify its source document",
                    path=path,
                )
            )
        elif version.documents and fragment.document_id not in version.documents:
            findings.append(
                ValidationFinding(
                    code=PROV_UNKNOWN_DOCUMENT,
                    severity=FindingSeverity.ERROR,
                    message=(
                        f"fragment document_id {fragment.document_id!r} does not resolve to "
                        "a document declared in the package"
                    ),
                    path=path,
                    related_ids=(fragment.document_id,),
                )
            )


def _check_rule(
    version: ProtocolVersion,
    rule_id: str,
    rule: Rule,
    findings: list[ValidationFinding],
) -> None:
    path = f"rules.{rule_id}"
    for action_ref in rule.action_refs:
        if action_ref not in version.actions:
            findings.append(
                ValidationFinding(
                    code=REF_UNKNOWN_ACTION,
                    severity=FindingSeverity.ERROR,
                    message=f"rule action_ref {action_ref!r} does not resolve to an action "
                    "in the package",
                    path=path,
                    related_ids=(action_ref,),
                )
            )
    for variable_ref in _rule_variable_refs(rule):
        if variable_ref not in version.variables:
            findings.append(
                ValidationFinding(
                    code=REF_UNKNOWN_VARIABLE,
                    severity=FindingSeverity.ERROR,
                    message=f"rule variable_ref {variable_ref!r} does not resolve to a "
                    "variable in the package",
                    path=path,
                    related_ids=(variable_ref,),
                )
            )
    provenance_path = f"{path}.provenance"
    _check_refs_resolve(rule.provenance, provenance_path, version.fragments, findings)
    _check_derivation_requirements(rule.provenance, provenance_path, version.fragments, findings)
    if (
        rule.provenance.derivation is DerivationState.UNRESOLVED
        and rule.validation_status in _REVIEWED_OR_VALIDATED
    ):
        findings.append(
            ValidationFinding(
                code=PROV_UNRESOLVED_CONFLICTING_STATUS,
                severity=FindingSeverity.ERROR,
                message=(
                    f"UNRESOLVED derivation conflicts with validation_status "
                    f"{rule.validation_status.value}"
                ),
                path=provenance_path,
                related_ids=(rule_id,),
            )
        )


def _check_action(
    version: ProtocolVersion,
    action_id: str,
    action: Action,
    findings: list[ValidationFinding],
) -> None:
    provenance = action.provenance
    if provenance is None:
        return
    path = f"actions.{action_id}.provenance"
    _check_refs_resolve(provenance, path, version.fragments, findings)
    _check_derivation_requirements(provenance, path, version.fragments, findings)


def _check_refs_resolve(
    provenance: Provenance,
    path: str,
    fragments: Mapping[str, SourceFragment],
    findings: list[ValidationFinding],
) -> None:
    for ref in provenance.fragment_refs:
        if ref not in fragments:
            findings.append(
                ValidationFinding(
                    code=REF_UNKNOWN_FRAGMENT,
                    severity=FindingSeverity.ERROR,
                    message=f"provenance references fragment {ref!r} that does not exist "
                    "in the package",
                    path=path,
                    related_ids=(ref,),
                )
            )


def _check_derivation_requirements(
    provenance: Provenance,
    path: str,
    fragments: Mapping[str, SourceFragment],
    findings: list[ValidationFinding],
) -> None:
    if provenance.derivation is DerivationState.SOURCE_STATED:
        _check_source_stated(provenance, path, fragments, findings)
    elif provenance.derivation is DerivationState.NORMALIZED:
        _check_normalized(provenance, path, findings)
    elif provenance.derivation is DerivationState.EXTRACTED:
        _check_extracted(provenance, path, findings)
    elif provenance.derivation is DerivationState.INFERRED:
        findings.append(
            ValidationFinding(
                code=PROV_INFERRED_NOT_VALIDATED,
                severity=FindingSeverity.INFO,
                message="INFERRED content is derived, not source-stated; it must not be "
                "treated as validated knowledge",
                path=path,
            )
        )
    elif provenance.derivation is DerivationState.UNRESOLVED:
        findings.append(
            ValidationFinding(
                code=PROV_UNRESOLVED_NOT_EXECUTABLE,
                severity=FindingSeverity.INFO,
                message="UNRESOLVED content must not be executed as validated knowledge",
                path=path,
            )
        )


def _check_source_stated(
    provenance: Provenance,
    path: str,
    fragments: Mapping[str, SourceFragment],
    findings: list[ValidationFinding],
) -> None:
    if not provenance.fragment_refs:
        findings.append(
            ValidationFinding(
                code=PROV_SOURCE_STATED_NO_REFERENCE,
                severity=FindingSeverity.ERROR,
                message="SOURCE_STATED provenance requires at least one fragment reference",
                path=path,
            )
        )
        return
    for ref in provenance.fragment_refs:
        fragment = fragments.get(ref)
        if fragment is not None and not (fragment.verbatim_text and fragment.verbatim_text.strip()):
            findings.append(
                ValidationFinding(
                    code=PROV_SOURCE_STATED_EMPTY_EVIDENCE,
                    severity=FindingSeverity.ERROR,
                    message=f"SOURCE_STATED provenance references fragment {ref!r} without "
                    "verbatim text evidence",
                    path=path,
                    related_ids=(ref,),
                )
            )


def _check_normalized(
    provenance: Provenance,
    path: str,
    findings: list[ValidationFinding],
) -> None:
    if not provenance.fragment_refs:
        findings.append(
            ValidationFinding(
                code=PROV_NORMALIZED_NO_REFERENCE,
                severity=FindingSeverity.ERROR,
                message="NORMALIZED provenance must retain at least one fragment reference",
                path=path,
            )
        )
    elif not provenance.notes:
        findings.append(
            ValidationFinding(
                code=PROV_NORMALIZED_NO_TRANSFORMATION_NOTE,
                severity=FindingSeverity.WARNING,
                message="NORMALIZED provenance should document the transformation in notes",
                path=path,
            )
        )


def _check_extracted(
    provenance: Provenance,
    path: str,
    findings: list[ValidationFinding],
) -> None:
    if not provenance.fragment_refs:
        findings.append(
            ValidationFinding(
                code=PROV_EXTRACTED_NO_REFERENCE,
                severity=FindingSeverity.WARNING,
                message="EXTRACTED provenance should retain the fragment it was extracted from",
                path=path,
            )
        )


def _rule_variable_refs(rule: Rule) -> set[str]:
    refs: set[str] = set()
    refs.update(_operand_variable_refs(rule.condition))
    if rule.applies_to is not None:
        refs.update(_operand_variable_refs(rule.applies_to))
    for exception in rule.exceptions:
        refs.update(_operand_variable_refs(exception))
    return refs


def _operand_variable_refs(operand: LogicalOperand) -> set[str]:
    if isinstance(operand, Condition):
        return {operand.variable_ref}
    refs: set[str] = set()
    for child in operand.operands:
        refs.update(_operand_variable_refs(child))
    return refs


def _check_test_cases(version: ProtocolVersion, findings: list[ValidationFinding]) -> None:
    for test_case_id, test_case in version.test_cases.items():
        path = f"test_cases.{test_case_id}"
        for variable_ref in test_case.inputs:
            if variable_ref not in version.variables:
                findings.append(
                    ValidationFinding(
                        code=REF_UNKNOWN_TEST_CASE_INPUT,
                        severity=FindingSeverity.ERROR,
                        message=f"test case input {variable_ref!r} does not resolve to a "
                        "variable in the package",
                        path=path,
                        related_ids=(variable_ref,),
                    )
                )
        for rule_ref in test_case.expected_results:
            if rule_ref not in version.rules:
                findings.append(
                    ValidationFinding(
                        code=REF_UNKNOWN_TEST_CASE_RULE,
                        severity=FindingSeverity.ERROR,
                        message=f"test case expected result {rule_ref!r} does not resolve "
                        "to a rule in the package",
                        path=path,
                        related_ids=(rule_ref,),
                    )
                )


def _check_validation_items(
    version: ProtocolVersion,
    findings: list[ValidationFinding],
) -> None:
    known_ids: set[str] = set()
    known_ids.update(version.variables)
    known_ids.update(version.rules)
    known_ids.update(version.actions)
    known_ids.update(version.test_cases)
    known_ids.update(version.validation_items)
    known_ids.update(version.fragments)
    for item_id, item in version.validation_items.items():
        path = f"validation_items.{item_id}"
        for related in item.related_ids:
            if related not in known_ids:
                findings.append(
                    ValidationFinding(
                        code=REF_UNKNOWN_RELATED_ID,
                        severity=FindingSeverity.ERROR,
                        message=f"validation item related_id {related!r} does not resolve "
                        "to any element in the package",
                        path=path,
                        related_ids=(related,),
                    )
                )
