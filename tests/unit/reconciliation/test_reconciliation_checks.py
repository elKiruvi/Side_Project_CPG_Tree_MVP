"""Reconciliation invariant checks."""

from __future__ import annotations

from cpg_tree.knowledge import (
    Action,
    ActionType,
    Condition,
    ConditionKind,
    DerivationState,
    Protocol,
    ProtocolVersion,
    Provenance,
    Rule,
    SourceFragment,
    Variable,
    VariableType,
)
from cpg_tree.reconciliation.checks import (
    FindingSeverity,
    ReconciliationReport,
    validate_reconciliation,
)
from cpg_tree.reconciliation.model import (
    ConflictRepresentation,
    ConflictResolution,
    ConflictStatus,
    EvidenceClass,
    PresentationRole,
    ReconciliationInventory,
    ReconciliationStatus,
    ReconciledCandidate,
    ReviewStatus,
    SourceConflict,
    SourceEvidenceStatus,
    SourceRepresentation,
)


def _candidate(
    candidate_id: str = "rel-test-001",
    **overrides: object,
) -> ReconciledCandidate:
    fields: dict[str, object] = {
        "candidate_id": candidate_id,
        "from_ref": "rule_a",
        "to_refs": ("rule_b",),
        "relation": "branches",
        "presentation_role": PresentationRole.FLOW,
        "branch_label": None,
        "evidence_quote": "source quote",
        "fragment_ids": ("frag_x",),
        "page": "1",
        "evidence_class": EvidenceClass.SOURCE_STATED,
        "review_status": ReviewStatus.PROPOSED,
        "reconciliation_status": ReconciliationStatus.READY_FOR_REVIEW,
        "source_representation": SourceRepresentation.TEXT,
        "source_location": None,
        "source_conflict_ids": (),
        "source_evidence_status": SourceEvidenceStatus.VERIFIED_TEXT,
        "reviewer_notes": "notes",
        "reconciliation_notes": "notes",
    }
    fields.update(overrides)
    return ReconciledCandidate(**fields)  # type: ignore[arg-type]


def _conflict(conflict_id: str = "SC-TEST-001") -> SourceConflict:
    return SourceConflict(
        conflict_id=conflict_id,
        topic="threshold disagreement",
        status=ConflictStatus.OPEN,
        resolution=ConflictResolution.UNRESOLVED,
        representations=(
            ConflictRepresentation(
                SourceRepresentation.TEXT, 4, "value >= 2", SourceEvidenceStatus.VERIFIED_TEXT
            ),
            ConflictRepresentation(
                SourceRepresentation.DIAGRAM,
                6,
                "value > 2",
                SourceEvidenceStatus.PENDING_VISUAL_CONFIRMATION,
            ),
        ),
        notes="never select a winner",
    )


def _report(
    candidates: tuple[ReconciledCandidate, ...],
    conflicts: tuple[SourceConflict, ...] = (),
    package: ProtocolVersion | None = None,
) -> ReconciliationReport:
    inventory = ReconciliationInventory(
        protocol="TEST-PL-999",
        version="v01",
        candidates=candidates,
        conflicts=conflicts,
    )
    return validate_reconciliation(inventory, package)


def _error_codes(report: ReconciliationReport) -> set[str]:
    return {
        finding.code
        for finding in report.findings
        if finding.severity is FindingSeverity.ERROR
    }


def test_valid_candidate_produces_no_errors() -> None:
    report = _report((_candidate(),))
    assert report.is_valid()
    assert report.findings == ()


def test_duplicate_candidate_ids_are_errors() -> None:
    report = _report((_candidate(), _candidate()))
    assert "RECON.DUPLICATE_CANDIDATE" in _error_codes(report)
    assert not report.is_valid()


def test_duplicate_conflict_ids_are_errors() -> None:
    report = _report((), (_conflict(), _conflict()))
    assert "RECON.DUPLICATE_CONFLICT" in _error_codes(report)


def test_inferred_evidence_cannot_be_flow() -> None:
    report = _report(
        (
            _candidate(
                evidence_class=EvidenceClass.INFERRED,
                reconciliation_status=ReconciliationStatus.INFERRED_STRUCTURE,
                presentation_role=PresentationRole.FLOW,
            ),
        )
    )
    assert "RECON.FLOW_EVIDENCE_FORBIDDEN" in _error_codes(report)


