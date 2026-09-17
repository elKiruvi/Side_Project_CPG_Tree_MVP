# ruff: noqa: TRY004
"""Deterministic checks for reconciliation inventories (Phase 10 D2.5).

The checks enforce the reconciliation invariants only; they never evaluate
clinical conditions and never decide whether a relationship is clinically
meaningful. ``is_valid`` means "no reconciliation invariant is broken",
nothing more.

The optional ``package`` argument enables strict mode: canonical references
of READY_FOR_REVIEW / INFERRED_STRUCTURE candidates with FLOW, REFERENCE, or
COMPOSITION roles must resolve against the package's rules, variables,
actions, and fragments. Without a package, only structural invariants run.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from cpg_tree.knowledge.protocol import ProtocolVersion
from cpg_tree.reconciliation.model import (
    FLOW_ALLOWED_EVIDENCE,
    EvidenceClass,
    PresentationRole,
    ReconciliationInventory,
    ReconciliationStatus,
    ReconciledCandidate,
    ReviewStatus,
)


class FindingSeverity(StrEnum):
    """Severity of a reconciliation finding."""

    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass(frozen=True, slots=True)
class ReconciliationFinding:
    """One machine-readable reconciliation outcome."""

    code: str
    severity: FindingSeverity
    path: str
    message: str


@dataclass(frozen=True, slots=True)
class ReconciliationReport:
    """Deterministic result of reconciling one inventory."""

    protocol: str
    version: str
    findings: tuple[ReconciliationFinding, ...]

    def is_valid(self) -> bool:
        """True when no ERROR findings exist."""
        return not any(finding.severity is FindingSeverity.ERROR for finding in self.findings)


_ACTIVE_ROLES = frozenset(
    {PresentationRole.FLOW, PresentationRole.REFERENCE, PresentationRole.COMPOSITION}
)
_PRESENTATION_SAFE_ROLES = frozenset(
    {
        PresentationRole.INTERNAL,
        PresentationRole.EXCEPTION_CONTEXT,
        PresentationRole.BRANCH_CONTEXT,
    }
)
_REVIEWABLE_ROLES = _ACTIVE_ROLES | _PRESENTATION_SAFE_ROLES
_TERMINAL_PREFIX = "TERMINAL:"
_EXCEPTED_PREFIX = "EXCEPTED:"
_BRANCH_CONTEXT_PREFIX = "BRANCH_CONTEXT:"
_DESCRIPTION_PATTERNS = ("(", "[")
_UNRESOLVED_ALLOWED_STATUSES = frozenset(
    {ReconciliationStatus.GAP, ReconciliationStatus.UNRESOLVED_MAPPING}
)
_CONFLICT_STATUS_ROLES = frozenset({PresentationRole.COMPOSITION, PresentationRole.REFERENCE})


def validate_reconciliation(
    inventory: ReconciliationInventory,
    package: ProtocolVersion | None = None,
) -> ReconciliationReport:
    """Run every reconciliation invariant and return a deterministic report."""
    findings: list[ReconciliationFinding] = []
    _check_candidate_ids(inventory, findings)
    _check_conflict_ids(inventory, findings)
    conflict_ids = {conflict.conflict_id for conflict in inventory.conflicts}
    known_ids: Mapping[str, frozenset[str]] = {}
    if package is not None:
        known_ids = {
            "rules": frozenset(package.rules),
            "variables": frozenset(package.variables),
            "actions": frozenset(package.actions),
        }
    for candidate in inventory.candidates:
        _check_candidate(candidate, inventory, conflict_ids, known_ids, findings)
    return ReconciliationReport(
        protocol=inventory.protocol,
        version=inventory.version,
        findings=tuple(findings),
    )


def _check_candidate_ids(
    inventory: ReconciliationInventory,
    findings: list[ReconciliationFinding],
) -> None:
    seen: dict[str, int] = {}
    for index, candidate in enumerate(inventory.candidates):
        previous = seen.get(candidate.candidate_id)
        if previous is not None:
            findings.append(
                ReconciliationFinding(
                    code="RECON.DUPLICATE_CANDIDATE",
                    severity=FindingSeverity.ERROR,
                    path=f"candidates[{index}]",
                    message=(
                        f"candidate id {candidate.candidate_id!r} repeats the id at "
                        f"candidates[{previous}]"
                    ),
                )
            )
        else:
            seen[candidate.candidate_id] = index


def _check_conflict_ids(
    inventory: ReconciliationInventory,
    findings: list[ReconciliationFinding],
) -> None:
    seen: dict[str, int] = {}
    for index, conflict in enumerate(inventory.conflicts):
        previous = seen.get(conflict.conflict_id)
        if previous is not None:
            findings.append(
                ReconciliationFinding(
                    code="RECON.DUPLICATE_CONFLICT",
                    severity=FindingSeverity.ERROR,
                    path=f"conflicts[{index}]",
                    message=(
                        f"conflict id {conflict.conflict_id!r} repeats the id at "
                        f"conflicts[{previous}]"
                    ),
                )
            )
        else:
            seen[conflict.conflict_id] = index


def _check_candidate(
    candidate: ReconciledCandidate,
    inventory: ReconciliationInventory,
    conflict_ids: frozenset[str],
    known_ids: Mapping[str, frozenset[str]],
    findings: list[ReconciliationFinding],
) -> None:
    path = f"candidates[{candidate.candidate_id}]"
    _check_evidence_rules(candidate, path, findings)
    _check_status_role_coherence(candidate, path, findings)
    _check_evidence_retention(candidate, path, findings)
    for conflict_id in candidate.source_conflict_ids:
        if conflict_id not in conflict_ids:
            findings.append(
                ReconciliationFinding(
                    code="RECON.DANGLING_CONFLICT_REF",
                    severity=FindingSeverity.ERROR,
                    path=path,
                    message=(
                        f"source_conflict_ids references unknown conflict {conflict_id!r} "
                        f"of {inventory.protocol} {inventory.version}"
                    ),
                )
            )
    if known_ids:
        _check_canonical_refs(candidate, path, known_ids, findings)


def _check_evidence_rules(
    candidate: ReconciledCandidate,
    path: str,
    findings: list[ReconciliationFinding],
) -> None:
    if (
        candidate.presentation_role is PresentationRole.FLOW
        and candidate.evidence_class not in FLOW_ALLOWED_EVIDENCE
    ):
        findings.append(
            ReconciliationFinding(
                code="RECON.FLOW_EVIDENCE_FORBIDDEN",
                severity=FindingSeverity.ERROR,
                path=path,
                message=(
                    f"FLOW role requires evidence class in {sorted(m.value for m in FLOW_ALLOWED_EVIDENCE)}; "
                    f"got {candidate.evidence_class.value}"
                ),
            )
        )
    if (
        candidate.presentation_role is PresentationRole.FLOW
        and not candidate.fragment_ids
        and not candidate.source_location
    ):
        findings.append(
            ReconciliationFinding(
                code="RECON.FLOW_WITHOUT_EVIDENCE",
                severity=FindingSeverity.ERROR,
                path=path,
                message="FLOW role requires at least one fragment id or a source location",
            )
        )
    if (
        candidate.evidence_class is EvidenceClass.INFERRED
        and candidate.reconciliation_status is not ReconciliationStatus.INFERRED_STRUCTURE
    ):
        findings.append(
            ReconciliationFinding(
                code="RECON.INFERRED_NOT_FLAGGED",
                severity=FindingSeverity.ERROR,
                path=path,
                message=(
                    "INFERRED evidence requires reconciliation_status INFERRED_STRUCTURE; "
                    f"got {candidate.reconciliation_status.value}"
                ),
            )
        )
    if (
        candidate.evidence_class is EvidenceClass.UNRESOLVED
        and candidate.reconciliation_status not in _UNRESOLVED_ALLOWED_STATUSES
    ):
        findings.append(
            ReconciliationFinding(
                code="RECON.UNRESOLVED_NOT_FLAGGED",
                severity=FindingSeverity.ERROR,
                path=path,
                message=(
                    "UNRESOLVED evidence requires reconciliation_status GAP or "
                    f"UNRESOLVED_MAPPING; got {candidate.reconciliation_status.value}"
                ),
            )
        )


def _check_status_role_coherence(
    candidate: ReconciledCandidate,
    path: str,
    findings: list[ReconciliationFinding],
) -> None:
    status = candidate.reconciliation_status
    role = candidate.presentation_role
    if status is ReconciliationStatus.OMITTED and role is not PresentationRole.OMITTED:
        findings.append(
            ReconciliationFinding(
                code="RECON.OMITTED_ROLE_MISMATCH",
                severity=FindingSeverity.ERROR,
                path=path,
                message=f"status OMITTED requires presentation_role OMITTED; got {role.value}",
            )
        )
    if status is ReconciliationStatus.GAP and role is not PresentationRole.GAP:
        findings.append(
            ReconciliationFinding(
                code="RECON.GAP_ROLE_MISMATCH",
                severity=FindingSeverity.ERROR,
                path=path,
                message=f"status GAP requires presentation_role GAP; got {role.value}",
            )
        )
    if role is PresentationRole.OMITTED and status not in {
        ReconciliationStatus.OMITTED,
        ReconciliationStatus.REJECTED,
    }:
        findings.append(
            ReconciliationFinding(
                code="RECON.ROLE_OMITTED_STATUS_MISMATCH",
                severity=FindingSeverity.ERROR,
                path=path,
                message=(
                    "presentation_role OMITTED requires status OMITTED or REJECTED; "
                    f"got {status.value}"
                ),
            )
        )
    if status is ReconciliationStatus.REJECTED and role is not PresentationRole.OMITTED:
        findings.append(
            ReconciliationFinding(
                code="RECON.REJECTED_ROLE_MISMATCH",
                severity=FindingSeverity.ERROR,
                path=path,
                message=f"status REJECTED requires presentation_role OMITTED; got {role.value}",
            )
        )
    if (
        status is ReconciliationStatus.READY_FOR_REVIEW
        and role in _REVIEWABLE_ROLES
        and candidate.review_status is not ReviewStatus.PROPOSED
    ):
        findings.append(
            ReconciliationFinding(
                code="RECON.READY_WITHOUT_PROPOSED_REVIEW",
                severity=FindingSeverity.ERROR,
                path=path,
                message="READY_FOR_REVIEW candidates must keep review_status PROPOSED",
            )
        )
    if role in _PRESENTATION_SAFE_ROLES and status is not ReconciliationStatus.READY_FOR_REVIEW:
        findings.append(
            ReconciliationFinding(
                code="RECON.PRESENTATION_SAFE_STATUS_MISMATCH",
                severity=FindingSeverity.ERROR,
                path=path,
                message=(
                    f"presentation role {role.value} requires status READY_FOR_REVIEW; "
                    f"got {status.value}"
                ),
            )
        )
    if role is PresentationRole.BRANCH_CONTEXT and not candidate.from_ref.startswith(
        _BRANCH_CONTEXT_PREFIX
    ):
        findings.append(
            ReconciliationFinding(
                code="RECON.BRANCH_ANCHOR_REQUIRED",
                severity=FindingSeverity.ERROR,
                path=path,
                message=(
                    "BRANCH_CONTEXT rows require a presentation-only branch anchor "
                    f"('{_BRANCH_CONTEXT_PREFIX}<text>') as 'from'"
                ),
            )
        )
    if role is PresentationRole.FLOW and (
        candidate.from_ref.startswith(_BRANCH_CONTEXT_PREFIX)
        or any(ref.startswith(_BRANCH_CONTEXT_PREFIX) for ref in candidate.to_refs)
    ):
        findings.append(
            ReconciliationFinding(
                code="RECON.BRANCH_ANCHOR_IN_FLOW",
                severity=FindingSeverity.ERROR,
                path=path,
                message=(
                    "FLOW rows must not use presentation-only branch anchors; "
                    "use BRANCH_CONTEXT role for condition-based alternatives"
                ),
            )
        )
    if role in {PresentationRole.REFERENCE, PresentationRole.COMPOSITION} and (
        candidate.from_ref.startswith(_BRANCH_CONTEXT_PREFIX)
        or any(ref.startswith(_BRANCH_CONTEXT_PREFIX) for ref in candidate.to_refs)
    ):
        findings.append(
            ReconciliationFinding(
                code="RECON.BRANCH_ANCHOR_IN_ACTIVE_ROLE",
                severity=FindingSeverity.ERROR,
                path=path,
                message=(
                    f"{role.value} rows must not use presentation-only branch anchors; "
                    "use BRANCH_CONTEXT role for condition-based alternatives"
                ),
            )
        )
    if (
        status is ReconciliationStatus.CONFLICT
        and role not in _CONFLICT_STATUS_ROLES
    ):
        findings.append(
            ReconciliationFinding(
                code="RECON.CONFLICT_ROLE_MISMATCH",
                severity=FindingSeverity.ERROR,
                path=path,
                message=(
                    "status CONFLICT requires presentation_role COMPOSITION or REFERENCE; "
                    f"got {role.value}"
                ),
            )
        )
    if (
        status is ReconciliationStatus.CONFLICT
        and not candidate.source_conflict_ids
    ):
        findings.append(
            ReconciliationFinding(
                code="RECON.CONFLICT_WITHOUT_REF",
                severity=FindingSeverity.ERROR,
                path=path,
                message="status CONFLICT requires at least one source_conflict_id",
            )
        )


def _check_evidence_retention(
    candidate: ReconciledCandidate,
    path: str,
    findings: list[ReconciliationFinding],
) -> None:
    if candidate.presentation_role not in {PresentationRole.GAP, PresentationRole.OMITTED}:
        return
    has_evidence = bool(
        candidate.fragment_ids
        or candidate.evidence_quote.strip()
        or candidate.reconciliation_notes.strip()
    )
    if not has_evidence:
        findings.append(
            ReconciliationFinding(
                code="RECON.NO_RETAINED_EVIDENCE",
                severity=FindingSeverity.ERROR,
                path=path,
                message="GAP/OMITTED candidates must retain source evidence or notes",
            )
        )


def _check_canonical_refs(
    candidate: ReconciledCandidate,
    path: str,
    known_ids: Mapping[str, frozenset[str]],
    findings: list[ReconciliationFinding],
) -> None:
    if candidate.reconciliation_status not in {
        ReconciliationStatus.READY_FOR_REVIEW,
        ReconciliationStatus.INFERRED_STRUCTURE,
    }:
        return
    role = candidate.presentation_role
    if role in _ACTIVE_ROLES:
        _check_active_refs(candidate, path, known_ids, findings)
    elif role is PresentationRole.INTERNAL:
        _check_internal_refs(candidate, path, known_ids, findings)
    elif role is PresentationRole.EXCEPTION_CONTEXT:
        _check_exception_refs(candidate, path, known_ids, findings)
    elif role is PresentationRole.BRANCH_CONTEXT:
        _check_branch_refs(candidate, path, known_ids, findings)


def _check_active_refs(
    candidate: ReconciledCandidate,
    path: str,
    known_ids: Mapping[str, frozenset[str]],
    findings: list[ReconciliationFinding],
) -> None:
    from_ref = candidate.from_ref
    if _is_description(from_ref) and not _is_pseudo_ref(from_ref):
        findings.append(
            ReconciliationFinding(
                code="RECON.UNRESOLVED_REF",
                severity=FindingSeverity.ERROR,
                path=path,
                message=(
                    f"from reference {from_ref!r} is a free-text description; "
                    "active candidates require canonical ids or TERMINAL:/EXCEPTED: pseudo-refs"
                ),
            )
        )
        return
    for label, ref in [("from", from_ref)] + [("to", ref) for ref in candidate.to_refs]:
        if _is_pseudo_ref(ref):
            continue
        if not _is_known(ref, known_ids):
            _unknown_ref_finding(label, ref, path, findings)


def _check_internal_refs(
    candidate: ReconciledCandidate,
    path: str,
    known_ids: Mapping[str, frozenset[str]],
    findings: list[ReconciliationFinding],
) -> None:
    if not _is_known_rule(candidate.from_ref, known_ids):
        findings.append(
            ReconciliationFinding(
                code="RECON.INTERNAL_FROM_NOT_RULE",
                severity=FindingSeverity.ERROR,
                path=path,
                message=(
                    f"INTERNAL rows require a canonical rule as 'from'; "
                    f"got {candidate.from_ref!r}"
                ),
            )
        )
    for ref in candidate.to_refs:
        if ref not in known_ids["actions"]:
            findings.append(
                ReconciliationFinding(
                    code="RECON.INTERNAL_TO_NOT_ACTION",
                    severity=FindingSeverity.ERROR,
                    path=path,
                    message=(
                        f"INTERNAL rows require a canonical action as 'to'; got {ref!r}"
                    ),
                )
            )


def _check_exception_refs(
    candidate: ReconciledCandidate,
    path: str,
    known_ids: Mapping[str, frozenset[str]],
    findings: list[ReconciliationFinding],
) -> None:
    if not _is_known_rule(candidate.from_ref, known_ids):
        findings.append(
            ReconciliationFinding(
                code="RECON.EXCEPTION_FROM_NOT_RULE",
                severity=FindingSeverity.ERROR,
                path=path,
                message=(
                    f"EXCEPTION_CONTEXT rows require a canonical rule as 'from'; "
                    f"got {candidate.from_ref!r}"
                ),
            )
        )
    for ref in candidate.to_refs:
        if ref.startswith(_EXCEPTED_PREFIX):
            continue
        if ref.startswith(_TERMINAL_PREFIX):
            findings.append(
                ReconciliationFinding(
                    code="RECON.EXCEPTION_TERMINAL_FORBIDDEN",
                    severity=FindingSeverity.ERROR,
                    path=path,
                    message=(
                        "EXCEPTION_CONTEXT rows must not invent a terminal destination; "
                        "the source declares no destination for this exception"
                    ),
                )
            )
            continue
        if not _is_known(ref, known_ids):
            _unknown_ref_finding("to", ref, path, findings)


def _check_branch_refs(
    candidate: ReconciledCandidate,
    path: str,
    known_ids: Mapping[str, frozenset[str]],
    findings: list[ReconciliationFinding],
) -> None:
    for ref in candidate.to_refs:
        if not _is_known(ref, known_ids):
            _unknown_ref_finding("to", ref, path, findings)


def _is_known(ref: str, known_ids: Mapping[str, frozenset[str]]) -> bool:
    return ref in known_ids["rules"] | known_ids["variables"] | known_ids["actions"]


def _is_known_rule(ref: str, known_ids: Mapping[str, frozenset[str]]) -> bool:
    return ref in known_ids["rules"]


def _unknown_ref_finding(
    label: str,
    ref: str,
    path: str,
    findings: list[ReconciliationFinding],
) -> None:
    findings.append(
        ReconciliationFinding(
            code="RECON.UNKNOWN_CANONICAL_REF",
            severity=FindingSeverity.ERROR,
            path=path,
            message=f"{label} reference {ref!r} does not resolve in the package",
        )
    )


def _is_pseudo_ref(ref: str) -> bool:
    return (
        ref.startswith(_TERMINAL_PREFIX)
        or ref.startswith(_EXCEPTED_PREFIX)
        or ref.startswith(_BRANCH_CONTEXT_PREFIX)
    )


def _is_description(ref: str) -> bool:
    return ref.startswith(_DESCRIPTION_PATTERNS) or not ref.replace("_", "a").isalnum()