def test_unresolved_evidence_cannot_be_flow() -> None:
    report = _report(
        (
            _candidate(
                evidence_class=EvidenceClass.UNRESOLVED,
                reconciliation_status=ReconciliationStatus.GAP,
                presentation_role=PresentationRole.FLOW,
            ),
        )
    )
    assert "RECON.FLOW_EVIDENCE_FORBIDDEN" in _error_codes(report)


def test_flow_requires_evidence() -> None:
    report = _report(
        (
            _candidate(
                fragment_ids=(),
                source_location=None,
            ),
        )
    )
    assert "RECON.FLOW_WITHOUT_EVIDENCE" in _error_codes(report)


def test_inferred_evidence_must_be_flagged() -> None:
    report = _report(
        (
            _candidate(
                evidence_class=EvidenceClass.INFERRED,
                reconciliation_status=ReconciliationStatus.READY_FOR_REVIEW,
                presentation_role=PresentationRole.COMPOSITION,
            ),
        )
    )
    assert "RECON.INFERRED_NOT_FLAGGED" in _error_codes(report)


def test_unresolved_evidence_must_be_flagged() -> None:
    report = _report(
        (
            _candidate(
                evidence_class=EvidenceClass.UNRESOLVED,
                reconciliation_status=ReconciliationStatus.READY_FOR_REVIEW,
                presentation_role=PresentationRole.COMPOSITION,
            ),
        )
    )
    assert "RECON.UNRESOLVED_NOT_FLAGGED" in _error_codes(report)


def test_gap_role_requires_gap_or_unresolved_mapping() -> None:
    report = _report(
        (
            _candidate(
                evidence_class=EvidenceClass.UNRESOLVED,
                reconciliation_status=ReconciliationStatus.GAP,
                presentation_role=PresentationRole.GAP,
                relation="missing",
                to_refs=("(missing content)",),
            ),
        )
    )
    assert report.is_valid()


def test_omitted_role_and_status_must_agree() -> None:
    report = _report(
        (
            _candidate(
                presentation_role=PresentationRole.OMITTED,
                reconciliation_status=ReconciliationStatus.READY_FOR_REVIEW,
                relation="references",
                to_refs=("(procedural instruction)",),
            ),
        )
    )
    assert "RECON.ROLE_OMITTED_STATUS_MISMATCH" in _error_codes(report)


def test_rejected_status_requires_omitted_role() -> None:
    report = _report(
        (
            _candidate(
                presentation_role=PresentationRole.REFERENCE,
                reconciliation_status=ReconciliationStatus.REJECTED,
            ),
        )
    )
    assert "RECON.REJECTED_ROLE_MISMATCH" in _error_codes(report)


def test_ready_for_review_requires_proposed_review_status() -> None:
    report = _report(
        (
            _candidate(
                review_status=ReviewStatus.APPROVED,
            ),
        )
    )
    assert "RECON.READY_WITHOUT_PROPOSED_REVIEW" in _error_codes(report)


def test_gap_and_omitted_retain_evidence() -> None:
    report = _report(
        (
            _candidate(
                presentation_role=PresentationRole.GAP,
                reconciliation_status=ReconciliationStatus.GAP,
                evidence_class=EvidenceClass.UNRESOLVED,
                relation="missing",
                to_refs=("(missing)",),
                evidence_quote=" ",
                fragment_ids=(),
                reconciliation_notes=" ",
            ),
        )
    )
    assert "RECON.NO_RETAINED_EVIDENCE" in _error_codes(report)


def test_dangling_conflict_reference_is_an_error() -> None:
    report = _report(
        (_candidate(source_conflict_ids=("SC-MISSING",)),),
        conflicts=(_conflict(),),
    )
    assert "RECON.DANGLING_CONFLICT_REF" in _error_codes(report)


def test_conflict_status_requires_conflict_ref_and_safe_role() -> None:
    report = _report(
        (
            _candidate(
                reconciliation_status=ReconciliationStatus.CONFLICT,
                presentation_role=PresentationRole.COMPOSITION,
                source_conflict_ids=("SC-TEST-001",),
            ),
        ),
        conflicts=(_conflict(),),
    )
    assert report.is_valid()
    without_ref = _report(
        (
            _candidate(
                reconciliation_status=ReconciliationStatus.CONFLICT,
                presentation_role=PresentationRole.COMPOSITION,
            ),
        ),
        conflicts=(_conflict(),),
    )
    assert "RECON.CONFLICT_WITHOUT_REF" in _error_codes(without_ref)
    flow_conflict = _report(
        (
            _candidate(
                reconciliation_status=ReconciliationStatus.CONFLICT,
                presentation_role=PresentationRole.FLOW,
                source_conflict_ids=("SC-TEST-001",),
            ),
        ),
        conflicts=(_conflict(),),
    )
    assert "RECON.CONFLICT_ROLE_MISMATCH" in _error_codes(flow_conflict)


def _tiny_package() -> ProtocolVersion:
    protocol = Protocol(id="TEST-PL-999", name="Synthetic protocol")
    variable = Variable(
        id="flag_x",
        type=VariableType.BOOLEAN,
        label="Flag x",
        provenance=Provenance(DerivationState.SOURCE_STATED, ("frag_x",)),
    )
    condition = Condition(kind=ConditionKind.FLAG, variable_ref="flag_x", expected=True)
    rule_a = Rule(
        id="rule_a",
        condition=condition,
        action_refs=(),
        provenance=Provenance(DerivationState.SOURCE_STATED, ("frag_x",)),
    )
    rule_b = Rule(
        id="rule_b",
        condition=condition,
        action_refs=(),
        provenance=Provenance(DerivationState.SOURCE_STATED, ("frag_x",)),
    )
    action = Action(id="act_x", type=ActionType.REQUEST_TEST)
    fragment = SourceFragment(id="frag_x", document_id="doc_x", page=1)
    return ProtocolVersion(
        protocol=protocol,
        version="v01",
        variables={"flag_x": variable},
        rules={"rule_a": rule_a, "rule_b": rule_b},
        actions={"act_x": action},
        fragments={"frag_x": fragment},
    )


def test_unknown_canonical_ref_rejected_in_strict_mode() -> None:
    package = _tiny_package()
    report = _report(
        (
            _candidate(
                from_ref="rule_no_existe",
            ),
        ),
        package=package,
    )
    assert "RECON.UNKNOWN_CANONICAL_REF" in _error_codes(report)


def test_canonical_refs_resolve_in_strict_mode() -> None:
    package = _tiny_package()
    report = _report((_candidate(),), package=package)
    assert report.is_valid()


def test_action_refs_resolve_in_strict_mode() -> None:
    package = _tiny_package()
    report = _report(
        (_candidate(from_ref="rule_a", to_refs=("act_x",)),),
        package=package,
    )
    assert report.is_valid()


def test_terminal_pseudo_ref_is_accepted() -> None:
    package = _tiny_package()
    report = _report(
        (
            _candidate(
                relation="branches",
                branch_label="NO",
                to_refs=("TERMINAL: diagnóstico descartado",),
            ),
        ),
        package=package,
    )
    assert report.is_valid()


def test_description_ref_is_rejected_for_active_candidates() -> None:
    package = _tiny_package()
    report = _report(
        (_candidate(from_ref="(contexto de tratamiento)",),),
        package=package,
    )
    assert "RECON.UNRESOLVED_REF" in _error_codes(report)


def test_rejected_rows_skip_strict_canonical_check() -> None:
    package = _tiny_package()
    report = _report(
        (
            _candidate(
                from_ref="(condición clínica)",
                presentation_role=PresentationRole.OMITTED,
                reconciliation_status=ReconciliationStatus.REJECTED,
                relation="gates",
            ),
        ),
        package=package,
    )
    assert report.is_valid()


def test_report_is_deterministic() -> None:
    candidates = (_candidate(),)
    first = _report(candidates)
    second = _report(candidates)
    assert first == second


def test_report_metadata_matches_inventory() -> None:
    report = _report((_candidate(),))
    assert report.protocol == "TEST-PL-999"
    assert report.version == "v01"


# ---------------------------------------------------------------------------
# Presentation-safe role rules (D3 safety)
# ---------------------------------------------------------------------------


def test_branch_context_requires_branch_anchor() -> None:
    report = _report(
        (
            _candidate(
                from_ref="rule_a",
                presentation_role=PresentationRole.BRANCH_CONTEXT,
                relation="branches",
                branch_label="sin FR",
            ),
        )
    )
    assert "RECON.BRANCH_ANCHOR_REQUIRED" in _error_codes(report)


def test_branch_anchor_forbidden_in_flow() -> None:
    report = _report(
        (
            _candidate(
                from_ref="BRANCH_CONTEXT: contexto de presentación",
                presentation_role=PresentationRole.FLOW,
            ),
        )
    )
    assert "RECON.BRANCH_ANCHOR_IN_FLOW" in _error_codes(report)


def test_branch_anchor_forbidden_in_reference_and_composition() -> None:
    for role in (PresentationRole.REFERENCE, PresentationRole.COMPOSITION):
        report = _report(
            (
                _candidate(
                    from_ref="BRANCH_CONTEXT: contexto de presentación",
                    presentation_role=role,
                ),
            )
        )
        assert "RECON.BRANCH_ANCHOR_IN_ACTIVE_ROLE" in _error_codes(report)


def test_valid_branch_context_passes_strict_mode() -> None:
    package = _tiny_package()
    report = _report(
        (
            _candidate(
                from_ref="BRANCH_CONTEXT: selección empírica según FR/choque",
                to_refs=("rule_a",),
                presentation_role=PresentationRole.BRANCH_CONTEXT,
                relation="branches",
                branch_label="con choque",
            ),
        ),
        package=package,
    )
    assert report.is_valid()


def test_internal_refs_must_be_canonical_rule_and_action() -> None:
    package = _tiny_package()
    report = _report(
        (
            _candidate(
                from_ref="rule_a",
                to_refs=("act_x",),
                presentation_role=PresentationRole.INTERNAL,
                relation="attaches",
                branch_label=None,
            ),
        ),
        package=package,
    )
    assert report.is_valid()
    bad_from = _report(
        (
            _candidate(
                from_ref="flag_x",
                to_refs=("act_x",),
                presentation_role=PresentationRole.INTERNAL,
                relation="attaches",
            ),
        ),
        package=package,
    )
    assert "RECON.INTERNAL_FROM_NOT_RULE" in _error_codes(bad_from)
    bad_to = _report(
        (
            _candidate(
                from_ref="rule_a",
                to_refs=("rule_b",),
                presentation_role=PresentationRole.INTERNAL,
                relation="attaches",
            ),
        ),
        package=package,
    )
    assert "RECON.INTERNAL_TO_NOT_ACTION" in _error_codes(bad_to)


def test_exception_context_refs() -> None:
    package = _tiny_package()
    report = _report(
        (
            _candidate(
                from_ref="rule_a",
                to_refs=("EXCEPTED: destino no declarado en la fuente",),
                presentation_role=PresentationRole.EXCEPTION_CONTEXT,
                relation="excepts",
                branch_label="excepción",
            ),
        ),
        package=package,
    )
    assert report.is_valid()
    bad_from = _report(
        (
            _candidate(
                from_ref="(contexto)",
                to_refs=("rule_b",),
                presentation_role=PresentationRole.EXCEPTION_CONTEXT,
                relation="excepts",
            ),
        ),
        package=package,
    )
    assert "RECON.EXCEPTION_FROM_NOT_RULE" in _error_codes(bad_from)
    invented_terminal = _report(
        (
            _candidate(
                from_ref="rule_a",
                to_refs=("TERMINAL: estado inventado",),
                presentation_role=PresentationRole.EXCEPTION_CONTEXT,
                relation="excepts",
            ),
        ),
        package=package,
    )
    assert "RECON.EXCEPTION_TERMINAL_FORBIDDEN" in _error_codes(invented_terminal)


def test_presentation_safe_roles_require_ready_for_review() -> None:
    for role in (
        PresentationRole.INTERNAL,
        PresentationRole.EXCEPTION_CONTEXT,
        PresentationRole.BRANCH_CONTEXT,
    ):
        report = _report(
            (
                _candidate(
                    from_ref="BRANCH_CONTEXT: x" if role is PresentationRole.BRANCH_CONTEXT else "rule_a",
                    presentation_role=role,
                    reconciliation_status=ReconciliationStatus.REJECTED,
                ),
            )
        )
        assert "RECON.PRESENTATION_SAFE_STATUS_MISMATCH" in _error_codes(report)
